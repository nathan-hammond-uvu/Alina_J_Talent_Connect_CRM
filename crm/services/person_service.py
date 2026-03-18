from crm.persistence.json_store import JsonDataStore
from crm.persistence.repositories import PersonRepository


class PersonService:
    def __init__(self, store: JsonDataStore):
        self._store = store
        self._persons = PersonRepository(store)

    def list_persons(self) -> list:
        return self._persons.all()

    def get_person(self, person_id: int) -> dict | None:
        return self._persons.get(person_id)

    def create_person(
        self,
        first_name: str,
        last_name: str,
        email: str = "",
        phone: str = "",
        address: str = "",
        city: str = "",
        state: str = "",
        zip_code: str = "",
        display_name: str = "",
    ) -> dict:
        full_name = f"{first_name} {last_name}".strip()
        return self._persons.add({
            "first_name": first_name,
            "last_name": last_name,
            "full_name": full_name,
            "display_name": display_name or full_name,
            "email": email,
            "phone": phone,
            "address": address,
            "city": city,
            "state": state,
            "zip": zip_code,
        })

    def find_or_create_person(
        self,
        person_id: int | None,
        first_name: str = "",
        last_name: str = "",
        email: str = "",
        phone: str = "",
        address: str = "",
        city: str = "",
        state: str = "",
        zip_code: str = "",
        display_name: str = "",
    ) -> dict:
        """Return an existing person by ID, or create a new one.

        If `person_id` is provided and the record exists, return it.
        Otherwise create a new Person record with the supplied fields.
        """
        if person_id:
            existing = self.get_person(person_id)
            if existing:
                return existing
        return self.create_person(
            first_name=first_name,
            last_name=last_name,
            email=email,
            phone=phone,
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            display_name=display_name,
        )

    def update_person(self, person_id: int, **updates) -> dict | None:
        return self._persons.update(PersonRepository.ID_FIELD, person_id, updates)
