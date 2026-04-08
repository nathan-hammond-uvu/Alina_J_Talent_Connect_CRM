"""Dashboard blueprint – the CRM command-centre home page."""
from flask import Blueprint, render_template, current_app

from crm.ui.web.routes.helpers import login_required, get_current_user, portal_context
from crm.services.dashboard_service import DashboardService

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/portal")


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    user = get_current_user()
    ctx = portal_context(user)
    ctx["active_page"] = "home"

    store = current_app.config["store"]
    svc = DashboardService(store)
    ctx["dash"] = svc.build(user)

    return render_template("dashboard.html", **ctx)
