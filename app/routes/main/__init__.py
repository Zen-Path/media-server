from flask import Blueprint

bp = Blueprint("main", __name__)

# We import the routes so they can register themselves - @bp.route(...)
from app.routes.main import routes  # noqa: E402, F401
