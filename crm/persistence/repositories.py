from __future__ import annotations
from typing import Callable
from crm.persistence.json_store import JsonDataStore


class Repository:
    """Stateless repository – every operation loads fresh data from the store."""

    def __init__(self, store: JsonDataStore, key: str):
        self._store = store
        self._key = key

    def all(self) -> list:
        return list(self._store.load().get(self._key, []))

    def get_by_id(self, id_field: str, value) -> dict | None:
        return next(
            (item for item in self._store.load().get(self._key, []) if item.get(id_field) == value),
            None,
        )

    def add(self, item: dict) -> dict:
        data = self._store.load()
        new_id = self._store.next_id(data)
        id_field = self._key.rstrip("s").replace("brand_representative", "brand_rep") + "_id"
        if id_field not in item:
            item = {id_field: new_id, **item}
        data.setdefault(self._key, []).append(item)
        self._store.save(data)
        return item

    def update(self, id_field: str, value, updates: dict) -> dict | None:
        data = self._store.load()
        for item in data.get(self._key, []):
            if item.get(id_field) == value:
                item.update(updates)
                self._store.save(data)
                return item
        return None

    def delete(self, id_field: str, value) -> bool:
        data = self._store.load()
        original = data.get(self._key, [])
        filtered = [item for item in original if item.get(id_field) != value]
        if len(filtered) == len(original):
            return False
        data[self._key] = filtered
        self._store.save(data)
        return True

    def find(self, predicate: Callable[[dict], bool]) -> list:
        return [item for item in self._store.load().get(self._key, []) if predicate(item)]


# ---------------------------------------------------------------------------
# Typed repositories – each pins its own key and id_field for convenience
# ---------------------------------------------------------------------------

class RoleRepository(Repository):
    ID_FIELD = "role_id"

    def __init__(self, store: JsonDataStore):
        super().__init__(store, "roles")

    def get(self, role_id: int) -> dict | None:
        return self.get_by_id(self.ID_FIELD, role_id)


class PersonRepository(Repository):
    ID_FIELD = "person_id"

    def __init__(self, store: JsonDataStore):
        super().__init__(store, "persons")

    def get(self, person_id: int) -> dict | None:
        return self.get_by_id(self.ID_FIELD, person_id)


class UserRepository(Repository):
    ID_FIELD = "user_id"

    def __init__(self, store: JsonDataStore):
        super().__init__(store, "users")

    def get(self, user_id: int) -> dict | None:
        return self.get_by_id(self.ID_FIELD, user_id)

    def get_by_username(self, username: str) -> dict | None:
        return next(
            (u for u in self._store.load().get("users", []) if u["username"] == username),
            None,
        )


class EmployeeRepository(Repository):
    ID_FIELD = "employee_id"

    def __init__(self, store: JsonDataStore):
        super().__init__(store, "employees")

    def get(self, employee_id: int) -> dict | None:
        return self.get_by_id(self.ID_FIELD, employee_id)


class ClientRepository(Repository):
    ID_FIELD = "client_id"

    def __init__(self, store: JsonDataStore):
        super().__init__(store, "clients")

    def get(self, client_id: int) -> dict | None:
        return self.get_by_id(self.ID_FIELD, client_id)


class BrandRepository(Repository):
    ID_FIELD = "brand_id"

    def __init__(self, store: JsonDataStore):
        super().__init__(store, "brands")

    def get(self, brand_id: int) -> dict | None:
        return self.get_by_id(self.ID_FIELD, brand_id)


class BrandRepRepository(Repository):
    ID_FIELD = "brand_rep_id"

    def __init__(self, store: JsonDataStore):
        super().__init__(store, "brand_representatives")

    def get(self, brand_rep_id: int) -> dict | None:
        return self.get_by_id(self.ID_FIELD, brand_rep_id)


class DealRepository(Repository):
    ID_FIELD = "deal_id"

    def __init__(self, store: JsonDataStore):
        super().__init__(store, "deals")

    def get(self, deal_id: int) -> dict | None:
        return self.get_by_id(self.ID_FIELD, deal_id)


class ContractRepository(Repository):
    ID_FIELD = "contract_id"

    def __init__(self, store: JsonDataStore):
        super().__init__(store, "contracts")

    def get(self, contract_id: int) -> dict | None:
        return self.get_by_id(self.ID_FIELD, contract_id)


class SocialMediaRepository(Repository):
    ID_FIELD = "social_media_id"

    def __init__(self, store: JsonDataStore):
        super().__init__(store, "social_media_accounts")

    def get(self, social_media_id: int) -> dict | None:
        return self.get_by_id(self.ID_FIELD, social_media_id)
