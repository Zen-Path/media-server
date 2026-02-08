from typing import Any, Optional, Tuple, Union

from flask import Response, jsonify
from scripts.media_server.app.utils.tools import recursive_camelize


def api_response(
    data: Any = None,
    error: Optional[str] = None,
    status: Optional[Union[bool, str]] = None,
    status_code: int = 200,
) -> Tuple[Response, int]:
    """
    Standardized API response structure.

    Converts data fields to camel case.

    If explicit 'status' is passed, use it, otherwise, 'status' is False if:
    - an error message exists
    - the HTTP status code is a failure code (>= 400)

    Args:
        data: The payload to return.
        error: Error message if operation failed.
        status: Explicit status override.
        status_code: HTTP status code.
    """
    final_data = None
    if data is not None:
        final_data = recursive_camelize(data)

    if status is not None:
        final_status = status
    else:
        final_status = (error is None) and (status_code < 400)

    response = {
        "status": final_status,
        "data": final_data,
        "error": error,
    }
    return jsonify(response), status_code
