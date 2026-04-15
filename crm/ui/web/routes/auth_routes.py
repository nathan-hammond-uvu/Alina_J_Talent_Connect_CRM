from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app

from crm.ui.web.routes.helpers import get_current_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def home():
    if get_current_user():
        return redirect(url_for("dashboard.dashboard"))
    return render_template("auth/home.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if get_current_user():
        return redirect(url_for("dashboard.dashboard"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        auth_svc = current_app.config["auth_service"]
        user = auth_svc.authenticate(username, password)
        if user:
            session["user_id"] = user["user_id"]
            return redirect(url_for("dashboard.dashboard"))
        error = "Invalid username or password."
    return render_template("auth/login.html", error=error)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if get_current_user():
        return redirect(url_for("dashboard.dashboard"))
    error = None
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        first_name = request.form.get("first_name", "").strip()
        last_name = request.form.get("last_name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()

        if not username or not password or not first_name or not last_name:
            error = "Username, password, first name, and last name are required."
        else:
            # Check username not already taken
            store = current_app.config["store"]
            data = store.load()
            if any(u["username"] == username for u in data.get("users", [])):
                error = "Username already taken."
            else:
                auth_svc = current_app.config["auth_service"]
                full_name = f"{first_name} {last_name}".strip()
                person_fields = {
                    "first_name": first_name,
                    "last_name": last_name,
                    "full_name": full_name,
                    "display_name": first_name,
                    "email": email,
                    "phone": phone,
                    "address": "",
                    "city": "",
                    "state": "",
                    "zip": "",
                }
                user = auth_svc.register_user(person_fields, username, password)
                session["user_id"] = user["user_id"]
                flash("Registration successful! Welcome.", "success")
                return redirect(url_for("dashboard.dashboard"))
    return render_template("auth/register.html", error=error)


@auth_bp.route("/developers")
def developers():
    return render_template("auth/developers.html")


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.home"))
