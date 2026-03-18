"""CRUD routes for Employees, Creators, Brand Contacts, Brands, Deals, Contracts."""
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, current_app, abort
)

from crm.ui.web.routes.helpers import login_required, get_current_user, portal_context, get_person

entity_bp = Blueprint("entity", __name__, url_prefix="/portal")


# ---------------------------------------------------------------------------
# Persons (helper – used by create flows)
# ---------------------------------------------------------------------------

def _handle_person_form(f, store, person_svc) -> int:
    """Parse person form fields and return a valid person_id."""
    mode = f.get("person_mode", "new")
    if mode == "existing":
        pid = int(f.get("person_id", 0) or 0)
        if pid:
            data = store.load()
            exists = next((p for p in data.get("persons", []) if p["person_id"] == pid), None)
            if exists:
                return pid
    person = person_svc.create_person(
        first_name=f.get("first_name", ""),
        last_name=f.get("last_name", ""),
        email=f.get("email", ""),
        phone=f.get("phone", ""),
        address=f.get("address", ""),
        city=f.get("city", ""),
        state=f.get("state", ""),
        zip_code=f.get("zip", ""),
        display_name=f.get("display_name", ""),
    )
    return person["person_id"]


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
    enriched = []
    for emp in scoped:
        person = persons.get(emp.get("person_id"), {})
        enriched.append({**emp, "person": person})
    ctx = portal_context(user)
    ctx.update({
        "employees": enriched,
        "all_employees": all_emp,
        "all_persons": data.get("persons", []),
        "can_edit": policy.can_edit("employees", user),
        "can_delete": policy.can_delete("employees", user),
        "active_page": "employees",
    })
    return render_template("entities/employees.html", **ctx)


@entity_bp.route("/employees/add", methods=["POST"])
@login_required
def employees_add():
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_create("employees", user):
        abort(403)
    store = current_app.config["store"]
    emp_svc = current_app.config["employee_service"]
    person_svc = current_app.config["person_service"]
    f = request.form
    try:
        person_id = _handle_person_form(f, store, person_svc)
        emp_svc.add_employee(
            person_id=person_id,
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
    store = current_app.config["store"]
    data = store.load()
    target = next((e for e in data.get("employees", []) if e["employee_id"] == emp_id), None)
    if not policy.can_update("employees", user, target):
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
    store = current_app.config["store"]
    data = store.load()
    target = next((e for e in data.get("employees", []) if e["employee_id"] == emp_id), None)
    if not policy.can_delete("employees", user, target):
        abort(403)
    emp_svc = current_app.config["employee_service"]
    if emp_svc.delete_employee(emp_id):
        flash("Employee deleted.", "success")
    else:
        flash("Employee not found.", "danger")
    return redirect(url_for("entity.employees"))


# ---------------------------------------------------------------------------
# Creators  (formerly Clients)
# ---------------------------------------------------------------------------

@entity_bp.route("/creators")
@login_required
def creators():
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_view("creators", user):
        abort(403)
    store = current_app.config["store"]
    data = store.load()
    all_creators = data.get("creators", [])
    scoped = policy.scope_creators(user, all_creators)
    employees = {e["employee_id"]: e for e in data.get("employees", [])}
    persons = {p["person_id"]: p for p in data.get("persons", [])}
    enriched = []
    for creator in scoped:
        emp = employees.get(creator.get("employee_id"), {})
        emp_person = persons.get(emp.get("person_id"), {}) if emp else {}
        person = persons.get(creator.get("person_id"), {})
        enriched.append({**creator, "employee": emp, "employee_person": emp_person, "person": person})
    ctx = portal_context(user)
    ctx.update({
        "creators": enriched,
        "employees": data.get("employees", []),
        "all_persons": data.get("persons", []),
        "can_edit": policy.can_edit("creators", user),
        "can_delete": policy.can_delete("creators", user),
        "active_page": "creators",
    })
    return render_template("entities/creators.html", **ctx)


@entity_bp.route("/clients")
@login_required
def clients_redirect():
    """Legacy redirect: /portal/clients -> /portal/creators."""
    return redirect(url_for("entity.creators"), 301)


@entity_bp.route("/creators/add", methods=["POST"])
@login_required
def creators_add():
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_create("creators", user):
        abort(403)
    store = current_app.config["store"]
    creator_svc = current_app.config["creator_service"]
    person_svc = current_app.config["person_service"]
    f = request.form
    try:
        person_id = _handle_person_form(f, store, person_svc)
        creator_svc.add_creator(
            person_id=person_id,
            employee_id=int(f.get("employee_id", 0) or 0),
            description=f.get("description", ""),
        )
        flash("Creator added.", "success")
    except Exception as e:
        flash(f"Error adding creator: {e}", "danger")
    return redirect(url_for("entity.creators"))


@entity_bp.route("/creators/<int:creator_id>/edit", methods=["POST"])
@login_required
def creators_edit(creator_id: int):
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_update("creators", user):
        abort(403)
    creator_svc = current_app.config["creator_service"]
    f = request.form
    updates = {
        "employee_id": int(f.get("employee_id", 0) or 0),
        "description": f.get("description", ""),
    }
    if creator_svc.update_creator(creator_id, **updates):
        flash("Creator updated.", "success")
    else:
        flash("Creator not found.", "danger")
    return redirect(url_for("entity.creators"))


@entity_bp.route("/creators/<int:creator_id>/delete", methods=["POST"])
@login_required
def creators_delete(creator_id: int):
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_delete("creators", user):
        abort(403)
    creator_svc = current_app.config["creator_service"]
    if creator_svc.delete_creator(creator_id):
        flash("Creator deleted.", "success")
    else:
        flash("Creator not found.", "danger")
    return redirect(url_for("entity.creators"))


# ---------------------------------------------------------------------------
# Brand Contacts  (formerly Brand Representatives)
# ---------------------------------------------------------------------------

@entity_bp.route("/brand_contacts")
@login_required
def brand_contacts():
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_view("brand_contacts", user):
        abort(403)
    store = current_app.config["store"]
    data = store.load()
    all_contacts = data.get("brand_contacts", [])
    persons = {p["person_id"]: p for p in data.get("persons", [])}
    brands_map = {b["brand_id"]: b for b in data.get("brands", [])}
    enriched = []
    for contact in all_contacts:
        person = persons.get(contact.get("person_id"), {})
        brand = brands_map.get(contact.get("brand_id"), {})
        enriched.append({**contact, "person": person, "brand": brand})
    ctx = portal_context(user)
    ctx.update({
        "brand_contacts": enriched,
        "brands": data.get("brands", []),
        "all_persons": data.get("persons", []),
        "can_edit": policy.can_edit("brand_contacts", user),
        "can_delete": policy.can_delete("brand_contacts", user),
        "active_page": "brand_contacts",
    })
    return render_template("entities/brand_contacts.html", **ctx)


@entity_bp.route("/brand_contacts/add", methods=["POST"])
@login_required
def brand_contacts_add():
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_create("brand_contacts", user):
        abort(403)
    store = current_app.config["store"]
    bc_svc = current_app.config["brand_contact_service"]
    person_svc = current_app.config["person_service"]
    f = request.form
    try:
        person_id = _handle_person_form(f, store, person_svc)
        bc_svc.add_brand_contact(
            person_id=person_id,
            brand_id=int(f.get("brand_id", 0) or 0),
            notes=f.get("notes", ""),
        )
        flash("Brand contact added.", "success")
    except Exception as e:
        flash(f"Error adding brand contact: {e}", "danger")
    return redirect(url_for("entity.brand_contacts"))


@entity_bp.route("/brand_contacts/<int:bc_id>/edit", methods=["POST"])
@login_required
def brand_contacts_edit(bc_id: int):
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_update("brand_contacts", user):
        abort(403)
    bc_svc = current_app.config["brand_contact_service"]
    f = request.form
    updates = {
        "brand_id": int(f.get("brand_id", 0) or 0),
        "notes": f.get("notes", ""),
    }
    if bc_svc.update_brand_contact(bc_id, **updates):
        flash("Brand contact updated.", "success")
    else:
        flash("Brand contact not found.", "danger")
    return redirect(url_for("entity.brand_contacts"))


@entity_bp.route("/brand_contacts/<int:bc_id>/delete", methods=["POST"])
@login_required
def brand_contacts_delete(bc_id: int):
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_delete("brand_contacts", user):
        abort(403)
    bc_svc = current_app.config["brand_contact_service"]
    if bc_svc.delete_brand_contact(bc_id):
        flash("Brand contact deleted.", "success")
    else:
        flash("Brand contact not found.", "danger")
    return redirect(url_for("entity.brand_contacts"))


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
        "active_page": "brands",
    })
    return render_template("entities/brands.html", **ctx)


