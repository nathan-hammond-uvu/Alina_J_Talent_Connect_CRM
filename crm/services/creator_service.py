from crm.persistence.json_store import JsonDataStore
from crm.persistence.repositories import CreatorRepository


class CreatorService:
    def __init__(self, store: JsonDataStore):
        self._store = store
        self._creators = CreatorRepository(store)

    def list_creators(self) -> list:
        return self._creators.all()

    def get_creator(self, creator_id: int) -> dict | None:
        return self._creators.get(creator_id)

    def add_creator(self, person_id: int, employee_id: int, description: str = "") -> dict:
        return self._creators.add({
            "person_id": person_id,
            "employee_id": employee_id,
            "description": description,
        })

    def update_creator(self, creator_id: int, **updates) -> dict | None:
        return self._creators.update(CreatorRepository.ID_FIELD, creator_id, updates)

    def delete_creator(self, creator_id: int) -> bool:
        return self._creators.delete(CreatorRepository.ID_FIELD, creator_id)

    def get_creators_for_employee(self, employee_id: int) -> list:
        return self._creators.find(lambda c: c.get("employee_id") == employee_id)

    def _serialize_creator(self, creator: dict, person: dict | None = None) -> dict:
        name = ""
        if person:
            name = person.get("display_name") or person.get("full_name") or ""
            if not name:
                first_name = person.get("first_name", "")
                last_name = person.get("last_name", "")
                name = (first_name + " " + last_name).strip()
        if not name:
            name = creator.get("description", "")
        return {
            "id": creator.get("creator_id"),
            "creator_id": creator.get("creator_id"),
            "person_id": creator.get("person_id"),
            "employee_id": creator.get("employee_id"),
            "name": name,
            "description": creator.get("description", ""),
        }

    def list_creators_for_user(self, user: dict, policy) -> list:
        data = self._store.load()
        visible_creators = policy.scope_creators(user, data.get("creators", []))
        persons = {p.get("person_id"): p for p in data.get("persons", [])}
        return [self._serialize_creator(creator, persons.get(creator.get("person_id"))) for creator in visible_creators]

    def get_creator_for_user(self, user: dict, creator_id: int, policy) -> dict | None:
        data = self._store.load()
        creator = next((c for c in data.get("creators", []) if c.get("creator_id") == creator_id), None)
        if creator is None:
            return None
        visible_ids = {item.get("creator_id") for item in policy.scope_creators(user, data.get("creators", []))}
        if creator_id not in visible_ids:
            return None
        person = next((p for p in data.get("persons", []) if p.get("person_id") == creator.get("person_id")), None)
        return self._serialize_creator(creator, person)
