"""Tests for PostgresDataStore.ensure_schema().

These tests use unittest.mock to patch psycopg so no real database is needed.
They verify that ensure_schema() issues CREATE TABLE statements for every
expected table.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, call, patch

from crm.persistence.postgres_store import PostgresDataStore, TABLE_MAP


def _make_mock_conn():
    """Return (mock_conn, mock_cur) with proper context-manager support."""
    mock_cur = MagicMock()
    mock_cur.__enter__ = MagicMock(return_value=mock_cur)
    mock_cur.__exit__ = MagicMock(return_value=False)

    mock_conn = MagicMock()
    mock_conn.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn.__exit__ = MagicMock(return_value=False)
    mock_conn.cursor.return_value = mock_cur

    return mock_conn, mock_cur


class TestEnsureSchema:
    def test_ensure_schema_creates_entity_tables(self):
        """ensure_schema() should CREATE TABLE for every entry in TABLE_MAP."""
        mock_conn, mock_cur = _make_mock_conn()

        with patch("crm.persistence.postgres_store.psycopg") as mock_psycopg:
            mock_psycopg.connect.return_value = mock_conn
            store = PostgresDataStore("postgresql://test")
            store.ensure_schema()

        sql_calls = [str(c) for c in mock_cur.execute.call_args_list]
        for table in TABLE_MAP:
            assert any(
                f"CREATE TABLE IF NOT EXISTS {table}" in c for c in sql_calls
            ), f"Expected CREATE TABLE IF NOT EXISTS {table}"

    def test_ensure_schema_creates_settings_table(self):
        """ensure_schema() should also create the settings table."""
        mock_conn, mock_cur = _make_mock_conn()

        with patch("crm.persistence.postgres_store.psycopg") as mock_psycopg:
            mock_psycopg.connect.return_value = mock_conn
            store = PostgresDataStore("postgresql://test")
            store.ensure_schema()

        sql_calls = [str(c) for c in mock_cur.execute.call_args_list]
        assert any("CREATE TABLE IF NOT EXISTS settings" in c for c in sql_calls)

    def test_ensure_schema_calls_commit(self):
        """ensure_schema() should commit the transaction."""
        mock_conn, mock_cur = _make_mock_conn()

        with patch("crm.persistence.postgres_store.psycopg") as mock_psycopg:
            mock_psycopg.connect.return_value = mock_conn
            store = PostgresDataStore("postgresql://test")
            store.ensure_schema()

        mock_conn.commit.assert_called_once()

    def test_ensure_schema_total_table_count(self):
        """ensure_schema() creates exactly len(TABLE_MAP) + 1 tables (settings)."""
        mock_conn, mock_cur = _make_mock_conn()

        with patch("crm.persistence.postgres_store.psycopg") as mock_psycopg:
            mock_psycopg.connect.return_value = mock_conn
            store = PostgresDataStore("postgresql://test")
            store.ensure_schema()

        sql_calls = [str(c) for c in mock_cur.execute.call_args_list]
        create_calls = [c for c in sql_calls if "CREATE TABLE IF NOT EXISTS" in c]
        expected = len(TABLE_MAP) + 1  # entity tables + settings
        assert len(create_calls) == expected


class TestNextId:
    def test_next_id_derives_from_max(self):
        """next_id() derives the counter from existing IDs when _next_id is absent."""
        mock_conn, _ = _make_mock_conn()
        with patch("crm.persistence.postgres_store.psycopg") as mock_psycopg:
            mock_psycopg.connect.return_value = mock_conn
            store = PostgresDataStore("postgresql://test")

        data = {"roles": [{"role_id": 5}, {"role_id": 3}], "persons": [{"person_id": 10}]}
        new_id = store.next_id(data)
        assert new_id == 11  # max(5, 3, 10) + 1

    def test_next_id_increments_counter(self):
        """next_id() increments data['_next_id'] on each call."""
        mock_conn, _ = _make_mock_conn()
        with patch("crm.persistence.postgres_store.psycopg") as mock_psycopg:
            mock_psycopg.connect.return_value = mock_conn
            store = PostgresDataStore("postgresql://test")

        data = {"_next_id": 20}
        first = store.next_id(data)
        second = store.next_id(data)
        assert first == 21
        assert second == 22


class TestCheckConnectivity:
    def test_connectivity_ok(self):
        mock_conn, mock_cur = _make_mock_conn()
        with patch("crm.persistence.postgres_store.psycopg") as mock_psycopg:
            mock_psycopg.connect.return_value = mock_conn
            store = PostgresDataStore("postgresql://test")
            ok, msg = store.check_connectivity()

        assert ok is True
        assert "Connected" in msg

    def test_connectivity_failure(self):
        with patch("crm.persistence.postgres_store.psycopg") as mock_psycopg:
            mock_psycopg.connect.side_effect = Exception("connection refused")
            store = PostgresDataStore("postgresql://bad-host")
            ok, msg = store.check_connectivity()

        assert ok is False
        assert "connection refused" in msg
