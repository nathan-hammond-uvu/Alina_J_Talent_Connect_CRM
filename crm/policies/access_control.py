"""Access control policy using a data-driven Access Control Matrix (ACM).

Hard constraints (never overridden by ACM edits):
- Admin always has full access.
- Creator can never write anything.
- Managers cannot update/delete other managers.

All other permissions are read from the ACM stored in data.json so that
admins can fine-tune them from the Settings page.
"""
from __future__ import annotations

from crm.persistence.json_store import JsonDataStore
from crm.persistence.repositories import RoleRepository


# Roles that map to "Creator" for ACM look-up (their role_name may differ)
_CREATOR_ROLE_NAMES: frozenset[str] = frozenset({"Creator", "Client", "Rep"})

# Access hierarchy level (used for scope decisions)
ROLE_HIERARCHY: dict[str, int] = {
    "Admin": 5,
    "Manager": 4,
    "Employee": 3,
    "Creator": 2,
    "Client": 2,
    "Rep": 2,
    "User": 1,
}


def _acm_role_key(role_name: str) -> str:
    """Map a role_name to the matching ACM key."""
    if role_name in _CREATOR_ROLE_NAMES:
        return "Creator"
    return role_name


class AccessPolicy:
    """ACM-backed access control."""

    # Kept for backward-compat with code that inspects AccessPolicy.ROLE_HIERARCHY
    ROLE_HIERARCHY = ROLE_HIERARCHY

    def __init__(self, store: JsonDataStore):
        self._store = store
        self._roles = RoleRepository(store)

    # ------------------------------------------------------------------ #
    # Internal helpers                                                     #
    # ------------------------------------------------------------------ #

    def _get_role_name(self, user: dict) -> str:
        role = self._roles.get(user.get("role_id"))
        return role["role_name"] if role else "User"

    def _acm(self) -> dict:
        data = self._store.load()
        acm = data.get("access_control_matrix", {})
        if not acm:
            acm = JsonDataStore.DEFAULT_ACM
        return acm

    def _acm_perm(self, role_name: str, entity_type: str, action: str) -> bool:
        """Look up a single ACM cell, falling back to DEFAULT_ACM."""
        acm = self._acm()
        key = _acm_role_key(role_name)
        return bool(acm.get(key, {}).get(entity_type, {}).get(action, False))

    def _get_employee_for_user(self, user: dict, data: dict) -> dict | None:
        person_id = user.get("person_id")
        return next(
            (e for e in data.get("employees", []) if e.get("person_id") == person_id),
            None,
        )

    # ------------------------------------------------------------------ #
    # ACM CRUD checks                                                      #
    # ------------------------------------------------------------------ #

    def can_view(self, entity_type: str, user: dict) -> bool:
        role_name = self._get_role_name(user)
        if role_name == "Admin":
            return True
        return self._acm_perm(role_name, entity_type, "read")

    def can_edit(self, entity_type: str, user: dict) -> bool:
        """Check CREATE or UPDATE permission (generic edit gate)."""
        role_name = self._get_role_name(user)
        if role_name == "Admin":
            return True
        if _acm_role_key(role_name) == "Creator":
            return False
        return self._acm_perm(role_name, entity_type, "update") or self._acm_perm(role_name, entity_type, "create")

    def can_create(self, entity_type: str, user: dict) -> bool:
        role_name = self._get_role_name(user)
        if role_name == "Admin":
            return True
        if _acm_role_key(role_name) == "Creator":
            return False
        return self._acm_perm(role_name, entity_type, "create")

    def can_update(self, entity_type: str, user: dict, target: dict | None = None) -> bool:
        """Check update permission, honouring manager-vs-manager restriction."""
        role_name = self._get_role_name(user)
        if role_name == "Admin":
            return True
        if _acm_role_key(role_name) == "Creator":
            return False
        if role_name == "Manager" and entity_type == "employees" and target:
            # Managers cannot update *other* managers; they can update their own record
            if target.get("is_manager") and target.get("person_id") != user.get("person_id"):
                return False
        return self._acm_perm(role_name, entity_type, "update")

    def can_delete(self, entity_type: str, user: dict, target: dict | None = None) -> bool:
        role_name = self._get_role_name(user)
        if role_name == "Admin":
            return True
        if _acm_role_key(role_name) == "Creator":
            return False
        # Managers cannot delete *other* managers; they can delete their own record
        if role_name == "Manager" and entity_type == "employees" and target:
            if target.get("is_manager") and target.get("person_id") != user.get("person_id"):
                return False
        return self._acm_perm(role_name, entity_type, "delete")

    # ------------------------------------------------------------------ #
    # Scoping helpers                                                      #
    # ------------------------------------------------------------------ #

    def scope_creators(self, user: dict, all_creators: list) -> list:
        """Return creators the user may see."""
        role_name = self._get_role_name(user)
        if role_name in {"Admin", "Manager"}:
            return all_creators
        data = self._store.load()
        employee = self._get_employee_for_user(user, data)
        if not employee:
            return []
        emp_id = employee["employee_id"]
        return [c for c in all_creators if c.get("employee_id") == emp_id]

    # Keep backward-compat name used in tests / old code
    def scope_clients(self, user: dict, all_clients: list) -> list:
        return self.scope_creators(user, all_clients)

    def scope_employees(self, user: dict, all_employees: list) -> list:
        """Return employees the user may see."""
        role_name = self._get_role_name(user)
        if role_name == "Admin":
            return all_employees
        if role_name == "Manager":
            data = self._store.load()
            mgr_record = self._get_employee_for_user(user, data)
            if not mgr_record:
                return []
            mgr_id = mgr_record["employee_id"]
            return [e for e in all_employees if e.get("manager_id") == mgr_id or e["employee_id"] == mgr_id]
        # Employees only see themselves
        data = self._store.load()
        employee = self._get_employee_for_user(user, data)
        if not employee:
            return []
        return [employee]

    # ------------------------------------------------------------------ #
    # ACM admin helpers                                                    #
    # ------------------------------------------------------------------ #

    def can_edit_acm(self, user: dict) -> bool:
        """Only Admin can edit the ACM."""
        return self._get_role_name(user) == "Admin"

    def get_acm(self) -> dict:
        return self._acm()

    def save_acm(self, new_acm: dict) -> None:
        """Persist an updated ACM, preserving hard constraints."""
        # Enforce hard constraints: Admin always full, Creator always read-only
        for entity, perms in JsonDataStore.DEFAULT_ACM.get("Admin", {}).items():
            new_acm.setdefault("Admin", {})[entity] = dict(perms)

        creator_defaults = JsonDataStore.DEFAULT_ACM.get("Creator", {})
        for entity in creator_defaults:
            new_acm.setdefault("Creator", {})[entity] = {
                "create": False,
                "read": new_acm.get("Creator", {}).get(entity, {}).get("read", False),
                "update": False,
                "delete": False,
            }

        data = self._store.load()
        data["access_control_matrix"] = new_acm
        self._store.save(data)

