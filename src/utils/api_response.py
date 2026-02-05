from typing import Any, Optional, Tuple, Union

from flask import Response, jsonify


def api_response(
    data: Any = None,
    error: Optional[str] = None,
    status: Optional[Union[bool, str]] = None,
    status_code: int = 200,
) -> Tuple[Response, int]:
    """
    Standardized API response structure.

    Args:
        data: The payload to return.
        error: Error message if operation failed.
        status: Explicit status override.
                If None, inferred from error (True if error is None).
        status_code: HTTP status code.
    """
    final_status = status if status is not None else (error is None)

    response = {
        "status": final_status,
        "data": data,
        "error": error,
    }
    return jsonify(response), status_code
