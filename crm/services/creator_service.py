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
