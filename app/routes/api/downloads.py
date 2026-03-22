from typing import Tuple

from flask import Response, current_app, request
from marshmallow import ValidationError

from app.constants import API_DOWNLOADS, EventType
from app.routes.api import bp
from app.schemas.download import (
    DeleteDownloadsSchema,
    DownloadUpdateSchema,
    GetDownloadsQuerySchema,
)
from app.services import download_service
from app.utils.api_response import api_response
from app.utils.logger import logger


@bp.route(API_DOWNLOADS, methods=["GET"])
def get_downloads() -> Tuple[Response, int]:
    try:
        args = GetDownloadsQuerySchema().load(request.args)
    except ValidationError as err:
        return api_response(error=str(err.messages), status_code=400)

    id_list: list[int] | None = args.get("ids")  # type: ignore
    downloads = download_service.get_downloads(id_list)

    if id_list and len(id_list) == 1 and not downloads:
        return api_response(error="Download not found", status_code=404)

    data = [d.to_dict() for d in downloads]
    return api_response(data=data)


@bp.route(API_DOWNLOADS, methods=["PATCH"])
def update_downloads() -> Tuple[Response, int]:
    json_data = request.get_json(silent=True)

    if not json_data:
        return api_response(error="Missing JSON body", status_code=400)

    try:
        data = DownloadUpdateSchema(many=True).load(json_data)
        results = download_service.update_downloads(data)  # type: ignore

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
        logger.error(f"Download update error: {e}")
        return api_response(error=str(e), status_code=500)


@bp.route(API_DOWNLOADS, methods=["DELETE"])
def delete_downloads() -> Tuple[Response, int]:
    json_data = request.get_json()

    try:
        data = DeleteDownloadsSchema().load(json_data)
        deleted_ids = download_service.delete_downloads(data["ids"])  # type: ignore

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
        logger.error(f"Download delete error: {e}")
        return api_response(error=str(e), status_code=500)
