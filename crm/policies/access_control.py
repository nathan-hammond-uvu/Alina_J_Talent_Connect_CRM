from crm.persistence.json_store import JsonDataStore
from crm.persistence.repositories import RoleRepository


class AccessPolicy:
    """RBAC-based access control."""

    ROLE_HIERARCHY: dict[str, int] = {
        "Admin": 4,
        "Manager": 3,
        "Employee": 2,
        "User": 1,
        "Client": 1,
        "Rep": 1,
    }

    def __init__(self, store: JsonDataStore):
        self._store = store
        self._roles = RoleRepository(store)

    def _get_role_name(self, user: dict) -> str:
        role = self._roles.get(user.get("role_id"))
        return role["role_name"] if role else "User"

    def can_view(self, entity_type: str, user: dict) -> bool:
        role_name = self._get_role_name(user)
        if role_name == "Admin":
            return True
        if role_name == "Manager":
            return entity_type in {"employees", "clients", "deals", "contracts", "brands"}
        if role_name == "Employee":
            return entity_type in {"clients", "deals", "brands"}
        # User / Client / Rep
        return entity_type in {"deals"}

    def can_edit(self, entity_type: str, user: dict) -> bool:
        role_name = self._get_role_name(user)
        if role_name == "Admin":
            return True
        if role_name == "Manager":
            return entity_type in {"employees", "clients", "deals", "contracts"}
        if role_name == "Employee":
            return entity_type in {"clients"}
        return False

    def can_delete(self, entity_type: str, user: dict) -> bool:
        role_name = self._get_role_name(user)
        if role_name == "Admin":
            return True
        if role_name == "Manager":
            return entity_type in {"clients", "deals"}
        return False

    def scope_clients(self, user: dict, all_clients: list) -> list:
        """Return the subset of clients the user may see."""
        role_name = self._get_role_name(user)
        if role_name in {"Admin", "Manager"}:
            return all_clients
        # Employee: only their own clients
        person_id = user.get("person_id")
        data = self._store.load()
        employee = next(
            (e for e in data.get("employees", []) if e.get("person_id") == person_id),
            None,
        )
        if not employee:
            return []
        emp_id = employee["employee_id"]
        return [c for c in all_clients if c.get("employee_id") == emp_id]

    def scope_employees(self, user: dict, all_employees: list) -> list:
        """Return the subset of employees the user may see."""
        role_name = self._get_role_name(user)
        if role_name == "Admin":
            return all_employees
        if role_name == "Manager":
            person_id = user.get("person_id")
            data = self._store.load()
            mgr_record = next(
                (e for e in data.get("employees", []) if e.get("person_id") == person_id),
                None,
            )
            if not mgr_record:
                return []
            mgr_id = mgr_record["employee_id"]
            return [e for e in all_employees if e.get("manager_id") == mgr_id or e["employee_id"] == mgr_id]
        return []
