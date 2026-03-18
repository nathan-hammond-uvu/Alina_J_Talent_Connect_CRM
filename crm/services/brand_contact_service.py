from crm.persistence.json_store import JsonDataStore
from crm.persistence.repositories import BrandContactRepository


class BrandContactService:
    def __init__(self, store: JsonDataStore):
        self._store = store
        self._contacts = BrandContactRepository(store)

    def list_brand_contacts(self) -> list:
        return self._contacts.all()

    def get_brand_contact(self, brand_contact_id: int) -> dict | None:
        return self._contacts.get(brand_contact_id)

    def add_brand_contact(self, person_id: int, brand_id: int = 0, notes: str = "") -> dict:
        return self._contacts.add({
            "person_id": person_id,
            "brand_id": brand_id,
            "notes": notes,
        })

    def update_brand_contact(self, brand_contact_id: int, **updates) -> dict | None:
        return self._contacts.update(BrandContactRepository.ID_FIELD, brand_contact_id, updates)

    def delete_brand_contact(self, brand_contact_id: int) -> bool:
        return self._contacts.delete(BrandContactRepository.ID_FIELD, brand_contact_id)

    def get_contacts_for_brand(self, brand_id: int) -> list:
        return self._contacts.find(lambda c: c.get("brand_id") == brand_id)
