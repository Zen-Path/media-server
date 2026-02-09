from flask import Blueprint

bp = Blueprint("api", __name__)

from app.routes.api import (  # noqa: E402, F401
    downloads,
    general,
    logging_middleware,
    media,
)
