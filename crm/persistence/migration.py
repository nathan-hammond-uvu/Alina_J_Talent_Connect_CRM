"""One-time data migration: rename entities and backfill person_id links.

Run automatically at app startup when the old schema keys are detected.
A backup copy of the original data.json is created before any changes.
"""
from __future__ import annotations

import copy
import json
import os
import shutil


def needs_migration(data: dict) -> bool:
    """Return True if the data still uses old schema keys."""
    return "clients" in data or "brand_representatives" in data


def migrate(data: dict) -> dict:
    """Return a migrated copy of *data* (does not save to disk)."""
    data = copy.deepcopy(data)

    # ------------------------------------------------------------------ #
    # 1.  Rename top-level keys                                           #
    # ------------------------------------------------------------------ #
    if "clients" in data:
        old_clients = data.pop("clients")
        # Remap client_id -> creator_id; keep employee_id link
        migrated_creators = []
        for c in old_clients:
            nc = dict(c)
            if "client_id" in nc and "creator_id" not in nc:
                nc["creator_id"] = nc.pop("client_id")
            migrated_creators.append(nc)
        data.setdefault("creators", [])
        # Merge: only add records that don't already exist by creator_id
        existing_ids = {c.get("creator_id") for c in data["creators"]}
        for mc in migrated_creators:
            if mc.get("creator_id") not in existing_ids:
                data["creators"].append(mc)

    if "brand_representatives" in data:
        old_reps = data.pop("brand_representatives")
        migrated_contacts = []
        for r in old_reps:
            nc = dict(r)
            if "brand_rep_id" in nc and "brand_contact_id" not in nc:
                nc["brand_contact_id"] = nc.pop("brand_rep_id")
            migrated_contacts.append(nc)
        data.setdefault("brand_contacts", [])
        existing_ids = {c.get("brand_contact_id") for c in data["brand_contacts"]}
        for mc in migrated_contacts:
            if mc.get("brand_contact_id") not in existing_ids:
                data["brand_contacts"].append(mc)

    # ------------------------------------------------------------------ #
    # 2.  Ensure default collections exist                                #
    # ------------------------------------------------------------------ #
    for key in ("creators", "brand_contacts", "social_media_accounts"):
        data.setdefault(key, [])

    # ------------------------------------------------------------------ #
    # 3.  Backfill person_id on creators that lack one                    #
    # ------------------------------------------------------------------ #
    persons: list[dict] = data.get("persons", [])
    existing_person_ids = {p["person_id"] for p in persons}

    def _next_id() -> int:
        nid = data.get("_next_id", 0) + 1
        data["_next_id"] = nid
        return nid

    for creator in data.get("creators", []):
        if creator.get("person_id"):
            continue
        # Create a minimal person record from whatever fields exist
        first = creator.get("first_name", "")
        last = creator.get("last_name", "")
        full = creator.get("full_name") or f"{first} {last}".strip() or f"Creator {creator.get('creator_id')}"
        new_pid = _next_id()
        while new_pid in existing_person_ids:
            new_pid = _next_id()
        person = {
            "person_id": new_pid,
            "first_name": first,
            "last_name": last,
            "full_name": full,
            "display_name": creator.get("display_name", full),
            "email": creator.get("email", ""),
            "phone": creator.get("phone", ""),
            "address": creator.get("address", ""),
            "city": creator.get("city", ""),
            "state": creator.get("state", ""),
            "zip": creator.get("zip", ""),
        }
        persons.append(person)
        existing_person_ids.add(new_pid)
        creator["person_id"] = new_pid

    # ------------------------------------------------------------------ #
    # 4.  Backfill person_id on brand_contacts that lack one              #
    # ------------------------------------------------------------------ #
    for contact in data.get("brand_contacts", []):
        if contact.get("person_id"):
            continue
        first = contact.get("first_name", "")
        last = contact.get("last_name", "")
        full = contact.get("full_name") or f"{first} {last}".strip() or f"Contact {contact.get('brand_contact_id')}"
        new_pid = _next_id()
        while new_pid in existing_person_ids:
            new_pid = _next_id()
        person = {
            "person_id": new_pid,
            "first_name": first,
            "last_name": last,
            "full_name": full,
            "display_name": contact.get("display_name", full),
            "email": contact.get("email", ""),
            "phone": contact.get("phone", ""),
            "address": contact.get("address", ""),
            "city": contact.get("city", ""),
            "state": contact.get("state", ""),
            "zip": contact.get("zip", ""),
        }
        persons.append(person)
        existing_person_ids.add(new_pid)
        contact["person_id"] = new_pid

    data["persons"] = persons

    # ------------------------------------------------------------------ #
    # 5.  Ensure access_control_matrix is present                         #
    # ------------------------------------------------------------------ #
    from crm.persistence.json_store import JsonDataStore
    data.setdefault("access_control_matrix", JsonDataStore.DEFAULT_ACM)

    # ------------------------------------------------------------------ #
    # 6.  Update deal references: client_id -> creator_id                 #
    # ------------------------------------------------------------------ #
    for deal in data.get("deals", []):
        if "client_id" in deal and "creator_id" not in deal:
            deal["creator_id"] = deal.pop("client_id")
        # brand_rep_id -> brand_contact_id
        if "brand_rep_id" in deal and "brand_contact_id" not in deal:
            deal["brand_contact_id"] = deal.pop("brand_rep_id")

    return data


def run_migration(filepath: str) -> bool:
    """Load *filepath*, migrate if needed, write back safely.

    Returns True if migration was performed, False if not needed.
    """
    if not os.path.exists(filepath):
        return False

    with open(filepath, "r") as f:
        data = json.load(f)

    if not needs_migration(data):
        # Still ensure ACM exists even on already-migrated files
        from crm.persistence.json_store import JsonDataStore
        if "access_control_matrix" not in data:
            data["access_control_matrix"] = JsonDataStore.DEFAULT_ACM
            with open(filepath, "w") as f:
                json.dump(data, f, indent=4)
        return False

    # Create backup
    backup_path = filepath + ".pre_chunk6.bak"
    if not os.path.exists(backup_path):
        shutil.copy2(filepath, backup_path)
        print(f"[migration] Backup written to {backup_path}")

    migrated = migrate(data)

    with open(filepath, "w") as f:
        json.dump(migrated, f, indent=4)

    print("[migration] data.json migrated to v2 schema (creators / brand_contacts).")
    return True
