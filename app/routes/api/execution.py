from typing import Tuple

from flask import Response, current_app, request
from marshmallow import ValidationError

from app.constants import EventType
from app.routes.api import bp
from app.schemas.execution import DownloadRequestSchema
from app.services import execution_service
from app.utils.api_response import api_response
from app.utils.logger import logger


@bp.route("/media/download", methods=["POST"])
def execute_download() -> Tuple[Response, int]:
    """
    Trigger a media download.
    """
    json_data = request.get_json(silent=True)
    if not json_data:
        return api_response(error="Missing JSON payload", status_code=400)

    try:
        data = DownloadRequestSchema().load(json_data)
        items = data["items"]
        range_start = data.get("range_start")
        range_end = data.get("range_end")

        report, finalized_records = execution_service.process_download_request(
            items, range_start, range_end
        )

        if finalized_records:
            try:
                current_app.config["ANNOUNCER"].announce(
                    EventType.UPDATE, finalized_records
                )
            except Exception as e:
                logger.warning(f"Announcer failed: {e}")

        return api_response(data=report)

    except ValidationError as err:
        return api_response(error=str(err.messages), status_code=400)
