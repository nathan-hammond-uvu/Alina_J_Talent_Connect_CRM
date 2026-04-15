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


@api_v1_bp.get("/items")
@api_login_required
def list_items():
    user = get_current_user()
    creator_svc = current_app.config["creator_service"]
    policy = current_app.config["access_policy"]
    items = creator_svc.list_creators_for_user(user, policy)
    return jsonify({"items": items})


@api_v1_bp.get("/items/<int:item_id>")
@api_login_required
def get_item(item_id: int):
    user = get_current_user()
    creator_svc = current_app.config["creator_service"]
    policy = current_app.config["access_policy"]
    item = creator_svc.get_creator_for_user(user, item_id, policy)
    if item is None:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"item": item})