"""Admin-only database dashboard blueprint.

Routes
------
GET  /admin/db          – show DB backend info, connectivity, and table row counts
POST /admin/db/import   – trigger a one-time idempotent import from data.json
"""
from __future__ import annotations

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    url_for,
)

from crm.ui.web.routes.helpers import get_current_user, login_required, portal_context

admin_db_bp = Blueprint("admin_db", __name__)


def _get_admin_user():
    """Return the current user if they are Admin, otherwise abort(403)."""
    user = get_current_user()
    if user is None:
        abort(403)
    if not current_app.config["access_policy"].is_admin(user):
        abort(403)
    return user


@admin_db_bp.route("/admin/db")
@login_required
def db_dashboard():
    """Admin-only database dashboard."""
    user = _get_admin_user()

    store = current_app.config["store"]
    backend = current_app.config.get("storage_backend", "json")

    ctx: dict = {
        "backend": backend,
        "is_postgres": backend == "postgres",
        "active_page": "admin_db",
    }

    if backend == "postgres":
        ok, status_msg = store.check_connectivity()
        ctx["db_connected"] = ok
        ctx["db_status"] = status_msg
        if ok:
            ctx["table_counts"] = store.get_table_counts()
            from crm.persistence.postgres_import import get_last_import_timestamp
            ctx["last_import_at"] = get_last_import_timestamp(store)

    ctx.update(portal_context(user))
    return render_template("admin/db_dashboard.html", **ctx)


@admin_db_bp.route("/admin/db/import", methods=["POST"])
@login_required
def db_import():
    """Trigger an idempotent import from data.json into PostgreSQL."""
    _get_admin_user()

    backend = current_app.config.get("storage_backend", "json")
    if backend != "postgres":
        flash("Import is only available when using the PostgreSQL backend.", "warning")
        return redirect(url_for("admin_db.db_dashboard"))

    store = current_app.config["store"]
    json_path = current_app.config.get("data_path", "data.json")

    from crm.persistence.postgres_import import import_from_json
    result = import_from_json(json_path, store)

    category = "success" if result["success"] else "danger"
    flash(result["message"], category)
    return redirect(url_for("admin_db.db_dashboard"))
