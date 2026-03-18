"""Tests for the one-time data migration (migration.py)."""
import copy
import pytest

from crm.persistence.migration import migrate, needs_migration, run_migration


# ---------------------------------------------------------------------------
# needs_migration
# ---------------------------------------------------------------------------

def test_needs_migration_old_clients_key():
    data = {"clients": [], "brand_representatives": []}
    assert needs_migration(data) is True


def test_needs_migration_already_migrated():
    data = {"creators": [], "brand_contacts": []}
    assert needs_migration(data) is False


def test_needs_migration_partial():
    data = {"clients": []}
    assert needs_migration(data) is True


# ---------------------------------------------------------------------------
# migrate – key renames
# ---------------------------------------------------------------------------

def test_migrate_renames_clients_to_creators():
    data = {"clients": [{"client_id": 1, "employee_id": 10, "description": "C1"}]}
    result = migrate(data)
    assert "clients" not in result
    assert "creators" in result
    assert result["creators"][0]["creator_id"] == 1


def test_migrate_renames_brand_representatives_to_brand_contacts():
    data = {"brand_representatives": [{"brand_rep_id": 1, "notes": "Rep1"}]}
    result = migrate(data)
    assert "brand_representatives" not in result
    assert "brand_contacts" in result
    assert result["brand_contacts"][0]["brand_contact_id"] == 1


def test_migrate_preserves_existing_creators():
    data = {
        "clients": [{"client_id": 100, "description": "Old"}],
        "creators": [{"creator_id": 200, "person_id": 50, "description": "New"}],
    }
    result = migrate(data)
    ids = {c["creator_id"] for c in result["creators"]}
    # Both should exist
    assert 100 in ids
    assert 200 in ids


# ---------------------------------------------------------------------------
# migrate – person_id backfill
# ---------------------------------------------------------------------------

def test_migrate_backfills_person_id_on_creator():
    data = {
        "clients": [{"client_id": 1, "first_name": "Alice", "last_name": "Smith", "email": "a@x.com"}],
        "persons": [],
        "_next_id": 0,
    }
    result = migrate(data)
    creator = result["creators"][0]
    assert "person_id" in creator
    # The person should have been created
    pid = creator["person_id"]
    matching_persons = [p for p in result["persons"] if p["person_id"] == pid]
    assert len(matching_persons) == 1
    assert matching_persons[0]["first_name"] == "Alice"


def test_migrate_skips_backfill_when_person_id_exists():
    data = {
        "clients": [{"client_id": 1, "person_id": 42, "description": ""}],
        "persons": [{"person_id": 42, "full_name": "Existing", "first_name": "", "last_name": "",
                     "display_name": "Existing", "email": "", "phone": "", "address": "",
                     "city": "", "state": "", "zip": ""}],
        "_next_id": 50,
    }
    result = migrate(data)
    creator = result["creators"][0]
    assert creator["person_id"] == 42  # unchanged


def test_migrate_backfills_person_id_on_brand_contact():
    data = {
        "brand_representatives": [{"brand_rep_id": 1, "first_name": "Bob", "last_name": "Jones"}],
        "persons": [],
        "_next_id": 0,
    }
    result = migrate(data)
    contact = result["brand_contacts"][0]
    assert "person_id" in contact
    pid = contact["person_id"]
    assert any(p["person_id"] == pid for p in result["persons"])


# ---------------------------------------------------------------------------
# migrate – ACM seeding
# ---------------------------------------------------------------------------

def test_migrate_seeds_acm_when_missing():
    data = {"clients": [], "_next_id": 1}
    result = migrate(data)
    assert "access_control_matrix" in result
    assert "Admin" in result["access_control_matrix"]


def test_migrate_preserves_existing_acm():
    custom_acm = {"Admin": {"persons": {"create": True, "read": True, "update": True, "delete": True}}}
    data = {"clients": [], "_next_id": 1, "access_control_matrix": custom_acm}
    result = migrate(data)
    # Should not overwrite if already present
    assert result["access_control_matrix"] == custom_acm


# ---------------------------------------------------------------------------
# run_migration (file-based)
# ---------------------------------------------------------------------------

def test_run_migration_creates_backup(tmp_path):
    import json, os
    filepath = str(tmp_path / "data.json")
    data = {"clients": [{"client_id": 1, "description": "C"}], "_next_id": 5, "persons": []}
    with open(filepath, "w") as f:
        json.dump(data, f)

    run_migration(filepath)

    # Backup should exist
    backup = filepath + ".pre_chunk6.bak"
    assert os.path.exists(backup)


def test_run_migration_returns_true_when_migration_needed(tmp_path):
    import json
    filepath = str(tmp_path / "data.json")
    data = {"clients": [], "_next_id": 1}
    with open(filepath, "w") as f:
        json.dump(data, f)

    result = run_migration(filepath)
    assert result is True


def test_run_migration_returns_false_when_not_needed(tmp_path):
    import json
    filepath = str(tmp_path / "data.json")
    data = {"creators": [], "brand_contacts": [], "access_control_matrix": {}, "_next_id": 1}
    with open(filepath, "w") as f:
        json.dump(data, f)

    result = run_migration(filepath)
    assert result is False


def test_run_migration_missing_file_returns_false(tmp_path):
    filepath = str(tmp_path / "nonexistent.json")
    result = run_migration(filepath)
    assert result is False
