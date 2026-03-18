from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app

from crm.ui.web.routes.helpers import login_required, get_current_user, portal_context, get_person
from crm.persistence.json_store import JsonDataStore

settings_bp = Blueprint("settings", __name__, url_prefix="/portal")

# Ordered role list for the ACM table
_ACM_ROLES = ["Admin", "Manager", "Employee", "Creator", "User"]
_ACM_ENTITIES = ["persons", "users", "employees", "creators", "brand_contacts", "brands", "deals", "contracts"]
_ACM_ACTIONS = ["create", "read", "update", "delete"]


@settings_bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    user = get_current_user()
    ctx = portal_context(user)
    store = current_app.config["store"]
    auth_svc = current_app.config["auth_service"]
    policy = current_app.config["access_policy"]

    if request.method == "POST":
        action = request.form.get("action", "")
        data = store.load()

        if action == "update_profile":
            person = next((p for p in data.get("persons", []) if p["person_id"] == user.get("person_id")), None)
            if person:
                person.update({
                    "first_name": request.form.get("first_name", person.get("first_name", "")),
                    "last_name": request.form.get("last_name", person.get("last_name", "")),
                    "full_name": request.form.get("full_name", person.get("full_name", "")),
                    "display_name": request.form.get("display_name", person.get("display_name", "")),
                    "email": request.form.get("email", person.get("email", "")),
                    "phone": request.form.get("phone", person.get("phone", "")),
                    "address": request.form.get("address", person.get("address", "")),
                    "city": request.form.get("city", person.get("city", "")),
                    "state": request.form.get("state", person.get("state", "")),
                    "zip": request.form.get("zip", person.get("zip", "")),
                })
                store.save(data)
                flash("Profile updated.", "success")
            else:
                flash("Person record not found.", "danger")

        elif action == "change_password":
            current_pw = request.form.get("current_password", "")
            new_pw = request.form.get("new_password", "")
            confirm_pw = request.form.get("confirm_password", "")

            if not auth_svc.verify_password(user["password"], current_pw):
                flash("Current password is incorrect.", "danger")
            elif len(new_pw) < 6:
                flash("New password must be at least 6 characters.", "danger")
            elif new_pw != confirm_pw:
                flash("New passwords do not match.", "danger")
            else:
                for u in data.get("users", []):
                    if u["user_id"] == user["user_id"]:
                        u["password"] = auth_svc.hash_password(new_pw)
                        break
                store.save(data)
                flash("Password updated successfully.", "success")

        elif action == "update_acm":
            if not policy.can_edit_acm(user):
                flash("Permission denied: only admins can edit the Access Control Matrix.", "danger")
            else:
                new_acm = {}
                for role in _ACM_ROLES:
                    new_acm[role] = {}
                    for entity in _ACM_ENTITIES:
                        new_acm[role][entity] = {}
                        for act in _ACM_ACTIONS:
                            field_name = f"acm_{role}_{entity}_{act}"
                            new_acm[role][entity][act] = request.form.get(field_name) == "on"
                policy.save_acm(new_acm)
                flash("Access Control Matrix updated.", "success")

        return redirect(url_for("settings.settings"))

    person = get_person(user.get("person_id"))
    ctx["person"] = person
    ctx["acm"] = policy.get_acm()
    ctx["acm_roles"] = _ACM_ROLES
    ctx["acm_entities"] = _ACM_ENTITIES
    ctx["acm_actions"] = _ACM_ACTIONS
    ctx["can_edit_acm"] = policy.can_edit_acm(user)
    return render_template("settings/settings.html", **ctx)

