import time

from flask import Response, current_app, g, request

from app.routes.api import bp
from app.utils.log_helpers import build_request_log, build_response_log
from app.utils.logger import logger

# Max bytes to attempt pretty-printing, otherwise use the raw text for performance
MAX_PRETTY_PRINT_SIZE = 50 * 1024  # 50 KB
LOG_TRUNCATE_LENGTH = 1000


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

    # Only attempt to parse body if content actually exists
    if request.content_length and request.content_length > 0:
        try:
            if request.is_json:
                body = request.get_json(silent=True)
            elif request.form:
                body = request.form.to_dict()
            else:
                body = request.get_data(as_text=True)

        except Exception:
            body = "<Unparseable Body>"

    log_str = build_request_log(params, body, max_length=LOG_TRUNCATE_LENGTH)
    if log_str:
        logger.info(log_str)


@bp.after_request
def log_response(response: Response):
    if getattr(g, "skip_logging", False):
        return response

    duration = time.time() - g.get("start_time", time.time())

    try:
        # If the payload is massive, skip JSON parsing/formatting entirely.
        if response.content_length and response.content_length > MAX_PRETTY_PRINT_SIZE:
            data = response.get_data(as_text=True)[:LOG_TRUNCATE_LENGTH]
        elif response.is_json:
            data = response.get_json()
        else:
            data = response.get_data(as_text=True)

    except Exception:
        data = "<Unreadable Response>"

    log_str = build_response_log(
        method=request.method,
        path=request.path,
        duration=duration,
        data=data,
        max_length=LOG_TRUNCATE_LENGTH,
    )
    logger.info(log_str)

    return response
