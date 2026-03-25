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
        "is_db_backend": backend in ("postgres", "sqlite"),
        "active_page": "admin_db",
    }

    if backend in ("postgres", "sqlite"):
        ok, status_msg = store.check_connectivity()
        ctx["db_connected"] = ok
        ctx["db_status"] = status_msg
        if ok:
            ctx["table_counts"] = store.get_table_counts()
            if backend == "postgres":
                from crm.persistence.postgres_import import get_last_import_timestamp
                ctx["last_import_at"] = get_last_import_timestamp(store)
            else:
                ctx["last_import_at"] = None

    ctx.update(portal_context(user))
    return render_template("admin/db_dashboard.html", **ctx)


@admin_db_bp.route("/admin/db/import", methods=["POST"])
@login_required
def db_import():
    """Trigger an idempotent import from data.json into the database."""
    _get_admin_user()

    backend = current_app.config.get("storage_backend", "json")
    if backend not in ("postgres", "sqlite"):
        flash("Import is only available when using a database backend (postgres or sqlite).", "warning")
        return redirect(url_for("admin_db.db_dashboard"))

    store = current_app.config["store"]
    json_path = current_app.config.get("data_path", "data.json")

    if backend == "postgres":
        from crm.persistence.postgres_import import import_from_json
        result = import_from_json(json_path, store)
        category = "success" if result["success"] else "danger"
        flash(result["message"], category)
    else:
        # SQLite: check if already seeded, then seed
        import json as _json
        import os
        from crm.persistence.migration import migrate, needs_migration
        from crm.persistence.json_store import JsonDataStore

        existing = store.load()
        if existing.get("roles"):
            flash("Data already exists in the database — import skipped (idempotent).", "success")
        elif not os.path.exists(json_path):
            flash(f"JSON file not found: {json_path}", "danger")
        else:
            try:
                with open(json_path) as f:
                    raw = _json.load(f)
                seeded = migrate(raw) if needs_migration(raw) else raw
                seeded.setdefault("access_control_matrix", JsonDataStore.DEFAULT_ACM)
                store.save(seeded)
                flash("Import completed successfully.", "success")
            except Exception as exc:
                flash(f"Import failed: {exc}", "danger")

    return redirect(url_for("admin_db.db_dashboard"))
