import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from flask import Flask
from dotenv import load_dotenv

from crm.persistence.json_store import JsonDataStore
from crm.persistence.migration import run_migration
from crm.services.auth_service import AuthService
from crm.services.employee_service import EmployeeService
from crm.services.creator_service import CreatorService
from crm.services.brand_contact_service import BrandContactService
from crm.services.person_service import PersonService
from crm.services.deal_service import DealService
from crm.services.contract_service import ContractService
from crm.services.api_v1_service import ApiV1Service
from crm.policies.access_control import AccessPolicy


def create_app(data_path: str | None = None, storage_backend: str | None = None) -> Flask:
    """Flask application factory.

    Storage backend is selected via environment variables:
      CRM_STORAGE_BACKEND=json      (default) – uses data.json
      CRM_STORAGE_BACKEND=sqlite    – uses SQLAlchemy + SQLite
      CRM_STORAGE_BACKEND=postgres  – uses PostgreSQL (requires DATABASE_URL)
      DATABASE_URL=...              – connection URL for sqlite or postgres backends
      CRM_AUTO_IMPORT=1             – auto-import data.json into the DB on startup
    """
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")

    resolved_path = data_path or "data.json"

    # ------------------------------------------------------------------ #
    # Storage backend selection                                            #
    # ------------------------------------------------------------------ #
    # If a caller passes a specific JSON path (common in tests), default to
    # JSON storage for deterministic behavior unless backend is explicitly set.
    if storage_backend:
        backend = storage_backend.lower()
    elif data_path is not None and "CRM_STORAGE_BACKEND" not in os.environ:
        backend = "json"
    else:
        backend = os.environ.get("CRM_STORAGE_BACKEND", "json").lower()
    database_url = os.environ.get("DATABASE_URL", "")

    if backend == "postgres" and database_url:
        from crm.persistence.postgres_store import PostgresDataStore
        store = PostgresDataStore(database_url)
        store.ensure_schema()

        # Optional automatic import from data.json at startup
        if os.environ.get("CRM_AUTO_IMPORT", "0") == "1":
            from crm.persistence.postgres_import import import_from_json
            result = import_from_json(resolved_path, store)
            if not result.get("skipped"):
                print(f"[app] Auto-import: {result.get('message')}")

    elif backend == "sqlite":
        from crm.persistence.sqlite_store import SqliteDataStore
        db_url = database_url or "sqlite:///project.db"
        store = SqliteDataStore(db_url)
        store.ensure_schema()

        # Optional automatic import from data.json at startup
        if os.environ.get("CRM_AUTO_IMPORT", "0") == "1":
            existing = store.load()
            if not existing.get("roles"):
                import json
                from crm.persistence.migration import migrate, needs_migration
                from crm.persistence.json_store import JsonDataStore as _JDS
                if os.path.exists(resolved_path):
                    with open(resolved_path) as f:
                        raw = json.load(f)
                    seeded = migrate(raw) if needs_migration(raw) else raw
                    seeded.setdefault("access_control_matrix", _JDS.DEFAULT_ACM)
                    store.save(seeded)
                    print("[app] Auto-seeded SQLite DB from data.json.")

    else:
        backend = "json"
        # Run schema migration once (no-op if already migrated)
        run_migration(resolved_path)
        store = JsonDataStore(resolved_path)

    # Attach services to app context so routes can reach them via current_app
    app.config["store"] = store
    app.config["storage_backend"] = backend
    app.config["data_path"] = resolved_path
    app.config["auth_service"] = AuthService(store)
    app.config["employee_service"] = EmployeeService(store)
    app.config["creator_service"] = CreatorService(store)
    app.config["brand_contact_service"] = BrandContactService(store)
    app.config["person_service"] = PersonService(store)
    app.config["deal_service"] = DealService(store)
    app.config["contract_service"] = ContractService(store)
    app.config["api_v1_service"] = ApiV1Service(store)
    app.config["access_policy"] = AccessPolicy(store)

    # Register blueprints
    from crm.ui.web.routes.auth_routes import auth_bp
    from crm.ui.web.routes.portal_routes import portal_bp
    from crm.ui.web.routes.entity_routes import entity_bp
    from crm.ui.web.routes.settings_routes import settings_bp
    from crm.ui.web.routes.admin_db_routes import admin_db_bp
    from crm.ui.web.routes.dashboard_routes import dashboard_bp
    from crm.ui.web.routes.api_v1_routes import api_v1_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(entity_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(admin_db_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(api_v1_bp)

    # Error handlers
    @app.errorhandler(403)
    def forbidden(e):
        from flask import render_template
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(e):
        from flask import render_template
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        from flask import render_template
        return render_template("errors/500.html"), 500

    return app


if __name__ == "__main__":
    create_app().run(debug=os.environ.get("FLASK_DEBUG", "0") == "1")
