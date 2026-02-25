import json
import os
import tempfile
import pytest

from crm.persistence.json_store import JsonDataStore
from crm.services.auth_service import AuthService


def _make_store(tmp_path: str) -> JsonDataStore:
    """Create a JsonDataStore backed by a fresh temp file."""
    filepath = os.path.join(tmp_path, "test_data.json")
    store = JsonDataStore(filepath)
    data = store.load()
    # Bootstrap a 'User' role so register_user works
    role_id = store.next_id(data)
    data["roles"].append({"role_id": role_id, "role_name": "User"})
    store.save(data)
    return store


@pytest.fixture
def store(tmp_path):
    return _make_store(str(tmp_path))


@pytest.fixture
def auth(store):
    return AuthService(store)


class TestHashPassword:
    def test_returns_hash_not_plaintext(self, auth):
        hashed = auth.hash_password("secret")
        assert hashed != "secret"
        assert hashed.startswith(("pbkdf2:", "scrypt:"))


class TestVerifyPassword:
    def test_hashed_password_correct(self, auth):
        hashed = auth.hash_password("mypassword")
        assert auth.verify_password(hashed, "mypassword") is True

    def test_hashed_password_wrong(self, auth):
        hashed = auth.hash_password("mypassword")
        assert auth.verify_password(hashed, "wrong") is False

    def test_plaintext_migration_correct(self, auth):
        # Legacy plaintext passwords should compare directly
        assert auth.verify_password("admin", "admin") is True

    def test_plaintext_migration_wrong(self, auth):
        assert auth.verify_password("admin", "notadmin") is False


class TestAuthenticate:
    def test_returns_none_for_unknown_user(self, auth):
        assert auth.authenticate("nobody", "pass") is None

    def test_returns_none_for_wrong_password(self, auth):
        auth.register_user(
            {"first_name": "A", "last_name": "B", "full_name": "A B",
             "display_name": "AB", "email": "a@b.com", "phone": "", "address": "",
             "city": "", "state": "", "zip": ""},
            "testuser", "correctpass",
        )
        assert auth.authenticate("testuser", "wrongpass") is None

    def test_returns_user_dict_on_success(self, auth):
        auth.register_user(
            {"first_name": "A", "last_name": "B", "full_name": "A B",
             "display_name": "AB", "email": "a@b.com", "phone": "", "address": "",
             "city": "", "state": "", "zip": ""},
            "gooduser", "goodpass",
        )
        user = auth.authenticate("gooduser", "goodpass")
        assert user is not None
        assert user["username"] == "gooduser"

    def test_plaintext_password_upgraded_on_login(self, store, auth):
        """A stored plaintext password should be hashed after successful login."""
        data = store.load()
        user_id = store.next_id(data)
        person_id = store.next_id(data)
        role_id = data["roles"][0]["role_id"]
        data["persons"].append({"person_id": person_id, "first_name": "P", "last_name": "Q",
                                 "full_name": "P Q", "display_name": "PQ", "email": "p@q.com",
                                 "phone": "", "address": "", "city": "", "state": "", "zip": ""})
        data["users"].append({"user_id": user_id, "username": "legacy",
                               "password": "plaintext", "role_id": role_id, "person_id": person_id})
        store.save(data)
        # Re-init auth so it picks up fresh data
        fresh_auth = AuthService(store)
        result = fresh_auth.authenticate("legacy", "plaintext")
        assert result is not None
        # Password in store should now be hashed
        updated = store.load()
        stored_pw = next(u["password"] for u in updated["users"] if u["username"] == "legacy")
        assert stored_pw.startswith(("pbkdf2:", "scrypt:"))


class TestRegisterUser:
    def test_creates_user_with_hashed_password(self, auth, store):
        auth.register_user(
            {"first_name": "Jane", "last_name": "Doe", "full_name": "Jane Doe",
             "display_name": "Jane", "email": "jane@doe.com", "phone": "555-1234",
             "address": "123 St", "city": "SLC", "state": "UT", "zip": "84101"},
            "janedoe", "password123",
        )
        data = store.load()
        user = next((u for u in data["users"] if u["username"] == "janedoe"), None)
        assert user is not None
        assert user["password"] != "password123"
        assert user["password"].startswith(("pbkdf2:", "scrypt:"))

    def test_creates_person_record(self, auth, store):
        auth.register_user(
            {"first_name": "Bob", "last_name": "Smith", "full_name": "Bob Smith",
             "display_name": "Bob", "email": "bob@smith.com", "phone": "", "address": "",
             "city": "", "state": "", "zip": ""},
            "bobsmith", "pass",
        )
        data = store.load()
        person = next((p for p in data["persons"] if p["first_name"] == "Bob"), None)
        assert person is not None
        assert person["last_name"] == "Smith"
