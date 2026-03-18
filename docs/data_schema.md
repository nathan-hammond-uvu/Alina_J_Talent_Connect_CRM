# Data Schema — Alina J Talent Connect CRM

> **Last updated:** Chunk 6 (Database-Ready People Model + ACM)

## Overview

All data is stored in `data.json` as a JSON object with top-level keys for each entity collection.

### Top-level keys (v2 schema)

```json
{
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
  "_next_id": 1
}
```

> **Renamed in v2 (Chunk 6):**
> - `clients` → `creators`
> - `brand_representatives` → `brand_contacts`
>
> The migration routine (`crm/persistence/migration.py`) handles existing files automatically on startup.

---

## Entities

### Role
Defines the access level of a user.

| Field | Type | Description |
|-------|------|-------------|
| `role_id` | int | Primary key |
| `role_name` | str | One of: `User`, `Employee`, `Manager`, `Admin`, `Creator` |

---

### Person
Represents any real-world individual (employee, creator, contact, admin, etc.). **All "human" records reference a Person.**

| Field | Type | Description |
|-------|------|-------------|
| `person_id` | int | Primary key |
| `first_name` | str | Given name |
| `last_name` | str | Family name |
| `full_name` | str | Concatenated first + last name |
| `display_name` | str | Preferred display / stage name |
| `email` | str | Email address |
| `phone` | str | Phone number |
| `address` | str | Street address |
| `city` | str | City |
| `state` | str | State / province |
| `zip` | str | ZIP / postal code |

---

### User
Authentication record linked to a `Person`.

| Field | Type | Description |
|-------|------|-------------|
| `user_id` | int | Primary key |
| `username` | str | Unique login name |
| `password` | str | Werkzeug password hash (legacy: plaintext, auto-upgraded on login) |
| `role_id` | int | FK → `Role.role_id` |
| `person_id` | int | FK → `Person.person_id` |

---

### Employee
Represents a staff member at the agency.

| Field | Type | Description |
|-------|------|-------------|
| `employee_id` | int | Primary key |
| `person_id` | int | FK → `Person.person_id` (required) |
| `position` | str | Job position / department |
| `title` | str | Job title |
| `manager_id` | int | FK → `Employee.employee_id` (0 = no manager) |
| `start_date` | str | Employment start date (YYYY-MM-DD) |
| `end_date` | str \| null | Employment end date (YYYY-MM-DD), null if active |
| `is_active` | bool | Whether currently employed |
| `is_manager` | bool | Whether this employee manages others |

---

### Creator
Represents a talent / influencer managed by an employee. *(Formerly "Client")*

| Field | Type | Description |
|-------|------|-------------|
| `creator_id` | int | Primary key |
| `person_id` | int | FK → `Person.person_id` (required) |
| `employee_id` | int | FK → `Employee.employee_id` (assigned agent) |
| `description` | str | Short description / bio |

---

### SocialMediaAccount
A social-media profile linked to a `Creator`.

| Field | Type | Description |
|-------|------|-------------|
| `social_media_id` | int | Primary key |
| `creator_id` | int | FK → `Creator.creator_id` |
| `account_type` | str | Platform name (e.g., `Instagram`, `TikTok`) |
| `link` | str | Profile URL |

---

### Brand
A company or brand that may sponsor creators.

| Field | Type | Description |
|-------|------|-------------|
| `brand_id` | int | Primary key |
| `description` | str | Brand name / description |

---

### BrandContact
A person who represents a `Brand` in deal negotiations. *(Formerly "BrandRepresentative")*

| Field | Type | Description |
|-------|------|-------------|
| `brand_contact_id` | int | Primary key |
| `person_id` | int | FK → `Person.person_id` (required) |
| `brand_id` | int | FK → `Brand.brand_id` |
| `notes` | str | Additional notes |

---

### Deal
A pitch / sponsorship deal between a `Creator` and a `Brand`.

| Field | Type | Description |
|-------|------|-------------|
| `deal_id` | int | Primary key |
| `client_id` | int | FK → `Creator.creator_id` (legacy field name retained for compatibility) |
| `brand_id` | int | FK → `Brand.brand_id` |
| `brand_rep_id` | int | FK → `BrandContact.brand_contact_id` (legacy field name retained) |
| `pitch_date` | str | Date the deal was pitched (YYYY-MM-DD) |
| `is_active` | bool | Whether the deal is still in progress |
| `is_successful` | bool | Whether the deal was successfully closed |

---

### Contract
A formal contract associated with a closed `Deal`.

| Field | Type | Description |
|-------|------|-------------|
| `contract_id` | int | Primary key |
| `deal_id` | int | FK → `Deal.deal_id` |
| `details` | str | Contract description / scope |
| `payment` | float | Total payment amount |
| `agency_percentage` | float | Agency commission percentage (0–100) |
| `start_date` | str | Contract start date (YYYY-MM-DD) |
| `end_date` | str | Contract end date (YYYY-MM-DD) |
| `status` | str | One of: `Sent`, `Pending`, `Accepted`, `Rejected` |
| `is_approved` | bool | Whether the contract has been formally approved |

---

## Relationships

```
Person ──< User
Person ──< Employee
Person ──< Creator
Person ──< BrandContact

Role ──< User

Employee ──< Creator
Employee ──< Employee (self-referencing via manager_id)

Creator ──< SocialMediaAccount
Creator ──< Deal (via client_id)

Brand ──< BrandContact
Brand ──< Deal

BrandContact ──< Deal (via brand_rep_id)

Deal ──< Contract
```

---

## Access Control Matrix (ACM)

Stored in `data.json` under the `access_control_matrix` key. Structure:

```json
{
  "Admin":    { "<entity>": { "create": true, "read": true, "update": true, "delete": true } },
  "Manager":  { "<entity>": { ... } },
  "Employee": { "<entity>": { ... } },
  "Creator":  { "<entity>": { "create": false, "read": true, "update": false, "delete": false } },
  "User":     { "<entity>": { ... } }
}
```

**Hard constraints (not overridable by ACM edits):**
- `Admin` always has full access to everything.
- `Creator` can never write (create/update/delete) anything.
- `Manager` cannot update or delete other `Manager` employee records.

**Default permission rules:**
- Admin: full CRUD on all entities.
- Manager: full CRUD except cannot delete employees; cannot touch other managers.
- Employee: can manage own creators and all brand_contacts; read-only on most else.
- Creator: read-only on select entities (creators, brands, deals).
- User: read-only on deals only.

---

## Internal Fields

| Field | Type | Description |
|-------|------|-------------|
| `_next_id` | int | Auto-increment counter stored in `data.json`. Managed by `JsonDataStore.next_id()`. Not an entity field. |

---

## Migration

The migration module at `crm/persistence/migration.py` handles upgrading `data.json` from v1 to v2 schema automatically at app startup:

1. Renames `clients` → `creators` (remapping `client_id` → `creator_id`).
2. Renames `brand_representatives` → `brand_contacts` (remapping `brand_rep_id` → `brand_contact_id`).
3. Backfills `person_id` on any creator or brand_contact that lacks one.
4. Seeds the `access_control_matrix` if missing.
5. Creates a backup at `data.json.pre_chunk6.bak` before making changes.

