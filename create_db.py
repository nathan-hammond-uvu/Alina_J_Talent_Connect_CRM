#!/usr/bin/env python3
"""Initialize the SQLite database (project.db) from data.json.

Creates all relational tables (via SQLAlchemy) and seeds them with the
content of data.json, applying the schema migration automatically when the
old key names (``clients``, ``brand_representatives``) are detected.

The operation is **idempotent**: if the database already contains role rows
the seed step is skipped without error.

Usage::

    python create_db.py

Environment variables:
    DATABASE_URL      – SQLAlchemy URL (default: sqlite:///project.db)
    DATA_JSON_PATH    – path to data.json (default: ./data.json)
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Ensure the project root is on sys.path so 'crm' is importable.
sys.path.insert(0, str(Path(__file__).parent))

from crm.persistence.sqlite_store import SqliteDataStore
from crm.persistence.migration import migrate, needs_migration
from crm.persistence.json_store import JsonDataStore

_ROOT = Path(__file__).parent
DB_URL = os.environ.get("DATABASE_URL", f"sqlite:///{_ROOT / 'project.db'}")
JSON_PATH = os.environ.get("DATA_JSON_PATH", str(_ROOT / "data.json"))


def main() -> None:
    store = SqliteDataStore(DB_URL)
    print(f"[create_db] Ensuring schema …  ({DB_URL})")
    store.ensure_schema()

    # Idempotency check: skip seed if data already present
    existing = store.load()
    if existing.get("roles"):
        print("[create_db] Database already contains data — skipping seed.")
        _print_counts(store)
        return

    if not os.path.exists(JSON_PATH):
        print(f"[create_db] {JSON_PATH} not found — empty database created.")
        return

    with open(JSON_PATH) as f:
        raw = json.load(f)

    data = migrate(raw) if needs_migration(raw) else raw
    data.setdefault("access_control_matrix", JsonDataStore.DEFAULT_ACM)

    store.save(data)
    print(f"[create_db] Seeded database from {JSON_PATH}.")
    _print_counts(store)


def _print_counts(store: SqliteDataStore) -> None:
    counts = store.get_table_counts()
    for table, count in counts.items():
        if count:
            print(f"[create_db]   {table}: {count} row(s)")


if __name__ == "__main__":
    main()
