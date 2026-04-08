from flask import Blueprint, render_template, request, redirect, url_for, current_app

from crm.ui.web.routes.helpers import login_required, get_current_user, portal_context

portal_bp = Blueprint("portal", __name__, url_prefix="/portal")


@portal_bp.route("/")
@login_required
def portal_home():
    return redirect(url_for("dashboard.dashboard"))


@portal_bp.route("/search")
@login_required
def search():
    user = get_current_user()
    ctx = portal_context(user)
    query = request.args.get("q", "").strip()
    results = []

    if query:
        store = current_app.config["store"]
        policy = current_app.config["access_policy"]
        data = store.load()
        q = query.lower()

        def _matches(record: dict) -> bool:
            return any(q in str(v).lower() for v in record.values())

        # Employees
        if policy.can_view("employees", user):
            all_emp = data.get("employees", [])
            scoped = policy.scope_employees(user, all_emp)
            persons = {p["person_id"]: p for p in data.get("persons", [])}
            for emp in scoped:
                person = persons.get(emp.get("person_id"), {})
                combined = {**emp, **{f"person_{k}": v for k, v in person.items()}}
                if _matches(combined):
                    label = person.get("full_name") or person.get("display_name") or f"Employee #{emp['employee_id']}"
                    results.append({
                        "type": "Employee",
                        "label": label,
                        "url": f"/portal/employees#{emp['employee_id']}",
                        "id": emp["employee_id"],
                    })

        # Creators (formerly Clients)
        if policy.can_view("creators", user):
            all_creators = data.get("creators", [])
            scoped = policy.scope_creators(user, all_creators)
            persons = {p["person_id"]: p for p in data.get("persons", [])}
            for creator in scoped:
                person = persons.get(creator.get("person_id"), {})
                combined = {**creator, **{f"person_{k}": v for k, v in person.items()}}
                if _matches(combined):
                    label = person.get("full_name") or person.get("display_name") or creator.get("description") or f"Creator #{creator['creator_id']}"
                    results.append({
                        "type": "Creator",
                        "label": label,
                        "url": f"/portal/creators#{creator['creator_id']}",
                        "id": creator["creator_id"],
                    })

        # Brand Contacts
        if policy.can_view("brand_contacts", user):
            bc_persons = {p["person_id"]: p for p in data.get("persons", [])}
            for contact in data.get("brand_contacts", []):
                person = bc_persons.get(contact.get("person_id"), {})
                combined = {**contact, **{f"person_{k}": v for k, v in person.items()}}
                if _matches(combined):
                    label = person.get("full_name") or person.get("display_name") or f"Brand Contact #{contact['brand_contact_id']}"
                    results.append({
                        "type": "Brand Contact",
                        "label": label,
                        "url": f"/portal/brand_contacts#{contact['brand_contact_id']}",
                        "id": contact["brand_contact_id"],
                    })

        # Brands
        if policy.can_view("brands", user):
            for brand in data.get("brands", []):
                if _matches(brand):
                    results.append({
                        "type": "Brand",
                        "label": brand.get("name") or brand.get("brand_name") or f"Brand #{brand['brand_id']}",
                        "url": f"/portal/brands#{brand['brand_id']}",
                        "id": brand["brand_id"],
                    })

        # Deals
        if policy.can_view("deals", user):
            for deal in data.get("deals", []):
                if _matches(deal):
                    results.append({
                        "type": "Deal",
                        "label": f"Deal #{deal['deal_id']}",
                        "url": f"/portal/deals#{deal['deal_id']}",
                        "id": deal["deal_id"],
                    })

        # Contracts
        if policy.can_view("contracts", user):
            for contract in data.get("contracts", []):
                if _matches(contract):
                    results.append({
                        "type": "Contract",
                        "label": f"Contract #{contract['contract_id']}",
                        "url": f"/portal/contracts#{contract['contract_id']}",
                        "id": contract["contract_id"],
                    })

    ctx["query"] = query
    ctx["results"] = results
    return render_template("portal/search.html", **ctx)


@portal_bp.route("/performance")
@login_required
def performance():
    user = get_current_user()
    ctx = portal_context(user)
    ctx["page_title"] = "Performance"
    return render_template("portal/coming_soon.html", **ctx)


@portal_bp.route("/tasks")
@login_required
def tasks():
    user = get_current_user()
    ctx = portal_context(user)
    ctx["page_title"] = "Tasks"
    return render_template("portal/coming_soon.html", **ctx)


@portal_bp.route("/discover")
@login_required
def discover():
    user = get_current_user()
    ctx = portal_context(user)
    ctx["page_title"] = "Discover"
    return render_template("portal/coming_soon.html", **ctx)
