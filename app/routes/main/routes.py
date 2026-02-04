from flask import redirect, render_template

from app.routes.main import bp


@bp.route("/")
def index():
    return redirect("/dashboard")


@bp.route("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")
