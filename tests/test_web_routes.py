"""Smoke tests for the Flask web routes."""
import os
import pytest

from crm.ui.web.app import create_app
from crm.persistence.json_store import JsonDataStore
from crm.services.auth_service import AuthService


def _bootstrap(tmp_path: str) -> tuple[str, int]:
    """Create a minimal data.json and return (filepath, admin_user_id)."""
    filepath = os.path.join(tmp_path, "data.json")
    store = JsonDataStore(filepath)
    data = store.load()

    # Roles
    for role_name in ["User", "Employee", "Manager", "Admin"]:
        rid = store.next_id(data)
        data["roles"].append({"role_id": rid, "role_name": role_name})

    # Admin person + user
    person_id = store.next_id(data)
    data["persons"].append({
        "person_id": person_id, "first_name": "Ad", "last_name": "Min",
        "full_name": "Ad Min", "display_name": "Admin",
        "email": "a@b.com", "phone": "", "address": "", "city": "", "state": "", "zip": "",
    })
    admin_role = next(r for r in data["roles"] if r["role_name"] == "Admin")
    user_id = store.next_id(data)
    auth = AuthService(store)
    hashed = auth.hash_password("adminpass")
    data["users"].append({
        "user_id": user_id, "username": "admin_test",
        "password": hashed, "role_id": admin_role["role_id"], "person_id": person_id,
    })

    # Low-privilege user with a scoped employee + creator record
    low_person_id = store.next_id(data)
    data["persons"].append({
        "person_id": low_person_id, "first_name": "Low", "last_name": "User",
        "full_name": "Low User", "display_name": "Low User",
        "email": "low@example.com", "phone": "", "address": "", "city": "", "state": "", "zip": "",
    })
    low_user_role = next(r for r in data["roles"] if r["role_name"] == "User")
    low_user_id = store.next_id(data)
    low_auth = AuthService(store)
    low_hashed = low_auth.hash_password("lowpass")
    data["users"].append({
        "user_id": low_user_id, "username": "low_test",
        "password": low_hashed, "role_id": low_user_role["role_id"], "person_id": low_person_id,
    })

    employee_role = next(r for r in data["roles"] if r["role_name"] == "Employee")
    employee_user_id = store.next_id(data)
    employee_auth = AuthService(store)
    employee_hashed = employee_auth.hash_password("employeepass")
    data["users"].append({
        "user_id": employee_user_id, "username": "employee_test",
        "password": employee_hashed, "role_id": employee_role["role_id"], "person_id": low_person_id,
    })

    low_employee_id = store.next_id(data)
    data["employees"].append({
        "employee_id": low_employee_id,
        "person_id": low_person_id,
        "position": "Associate",
        "title": "Creator Liaison",
        "manager_id": 0,
        "start_date": "2024-01-01",
        "end_date": None,
        "is_active": True,
        "is_manager": False,
    })

    data["creators"].append({
        "creator_id": store.next_id(data),
        "person_id": low_person_id,
        "employee_id": low_employee_id,
        "description": "Low scope creator",
    })

    low_creator_id = data["creators"][-1]["creator_id"]

    data["creators"].append({
        "creator_id": store.next_id(data),
        "person_id": person_id,
        "employee_id": 999,
        "description": "Out of scope creator",
    })

    social_media_id = store.next_id(data)
    data["social_media_accounts"].append({
        "social_media_id": social_media_id,
        "creator_id": low_creator_id,
        "account_type": "Instagram",
        "link": "https://instagram.com/low-user",
    })

    brand_id = store.next_id(data)
    data["brands"].append({
        "brand_id": brand_id,
        "name": "Acme Media",
        "industry": "Media",
        "website": "https://acme.example.com",
        "notes": "Primary brand",
    })

    brand_contact_id = store.next_id(data)
    data["brand_contacts"].append({
        "brand_contact_id": brand_contact_id,
        "person_id": low_person_id,
        "brand_id": brand_id,
        "notes": "Brand contact for Acme Media",
    })

    deal_id = store.next_id(data)
    data["deals"].append({
        "deal_id": deal_id,
        "creator_id": low_creator_id,
        "brand_id": brand_id,
        "brand_contact_id": brand_contact_id,
        "pitch_date": "2024-02-01",
        "is_active": True,
        "is_successful": False,
    })

    contract_id = store.next_id(data)
    data["contracts"].append({
        "contract_id": contract_id,
        "deal_id": deal_id,
        "details": "Annual sponsorship contract",
        "payment": 5000.0,
        "agency_percentage": 12.5,
        "start_date": "2024-03-01",
        "end_date": "2024-12-31",
        "status": "Pending",
        "is_approved": False,
    })
    store.save(data)
    return filepath, user_id