@entity_bp.route("/brands/add", methods=["POST"])
@login_required
def brands_add():
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_create("brands", user):
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
    if not policy.can_update("brands", user):
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
        "creators": data.get("creators", []),
        "brands": data.get("brands", []),
        "brand_contacts": data.get("brand_contacts", []),
        "can_edit": policy.can_edit("deals", user),
        "can_delete": policy.can_delete("deals", user),
        "active_page": "deals",
    })
    return render_template("entities/deals.html", **ctx)


@entity_bp.route("/deals/add", methods=["POST"])
@login_required
def deals_add():
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_create("deals", user):
        abort(403)
    deal_svc = current_app.config["deal_service"]
    f = request.form
    try:
        deal_svc.create_deal(
            client_id=int(f.get("creator_id", 0)),
            brand_id=int(f.get("brand_id", 0)),
            brand_rep_id=int(f.get("brand_contact_id", 0) or 0),
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
    if not policy.can_update("deals", user):
        abort(403)
    store = current_app.config["store"]
    f = request.form
    data = store.load()
    deal = next((d for d in data.get("deals", []) if d["deal_id"] == deal_id), None)
    if deal:
        deal.update({
            "creator_id": int(f.get("creator_id", deal.get("creator_id", deal.get("client_id", 0)))),
            "brand_id": int(f.get("brand_id", deal.get("brand_id", 0))),
            "brand_contact_id": int(f.get("brand_contact_id", 0) or 0),
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
        "active_page": "contracts",
    })
    return render_template("entities/contracts.html", **ctx)


@entity_bp.route("/contracts/add", methods=["POST"])
@login_required
def contracts_add():
    user = get_current_user()
    policy = current_app.config["access_policy"]
    if not policy.can_create("contracts", user):
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
    if not policy.can_update("contracts", user):
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
