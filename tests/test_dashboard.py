"""Tests for DashboardService and the /portal/dashboard route."""
import os
from datetime import date, timedelta

import pytest

from crm.persistence.json_store import JsonDataStore
from crm.services.auth_service import AuthService
from crm.services.dashboard_service import DashboardService
from crm.ui.web.app import create_app


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_store(tmp_path: str) -> JsonDataStore:
    filepath = os.path.join(tmp_path, "test_data.json")
    return JsonDataStore(filepath)


def _bootstrap_app(tmp_path: str) -> tuple[str, int]:
    """Minimal data.json with an admin user; returns (path, user_id)."""
    filepath = os.path.join(tmp_path, "data.json")
    store = JsonDataStore(filepath)
    data = store.load()

    for role_name in ["User", "Employee", "Manager", "Admin"]:
        rid = store.next_id(data)
        data["roles"].append({"role_id": rid, "role_name": role_name})

    person_id = store.next_id(data)
    data["persons"].append({
        "person_id": person_id, "first_name": "Ad", "last_name": "Min",
        "full_name": "Ad Min", "display_name": "Admin",
        "email": "a@b.com", "phone": "", "address": "",
        "city": "", "state": "", "zip": "",
    })
    admin_role = next(r for r in data["roles"] if r["role_name"] == "Admin")
    user_id = store.next_id(data)
    auth = AuthService(store)
    hashed = auth.hash_password("adminpass")
    data["users"].append({
        "user_id": user_id, "username": "admin_test",
        "password": hashed, "role_id": admin_role["role_id"],
        "person_id": person_id,
    })
    store.save(data)
    return filepath, user_id


@pytest.fixture
def store(tmp_path):
    return _make_store(str(tmp_path))


@pytest.fixture
def client(tmp_path):
    filepath, admin_user_id = _bootstrap_app(str(tmp_path))
    app = create_app(data_path=filepath, storage_backend="json")
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c, admin_user_id


def _login(c, username="admin_test", password="adminpass"):
    return c.post("/login", data={"username": username, "password": password},
                  follow_redirects=True)


# ---------------------------------------------------------------------------
# DashboardService unit tests
# ---------------------------------------------------------------------------

class TestDashboardServiceEmptyData:
    def test_build_returns_required_keys(self, store):
        svc = DashboardService(store)
        result = svc.build(user={})
        assert "cards" in result
        assert "needs_attention" in result
        assert "quick_actions" in result
        assert "recent_activity" in result

    def test_cards_have_expected_ids(self, store):
        svc = DashboardService(store)
        cards = svc.build(user={})["cards"]
        ids = [c["id"] for c in cards]
        assert "talent" in ids
        assert "brands" in ids
        assert "active_deals" in ids
        assert "contracts" in ids

    def test_empty_store_gives_zero_counts(self, store):
        svc = DashboardService(store)
        cards = svc.build(user={})["cards"]
        for card in cards:
            assert card["value"] == 0

    def test_needs_attention_empty_when_no_data(self, store):
        svc = DashboardService(store)
        assert svc.build(user={})["needs_attention"] == []

    def test_recent_activity_empty_when_no_data(self, store):
        svc = DashboardService(store)
        assert svc.build(user={})["recent_activity"] == []

    def test_quick_actions_always_present(self, store):
        svc = DashboardService(store)
        actions = svc.build(user={})["quick_actions"]
        assert len(actions) >= 3
        for action in actions:
            assert "label" in action
            assert "url" in action


class TestDashboardServiceCounts:
    def test_creator_count(self, store):
        data = store.load()
        data["creators"].append({"creator_id": 1, "person_id": 1, "employee_id": 1, "description": "A"})
        data["creators"].append({"creator_id": 2, "person_id": 2, "employee_id": 1, "description": "B"})
        store.save(data)
        svc = DashboardService(store)
        cards = {c["id"]: c for c in svc.build(user={})["cards"]}
        assert cards["talent"]["value"] == 2

    def test_brand_count(self, store):
        data = store.load()
        data["brands"].append({"brand_id": 1, "description": "Acme"})
        store.save(data)
        svc = DashboardService(store)
        cards = {c["id"]: c for c in svc.build(user={})["cards"]}
        assert cards["brands"]["value"] == 1

    def test_active_deal_count_excludes_inactive(self, store):
        data = store.load()
        data["deals"].append({
            "deal_id": 1, "client_id": 1, "brand_id": 1,
            "brand_rep_id": 0, "pitch_date": "2024-01-01",
            "is_active": True, "is_successful": False,
        })
        data["deals"].append({
            "deal_id": 2, "client_id": 1, "brand_id": 1,
            "brand_rep_id": 0, "pitch_date": "2023-01-01",
            "is_active": False, "is_successful": True,
        })
        store.save(data)
        svc = DashboardService(store)
        cards = {c["id"]: c for c in svc.build(user={})["cards"]}
        assert cards["active_deals"]["value"] == 1


