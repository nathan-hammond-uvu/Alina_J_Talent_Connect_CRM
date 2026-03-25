"""Import data from a JSON file into PostgreSQL (idempotent).

Usage::

    from crm.persistence.postgres_import import import_from_json
    result = import_from_json("/path/to/data.json", postgres_store)

The import is idempotent: if the ``roles`` table already contains rows the
function returns immediately without changing anything.
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone

from crm.persistence.postgres_store import PostgresDataStore, TABLE_MAP
from crm.persistence.migration import migrate, needs_migration


# Insert order respects FK dependencies
_IMPORT_ORDER = [
    "roles",
    "persons",
    "users",
    "employees",
    "creators",
    "social_media_accounts",
    "brands",
    "brand_contacts",
    "deals",
    "contracts",
]


def import_from_json(json_path: str, store: PostgresDataStore) -> dict:
    """Import entities from *json_path* into the PostgreSQL database.

    Returns a result dict with keys:
      - ``success`` (bool)
      - ``message`` (str)
      - ``skipped`` (bool, optional) – True when data already existed
      - ``inserted`` (dict, optional) – per-table counts
      - ``timestamp`` (str, optional) – ISO-8601 UTC time of this import
    """
    if not os.path.exists(json_path):
        return {
            "success": False,
            "message": f"JSON file not found: {json_path}",
        }

    with open(json_path, "r") as f:
        raw_data = json.load(f)

    # Apply schema migrations (clients → creators, etc.) in-memory
    data = migrate(raw_data) if needs_migration(raw_data) else raw_data

    # Idempotency check: skip if roles table already has rows
    counts = store.get_table_counts()
    if counts.get("roles", 0) > 0:
        return {
            "success": True,
            "message": (
                "Data already exists in the database — import skipped (idempotent)."
            ),
            "skipped": True,
        }

    inserted: dict[str, int] = {}
    timestamp = datetime.now(timezone.utc).isoformat()

    conn = store._connect()
    try:
        with conn.cursor() as cur:
            for table in _IMPORT_ORDER:
                id_field = TABLE_MAP.get(table)
                if id_field is None:
                    continue
                items = data.get(table, [])
                count = 0
                for item in items:
                    item_id = item.get(id_field)
                    if item_id is None:
                        continue
                    cur.execute(
                        f"INSERT INTO {table} ({id_field}, data) "
                        f"VALUES (%s, %s::jsonb) "
                        f"ON CONFLICT ({id_field}) DO NOTHING",
                        [item_id, json.dumps(item)],
                    )
                    count += 1
                inserted[table] = count

            # Import access_control_matrix into settings
            acm = data.get("access_control_matrix")
            if acm:
                cur.execute(
                    "INSERT INTO settings (key, value) VALUES (%s, %s::jsonb) "
                    "ON CONFLICT (key) DO NOTHING",
                    ["access_control_matrix", json.dumps(acm)],
                )

            # Seed _next_id in settings
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
            cur.execute(
                "INSERT INTO settings (key, value) VALUES (%s, %s::jsonb) "
                "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                ["_next_id", json.dumps(max_id)],
            )

            # Record last import timestamp
            cur.execute(
                "INSERT INTO settings (key, value) VALUES (%s, %s::jsonb) "
                "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                ["last_import_at", json.dumps(timestamp)],
            )

        conn.commit()
    except Exception as exc:
        conn.rollback()
        return {"success": False, "message": f"Import failed: {exc}"}
    finally:
        conn.close()

    return {
        "success": True,
        "message": "Import completed successfully.",
        "inserted": inserted,
        "timestamp": timestamp,
    }


def get_last_import_timestamp(store: PostgresDataStore) -> str | None:
    """Return the ISO-8601 UTC timestamp of the last successful import, or None."""
    conn = store._connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT value FROM settings WHERE key = 'last_import_at'")
            row = cur.fetchone()
            if row is None:
                return None
            val = row[0]
            return val if isinstance(val, str) else json.dumps(val)
    except Exception:
        return None
    finally:
        conn.close()
