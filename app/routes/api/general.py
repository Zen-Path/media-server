import json
import time
from datetime import datetime, timezone
from functools import wraps
from typing import Tuple

from colorama import Fore, Style
from flask import Response, current_app, g, request

from app.constants import APP_VERSION
from app.routes.api import bp
from app.utils.api_response import api_response
from app.utils.logger import logger
from app.utils.sse import event_generator

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


# LOGGING


def skip_logging(f):
    """
    Decorator to mark a route to skip logging.
    """

    # Using @wraps ensures metadata (like docstrings) is preserved.
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    wrapper._skip_logging = True
    return wrapper


@bp.before_request
def log_request():
    if request.endpoint:
        view_func = current_app.view_functions.get(request.endpoint)
        if view_func and getattr(view_func, "_skip_logging", False):
            g.skip_logging = True
            return

    g.start_time = time.time()

    params = request.args.to_dict()
    body = None
    try:
        if request.is_json:
            body = request.get_json(silent=True)
        elif request.form:
            body = request.form.to_dict()
        elif request.data:
            body = request.data.decode("utf-8", errors="ignore")
    except Exception:
        body = "<Unparseable Body>"

    output_lines = [f"{Fore.LIGHTBLUE_EX}REQUEST{Fore.LIGHTBLACK_EX}:"]
    if params:
        output_lines.append(f"params: {json.dumps(params, indent=4)}")

    if body:
        data_fmt = (
            json.dumps(body, indent=4) if isinstance(body, (dict, list)) else body
        )
        output_lines.append(f"body: {data_fmt}{Style.RESET_ALL}")

    logger.info("\n".join(output_lines))


@bp.after_request
def log_response(response):
    if getattr(g, "skip_logging", False):
        return response

    duration = time.time() - g.get("start_time", time.time())

    max_response_length = 1000
    try:
        if response.is_json:
            json_data = response.get_json()
            json_fmt = json.dumps(json_data, indent=4, ensure_ascii=False)
        else:
            json_fmt = response.get_data(as_text=True)
            if len(json_fmt) > max_response_length:
                json_fmt = json_fmt[:max_response_length] + "... (truncated)"

    except Exception:
        json_fmt = "<Unreadable Response>"

    logger.info(
        f"{Fore.LIGHTYELLOW_EX}RESPONSE{Fore.LIGHTBLACK_EX}: "
        f"{request.method} {request.path} (duration: {duration:.4f}s):\n"
        f"{json_fmt}{Style.RESET_ALL}\n"
    )

    return response


# ROUTES


@bp.route("/health", methods=["GET"])
@skip_logging
def health_check() -> Tuple[Response, int]:
    """
    Public health check endpoint.
    """
    return api_response(
        status="ok",
        data={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "version": APP_VERSION,
        },
    )


@bp.route("/events")
def sse_events() -> Response:
    """
    Server-Sent Events (SSE) endpoint.
    """
    announcer = current_app.config["ANNOUNCER"]
    return Response(event_generator(announcer), mimetype="text/event-stream")