@pytest.fixture
def client(tmp_path):
    filepath, admin_user_id = _bootstrap(str(tmp_path))
    app = create_app(data_path=filepath, storage_backend="json")
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as c:
        yield c, admin_user_id


def _login(c, username="admin_test", password="adminpass"):
    return c.post("/login", data={"username": username, "password": password}, follow_redirects=True)


class TestPublicRoutes:
    def test_homepage_accessible(self, client):
        c, _ = client
        resp = c.get("/")
        assert resp.status_code == 200
        assert b"Talent Connect" in resp.data

    def test_login_page_accessible(self, client):
        c, _ = client
        resp = c.get("/login")
        assert resp.status_code == 200

    def test_register_page_accessible(self, client):
        c, _ = client
        resp = c.get("/register")
        assert resp.status_code == 200

    def test_developers_page_accessible(self, client):
        c, _ = client
        resp = c.get("/developers")
        assert resp.status_code == 200
        assert b"API" in resp.data or b"Developers" in resp.data

    def test_portal_redirects_to_login_unauthenticated(self, client):
        c, _ = client
        resp = c.get("/portal/")
        assert resp.status_code in (301, 302)
        assert "/login" in resp.headers.get("Location", "")


class TestAuth:
    def test_login_success_redirects_to_portal(self, client):
        c, _ = client
        resp = _login(c)
        assert resp.status_code == 200
        assert b"Dashboard" in resp.data or b"Portal Home" in resp.data

    def test_login_bad_password_shows_error(self, client):
        c, _ = client
        resp = c.post("/login", data={"username": "admin_test", "password": "wrong"})
        assert resp.status_code == 200
        assert b"Invalid" in resp.data

    def test_logout_redirects_to_home(self, client):
        c, _ = client
        _login(c)
        resp = c.post("/logout", follow_redirects=False)
        assert resp.status_code in (301, 302)

    def test_register_new_user(self, client):
        c, _ = client
        resp = c.post("/register", data={
            "first_name": "Test", "last_name": "User",
            "email": "t@u.com", "phone": "",
            "username": "newuser123", "password": "password123",
        }, follow_redirects=True)
        assert resp.status_code == 200


class TestPortalAuthenticated:
    def test_portal_home_accessible(self, client):
        c, _ = client
        _login(c)
        resp = c.get("/portal/", follow_redirects=True)
        assert resp.status_code == 200
        assert b"Dashboard" in resp.data

    def test_search_page_accessible(self, client):
        c, _ = client
        _login(c)
        resp = c.get("/portal/search")
        assert resp.status_code == 200

    def test_search_with_query(self, client):
        c, _ = client
        _login(c)
        resp = c.get("/portal/search?q=admin")
        assert resp.status_code == 200

    def test_employees_page_accessible(self, client):
        c, _ = client
        _login(c)
        resp = c.get("/portal/employees")
        assert resp.status_code == 200

    def test_clients_page_redirects_to_creators(self, client):
        """Legacy /portal/clients should redirect to /portal/creators."""
        c, _ = client
        _login(c)
        resp = c.get("/portal/clients")
        assert resp.status_code in (301, 302)

    def test_creators_page_accessible(self, client):
        c, _ = client
        _login(c)
        resp = c.get("/portal/creators")
        assert resp.status_code == 200

    def test_brands_page_accessible(self, client):
        c, _ = client
        _login(c)
        resp = c.get("/portal/brands")
        assert resp.status_code == 200

    def test_deals_page_accessible(self, client):
        c, _ = client
        _login(c)
        resp = c.get("/portal/deals")
        assert resp.status_code == 200

    def test_contracts_page_accessible(self, client):
        c, _ = client
        _login(c)
        resp = c.get("/portal/contracts")
        assert resp.status_code == 200

    def test_performance_coming_soon(self, client):
        c, _ = client
        _login(c)
        resp = c.get("/portal/performance")
        assert resp.status_code == 200
        assert b"Coming Soon" in resp.data or b"coming soon" in resp.data.lower()

    def test_tasks_coming_soon(self, client):
        c, _ = client
        _login(c)
        resp = c.get("/portal/tasks")
        assert resp.status_code == 200

    def test_discover_coming_soon(self, client):
        c, _ = client
        _login(c)
        resp = c.get("/portal/discover")
        assert resp.status_code == 200

    def test_settings_page_accessible(self, client):
        c, _ = client
        _login(c)
        resp = c.get("/portal/settings")
        assert resp.status_code == 200


