from __future__ import annotations

from crm.persistence.json_store import JsonDataStore


class ApiV1Service:
    def __init__(self, store: JsonDataStore):
        self._store = store

    def _load(self) -> dict:
        return self._store.load()

    def _records(self, entity: str) -> list:
        return list(self._load().get(entity, []))

    def _id_field(self, entity: str) -> str:
        return {
            "roles": "role_id",
            "persons": "person_id",
            "users": "user_id",
            "employees": "employee_id",
            "creators": "creator_id",
            "social_media_accounts": "social_media_id",
            "brands": "brand_id",
            "brand_contacts": "brand_contact_id",
            "deals": "deal_id",
            "contracts": "contract_id",
        }[entity]

    def _model_name(self, entity: str) -> str:
        return {
            "roles": "role",
            "persons": "person",
            "users": "user",
            "employees": "employee",
            "creators": "creator",
            "social_media_accounts": "social_media_account",
            "brands": "brand",
            "brand_contacts": "brand_contact",
            "deals": "deal",
            "contracts": "contract",
        }[entity]

    def _creator_id(self, record: dict) -> int | None:
        value = record.get("creator_id")
        if value is not None:
            return value
        return record.get("client_id")

    def _scope_records(self, entity: str, user: dict, policy, records: list[dict]) -> list[dict]:
        if entity == "employees":
            return policy.scope_employees(user, records)
        if entity == "creators":
            return policy.scope_creators(user, records)
        if entity == "social_media_accounts":
            data = self._load()
            visible_creators = {creator.get("creator_id") for creator in policy.scope_creators(user, data.get("creators", []))}
            return [record for record in records if record.get("creator_id") in visible_creators]
        if entity == "deals":
            data = self._load()
            visible_creators = {creator.get("creator_id") for creator in policy.scope_creators(user, data.get("creators", []))}
            return [record for record in records if self._creator_id(record) in visible_creators]
        if entity == "contracts":
            visible_deals = {
                record.get("deal_id")
                for record in self._scope_records("deals", user, policy, self._records("deals"))
            }
            return [record for record in records if record.get("deal_id") in visible_deals]
        return records

    def _serialize_user(self, record: dict) -> dict:
        data = dict(record)
        data.pop("password", None)
        return data

    def _serialize_creator(self, record: dict) -> dict:
        data = dict(record)
        person = next((person for person in self._load().get("persons", []) if person.get("person_id") == record.get("person_id")), None)
        name = ""
        if person:
            name = person.get("display_name") or person.get("full_name") or ""
            if not name:
                first_name = person.get("first_name", "")
                last_name = person.get("last_name", "")
                name = (first_name + " " + last_name).strip()
        if not name:
            name = record.get("description", "")
        data["name"] = name
        return data

    def _serialize_deal(self, record: dict) -> dict:
        data = dict(record)
        return data

    def _serialize_contract(self, record: dict) -> dict:
        data = dict(record)
        return data

    def _serialize(self, entity: str, record: dict) -> dict:
        data = dict(record)
        if entity == "users":
            data = self._serialize_user(data)
        elif entity == "creators":
            data = self._serialize_creator(data)
        elif entity == "deals":
            data = self._serialize_deal(data)
        elif entity == "contracts":
            data = self._serialize_contract(data)
        data.setdefault("id", data.get(self._id_field(entity)))
        return data

    def list_for_user(self, entity: str, user: dict, policy) -> list[dict] | None:
        if not policy.can_view(entity, user):
            return None
        records = self._scope_records(entity, user, policy, self._records(entity))
        return [self._serialize(entity, record) for record in records]

    def get_for_user(self, entity: str, item_id: int, user: dict, policy) -> dict | None:
        if not policy.can_view(entity, user):
            return None
        records = self._records(entity)
        id_field = self._id_field(entity)
        target = next((record for record in records if record.get(id_field) == item_id), None)
        if target is None:
            return None
        scoped_ids = {record.get(id_field) for record in self._scope_records(entity, user, policy, records)}
        if item_id not in scoped_ids:
            return None
        return self._serialize(entity, target)
