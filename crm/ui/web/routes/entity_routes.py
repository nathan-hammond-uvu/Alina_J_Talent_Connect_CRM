"""CRUD routes for Employees, Clients, Brands, Deals, Contracts."""
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, current_app, abort
)

from crm.ui.web.routes.helpers import login_required, get_current_user, portal_context, get_person

entity_bp = Blueprint("entity", __name__, url_prefix="/portal")


# ---------------------------------------------------------------------------
# Employees
# ---------------------------------------------------------------------------

@entity_bp.route("/employees")
@login_required
def employees():
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_view("employees", user):
        abort(403)
    store = current_app.config["store"]
    data = store.load()
    all_emp = data.get("employees", [])
    scoped = policy.scope_employees(user, all_emp)
    persons = {p["person_id"]: p for p in data.get("persons", [])}
    # Enrich employees with person data
    enriched = []
    for emp in scoped:
        person = persons.get(emp.get("person_id"), {})
        enriched.append({**emp, "person": person})
    all_persons = data.get("persons", [])
    ctx = portal_context(user)
    ctx.update({
        "employees": enriched,
        "all_persons": all_persons,
        "can_edit": policy.can_edit("employees", user),
        "can_delete": policy.can_delete("employees", user),
    })
    return render_template("entities/employees.html", **ctx)


@entity_bp.route("/employees/add", methods=["POST"])
@login_required
def employees_add():
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_edit("employees", user):
        abort(403)
    emp_svc = current_app.config["employee_service"]
    f = request.form
    try:
        emp_svc.add_employee(
            person_id=int(f.get("person_id", 0)),
            position=f.get("position", ""),
            title=f.get("title", ""),
            manager_id=int(f.get("manager_id", 0) or 0),
            start_date=f.get("start_date", ""),
            end_date=f.get("end_date") or None,
            is_active=f.get("is_active") == "on",
            is_manager=f.get("is_manager") == "on",
        )
        flash("Employee added.", "success")
    except Exception as e:
        flash(f"Error adding employee: {e}", "danger")
    return redirect(url_for("entity.employees"))


@entity_bp.route("/employees/<int:emp_id>/edit", methods=["POST"])
@login_required
def employees_edit(emp_id: int):
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_edit("employees", user):
        abort(403)
    emp_svc = current_app.config["employee_service"]
    f = request.form
    updates = {
        "position": f.get("position", ""),
        "title": f.get("title", ""),
        "manager_id": int(f.get("manager_id", 0) or 0),
        "start_date": f.get("start_date", ""),
        "end_date": f.get("end_date") or None,
        "is_active": f.get("is_active") == "on",
        "is_manager": f.get("is_manager") == "on",
    }
    result = emp_svc.update_employee(emp_id, **updates)
    if result:
        flash("Employee updated.", "success")
    else:
        flash("Employee not found.", "danger")
    return redirect(url_for("entity.employees"))


@entity_bp.route("/employees/<int:emp_id>/delete", methods=["POST"])
@login_required
def employees_delete(emp_id: int):
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_delete("employees", user):
        abort(403)
    emp_svc = current_app.config["employee_service"]
    if emp_svc.delete_employee(emp_id):
        flash("Employee deleted.", "success")
    else:
        flash("Employee not found.", "danger")
    return redirect(url_for("entity.employees"))


# ---------------------------------------------------------------------------
# Clients
# ---------------------------------------------------------------------------

@entity_bp.route("/clients")
@login_required
def clients():
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_view("clients", user):
        abort(403)
    store = current_app.config["store"]
    data = store.load()
    all_clients = data.get("clients", [])
    scoped = policy.scope_clients(user, all_clients)
    employees = {e["employee_id"]: e for e in data.get("employees", [])}
    persons = {p["person_id"]: p for p in data.get("persons", [])}
    enriched = []
    for client in scoped:
        emp = employees.get(client.get("employee_id"), {})
        person = persons.get(emp.get("person_id"), {}) if emp else {}
        enriched.append({**client, "employee": emp, "person": person})
    ctx = portal_context(user)
    ctx.update({
        "clients": enriched,
        "employees": data.get("employees", []),
        "can_edit": policy.can_edit("clients", user),
        "can_delete": policy.can_delete("clients", user),
    })
    return render_template("entities/clients.html", **ctx)


@entity_bp.route("/clients/add", methods=["POST"])
@login_required
def clients_add():
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_edit("clients", user):
        abort(403)
    client_svc = current_app.config["client_service"]
    f = request.form
    try:
        client_svc.add_client(
            employee_id=int(f.get("employee_id", 0)),
            description=f.get("description", ""),
        )
        flash("Client added.", "success")
    except Exception as e:
        flash(f"Error adding client: {e}", "danger")
    return redirect(url_for("entity.clients"))


