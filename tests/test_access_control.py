import os
import pytest

from crm.persistence.json_store import JsonDataStore
from crm.policies.access_control import AccessPolicy


def _bootstrap_store(tmp_path: str) -> tuple[JsonDataStore, dict]:
    filepath = os.path.join(tmp_path, "test_data.json")
    store = JsonDataStore(filepath)
    data = store.load()

    for role_name in ["User", "Employee", "Manager", "Admin", "Client", "Rep"]:
        rid = store.next_id(data)
        data["roles"].append({"role_id": rid, "role_name": role_name})

    # Add persons and employees for manager / employee scope tests
    # Person 100 -> Employee 200 (manager), Person 101 -> Employee 201 (report)
    data["persons"] += [
        {"person_id": 100, "first_name": "Mgr", "last_name": "One", "full_name": "Mgr One",
         "display_name": "M1", "email": "m@e.com", "phone": "", "address": "", "city": "", "state": "", "zip": ""},
        {"person_id": 101, "first_name": "Emp", "last_name": "Two", "full_name": "Emp Two",
         "display_name": "E2", "email": "e@e.com", "phone": "", "address": "", "city": "", "state": "", "zip": ""},
    ]
    data["employees"] += [
        {"employee_id": 200, "person_id": 100, "position": "lead", "title": "Lead", "manager_id": 0,
         "start_date": "2020-01-01", "end_date": None, "is_active": True, "is_manager": True},
        {"employee_id": 201, "person_id": 101, "position": "dev", "title": "Dev", "manager_id": 200,
         "start_date": "2021-01-01", "end_date": None, "is_active": True, "is_manager": False},
    ]
    # Clients owned by employee 201
    data["clients"] += [
        {"client_id": 300, "employee_id": 201, "description": "Client A"},
        {"client_id": 301, "employee_id": 200, "description": "Client B"},
    ]
    store.save(data)
    return store, data


def _user(role_name: str, data: dict, person_id: int | None = None) -> dict:
    role = next(r for r in data["roles"] if r["role_name"] == role_name)
    return {"user_id": 999, "username": role_name.lower(), "password": "x",
            "role_id": role["role_id"], "person_id": person_id}


@pytest.fixture
def setup(tmp_path):
    store, data = _bootstrap_store(str(tmp_path))
    policy = AccessPolicy(store)
    return store, data, policy


class TestAdminAccess:
    def test_can_view_all(self, setup):
        store, data, policy = setup
        user = _user("Admin", data)
        for entity in ("employees", "clients", "deals", "contracts", "brands"):
            assert policy.can_view(entity, user) is True

    def test_can_edit_all(self, setup):
        store, data, policy = setup
        user = _user("Admin", data)
        for entity in ("employees", "clients", "deals", "contracts"):
            assert policy.can_edit(entity, user) is True

    def test_can_delete_all(self, setup):
        store, data, policy = setup
        user = _user("Admin", data)
        for entity in ("employees", "clients", "deals", "contracts"):
            assert policy.can_delete(entity, user) is True


class TestManagerAccess:
    def test_can_view_employees_and_clients(self, setup):
        store, data, policy = setup
        user = _user("Manager", data)
        assert policy.can_view("employees", user) is True
        assert policy.can_view("clients", user) is True

    def test_cannot_delete_employees(self, setup):
        store, data, policy = setup
        user = _user("Manager", data)
        assert policy.can_delete("employees", user) is False

    def test_can_delete_clients(self, setup):
        store, data, policy = setup
        user = _user("Manager", data)
        assert policy.can_delete("clients", user) is True


class TestEmployeeAccess:
    def test_can_view_own_clients_only(self, setup):
        store, data, policy = setup
        # Employee 201 owns person_id 101
        user = _user("Employee", data, person_id=101)
        all_clients = data["clients"]
        scoped = policy.scope_clients(user, all_clients)
        assert all(c["employee_id"] == 201 for c in scoped)
        assert len(scoped) == 1

    def test_cannot_delete_anything(self, setup):
        store, data, policy = setup
        user = _user("Employee", data)
        for entity in ("employees", "clients", "deals", "contracts"):
            assert policy.can_delete(entity, user) is False


class TestUserAccess:
    def test_can_view_deals_only(self, setup):
        store, data, policy = setup
        user = _user("User", data)
        assert policy.can_view("deals", user) is True
        assert policy.can_view("employees", user) is False
        assert policy.can_view("clients", user) is False

    def test_cannot_edit_anything(self, setup):
        store, data, policy = setup
        user = _user("User", data)
        for entity in ("employees", "clients", "deals", "contracts"):
            assert policy.can_edit(entity, user) is False
