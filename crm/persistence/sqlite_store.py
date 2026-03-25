"""SQLite-backed data store implementing the same interface as JsonDataStore.

Uses SQLAlchemy ORM models defined in ``db_models.py`` so all data is stored
in proper relational tables (not JSONB blobs).  Any SQLAlchemy-supported
database URL can be used; the default is ``sqlite:///project.db``.

Interface mirrors JsonDataStore:
    store.load()        → dict
    store.save(data)    → None
    store.next_id(data) → int

Extra helpers (for the admin dashboard):
    store.ensure_schema()         → None
    store.check_connectivity()    → (bool, str)
    store.get_table_counts()      → dict[str, int]
"""
from __future__ import annotations

import json
from typing import Any

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from crm.persistence.db_models import (
    Base,
    BrandContactModel,
    BrandModel,
    ContractModel,
    CreatorModel,
    DealModel,
    EmployeeModel,
    PersonModel,
    RoleModel,
    SettingModel,
    SocialMediaAccountModel,
    UserModel,
)

# Ordered mapping: entity key → (ORM model class, primary-key attribute name)
# Order respects FK dependencies for seeding / import.
_MODEL_MAP: list[tuple[str, type, str]] = [
    ("roles",                 RoleModel,               "role_id"),
    ("persons",               PersonModel,             "person_id"),
    ("users",                 UserModel,               "user_id"),
    ("employees",             EmployeeModel,           "employee_id"),
    ("creators",              CreatorModel,            "creator_id"),
    ("social_media_accounts", SocialMediaAccountModel, "social_media_id"),
    ("brands",                BrandModel,              "brand_id"),
    ("brand_contacts",        BrandContactModel,       "brand_contact_id"),
    ("deals",                 DealModel,               "deal_id"),
    ("contracts",             ContractModel,           "contract_id"),
]


def _model_columns(model_cls: type) -> set[str]:
    """Return the set of column attribute names for a model class."""
    return {c.key for c in inspect(model_cls).mapper.column_attrs}


def _row_to_dict(obj: Any) -> dict:
    """Convert an ORM row object to a plain dict."""
    return {col: getattr(obj, col) for col in _model_columns(type(obj))}


def _normalize_item(key: str, item: dict) -> dict:
    """Translate legacy field names to current names before persisting.

    deal_service still stores deals with ``client_id`` / ``brand_rep_id``;
    DealModel uses ``creator_id`` / ``brand_contact_id``.
    """
    item = dict(item)
    if key == "deals":
        if "client_id" in item and "creator_id" not in item:
            item["creator_id"] = item.pop("client_id")
        if "brand_rep_id" in item and "brand_contact_id" not in item:
            item["brand_contact_id"] = item.pop("brand_rep_id")
    if key == "social_media_accounts":
        if "client_id" in item and "creator_id" not in item:
            item["creator_id"] = item.pop("client_id")
    return item


