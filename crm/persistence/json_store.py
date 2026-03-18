import json
import os
import copy


class JsonDataStore:
    DEFAULT_STRUCTURE: dict = {
        "roles": [],
        "persons": [],
        "users": [],
        "employees": [],
        "creators": [],
        "social_media_accounts": [],
        "brands": [],
        "brand_contacts": [],
        "deals": [],
        "contracts": [],
        "access_control_matrix": {},
        "_next_id": 1,
    }

    DEFAULT_ACM: dict = {
        "Admin": {
            "persons":        {"create": True,  "read": True,  "update": True,  "delete": True},
            "users":          {"create": True,  "read": True,  "update": True,  "delete": True},
            "employees":      {"create": True,  "read": True,  "update": True,  "delete": True},
            "creators":       {"create": True,  "read": True,  "update": True,  "delete": True},
            "brand_contacts": {"create": True,  "read": True,  "update": True,  "delete": True},
            "brands":         {"create": True,  "read": True,  "update": True,  "delete": True},
            "deals":          {"create": True,  "read": True,  "update": True,  "delete": True},
            "contracts":      {"create": True,  "read": True,  "update": True,  "delete": True},
        },
        "Manager": {
            "persons":        {"create": True,  "read": True,  "update": True,  "delete": True},
            "users":          {"create": False, "read": True,  "update": False, "delete": False},
            "employees":      {"create": True,  "read": True,  "update": True,  "delete": False},
            "creators":       {"create": True,  "read": True,  "update": True,  "delete": True},
            "brand_contacts": {"create": True,  "read": True,  "update": True,  "delete": True},
            "brands":         {"create": True,  "read": True,  "update": True,  "delete": True},
            "deals":          {"create": True,  "read": True,  "update": True,  "delete": True},
            "contracts":      {"create": True,  "read": True,  "update": True,  "delete": True},
        },
        "Employee": {
            "persons":        {"create": False, "read": True,  "update": True,  "delete": False},
            "users":          {"create": False, "read": False, "update": False, "delete": False},
            "employees":      {"create": False, "read": True,  "update": False, "delete": False},
            "creators":       {"create": True,  "read": True,  "update": True,  "delete": True},
            "brand_contacts": {"create": True,  "read": True,  "update": True,  "delete": False},
            "brands":         {"create": False, "read": True,  "update": False, "delete": False},
            "deals":          {"create": False, "read": True,  "update": False, "delete": False},
            "contracts":      {"create": False, "read": True,  "update": False, "delete": False},
        },
        "Creator": {
            "persons":        {"create": False, "read": True,  "update": False, "delete": False},
            "users":          {"create": False, "read": False, "update": False, "delete": False},
            "employees":      {"create": False, "read": False, "update": False, "delete": False},
            "creators":       {"create": False, "read": True,  "update": False, "delete": False},
            "brand_contacts": {"create": False, "read": True,  "update": False, "delete": False},
            "brands":         {"create": False, "read": True,  "update": False, "delete": False},
            "deals":          {"create": False, "read": True,  "update": False, "delete": False},
            "contracts":      {"create": False, "read": False, "update": False, "delete": False},
        },
        "User": {
            "persons":        {"create": False, "read": False, "update": False, "delete": False},
            "users":          {"create": False, "read": False, "update": False, "delete": False},
            "employees":      {"create": False, "read": False, "update": False, "delete": False},
            "creators":       {"create": False, "read": False, "update": False, "delete": False},
            "brand_contacts": {"create": False, "read": False, "update": False, "delete": False},
            "brands":         {"create": False, "read": False, "update": False, "delete": False},
            "deals":          {"create": False, "read": True,  "update": False, "delete": False},
            "contracts":      {"create": False, "read": False, "update": False, "delete": False},
        },
    }

    def __init__(self, filepath: str = "data.json"):
        self._filepath = filepath

    def load(self) -> dict:
        if os.path.exists(self._filepath):
            try:
                with open(self._filepath, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading data: {e}")
                return copy.deepcopy(self.DEFAULT_STRUCTURE)
        else:
            print("No data file found. Creating new data.json with default structure.")
            data = copy.deepcopy(self.DEFAULT_STRUCTURE)
            self.save(data)
            return data

    def save(self, data: dict) -> None:
        try:
            with open(self._filepath, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving data: {e}")

    def next_id(self, data: dict) -> int:
        """Return the next available ID, initialising from existing records if needed."""
        if "_next_id" not in data:
            # Backward-compat: derive from max ID across all entity lists
            max_id = 0
            for key, entity_list in data.items():
                if not isinstance(entity_list, list):
                    continue
                for item in entity_list:
                    if not isinstance(item, dict):
                        continue
                    for k, v in item.items():
                        if k.endswith("_id") and isinstance(v, int) and v > max_id:
                            max_id = v
            data["_next_id"] = max_id

        data["_next_id"] += 1
        return data["_next_id"]
