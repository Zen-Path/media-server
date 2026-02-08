from typing import Tuple

from common.logger import logger
from flask import Response, current_app, request
from marshmallow import ValidationError
from scripts.media_server.app.constants import EventType
from scripts.media_server.app.routes.api import bp
from scripts.media_server.app.schemas.download import (
    BulkDeleteSchema,
    DownloadUpdateSchema,
)
from scripts.media_server.app.services import download_service
from scripts.media_server.app.utils.api_response import api_response


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
def bulk_edit_downloads() -> Tuple[Response, int]:
    json_data = request.get_json(silent=True)

    if not json_data:
        return api_response(error="Missing JSON body", status_code=400)

    try:
        data = DownloadUpdateSchema(many=True).load(json_data)
        results = download_service.bulk_edit_downloads(data)  # type: ignore

        updates_to_announce = [
            {"id": res["id"], **res["updates"]}
            for res in results
            if res.get("status") and res.get("updates")
        ]

        if updates_to_announce:
            try:
                current_app.config["ANNOUNCER"].announce(
                    EventType.UPDATE, updates_to_announce
                )
            except Exception as e:
                logger.warning(f"Announcer failed: {e}")

        return api_response(data=results)

    except ValidationError as err:
        return api_response(error=str(err.messages), status_code=400)

    except Exception as e:
        logger.error(f"Bulk Edit Error: {e}")
        return api_response(error=str(e), status_code=500)


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
