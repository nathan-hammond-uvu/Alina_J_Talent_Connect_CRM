from crm.persistence.json_store import JsonDataStore
from crm.persistence.repositories import EmployeeRepository


class EmployeeService:
    def __init__(self, store: JsonDataStore):
        self._store = store
        self._employees = EmployeeRepository(store)

    def list_employees(self) -> list:
        return self._employees.all()

    def get_employee(self, employee_id: int) -> dict | None:
        return self._employees.get(employee_id)

    def add_employee(
        self,
        person_id: int,
        position: str,
        title: str,
        manager_id: int,
        start_date: str,
        end_date: str | None,
        is_active: bool,
        is_manager: bool,
    ) -> dict:
        return self._employees.add({
            "person_id": person_id,
            "position": position,
            "title": title,
            "manager_id": manager_id,
            "start_date": start_date,
            "end_date": end_date,
            "is_active": is_active,
            "is_manager": is_manager,
        })

    def update_employee(self, employee_id: int, **updates) -> dict | None:
        return self._employees.update(EmployeeRepository.ID_FIELD, employee_id, updates)

    def delete_employee(self, employee_id: int) -> bool:
        return self._employees.delete(EmployeeRepository.ID_FIELD, employee_id)

    def get_direct_reports(self, manager_employee_id: int) -> list:
        return self._employees.find(lambda e: e.get("manager_id") == manager_employee_id)
