"""Tests for postgres_import.import_from_json().

Uses unittest.mock to avoid needing a real database.
"""
from __future__ import annotations

import json
import os
import pytest
from unittest.mock import MagicMock, patch, call


def _make_mock_store(roles_count: int = 0, connect_side_effect=None):
    """Return a mock PostgresDataStore."""
    mock_store = MagicMock()
    mock_store.get_table_counts.return_value = {"roles": roles_count}

    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value = mock_cur

    if connect_side_effect:
        mock_store._connect.side_effect = connect_side_effect
    else:
        mock_store._connect.return_value = mock_conn

    return mock_store, mock_conn, mock_cur


class TestImportFromJson:
    def test_import_missing_file_returns_failure(self, tmp_path):
        """import_from_json() returns failure if the JSON file doesn't exist."""
        from crm.persistence.postgres_import import import_from_json

        mock_store, _, _ = _make_mock_store()
        result = import_from_json(str(tmp_path / "nonexistent.json"), mock_store)

        assert result["success"] is False
        assert "not found" in result["message"]

    def test_import_skips_when_data_exists(self, tmp_path):
        """import_from_json() is idempotent: skips when roles already present."""
        from crm.persistence.postgres_import import import_from_json

        json_path = str(tmp_path / "data.json")
        with open(json_path, "w") as f:
            json.dump({"roles": [{"role_id": 1, "role_name": "Admin"}]}, f)

        # DB already has 4 roles
        mock_store, _, _ = _make_mock_store(roles_count=4)
        result = import_from_json(json_path, mock_store)

        assert result["success"] is True
        assert result.get("skipped") is True
        # No DB writes should have been attempted
        mock_store._connect.assert_not_called()

    def test_import_inserts_data_into_db(self, tmp_path):
        """import_from_json() inserts all entities when DB is empty."""
        from crm.persistence.postgres_import import import_from_json

        sample_data = {
            "roles": [{"role_id": 1, "role_name": "Admin"}],
            "persons": [
                {
                    "person_id": 2,
                    "first_name": "A",
                    "last_name": "B",
                    "full_name": "A B",
                    "display_name": "AB",
                    "email": "",
                    "phone": "",
                    "address": "",
                    "city": "",
                    "state": "",
                    "zip": "",
                }
            ],
            "users": [],
            "employees": [],
            "creators": [],
            "social_media_accounts": [],
            "brands": [],
            "brand_contacts": [],
            "deals": [],
            "contracts": [],
        }
        json_path = str(tmp_path / "data.json")
        with open(json_path, "w") as f:
            json.dump(sample_data, f)

        mock_store, mock_conn, mock_cur = _make_mock_store(roles_count=0)
        result = import_from_json(json_path, mock_store)

        assert result["success"] is True
        assert result.get("skipped") is not True
        assert result["inserted"]["roles"] == 1
        assert result["inserted"]["persons"] == 1
        mock_conn.commit.assert_called_once()

    def test_import_handles_db_error(self, tmp_path):
        """import_from_json() returns failure dict on database error."""
        from crm.persistence.postgres_import import import_from_json

        json_path = str(tmp_path / "data.json")
        with open(json_path, "w") as f:
            json.dump({"roles": [{"role_id": 1, "role_name": "Admin"}]}, f)

        mock_store, mock_conn, mock_cur = _make_mock_store(roles_count=0)
        mock_cur.execute.side_effect = Exception("DB error")

        result = import_from_json(json_path, mock_store)

        assert result["success"] is False
        assert "Import failed" in result["message"]
        mock_conn.rollback.assert_called_once()

    def test_import_applies_migration_to_old_schema(self, tmp_path):
        """import_from_json() migrates 'clients'→'creators' before inserting."""
        from crm.persistence.postgres_import import import_from_json

        old_data = {
            "roles": [{"role_id": 1, "role_name": "Admin"}],
            "persons": [],
            "users": [],
            "employees": [],
            "clients": [{"client_id": 10, "person_id": None}],
            "social_media_accounts": [],
            "brands": [],
            "brand_representatives": [],
            "deals": [],
            "contracts": [],
        }
        json_path = str(tmp_path / "data.json")
        with open(json_path, "w") as f:
            json.dump(old_data, f)

        mock_store, mock_conn, mock_cur = _make_mock_store(roles_count=0)
        result = import_from_json(json_path, mock_store)

        assert result["success"] is True
        # 'creators' table should have been populated from 'clients'
        sql_calls = [str(c) for c in mock_cur.execute.call_args_list]
        assert any("INSERT INTO creators" in c for c in sql_calls)


class TestGetLastImportTimestamp:
    def test_returns_none_when_no_record(self):
        """get_last_import_timestamp() returns None when settings has no entry."""
        from crm.persistence.postgres_import import get_last_import_timestamp

        mock_cur = MagicMock()
        mock_cur.__enter__ = MagicMock(return_value=mock_cur)
        mock_cur.__exit__ = MagicMock(return_value=False)
        mock_cur.fetchone.return_value = None

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cur

        mock_store = MagicMock()
        mock_store._connect.return_value = mock_conn

        result = get_last_import_timestamp(mock_store)
        assert result is None

    def test_returns_timestamp_string(self):
        """get_last_import_timestamp() returns the stored timestamp."""
        from crm.persistence.postgres_import import get_last_import_timestamp

        ts = "2024-01-15T10:30:00+00:00"
        mock_cur = MagicMock()
        mock_cur.__enter__ = MagicMock(return_value=mock_cur)
        mock_cur.__exit__ = MagicMock(return_value=False)
        mock_cur.fetchone.return_value = (ts,)

        mock_conn = MagicMock()
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.cursor.return_value = mock_cur

        mock_store = MagicMock()
        mock_store._connect.return_value = mock_conn

        result = get_last_import_timestamp(mock_store)
        assert result == ts
