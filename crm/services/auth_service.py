from werkzeug.security import generate_password_hash, check_password_hash

from crm.persistence.json_store import JsonDataStore
from crm.persistence.repositories import UserRepository, PersonRepository, RoleRepository


class AuthService:
    def __init__(self, store: JsonDataStore):
        self._store = store
        self._users = UserRepository(store)
        self._persons = PersonRepository(store)
        self._roles = RoleRepository(store)

    def hash_password(self, password: str) -> str:
        return generate_password_hash(password)

    def verify_password(self, stored_hash: str, password: str) -> bool:
        """Handle both hashed and legacy plaintext passwords."""
        if stored_hash.startswith(("pbkdf2:", "scrypt:", "$2b$", "$2a$")):
            return check_password_hash(stored_hash, password)
        # Plaintext comparison for migration path
        return stored_hash == password

    def authenticate(self, username: str, password: str) -> dict | None:
        """Return the user dict on success, None otherwise.

        On a successful plaintext login the password is upgraded to a hash
        so future logins use the secure path.
        """
        user = self._users.get_by_username(username)
        if user is None:
            return None

        stored = user["password"]
        if not self.verify_password(stored, password):
            return None

        # Upgrade plaintext password to hash on first use
        if not stored.startswith(("pbkdf2:", "scrypt:", "$2b$", "$2a$")):
            data = self._store.load()
            for u in data.get("users", []):
                if u["user_id"] == user["user_id"]:
                    u["password"] = self.hash_password(password)
                    user = dict(user)
                    user["password"] = u["password"]
                    break
            self._store.save(data)

        return user

    def register_user(self, person_fields: dict, username: str, password: str) -> dict:
        """Create a Person + User, returning the new user dict."""
        data = self._store.load()

        role = next((r for r in data.get("roles", []) if r["role_name"] == "User"), None)
        if not role:
            raise ValueError("Default 'User' role not found.")

        person_id = self._store.next_id(data)
        person = {
            "person_id": person_id,
            "first_name": person_fields.get("first_name", ""),
            "last_name": person_fields.get("last_name", ""),
            "full_name": person_fields.get("full_name", ""),
            "display_name": person_fields.get("display_name", ""),
            "email": person_fields.get("email", ""),
            "phone": person_fields.get("phone", ""),
            "address": person_fields.get("address", ""),
            "city": person_fields.get("city", ""),
            "state": person_fields.get("state", ""),
            "zip": person_fields.get("zip", ""),
        }
        data.setdefault("persons", []).append(person)

        user_id = self._store.next_id(data)
        user = {
            "user_id": user_id,
            "username": username,
            "password": self.hash_password(password),
            "role_id": role["role_id"],
            "person_id": person_id,
        }
        data.setdefault("users", []).append(user)
        self._store.save(data)
        return user
