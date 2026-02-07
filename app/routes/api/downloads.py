from typing import Tuple

from common.logger import logger
from flask import Response, current_app, jsonify, request
from scripts.media_server.app.constants import DownloadStatus, EventType, MediaType
from scripts.media_server.app.extensions import db
from scripts.media_server.app.models.download import Download
from scripts.media_server.app.routes.api import bp
from scripts.media_server.app.services import download_service
from scripts.media_server.app.utils.api_response import api_response
from scripts.media_server.app.utils.tools import OperationResult


@bp.route("/downloads", methods=["GET"])
def get_all_downloads() -> Tuple[Response, int]:
    downloads = download_service.get_all_downloads()
    data = [d.to_dict() for d in downloads]
    return api_response(data=data)


@bp.route("/downloads/<int:download_id>", methods=["GET"])
def get_download(download_id: int) -> Tuple[Response, int]:
    download = download_service.get_download_by_id(download_id)
    if not download:
        return api_response(error="Download not found", status_code=404)
    return api_response(data=download.to_dict())


@bp.route("/bulkEdit", methods=["PATCH"])
def bulk_edit_entries():
    data = request.get_json()

    if not isinstance(data, list):
        return (
            jsonify(OperationResult(False, None, "Payload must be a list of objects")),
            400,
        )

    input_ids = [item.get("id") for item in data if item.get("id")]
    existing_downloads = Download.query.filter(Download.id.in_(input_ids)).all()

    # Create a lookup map for speed and deduplication
    download_map = {d.id: d for d in existing_downloads}

    results = []

    for item in data:
        entry_id = item.get("id")
        if not entry_id:
            results.append(OperationResult(False, None, "Missing 'id' field"))
            continue

        target = download_map.get(entry_id)
        if not target:
            results.append(OperationResult(False, entry_id, "ID not found in database"))
            continue

        try:
            has_updates = False

            if "title" in item:
                target.title = item["title"]
                has_updates = True

            if "mediaType" in item:
                media_type = item["mediaType"]
                try:
                    target.media_type = (
                        MediaType(media_type) if media_type is not None else None
                    )
                    has_updates = True
                except ValueError:
                    results.append(
                        OperationResult(
                            False, entry_id, f"Invalid mediaType: {media_type}"
                        )
                    )
                    continue

            if "status" in item:
                status = item["status"]
                try:
                    target.status = (
                        DownloadStatus(status) if status is not None else None
                    )
                    has_updates = True
                except ValueError:
                    results.append(
                        OperationResult(False, entry_id, f"Invalid status: {status}")
                    )
                    continue

            if not has_updates:
                results.append(OperationResult(False, entry_id, "No fields to update"))
                continue

            # Save changes for this specific object
            db.session.commit()
            results.append(OperationResult(True, entry_id))

            try:
                current_app.config["ANNOUNCER"].announce(
                    EventType.UPDATE, [target.to_dict()]
                )
            except Exception as e:
                logger.warning(f"Announcer failed: {e}")

        except Exception as e:
            db.session.rollback()
            results.append(OperationResult(False, entry_id, str(e)))

    master_result = OperationResult(True, results)
    return jsonify(master_result.to_dict()), 200


@bp.route("/bulkDelete", methods=["POST"])
def bulk_delete():
    data = request.get_json()
    ids = data.get("ids")

    if not ids or not isinstance(ids, list):
        return (
            jsonify(
                OperationResult(False, None, "Invalid or empty 'ids' list").to_dict()
            ),
            400,
        )

    unique_ids = list(set(ids))

    try:
        # Fetch existing records
        existing_records = Download.query.filter(Download.id.in_(unique_ids)).all()
        existing_ids = {d.id for d in existing_records}

        # Identify missing for the report
        results = []
        for entry_id in unique_ids:
            if entry_id in existing_ids:
                results.append(OperationResult(True, entry_id))
            else:
                results.append(OperationResult(False, entry_id, "Record ID not found"))

        # Bulk delete existing ones
        if existing_ids:
            Download.query.filter(Download.id.in_(list(existing_ids))).delete(
                synchronize_session=False
            )
            db.session.commit()

            # Even if notification fails, we should still delete the data.
            try:
                current_app.config["ANNOUNCER"].announce(
                    EventType.DELETE, {"ids": list(existing_ids)}
                )
            except Exception as e:
                logger.warning(f"Announcer failed: {e}")

        master_result = OperationResult(True, results)
        return jsonify(master_result.to_dict()), 200

    except Exception as e:
        db.session.rollback()
        return jsonify(OperationResult(False, None, str(e)).to_dict()), 500
