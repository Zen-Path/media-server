import secrets
from datetime import datetime, timezone
from typing import Tuple

from flask import Response, current_app, request
from scripts.media_server.app.routes.api import bp
from scripts.media_server.app.utils.api_response import api_response

# AUTH


@bp.before_request
def require_api_key() -> None | Tuple[Response, int]:
    """
    Global authorization middleware for the API endpoints.
    """
    # Bypass health checks
    if request.endpoint and request.endpoint.endswith("health_check"):
        return None

    provided_key = request.headers.get("X-API-Key") or request.args.get("apiKey")

    # Ensure the server is actually configured
    expected_key = current_app.config.get("API_SECRET_KEY")
    if not expected_key:
        return api_response(error="Server Config: No API Key set", status_code=500)

    if not provided_key:
        return api_response(error="Missing API Key", status_code=401)

    # Use compare_digest to prevent timing attacks
    if not secrets.compare_digest(provided_key, expected_key):
        return api_response(error="Invalid API Key", status_code=401)

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
def events():
    announcer = current_app.config["ANNOUNCER"]

    def stream():
        messages = announcer.listen()

        # Yield initial connection as BYTES to flush headers
        yield b": connected\n\n"

        try:
            while True:
                msg = messages.get()

                # Yield subsequent messages as BYTES
                if isinstance(msg, str):
                    yield msg.encode("utf-8")
                else:
                    yield msg
        except GeneratorExit:
            pass

    response = Response(stream(), mimetype="text/event-stream")
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    response.headers["Connection"] = "keep-alive"
    response.direct_passthrough = True

    return response
