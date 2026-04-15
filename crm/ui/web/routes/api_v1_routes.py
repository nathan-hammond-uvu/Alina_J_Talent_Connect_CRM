"""Versioned API routes for JSON clients."""
from functools import wraps

from flask import Blueprint, current_app, jsonify

from crm.ui.web.routes.helpers import get_current_user


api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")


def api_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if get_current_user() is None:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)

    return decorated


def _json_list(entity: str, response_key: str):
    @api_v1_bp.get(f"/{entity}", endpoint=f"{entity}_list")
    @api_login_required
    def list_view():
        user = get_current_user()
        api_svc = current_app.config["api_v1_service"]
        policy = current_app.config["access_policy"]
        items = api_svc.list_for_user(entity, user, policy)
        if items is None:
            return jsonify({"error": "Forbidden"}), 403
        return jsonify({response_key: items})

    list_view.__name__ = f"list_{entity}"
    return list_view


def _json_detail(entity: str, response_key: str):
    @api_v1_bp.get(f"/{entity}/<int:item_id>", endpoint=f"{entity}_detail")
    @api_login_required
    def detail_view(item_id: int):
        user = get_current_user()
        api_svc = current_app.config["api_v1_service"]
        policy = current_app.config["access_policy"]
        item = api_svc.get_for_user(entity, item_id, user, policy)
        if item is None:
            return jsonify({"error": "Not found"}), 404
        return jsonify({response_key[:-1] if response_key.endswith("s") else response_key: item})

    detail_view.__name__ = f"detail_{entity}"
    return detail_view


ENTITY_SPECS = [
    ("roles", "roles"),
    ("persons", "persons"),
    ("users", "users"),
    ("employees", "employees"),
    ("creators", "creators"),
    ("social_media_accounts", "social_media_accounts"),
    ("brands", "brands"),
    ("brand_contacts", "brand_contacts"),
    ("deals", "deals"),
    ("contracts", "contracts"),
]

for entity, response_key in ENTITY_SPECS:
    _json_list(entity, response_key)
    _json_detail(entity, response_key)


@api_v1_bp.get("/items")
@api_login_required
def list_items():
    user = get_current_user()
    api_svc = current_app.config["api_v1_service"]
    policy = current_app.config["access_policy"]
    items = api_svc.list_for_user("creators", user, policy)
    if items is None:
        return jsonify({"error": "Forbidden"}), 403
    return jsonify({"items": items})


@api_v1_bp.get("/items/<int:item_id>")
@api_login_required
def get_item(item_id: int):
    user = get_current_user()
    api_svc = current_app.config["api_v1_service"]
    policy = current_app.config["access_policy"]
    item = api_svc.get_for_user("creators", item_id, user, policy)
    if item is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"item": item})