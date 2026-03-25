# Chunk 7 — Seamless migration from `data.json` to PostgreSQL + Admin DB Dashboard (Web)

This chunk upgrades the web app in `nathan-hammond-uvu/Alina_J_Talent_Connect_CRM` from using `data.json` (currently wired in `crm/ui/web/app.py` via `JsonDataStore`) to using PostgreSQL **without breaking existing behavior**, and adds an **administrator-only database dashboard** when a user logs in with the **Admin** role (`role_name == "Admin"` in `roles`).

> Current reality check (from repo):
> - Web app factory: `crm/ui/web/app.py` creates a Flask app and injects `JsonDataStore("data.json")` into services.
> - Users & roles live in `data.json` (`roles` includes `"Admin"`; `users` has `admin` with `role_id: 4`).
> - Access control logic recognizes Admin as full access in `crm/policies/access_control.py`.

---

## Goals

1. **Migrate to PostgreSQL seamlessly**
   - Default to PostgreSQL when configured (via env var), otherwise keep JSON storage working.
   - Provide an **automatic one-time import** from the existing `data.json` into PostgreSQL (idempotent).
   - Keep existing services/routes working by preserving the store/repository interface.

2. **Administrator database dashboard**
   - Only visible/accessible to Admin users.
   - Provides basic operational visibility:
     - table row counts
     - recent records (optional)
     - health checks (DB connectivity)
     - a safe “Run import/migration” action (admin-only)
   - Must not expose credentials or allow arbitrary SQL execution (avoid building a SQL console).

---

## High-level Design

### A) Add a new Postgres-backed store that matches the Json store contract
Today the web app assumes:

- `store = JsonDataStore(path)`
- services use repositories (in `crm/persistence/repositories.py`) which call `store.load()` / `store.save()` patterns (JSON document semantics).

**Migration strategy:** implement a new `PostgresDataStore` that provides *equivalent repository operations*, but backed by relational tables.

There are two viable approaches:

#### Option 1 (recommended): migrate repositories to be storage-agnostic
- Introduce a repository interface layer and have **JsonRepositories** and **PostgresRepositories**.
- Services depend on repositories, not the raw store.

#### Option 2 (minimal change): emulate `load()` / `save()` on top of Postgres
- `PostgresDataStore.load()` returns a dict with keys `roles`, `persons`, `users`, etc.
- `PostgresDataStore.save(data)` writes back whole collections.
- This is easiest initially but less efficient long-term.

**For “seamless” migration with minimal disruption**, start with **Option 2** (emulation), then refactor later.

---

## B) Database schema (PostgreSQL)

Create tables that correspond to the JSON root keys (based on `data.json`):

- `roles(role_id PK, role_name)`
- `persons(person_id PK, first_name, last_name, full_name, display_name, email, phone, address, city, state, zip)`
- `users(user_id PK, username UNIQUE, password, role_id FK->roles, person_id FK->persons)`
- `employees(employee_id PK, person_id FK->persons, position, title, manager_id, start_date, end_date, is_active, is_manager)`
- `clients(...)` (currently empty in JSON, but include table for parity)
- `social_media_accounts(...)`
- `brands(...)`
- `brand_representatives(...)`
- `deals(...)`
- `contracts(...)`

Also, because `crm/policies/access_control.py` references an ACM stored in `data.json` under `access_control_matrix`, add:

- `settings(key TEXT PK, value JSONB NOT NULL)`
  - store `access_control_matrix` here as JSONB for now (keeps feature parity)

**Notes**
- Preserve IDs from JSON during import to avoid breaking references.
- Add indices for FK columns later if needed.

---

## C) Configuration & Seamless Switch

Use environment variables so deployment can toggle without code changes:

- `CRM_STORAGE_BACKEND` = `json` | `postgres` (default: `json` until you flip it)
- `DATABASE_URL` = PostgreSQL connection string (e.g. `postgresql://user:pass@host:5432/dbname`)
  - If you’re using `psycopg` v3, it supports this style directly.

Behavior:
- If `CRM_STORAGE_BACKEND=postgres` and `DATABASE_URL` is set → use Postgres.
- Else → use JSON store and behave exactly as before.

---

## D) One-time Import / Migration (Idempotent)

Add a migration/import routine:

1. Connect to Postgres
2. Ensure tables exist (`CREATE TABLE IF NOT EXISTS ...`)
3. Check if DB already has data (e.g., `SELECT COUNT(*) FROM roles`)
4. If empty, read `data.json` and insert rows
5. If not empty, do nothing (idempotent)

This can run:
- automatically at app startup (safe if idempotent), OR
- via an admin-only “Import from JSON” button in the dashboard (safer operationally)

**Recommended:** do both:
- On startup, only ensure schema exists.
- Import is admin-triggered (so you can choose the right moment), *but* also allow `CRM_AUTO_IMPORT=1` for dev.

---

## Implementation Tasks