class TestRBAC:
    def test_low_privilege_user_gets_403_on_employees(self, client):
        """A 'User' role user cannot view the employees page."""
        c, _ = client
        # Register a new (User-role) account – auto-logs in via register route
        c.post("/register", data={
            "first_name": "Low", "last_name": "Priv",
            "email": "", "phone": "",
            "username": "lowpriv_test", "password": "testpass",
        }, follow_redirects=False)
        # The session now belongs to the newly registered low-privilege user;
        # confirm access is denied.
        resp = c.get("/portal/employees")
        assert resp.status_code == 403

    def test_admin_can_add_and_delete_employee(self, client):
        c, _ = client
        _login(c)
        # Need a person to associate with
        from crm.persistence.json_store import JsonDataStore
        app_store = c.application.config["store"]
        data = app_store.load()
        person = data["persons"][0]

        resp = c.post("/portal/employees/add", data={
            "person_id": str(person["person_id"]),
            "position": "Tester",
            "title": "QA",
            "manager_id": "0",
            "start_date": "2024-01-01",
            "end_date": "",
            "is_active": "on",
        }, follow_redirects=True)
        assert resp.status_code == 200

        # Verify in data
        data = app_store.load()
        emp = next((e for e in data.get("employees", []) if e["position"] == "Tester"), None)
        assert emp is not None

        # Delete it
        resp = c.post(f"/portal/employees/{emp['employee_id']}/delete", follow_redirects=True)
        assert resp.status_code == 200


class TestApiV1Creators:
    def test_api_requires_authentication(self, client):
        c, _ = client
        resp = c.get("/api/v1/items")
        assert resp.status_code == 401
        assert resp.is_json
        assert resp.get_json() == {"error": "Unauthorized"}

    def test_api_list_returns_scoped_items(self, client):
        c, _ = client
        _login(c, username="employee_test", password="employeepass")
        resp = c.get("/api/v1/items")
        assert resp.status_code == 200
        payload = resp.get_json()
        assert "items" in payload
        assert len(payload["items"]) == 1
        assert payload["items"][0]["name"] == "Low User"

    def test_api_detail_returns_in_scope_item(self, client):
        c, _ = client
        _login(c, username="employee_test", password="employeepass")
        resp = c.get("/api/v1/items")
        item_id = resp.get_json()["items"][0]["id"]

        detail = c.get(f"/api/v1/items/{item_id}")
        assert detail.status_code == 200
        payload = detail.get_json()
        assert payload["item"]["id"] == item_id

    def test_api_detail_returns_404_for_missing_item(self, client):
        c, _ = client
        _login(c, username="employee_test", password="employeepass")
        resp = c.get("/api/v1/items/999999")
        assert resp.status_code == 404
        assert resp.get_json() == {"error": "Not found"}

    def test_api_detail_returns_404_for_out_of_scope_item(self, client):
        c, _ = client
        _login(c, username="employee_test", password="employeepass")
        resp = c.get("/api/v1/items")
        low_item_id = resp.get_json()["items"][0]["id"]

        c.post("/logout", follow_redirects=False)
        admin_login = _login(c)
        assert admin_login.status_code == 200
        admin_resp = c.get("/api/v1/items")
        admin_items = admin_resp.get_json()["items"]
        out_of_scope_id = next(item["id"] for item in admin_items if item["id"] != low_item_id)

        c.post("/logout", follow_redirects=False)
        _login(c, username="employee_test", password="employeepass")
        detail = c.get(f"/api/v1/items/{out_of_scope_id}")
        assert detail.status_code == 404
        assert detail.get_json() == {"error": "Not found"}


class TestApiV1Models:
    @pytest.mark.parametrize(
        ("path", "list_key", "singular_key"),
        [
            ("roles", "roles", "role"),
            ("persons", "persons", "person"),
            ("users", "users", "user"),
            ("employees", "employees", "employee"),
            ("creators", "creators", "creator"),
            ("social_media_accounts", "social_media_accounts", "social_media_account"),
            ("brands", "brands", "brand"),
            ("brand_contacts", "brand_contacts", "brand_contact"),
            ("deals", "deals", "deal"),
            ("contracts", "contracts", "contract"),
        ],
    )
    def test_model_list_and_detail(self, client, path, list_key, singular_key):
        c, _ = client
        _login(c)
        resp = c.get(f"/api/v1/{path}")
        assert resp.status_code == 200
        payload = resp.get_json()
        assert list_key in payload
        assert len(payload[list_key]) >= 1

        first_item = payload[list_key][0]
        item_id = first_item.get("id")
        assert item_id is not None

        detail = c.get(f"/api/v1/{path}/{item_id}")
        assert detail.status_code == 200
        detail_payload = detail.get_json()
        assert singular_key in detail_payload
        assert detail_payload[singular_key].get("id") == item_id

    def test_users_api_omits_password(self, client):
        c, _ = client
        _login(c)
        resp = c.get("/api/v1/users")
        assert resp.status_code == 200
        first_item = resp.get_json()["users"][0]
        assert "password" not in first_item
