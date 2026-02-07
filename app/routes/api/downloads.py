from typing import Tuple

from common.logger import logger
from flask import Response, current_app, jsonify, request
from marshmallow import ValidationError
from scripts.media_server.app.constants import DownloadStatus, EventType, MediaType
from scripts.media_server.app.extensions import db
from scripts.media_server.app.models.download import Download
from scripts.media_server.app.routes.api import bp
from scripts.media_server.app.schemas.download import BulkDeleteSchema
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
def bulk_delete_downloads() -> Tuple[Response, int]:
    json_data = request.get_json()

    try:
        data = BulkDeleteSchema().load(json_data)
        deleted_ids = download_service.bulk_delete_downloads(data["ids"])  # type: ignore

        if deleted_ids:
            try:
                current_app.config["ANNOUNCER"].announce(
                    EventType.DELETE, {"ids": deleted_ids}
                )
            except Exception as e:
                logger.warning(f"Announcer failed: {e}")

        return api_response(data={"ids": deleted_ids})

    except ValidationError as err:
        return api_response(error=str(err.messages), status_code=400)

    except Exception as e:
        logger.error(f"Bulk Delete Error: {e}")
        return api_response(error=str(e), status_code=500)
