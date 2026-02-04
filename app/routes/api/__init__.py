from flask import Blueprint

bp = Blueprint("api", __name__)

from app.routes.api import downloads, execution, general
