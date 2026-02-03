import json

from colorama import Fore, Style
from common.logger import logger
from flask import g, request


def skip_logging(f):
    """Decorator to mark a route to skip logging."""
    f._skip_logging = True
    return f


def register_logging(app):
    """Attach request/response logging to the given Flask app."""

    @app.before_request
    def log_request():
        view_func = app.view_functions.get(request.endpoint)
        if getattr(view_func, "_skip_logging", False):
            g.skip_logging = True
            return

        params = request.args.to_dict()
        try:
            data = request.get_json(silent=True)
        except Exception:
            data = None

        if data is None:
            if request.form:
                data = request.form.to_dict()
            else:
                data = request.data.decode("utf-8") if request.data else None

        output_lines = []
        output_lines.append(f"{Fore.LIGHTBLUE_EX}REQUEST{Fore.LIGHTBLACK_EX}:")
        if params:
            output_lines.append(f"params: {json.dumps(params, indent=4)}")

        data_fmt = (
            json.dumps(data, indent=4) if isinstance(data, (dict, list)) else data
        )
        output_lines.append(f"data: {data_fmt}{Style.RESET_ALL}")

        logger.info("\n".join(output_lines))

    @app.after_request
    def log_response(response):
        if getattr(g, "skip_logging", False):
            return response

        try:
            json_data = response.get_json()
            json_fmt = json.dumps(json_data, indent=4, ensure_ascii=False)
        except Exception:
            json_fmt = response.get_data(as_text=True)

        logger.info(
            f"{Fore.LIGHTYELLOW_EX}RESPONSE{Fore.LIGHTBLACK_EX}:\n{json_fmt}{Style.RESET_ALL}"
        )
        return response
