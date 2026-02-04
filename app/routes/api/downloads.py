from typing import Tuple

from flask import Response, current_app, request
from marshmallow import ValidationError

from app.constants import EventType
from app.routes.api import bp
from app.schemas.download import BulkDeleteSchema, DownloadUpdateSchema
from app.services import download_service
from app.utils.api_response import api_response


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
def bulk_update_downloads() -> Tuple[Response, int]:
    json_data = request.get_json()

    # Support single item update by wrapping dict in list
    if isinstance(json_data, dict):
        json_data = [json_data]

    try:
        data = DownloadUpdateSchema(many=True).load(json_data)
        results = download_service.bulk_update_downloads(data)

        announcer = current_app.config["ANNOUNCER"]
        for res in results:
            if res.get("status") and res.get("updates"):
                # Broadcast the ID + the fields that changed
                payload = {"id": res["id"], **res["updates"]}
                announcer.announce(EventType.UPDATE, payload)

        return api_response(data=results)

    except ValidationError as err:
        return api_response(error=err.messages, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Bulk Update Error: {e}")
        return api_response(error=str(e), status_code=500)


@bp.route("/downloads", methods=["DELETE"])
def bulk_delete_downloads() -> Tuple[Response, int]:
    json_data = request.get_json()

    try:
        data = BulkDeleteSchema().load(json_data)
        deleted_ids = download_service.bulk_delete_downloads(data["ids"])

        if deleted_ids:
            announcer = current_app.config["ANNOUNCER"]
            announcer.announce(EventType.DELETE, {"deletedIds": deleted_ids})

        return api_response(data=deleted_ids)

    except ValidationError as err:
        return api_response(error=err.messages, status_code=400)

    except Exception as e:
        current_app.logger.error(f"Bulk Delete Error: {e}")
        return api_response(error=str(e), status_code=500)
