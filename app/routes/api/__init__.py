from functools import wraps

from flask import Blueprint

bp = Blueprint("api", __name__)


def skip_logging(f):
    """
    Decorator to mark a route to skip logging.
    """

    # Using @wraps ensures metadata (like docstrings) is preserved.
    @wraps(f)
    def wrapper(*args, **kwargs):
        return f(*args, **kwargs)

    setattr(wrapper, "_skip_logging", True)
    return wrapper


from app.routes.api import (  # noqa: E402, F401
    downloads,
    execution,
    general,
    logging_middleware,
)