@entity_bp.route("/clients/<int:client_id>/edit", methods=["POST"])
@login_required
def clients_edit(client_id: int):
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_edit("clients", user):
        abort(403)
    client_svc = current_app.config["client_service"]
    f = request.form
    updates = {
        "employee_id": int(f.get("employee_id", 0)),
        "description": f.get("description", ""),
    }
    if client_svc.update_client(client_id, **updates):
        flash("Client updated.", "success")
    else:
        flash("Client not found.", "danger")
    return redirect(url_for("entity.clients"))


@entity_bp.route("/clients/<int:client_id>/delete", methods=["POST"])
@login_required
def clients_delete(client_id: int):
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_delete("clients", user):
        abort(403)
    client_svc = current_app.config["client_service"]
    if client_svc.delete_client(client_id):
        flash("Client deleted.", "success")
    else:
        flash("Client not found.", "danger")
    return redirect(url_for("entity.clients"))


# ---------------------------------------------------------------------------
# Brands
# ---------------------------------------------------------------------------

@entity_bp.route("/brands")
@login_required
def brands():
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_view("brands", user):
        abort(403)
    store = current_app.config["store"]
    data = store.load()
    ctx = portal_context(user)
    ctx.update({
        "brands": data.get("brands", []),
        "can_edit": policy.can_edit("brands", user),
        "can_delete": policy.can_delete("brands", user),
    })
    return render_template("entities/brands.html", **ctx)


@entity_bp.route("/brands/add", methods=["POST"])
@login_required
def brands_add():
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_edit("brands", user):
        abort(403)
    store = current_app.config["store"]
    f = request.form
    data = store.load()
    new_id = store.next_id(data)
    brand = {
        "brand_id": new_id,
        "name": f.get("name", ""),
        "industry": f.get("industry", ""),
        "website": f.get("website", ""),
        "notes": f.get("notes", ""),
    }
    data.setdefault("brands", []).append(brand)
    store.save(data)
    flash("Brand added.", "success")
    return redirect(url_for("entity.brands"))


@entity_bp.route("/brands/<int:brand_id>/edit", methods=["POST"])
@login_required
def brands_edit(brand_id: int):
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_edit("brands", user):
        abort(403)
    store = current_app.config["store"]
    f = request.form
    data = store.load()
    brand = next((b for b in data.get("brands", []) if b["brand_id"] == brand_id), None)
    if brand:
        brand.update({
            "name": f.get("name", ""),
            "industry": f.get("industry", ""),
            "website": f.get("website", ""),
            "notes": f.get("notes", ""),
        })
        store.save(data)
        flash("Brand updated.", "success")
    else:
        flash("Brand not found.", "danger")
    return redirect(url_for("entity.brands"))


@entity_bp.route("/brands/<int:brand_id>/delete", methods=["POST"])
@login_required
def brands_delete(brand_id: int):
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_delete("brands", user):
        abort(403)
    store = current_app.config["store"]
    data = store.load()
    original = data.get("brands", [])
    data["brands"] = [b for b in original if b["brand_id"] != brand_id]
    if len(data["brands"]) < len(original):
        store.save(data)
        flash("Brand deleted.", "success")
    else:
        flash("Brand not found.", "danger")
    return redirect(url_for("entity.brands"))


# ---------------------------------------------------------------------------
# Deals
# ---------------------------------------------------------------------------

@entity_bp.route("/deals")
@login_required
def deals():
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_view("deals", user):
        abort(403)
    store = current_app.config["store"]
    data = store.load()
    ctx = portal_context(user)
    ctx.update({
        "deals": data.get("deals", []),
        "clients": data.get("clients", []),
        "brands": data.get("brands", []),
        "brand_reps": data.get("brand_representatives", []),
        "can_edit": policy.can_edit("deals", user),
        "can_delete": policy.can_delete("deals", user),
    })
    return render_template("entities/deals.html", **ctx)


@entity_bp.route("/deals/add", methods=["POST"])
@login_required
def deals_add():
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_edit("deals", user):
        abort(403)
    deal_svc = current_app.config["deal_service"]
    f = request.form
    try:
        deal_svc.create_deal(
            client_id=int(f.get("client_id", 0)),
            brand_id=int(f.get("brand_id", 0)),
            brand_rep_id=int(f.get("brand_rep_id", 0) or 0),
            pitch_date=f.get("pitch_date", ""),
            is_active=f.get("is_active") == "on",
            is_successful=f.get("is_successful") == "on",
        )
        flash("Deal added.", "success")
    except Exception as e:
        flash(f"Error adding deal: {e}", "danger")
    return redirect(url_for("entity.deals"))