### 1) Dependencies
Update `requirements.txt` to include a Postgres driver:
- `psycopg[binary]>=3.1` (recommended) OR `psycopg2-binary` (legacy)

Also consider:
- `python-dotenv` for local dev (optional)

### 2) Add `crm/persistence/postgres_store.py`
Responsibilities:
- manage DB connection creation (use `DATABASE_URL`)
- `ensure_schema()` method to create tables
- `load()` returning full dict (collections)
- `save(data)` to write (initially can be limited if your app only uses CRUD via repositories; but for seamless compatibility implement full save)
- helper methods for reading/writing settings JSONB (`access_control_matrix`)

### 3) Update `crm/ui/web/app.py` to select backend
Replace hard-coded:

```python
store = JsonDataStore(resolved_path)
```

with:

- if postgres configured: `store = PostgresDataStore(database_url)`
- else: `store = JsonDataStore(resolved_path)`

Also:
- keep calling existing `run_migration(resolved_path)` for JSON schema migrations, but **only when using json backend**.
- add `ensure_schema()` call when using postgres backend.

### 4) Add `crm/persistence/postgres_import.py` (or inside postgres_store)
Implement `import_from_json(json_path)`:
- reads JSON file
- inserts rows in correct order (roles → persons → users → employees → rest)
- inserts `access_control_matrix` into `settings` as JSONB if present

### 5) Admin authorization helper
Add a small helper like:

- `is_admin_user(user: dict, store) -> bool`
  - Determine role_name for the user using role_id lookup
  - Keep consistent with `AccessPolicy` which treats `"Admin"` specially.

You already have `AccessPolicy._get_role_name(user)` internally, but it’s private.
You can either:
- add a public `AccessPolicy.is_admin(user)` method, OR
- implement a small utility in web routes that uses RoleRepository.

### 6) Administrator DB Dashboard (Web)
Add:
- `crm/ui/web/routes/admin_db_routes.py` blueprint at `/admin/db`

Features:
- GET `/admin/db`
  - requires login
  - requires admin
  - show:
    - DB backend in use (`json` vs `postgres`)
    - if postgres:
      - connectivity ok
      - row counts for each table
      - last import timestamp (store in `settings` like `last_import_at`)
- POST `/admin/db/import`
  - requires admin
  - triggers import from `data.json` into postgres (idempotent)
  - flash success/failure message

Template:
- `crm/ui/web/templates/admin/db_dashboard.html`

Navigation:
- Add link in your settings or portal page template only when admin.

**Security:**
- Do **not** allow arbitrary SQL.
- Do **not** display raw connection strings, only host/db name if you choose (or just “configured”).

---

## Suggested Minimal UI for Dashboard

**Card 1: Backend**
- Backend: postgres/json
- Status: connected / n/a

**Card 2: Table counts** (postgres only)
- roles: N
- persons: N
- users: N
- employees: N
- ...

**Card 3: Actions** (postgres only)
- Button: “Import from data.json”
- Button: “Re-run schema ensure” (optional)

---

## Testing Plan

### Unit tests
Add tests under `tests/`:
- `test_postgres_schema.py`:
  - calling `ensure_schema()` creates tables
- `test_postgres_import.py`:
  - import is idempotent (run twice; counts don’t double)
- `test_admin_routes.py`:
  - non-admin receives 403 on `/admin/db`
  - admin receives 200

### Manual smoke test (local)
1. Start app with JSON (default) → existing behavior unchanged.
2. Start postgres (docker), set:
   - `CRM_STORAGE_BACKEND=postgres`
   - `DATABASE_URL=...`
3. Visit `/admin/db` as admin (username `admin`, password as defined in your app) → see dashboard.
4. Click import → verify CRUD pages show data pulled from postgres.

---

## Docker (optional but helpful)
Add `docker-compose.yml` with:
- postgres service
- env var wiring

---

## Rollout / Migration Steps (Operational)

1. Deploy postgres + set `CRM_STORAGE_BACKEND=postgres` in staging, but do not import yet.
2. Admin logs in and runs import via dashboard.
3. Verify app reads from postgres.
4. Keep `data.json` as a backup artifact for one release cycle.
5. Later, remove JSON path or lock it behind a maintenance mode.

---

## Deliverables Checklist

- [ ] `crm/persistence/postgres_store.py`
- [ ] `crm/persistence/postgres_import.py` (or integrated in store)
- [ ] update `crm/ui/web/app.py` backend selection
- [ ] update `requirements.txt` for postgres driver
- [ ] new blueprint `crm/ui/web/routes/admin_db_routes.py`
- [ ] new template `crm/ui/web/templates/admin/db_dashboard.html`
- [ ] add link to dashboard for Admin users
- [ ] tests for schema/import/admin access

---

## Notes / Constraints

- This chunk is designed to **preserve current behavior** by default (JSON remains default until env var flips).
- Once postgres is stable, the next refactor would be: stop emulating JSON `load/save` and implement true repository-level SQL operations for performance and correctness.