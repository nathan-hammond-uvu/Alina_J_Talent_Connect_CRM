"""PostgreSQL-backed data store that emulates the JsonDataStore interface.

Uses Option 2 (load/save emulation): each entity collection is stored in its
own table with an integer primary key and a JSONB column holding the full
entity dict.  This keeps the existing service/repository layer unchanged.

Tables created:
  roles, persons, users, employees, creators, social_media_accounts,
  brands, brand_contacts, deals, contracts  (each: id_col INTEGER PK, data JSONB)
  settings  (key TEXT PK, value JSONB)
"""
from __future__ import annotations

import copy
import json
from typing import Any

try:
    import psycopg  # type: ignore
    PSYCOPG_AVAILABLE = True
except ImportError:  # pragma: no cover
    psycopg = None  # type: ignore
    PSYCOPG_AVAILABLE = False

from crm.persistence.json_store import JsonDataStore

# Mapping of JSON collection key → primary-key field name
TABLE_MAP: dict[str, str] = {
    "roles": "role_id",
    "persons": "person_id",
    "users": "user_id",
    "employees": "employee_id",
    "creators": "creator_id",
    "social_media_accounts": "social_media_id",
    "brands": "brand_id",
    "brand_contacts": "brand_contact_id",
    "deals": "deal_id",
    "contracts": "contract_id",
}


class PostgresDataStore:
    """Data store backed by PostgreSQL, implementing the same interface as
    JsonDataStore (load / save / next_id).
    """

    def __init__(self, database_url: str) -> None:
        if not PSYCOPG_AVAILABLE:
            raise ImportError(
                "psycopg is required for PostgreSQL backend. "
                "Install with: pip install 'psycopg[binary]>=3.1'"
            )
        self._database_url = database_url

    # ------------------------------------------------------------------ #
    # Connection helper                                                    #
    # ------------------------------------------------------------------ #

    def _connect(self):
        """Return a new psycopg connection (caller is responsible for closing)."""
        return psycopg.connect(self._database_url)

    # ------------------------------------------------------------------ #
    # Schema management                                                    #
    # ------------------------------------------------------------------ #

    def ensure_schema(self) -> None:
        """Create all required tables if they do not already exist."""
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                for table, id_field in TABLE_MAP.items():
                    cur.execute(
                        f"CREATE TABLE IF NOT EXISTS {table} "
                        f"({id_field} INTEGER PRIMARY KEY, data JSONB NOT NULL)"
                    )
                cur.execute(
                    "CREATE TABLE IF NOT EXISTS settings "
                    "(key TEXT PRIMARY KEY, value JSONB NOT NULL)"
                )
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------ #
    # Core store interface (mirrors JsonDataStore)                        #
    # ------------------------------------------------------------------ #

    def load(self) -> dict:
        """Load all data from PostgreSQL and return as a dict matching the
        JSON store format (same keys as JsonDataStore.DEFAULT_STRUCTURE).
        """
        result: dict[str, Any] = {}
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                for table in TABLE_MAP:
                    cur.execute(f"SELECT data FROM {table}")
                    rows = cur.fetchall()
                    items = []
                    for row in rows:
                        val = row[0]
                        if isinstance(val, str):
                            val = json.loads(val)
                        items.append(val)
                    result[table] = items

                # access_control_matrix stored in settings
                cur.execute(
                    "SELECT value FROM settings WHERE key = 'access_control_matrix'"
                )
                row = cur.fetchone()
                if row:
                    val = row[0]
                    result["access_control_matrix"] = (
                        json.loads(val) if isinstance(val, str) else val
                    )
                else:
                    result["access_control_matrix"] = {}

                # _next_id stored in settings
                cur.execute("SELECT value FROM settings WHERE key = '_next_id'")
                row = cur.fetchone()
                if row:
                    val = row[0]
                    result["_next_id"] = int(val) if not isinstance(val, int) else val
                else:
                    result["_next_id"] = 0
        except Exception as exc:
            print(f"[postgres_store] Error loading data: {exc}")
            return copy.deepcopy(JsonDataStore.DEFAULT_STRUCTURE)
        finally:
            conn.close()
        return result

    def save(self, data: dict) -> None:
        """Persist the full data dict to PostgreSQL.

        For each entity table: upsert items present in *data*, delete any
        rows whose ID is no longer in the collection.
        Also persists access_control_matrix and _next_id to the settings table.
        """
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                for table, id_field in TABLE_MAP.items():
                    items = data.get(table, [])

                    # Delete rows no longer in the collection
                    if items:
                        ids = [
                            item[id_field]
                            for item in items
                            if item.get(id_field) is not None
                        ]
                        if ids:
                            cur.execute(
                                f"DELETE FROM {table} WHERE {id_field} != ALL(%s)",
                                [ids],
                            )
                    else:
                        cur.execute(f"DELETE FROM {table}")

                    # Upsert each item
                    for item in items:
                        item_id = item.get(id_field)
                        if item_id is None:
                            continue
                        cur.execute(
                            f"INSERT INTO {table} ({id_field}, data) "
                            f"VALUES (%s, %s::jsonb) "
                            f"ON CONFLICT ({id_field}) DO UPDATE SET data = EXCLUDED.data",
                            [item_id, json.dumps(item)],
                        )

                # Persist access_control_matrix
                acm = data.get("access_control_matrix")
                if acm is not None:
                    cur.execute(
                        "INSERT INTO settings (key, value) "
                        "VALUES (%s, %s::jsonb) "
                        "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                        ["access_control_matrix", json.dumps(acm)],
                    )

                # Persist _next_id
                next_id = data.get("_next_id", 0)
                cur.execute(
                    "INSERT INTO settings (key, value) "
                    "VALUES (%s, %s::jsonb) "
                    "ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value",
                    ["_next_id", json.dumps(next_id)],
                )

            conn.commit()
        except Exception as exc:
            conn.rollback()
            print(f"[postgres_store] Error saving data: {exc}")
            raise
        finally:
            conn.close()

    def next_id(self, data: dict) -> int:
        """Return the next available global ID (same interface as JsonDataStore).

        Derives the counter from the maximum existing entity ID whenever
        ``_next_id`` is absent or 0 (i.e., uninitialized after a fresh seed).
        """
        if "_next_id" not in data or data["_next_id"] == 0:
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

    # ------------------------------------------------------------------ #
    # Dashboard helpers                                                    #
    # ------------------------------------------------------------------ #

    def check_connectivity(self) -> tuple[bool, str]:
        """Return (ok, message) indicating whether the DB is reachable."""
        try:
            conn = self._connect()
            try:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
            finally:
                conn.close()
            return True, "Connected"
        except Exception as exc:
            return False, str(exc)

    def get_table_counts(self) -> dict[str, int]:
        """Return a dict of {table_name: row_count} for all entity tables."""
        counts: dict[str, int] = {}
        conn = self._connect()
        try:
            with conn.cursor() as cur:
                for table in TABLE_MAP:
                    try:
                        cur.execute(f"SELECT COUNT(*) FROM {table}")
                        row = cur.fetchone()
                        counts[table] = int(row[0]) if row else 0
                    except Exception:
                        counts[table] = -1
        except Exception as exc:
            print(f"[postgres_store] Error getting table counts: {exc}")
        finally:
            conn.close()
        return counts
