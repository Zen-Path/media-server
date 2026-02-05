from datetime import datetime, timezone
from typing import Tuple

from flask import Response, current_app, request
from scripts.media_server.routes.api import bp
from scripts.media_server.src.utils.api_response import api_response
from scripts.media_server.src.utils.sse import event_generator

# AUTH


@bp.before_request
def require_api_key() -> None | Tuple[Response, int]:
    """
    Global authorization middleware for the API blueprint.
    """
    if request.endpoint and "health_check" in request.endpoint:
        return None

    # Check header (standard) or query string (for SSE)
    provided_key = request.headers.get("X-API-Key") or request.args.get("apiKey")
    expected_key = current_app.config.get("MEDIA_SERVER_KEY")

    if not provided_key or provided_key != expected_key:
        return api_response(error="Invalid or missing API Key", status_code=401)

    return None


# ROUTES


@bp.route("/health", methods=["GET"])
def health_check() -> Tuple[Response, int]:
    """
    Public health check endpoint.
    """
    return api_response(
        status="ok",
        data={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": current_app.config.get("APP_VERSION", ""),
        },
    )


@bp.route("/events")
def sse_events() -> Response:
    """
    Server-Sent Events (SSE) endpoint.
    """
    announcer = current_app.config["ANNOUNCER"]
    return Response(event_generator(announcer), mimetype="text/event-stream")
