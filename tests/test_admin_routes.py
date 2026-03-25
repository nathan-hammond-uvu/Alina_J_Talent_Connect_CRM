"""Tests for the admin DB dashboard routes (/admin/db).

These tests use the JSON backend (no real Postgres required).
They verify:
  - Non-admin users receive 403 on GET /admin/db
  - Non-admin users receive 403 on POST /admin/db/import
  - Admin users receive 200 on GET /admin/db
  - Admin users receive a redirect on POST /admin/db/import (JSON backend shows flash)
"""
from __future__ import annotations

import os
import pytest

from crm.ui.web.app import create_app
from crm.persistence.json_store import JsonDataStore
from crm.services.auth_service import AuthService


def _bootstrap(tmp_path: str) -> tuple[str, int, int]:
    """Create a data.json with admin and regular user. Returns (path, admin_id, user_id)."""
    filepath = os.path.join(tmp_path, "data.json")
    store = JsonDataStore(filepath)
    data = store.load()

    for role_name in ["User", "Employee", "Manager", "Admin"]:
        rid = store.next_id(data)
        data["roles"].append({"role_id": rid, "role_name": role_name})

    auth = AuthService(store)

    # Admin person + user
    admin_person_id = store.next_id(data)
    data["persons"].append({
        "person_id": admin_person_id, "first_name": "Ad", "last_name": "Min",
        "full_name": "Ad Min", "display_name": "Admin",
        "email": "admin@test.com", "phone": "", "address": "", "city": "", "state": "", "zip": "",
    })
    admin_role = next(r for r in data["roles"] if r["role_name"] == "Admin")
    admin_user_id = store.next_id(data)
    data["users"].append({
        "user_id": admin_user_id, "username": "admin_db_test",
        "password": auth.hash_password("adminpass"),
        "role_id": admin_role["role_id"], "person_id": admin_person_id,
    })

    # Regular user person + user
    user_person_id = store.next_id(data)
    data["persons"].append({
        "person_id": user_person_id, "first_name": "Re", "last_name": "Gular",
        "full_name": "Re Gular", "display_name": "Regular",
        "email": "regular@test.com", "phone": "", "address": "", "city": "", "state": "", "zip": "",
    })
    user_role = next(r for r in data["roles"] if r["role_name"] == "User")
    regular_user_id = store.next_id(data)
    data["users"].append({
        "user_id": regular_user_id, "username": "regular_db_test",
        "password": auth.hash_password("userpass"),
        "role_id": user_role["role_id"], "person_id": user_person_id,
    })

    store.save(data)
    return filepath, admin_user_id, regular_user_id


@pytest.fixture
def app_client(tmp_path):
    filepath, admin_id, regular_id = _bootstrap(str(tmp_path))
    app = create_app(data_path=filepath)
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as c:
        yield c, admin_id, regular_id


def _login(c, username, password):
    return c.post("/login", data={"username": username, "password": password}, follow_redirects=True)


class TestAdminDbDashboard:
    def test_unauthenticated_redirects_to_login(self, app_client):
        c, _, _ = app_client
        resp = c.get("/admin/db")
        # login_required decorator redirects unauthenticated users
        assert resp.status_code in (301, 302)
        assert "/login" in resp.headers.get("Location", "")

    def test_non_admin_gets_403(self, app_client):
        c, _, _ = app_client
        _login(c, "regular_db_test", "userpass")
        resp = c.get("/admin/db")
        assert resp.status_code == 403

    def test_admin_gets_200(self, app_client):
        c, _, _ = app_client
        _login(c, "admin_db_test", "adminpass")
        resp = c.get("/admin/db")
        assert resp.status_code == 200

    def test_dashboard_shows_backend_info(self, app_client):
        c, _, _ = app_client
        _login(c, "admin_db_test", "adminpass")
        resp = c.get("/admin/db")
        assert b"json" in resp.data.lower() or b"backend" in resp.data.lower()

    def test_dashboard_shows_db_dashboard_heading(self, app_client):
        c, _, _ = app_client
        _login(c, "admin_db_test", "adminpass")
        resp = c.get("/admin/db")
        assert b"Dashboard" in resp.data or b"dashboard" in resp.data.lower()


class TestAdminDbImport:
    def test_non_admin_import_gets_403(self, app_client):
        c, _, _ = app_client
        _login(c, "regular_db_test", "userpass")
        resp = c.post("/admin/db/import")
        assert resp.status_code == 403

    def test_unauthenticated_import_redirects_to_login(self, app_client):
        c, _, _ = app_client
        resp = c.post("/admin/db/import")
        assert resp.status_code in (301, 302)
        assert "/login" in resp.headers.get("Location", "")

    def test_admin_import_on_json_backend_shows_warning(self, app_client):
        """POST /admin/db/import with JSON backend flashes a warning and redirects."""
        c, _, _ = app_client
        _login(c, "admin_db_test", "adminpass")
        resp = c.post("/admin/db/import", follow_redirects=True)
        # Should redirect back to dashboard (follow_redirects=True → 200)
        assert resp.status_code == 200
        # Flash message about JSON backend
        assert b"PostgreSQL" in resp.data or b"postgres" in resp.data.lower() or b"Import" in resp.data


class TestAdminResetPassword:
    def test_reset_password_rejected_on_json_backend(self, app_client):
        c, _, _ = app_client
        _login(c, "admin_db_test", "adminpass")
        resp = c.post(
            "/admin/db/users/reset-password",
            data={"user_id": "1", "new_password": "newpass123", "confirm_password": "newpass123"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b"database backend" in resp.data.lower()

    def test_admin_can_reset_password_on_sqlite_backend(self, tmp_path, monkeypatch):
        filepath, _admin_id, _regular_id = _bootstrap(str(tmp_path))
        sqlite_path = os.path.join(str(tmp_path), "test_admin_reset.db")

        monkeypatch.setenv("CRM_STORAGE_BACKEND", "sqlite")
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{sqlite_path}")
        monkeypatch.setenv("CRM_AUTO_IMPORT", "1")

        app = create_app(data_path=filepath)
        app.config["TESTING"] = True
        app.config["WTF_CSRF_ENABLED"] = False

        with app.test_client() as c:
            _login(c, "admin_db_test", "adminpass")
            resp = c.post(
                "/admin/db/users/reset-password",
                data={
                    "user_id": str(_regular_id),
                    "new_password": "resetpass123",
                    "confirm_password": "resetpass123",
                },
                follow_redirects=True,
            )
            assert resp.status_code == 200
            assert b"Password reset successfully" in resp.data

        auth = app.config["auth_service"]
        assert auth.authenticate("regular_db_test", "userpass") is None
        assert auth.authenticate("regular_db_test", "resetpass123") is not None


class TestAdminNavLink:
    def test_admin_sees_db_dashboard_link(self, app_client):
        """Admin user should see the DB Dashboard link in the sidebar."""
        c, _, _ = app_client
        _login(c, "admin_db_test", "adminpass")
        resp = c.get("/portal/")
        assert resp.status_code == 200
        assert b"DB Dashboard" in resp.data or b"admin/db" in resp.data

    def test_non_admin_does_not_see_db_dashboard_link(self, app_client):
        """Regular user should NOT see the DB Dashboard link."""
        c, _, _ = app_client
        _login(c, "regular_db_test", "userpass")
        resp = c.get("/portal/")
        assert resp.status_code == 200
        assert b"DB Dashboard" not in resp.data
