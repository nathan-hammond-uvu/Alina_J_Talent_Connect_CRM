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
from crm.policies.access_control import AccessPolicy


def create_app(data_path: str | None = None) -> Flask:
    """Flask application factory."""
    # Load environment variables from .env for local development.
    load_dotenv()

    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")

    resolved_path = data_path or "data.json"

    # Run schema migration once (no-op if already migrated)
    run_migration(resolved_path)

    # Single shared store – mirrors the CLI's approach
    store = JsonDataStore(resolved_path)

    # Attach services to app context so routes can reach them via current_app
    app.config["store"] = store
    app.config["auth_service"] = AuthService(store)
    app.config["employee_service"] = EmployeeService(store)
    app.config["creator_service"] = CreatorService(store)
    app.config["brand_contact_service"] = BrandContactService(store)
    app.config["person_service"] = PersonService(store)
    app.config["deal_service"] = DealService(store)
    app.config["contract_service"] = ContractService(store)
    app.config["access_policy"] = AccessPolicy(store)

    # Register blueprints
    from crm.ui.web.routes.auth_routes import auth_bp
    from crm.ui.web.routes.portal_routes import portal_bp
    from crm.ui.web.routes.entity_routes import entity_bp
    from crm.ui.web.routes.settings_routes import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(portal_bp)
    app.register_blueprint(entity_bp)
    app.register_blueprint(settings_bp)

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
