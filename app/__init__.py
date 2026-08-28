from pathlib import Path

from flask import Flask, request
from flask_cors import CORS

from app.constants import API_PREFIX
from app.routes.api import bp as api_bp
from app.routes.main import bp as main_bp
from app.utils.api_response import api_response
from app.utils.tools import get_project_version

# APP

app = Flask(
    __name__,
    template_folder=Path(__file__).parent.parent / "frontend" / "templates",
    static_folder=Path(__file__).parent.parent / "frontend" / "static",
)

CORS(app)  # Enable CORS for all routes


app.register_blueprint(main_bp)
app.register_blueprint(api_bp)

app.config["APP_VERSION"] = get_project_version()


@app.context_processor
def inject_global_vars():
    return {
        "project_version": get_project_version(),
        "github_url": "https://github.com/Zen-Path/flexycon/tree/main/dotfiles/src/scripts/media_server",
        "site_name": "Media Server",
    }


@app.errorhandler(404)
def handle_404(e):
    if request.path.startswith(API_PREFIX):
        return api_response(
            error="Not Found",
            data={"message": f"The requested URL {request.path!r} was not found."},
            status_code=404,
        )

    # return render_template("404.html"), 404
    return e
