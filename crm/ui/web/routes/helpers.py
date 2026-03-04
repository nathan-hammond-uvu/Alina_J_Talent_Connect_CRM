"""Shared helpers for web routes."""
from functools import wraps

from flask import session, redirect, url_for, current_app, abort


def get_current_user() -> dict | None:
    """Return the currently logged-in user dict, or None."""
    user_id = session.get("user_id")
    if user_id is None:
        return None
    store = current_app.config["store"]
    data = store.load()
    return next((u for u in data.get("users", []) if u["user_id"] == user_id), None)


def get_person(person_id: int) -> dict | None:
    store = current_app.config["store"]
    data = store.load()
    return next((p for p in data.get("persons", []) if p["person_id"] == person_id), None)


def get_role_name(user: dict) -> str:
    store = current_app.config["store"]
    data = store.load()
    role = next((r for r in data.get("roles", []) if r["role_id"] == user.get("role_id")), None)
    return role["role_name"] if role else "User"


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if get_current_user() is None:
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


def portal_context(user: dict) -> dict:
    """Build the common template context for portal pages."""
    person = get_person(user.get("person_id"))
    role_name = get_role_name(user)
    display = (
        (person.get("display_name") or person.get("full_name", ""))
        if person
        else user.get("username", "")
    )
    return {
        "current_user": user,
        "current_person": person,
        "current_role": role_name,
        "display_name": display,
    }