class SqliteDataStore:
    """SQLAlchemy-backed data store (default: SQLite).

    Parameters
    ----------
    database_url:
        SQLAlchemy connection URL.  Examples::

            "sqlite:///project.db"                      # relative file
            "sqlite:////absolute/path/to/project.db"    # absolute file
            "sqlite:///:memory:"                        # in-memory (tests)
            "postgresql://user:pass@host/db"            # also works
    """

    def __init__(self, database_url: str = "sqlite:///project.db") -> None:
        self._database_url = database_url
        self._engine = create_engine(database_url, echo=False)
        self._Session = sessionmaker(bind=self._engine)

    # ------------------------------------------------------------------ #
    # Schema management                                                    #
    # ------------------------------------------------------------------ #

    def ensure_schema(self) -> None:
        """Create all tables if they do not already exist."""
        Base.metadata.create_all(self._engine)

    # ------------------------------------------------------------------ #
    # Core store interface (mirrors JsonDataStore)                        #
    # ------------------------------------------------------------------ #

    def load(self) -> dict:
        """Query all tables and return data in the same format as JsonDataStore."""
        result: dict[str, Any] = {}
        with self._Session() as session:
            for key, Model, _pk in _MODEL_MAP:
                rows = session.query(Model).all()
                result[key] = [_row_to_dict(r) for r in rows]

            # access_control_matrix
            acm_row = session.get(SettingModel, "access_control_matrix")
            result["access_control_matrix"] = (
                json.loads(acm_row.value) if acm_row else {}
            )

            # _next_id
            nid_row = session.get(SettingModel, "_next_id")
            result["_next_id"] = int(json.loads(nid_row.value)) if nid_row else 0

        return result

    def save(self, data: dict) -> None:
        """Persist all entity collections and settings to the database.

        For each table:
        - Rows whose PK is no longer in *data* are deleted.
        - Rows present in *data* are upserted (inserted or updated by PK).
        """
        with self._Session() as session:
            for key, Model, pk_attr in _MODEL_MAP:
                items = [_normalize_item(key, item) for item in data.get(key, [])]
                col_names = _model_columns(Model)

                incoming_ids = {
                    item[pk_attr]
                    for item in items
                    if item.get(pk_attr) is not None
                }

                # Delete rows not in the incoming collection
                pk_col = getattr(Model, pk_attr)
                if incoming_ids:
                    session.query(Model).filter(
                        pk_col.not_in(incoming_ids)
                    ).delete(synchronize_session=False)
                else:
                    session.query(Model).delete(synchronize_session=False)

                # Upsert each incoming item
                for item in items:
                    if item.get(pk_attr) is None:
                        continue
                    # Build an ORM instance with only columns that exist on the model
                    kwargs = {k: v for k, v in item.items() if k in col_names}
                    obj = Model(**kwargs)
                    session.merge(obj)

            # Persist access_control_matrix
            acm = data.get("access_control_matrix")
            if acm is not None:
                session.merge(
                    SettingModel(key="access_control_matrix", value=json.dumps(acm))
                )

            # Persist _next_id
            next_id = data.get("_next_id", 0)
            session.merge(SettingModel(key="_next_id", value=json.dumps(next_id)))

            session.commit()

    def next_id(self, data: dict) -> int:
        """Return the next available global ID (same interface as JsonDataStore).

        Derives the counter from the maximum existing entity ID whenever
        ``_next_id`` is absent or 0 (i.e., uninitialized after a fresh seed).
        """
        if "_next_id" not in data or data["_next_id"] == 0:
            max_id = 0
            for key_name, entity_list in data.items():
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
    # Dashboard helpers (shared API with PostgresDataStore)               #
    # ------------------------------------------------------------------ #

    def check_connectivity(self) -> tuple[bool, str]:
        """Return (ok, message) indicating whether the database is reachable."""
        try:
            with self._engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return True, "Connected"
        except Exception as exc:
            return False, str(exc)

    def get_table_counts(self) -> dict[str, int]:
        """Return a dict of {table_name: row_count} for all entity tables."""
        counts: dict[str, int] = {}
        with self._Session() as session:
            for key, Model, _pk in _MODEL_MAP:
                try:
                    counts[key] = session.query(Model).count()
                except Exception:
                    counts[key] = -1
        return counts

    def get_table_names(self) -> list[str]:
        """Return a sorted list of inspectable table names."""
        names = [key for key, _model, _pk in _MODEL_MAP]
        names.append("settings")
        return sorted(names)

    def get_table_columns(self, table_name: str) -> list[dict[str, str]]:
        """Return column metadata for *table_name*.

        Each entry includes keys: name, type, nullable.
        """
        if table_name not in self.get_table_names():
            return []

        inspector = inspect(self._engine)
        cols = inspector.get_columns(table_name)
        return [
            {
                "name": str(c.get("name", "")),
                "type": str(c.get("type", "")),
                "nullable": "YES" if c.get("nullable", True) else "NO",
            }
            for c in cols
        ]

    def get_table_rows(
        self,
        table_name: str,
        *,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[str], list[dict[str, Any]], int]:
        """Return (columns, rows, total_rows) for *table_name* with pagination."""
        if table_name not in self.get_table_names():
            return [], [], 0

        safe_page = max(1, int(page))
        safe_size = max(1, min(int(page_size), 100))
        offset = (safe_page - 1) * safe_size

        with self._engine.connect() as conn:
            total_rows = int(
                conn.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar() or 0
            )
            result = conn.execute(
                text(f"SELECT * FROM {table_name} LIMIT :limit OFFSET :offset"),
                {"limit": safe_size, "offset": offset},
            )
            columns = list(result.keys())
            rows = [dict(row._mapping) for row in result]

        return columns, rows, total_rows