@entity_bp.route("/deals/<int:deal_id>/edit", methods=["POST"])
@login_required
def deals_edit(deal_id: int):
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_edit("deals", user):
        abort(403)
    store = current_app.config["store"]
    f = request.form
    data = store.load()
    deal = next((d for d in data.get("deals", []) if d["deal_id"] == deal_id), None)
    if deal:
        deal.update({
            "client_id": int(f.get("client_id", deal.get("client_id", 0))),
            "brand_id": int(f.get("brand_id", deal.get("brand_id", 0))),
            "brand_rep_id": int(f.get("brand_rep_id", 0) or 0),
            "pitch_date": f.get("pitch_date", ""),
            "is_active": f.get("is_active") == "on",
            "is_successful": f.get("is_successful") == "on",
        })
        store.save(data)
        flash("Deal updated.", "success")
    else:
        flash("Deal not found.", "danger")
    return redirect(url_for("entity.deals"))


@entity_bp.route("/deals/<int:deal_id>/delete", methods=["POST"])
@login_required
def deals_delete(deal_id: int):
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_delete("deals", user):
        abort(403)
    store = current_app.config["store"]
    data = store.load()
    original = data.get("deals", [])
    data["deals"] = [d for d in original if d["deal_id"] != deal_id]
    if len(data["deals"]) < len(original):
        store.save(data)
        flash("Deal deleted.", "success")
    else:
        flash("Deal not found.", "danger")
    return redirect(url_for("entity.deals"))


# ---------------------------------------------------------------------------
# Contracts
# ---------------------------------------------------------------------------

@entity_bp.route("/contracts")
@login_required
def contracts():
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_view("contracts", user):
        abort(403)
    store = current_app.config["store"]
    data = store.load()
    ctx = portal_context(user)
    ctx.update({
        "contracts": data.get("contracts", []),
        "deals": data.get("deals", []),
        "can_edit": policy.can_edit("contracts", user),
        "can_delete": policy.can_delete("contracts", user),
    })
    return render_template("entities/contracts.html", **ctx)


@entity_bp.route("/contracts/add", methods=["POST"])
@login_required
def contracts_add():
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_edit("contracts", user):
        abort(403)
    contract_svc = current_app.config["contract_service"]
    f = request.form
    try:
        contract_svc.create_contract(
            deal_id=int(f.get("deal_id", 0)),
            details=f.get("details", ""),
            payment=float(f.get("payment", 0) or 0),
            agency_percentage=float(f.get("agency_percentage", 0) or 0),
            start_date=f.get("start_date", ""),
            end_date=f.get("end_date", ""),
            status=f.get("status", ""),
            is_approved=f.get("is_approved") == "on",
        )
        flash("Contract added.", "success")
    except Exception as e:
        flash(f"Error adding contract: {e}", "danger")
    return redirect(url_for("entity.contracts"))


@entity_bp.route("/contracts/<int:contract_id>/edit", methods=["POST"])
@login_required
def contracts_edit(contract_id: int):
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_edit("contracts", user):
        abort(403)
    store = current_app.config["store"]
    f = request.form
    data = store.load()
    contract = next((c for c in data.get("contracts", []) if c["contract_id"] == contract_id), None)
    if contract:
        contract.update({
            "deal_id": int(f.get("deal_id", contract.get("deal_id", 0))),
            "details": f.get("details", ""),
            "payment": float(f.get("payment", 0) or 0),
            "agency_percentage": float(f.get("agency_percentage", 0) or 0),
            "start_date": f.get("start_date", ""),
            "end_date": f.get("end_date", ""),
            "status": f.get("status", ""),
            "is_approved": f.get("is_approved") == "on",
        })
        store.save(data)
        flash("Contract updated.", "success")
    else:
        flash("Contract not found.", "danger")
    return redirect(url_for("entity.contracts"))


@entity_bp.route("/contracts/<int:contract_id>/delete", methods=["POST"])
@login_required
def contracts_delete(contract_id: int):
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_delete("contracts", user):
        abort(403)
    store = current_app.config["store"]
    data = store.load()
    original = data.get("contracts", [])
    data["contracts"] = [c for c in original if c["contract_id"] != contract_id]
    if len(data["contracts"]) < len(original):
        store.save(data)
        flash("Contract deleted.", "success")
    else:
        flash("Contract not found.", "danger")
    return redirect(url_for("entity.contracts"))
