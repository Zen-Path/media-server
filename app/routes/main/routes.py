from flask import redirect, render_template

from app.constants import PAGE_DASHBOARD
from app.routes.main import bp


@bp.route("/")
def index():
    return redirect(PAGE_DASHBOARD)


@bp.route(PAGE_DASHBOARD)
def dashboard_page():
    return render_template("dashboard.html")
