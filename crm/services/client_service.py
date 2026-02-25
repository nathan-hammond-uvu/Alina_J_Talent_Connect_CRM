from crm.persistence.json_store import JsonDataStore
from crm.persistence.repositories import ClientRepository


class ClientService:
    def __init__(self, store: JsonDataStore):
        self._store = store
        self._clients = ClientRepository(store)

    def list_clients(self) -> list:
        return self._clients.all()

    def get_client(self, client_id: int) -> dict | None:
        return self._clients.get(client_id)

    def add_client(self, employee_id: int, description: str) -> dict:
        return self._clients.add({"employee_id": employee_id, "description": description})

    def update_client(self, client_id: int, **updates) -> dict | None:
        return self._clients.update(ClientRepository.ID_FIELD, client_id, updates)

    def delete_client(self, client_id: int) -> bool:
        return self._clients.delete(ClientRepository.ID_FIELD, client_id)

    def get_clients_for_employee(self, employee_id: int) -> list:
        return self._clients.find(lambda c: c.get("employee_id") == employee_id)
