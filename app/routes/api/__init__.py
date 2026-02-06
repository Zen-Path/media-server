from flask import Blueprint

bp = Blueprint("api", __name__)

from scripts.media_server.app.routes.api import (  # noqa: E402, F401
    downloads,
    general,
    logging_middleware,
    media,
)