class TestDashboardServiceNeedsAttention:
    def test_expiring_contract_flagged(self, store):
        data = store.load()
        soon = (date.today() + timedelta(days=10)).isoformat()
        data["contracts"].append({
            "contract_id": 1, "deal_id": 1, "details": "",
            "payment": 0, "agency_percentage": 0,
            "start_date": "2024-01-01", "end_date": soon,
            "status": "Active", "is_approved": True,
        })
        store.save(data)
        svc = DashboardService(store)
        items = svc.build(user={})["needs_attention"]
        types = [i["type"] for i in items]
        assert "contract_expiring" in types

    def test_far_future_contract_not_flagged(self, store):
        data = store.load()
        far = (date.today() + timedelta(days=90)).isoformat()
        data["contracts"].append({
            "contract_id": 1, "deal_id": 1, "details": "",
            "payment": 0, "agency_percentage": 0,
            "start_date": "2024-01-01", "end_date": far,
            "status": "Active", "is_approved": True,
        })
        store.save(data)
        svc = DashboardService(store)
        items = svc.build(user={})["needs_attention"]
        types = [i["type"] for i in items]
        assert "contract_expiring" not in types

    def test_contract_missing_dates_flagged(self, store):
        data = store.load()
        data["contracts"].append({
            "contract_id": 2, "deal_id": 1, "details": "",
            "payment": 0, "agency_percentage": 0,
            "start_date": "", "end_date": "",
            "status": "Draft", "is_approved": False,
        })
        store.save(data)
        svc = DashboardService(store)
        items = svc.build(user={})["needs_attention"]
        types = [i["type"] for i in items]
        assert "contract_missing_dates" in types

    def test_deal_without_contract_flagged(self, store):
        data = store.load()
        data["deals"].append({
            "deal_id": 99, "client_id": 1, "brand_id": 1,
            "brand_rep_id": 0, "pitch_date": "2024-01-01",
            "is_active": True, "is_successful": False,
        })
        store.save(data)
        svc = DashboardService(store)
        items = svc.build(user={})["needs_attention"]
        types = [i["type"] for i in items]
        assert "deal_no_contract" in types

    def test_deal_with_contract_not_flagged(self, store):
        data = store.load()
        data["deals"].append({
            "deal_id": 10, "client_id": 1, "brand_id": 1,
            "brand_rep_id": 0, "pitch_date": "2024-01-01",
            "is_active": True, "is_successful": False,
        })
        far = (date.today() + timedelta(days=90)).isoformat()
        data["contracts"].append({
            "contract_id": 10, "deal_id": 10, "details": "",
            "payment": 0, "agency_percentage": 0,
            "start_date": "2024-01-01", "end_date": far,
            "status": "Active", "is_approved": True,
        })
        store.save(data)
        svc = DashboardService(store)
        items = svc.build(user={})["needs_attention"]
        types = [i["type"] for i in items]
        assert "deal_no_contract" not in types

    def test_needs_attention_capped_at_ten(self, store):
        data = store.load()
        # Add 15 deals without contracts
        for i in range(1, 16):
            data["deals"].append({
                "deal_id": i, "client_id": 1, "brand_id": 1,
                "brand_rep_id": 0, "pitch_date": "2024-01-01",
                "is_active": True, "is_successful": False,
            })
        store.save(data)
        svc = DashboardService(store)
        items = svc.build(user={})["needs_attention"]
        assert len(items) <= 10


class TestDashboardServiceRecentActivity:
    def test_recent_activity_includes_creators(self, store):
        data = store.load()
        data["creators"].append({
            "creator_id": 1, "person_id": 1, "employee_id": 1, "description": "A"
        })
        data["persons"].append({
            "person_id": 1, "first_name": "Alice", "last_name": "Smith",
            "full_name": "Alice Smith", "display_name": "Alice",
            "email": "", "phone": "", "address": "", "city": "", "state": "", "zip": "",
        })
        store.save(data)
        svc = DashboardService(store)
        activity = svc.build(user={})["recent_activity"]
        types = [a["type"] for a in activity]
        assert "Creator" in types

    def test_recent_activity_capped_at_eight(self, store):
        data = store.load()
        for i in range(1, 15):
            data["creators"].append({
                "creator_id": i, "person_id": i, "employee_id": 1, "description": f"C{i}"
            })
        store.save(data)
        svc = DashboardService(store)
        activity = svc.build(user={})["recent_activity"]
        assert len(activity) <= 8


# ---------------------------------------------------------------------------
# Route tests
# ---------------------------------------------------------------------------

class TestDashboardRoute:
    def test_unauthenticated_redirects_to_login(self, client):
        c, _ = client
        resp = c.get("/portal/dashboard")
        assert resp.status_code in (301, 302)
        assert "/login" in resp.headers.get("Location", "")

    def test_authenticated_gets_200(self, client):
        c, _ = client
        _login(c)
        resp = c.get("/portal/dashboard")
        assert resp.status_code == 200

    def test_dashboard_contains_key_sections(self, client):
        c, _ = client
        _login(c)
        resp = c.get("/portal/dashboard")
        assert b"Dashboard" in resp.data
        assert b"Overview" in resp.data
        assert b"Quick Actions" in resp.data

    def test_portal_home_redirects_to_dashboard(self, client):
        c, _ = client
        _login(c)
        resp = c.get("/portal/", follow_redirects=False)
        assert resp.status_code in (301, 302)
        assert "dashboard" in resp.headers.get("Location", "")

    def test_login_redirects_to_dashboard(self, client):
        c, _ = client
        resp = _login(c)
        assert resp.status_code == 200
        assert b"Dashboard" in resp.data
