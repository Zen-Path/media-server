from typing import Tuple

from flask import Response, current_app, request
from marshmallow import ValidationError

from app.constants import EventType
from app.routes.api import bp
from app.schemas.download import (
    BulkDeleteSchema,
    DownloadBulkUpdateSchema,
    DownloadUpdateBaseSchema,
)
from app.services import download_service
from app.utils.api_response import api_response
from app.utils.logger import logger


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


@bp.route("/downloads", methods=["PATCH"])
def batch_update_downloads() -> Tuple[Response, int]:
    json_data = request.get_json(silent=True)

    if not json_data:
        return api_response(error="Missing JSON body", status_code=400)

    try:
        data = DownloadBulkUpdateSchema(many=True).load(json_data)
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


@bp.route("/downloads/<int:download_id>", methods=["PATCH"])
def update_download(download_id: int) -> Tuple[Response, int]:
    json_data = request.get_json(silent=True)

    if not json_data:
        return api_response(error="Missing JSON body", status_code=400)

    try:
        updates = DownloadUpdateBaseSchema().load(json_data)

        # Inject the ID from the URL so the service knows what to target
        updates["id"] = download_id  # type: ignore

        results = download_service.bulk_edit_downloads([updates])  # type: ignore
        result = results[0]

        if not result["status"] and result.get("error") == "ID not found":
            return api_response(error="Download not found", status_code=404)

        if result.get("status") and result.get("updates"):
            try:
                updates_to_announce = [{"id": result["id"], **result["updates"]}]
                current_app.config["ANNOUNCER"].announce(
                    EventType.UPDATE, updates_to_announce
                )
            except Exception as e:
                logger.warning(f"Announcer failed: {e}")

        return api_response(data=result)

    except ValidationError as err:
        return api_response(error=str(err.messages), status_code=400)

    except Exception as e:
        logger.error(f"Update Error: {e}")
        return api_response(error=str(e), status_code=500)


@bp.route("/downloads", methods=["DELETE"])
def batch_delete_downloads() -> Tuple[Response, int]:
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


@bp.route("/downloads/<int:download_id>", methods=["DELETE"])
def delete_download(download_id: int) -> Tuple[Response, int]:
    deleted_ids = download_service.bulk_delete_downloads([download_id])

    try:
        if deleted_ids:
            try:
                current_app.config["ANNOUNCER"].announce(
                    EventType.DELETE, {"ids": deleted_ids}
                )
            except Exception as e:
                logger.warning(f"Announcer failed: {e}")

        return api_response(data={"ids": deleted_ids})

    except Exception as e:
        logger.error(f"Delete Error: {e}")
        return api_response(error=str(e), status_code=500)
