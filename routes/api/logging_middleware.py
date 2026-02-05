import json
import time
from functools import wraps

from colorama import Fore, Style
from common.logger import logger
from flask import current_app, g, request
from scripts.media_server.routes.api import bp


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
    if "apiKey" in params:
        params["apiKey"] = "***"

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
