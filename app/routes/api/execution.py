from typing import Tuple

from flask import Response, request
from marshmallow import ValidationError

from app.routes.api import bp
from app.schemas.execution import DownloadRequestSchema
from app.services import execution_service
from app.utils.api_response import api_response


@bp.route("/download", methods=["POST"])
def execute_download() -> Tuple[Response, int]:
    """
    Trigger a media download.
    """
    json_data = request.get_json()

    try:
        data = DownloadRequestSchema().load(json_data)

        report = execution_service.process_download_request(
            urls=data["urls"],
            media_type=data["media_type"],
            range_start=data["range_start"],
            range_end=data["range_end"],
        )

        return api_response(data=report)

    except ValidationError as err:
        return api_response(error=err.messages, status_code=400)

    except Exception as e:
        return api_response(error=str(e), status_code=500)
