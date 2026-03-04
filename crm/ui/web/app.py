import os
from flask import Flask

from crm.persistence.json_store import JsonDataStore
from crm.services.auth_service import AuthService
from crm.services.employee_service import EmployeeService
from crm.services.client_service import ClientService
from crm.services.deal_service import DealService
from crm.services.contract_service import ContractService
from crm.policies.access_control import AccessPolicy


def create_app(data_path: str | None = None) -> Flask:
    """Flask application factory."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )
    app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-prod")

    # Single shared store – mirrors the CLI's approach
    store = JsonDataStore(data_path or "data.json")

    # Attach services to app context so routes can reach them via current_app
    app.config["store"] = store
    app.config["auth_service"] = AuthService(store)
    app.config["employee_service"] = EmployeeService(store)
    app.config["client_service"] = ClientService(store)
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
