# Alina J Talent Connect CRM

A Python CRM application for managing people, creators, brands, deals, and contracts.

The project includes:
- A CLI app entry point.
- A Flask web portal with authentication and role-based access control.
- Multiple storage backends with a seamless switch model:
  - JSON file backend (default)
  - SQLite backend
  - PostgreSQL backend
- An Admin-only database dashboard for operational visibility and import actions.

## Tech Stack

- Python 3.11+
- Flask
- SQLAlchemy (SQLite backend)
- psycopg v3 (PostgreSQL backend)
- pytest

## Project Highlights

- CRUD services for roles, persons, users, employees, creators, social media accounts, brands, brand contacts, deals, and contracts.
- Role-based permissions via an access control matrix.
- Password hashing for stored user passwords.
- Storage backend selection through environment variables.
- Idempotent JSON-to-database import flow.
- Admin DB dashboard with:
  - backend/status visibility
  - table counts
  - table explorer with pagination
  - import action
  - admin password reset tool

## Quick Start

### 1. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Run the web app (default JSON backend)

```powershell
python -m flask --app crm.ui.web.app:create_app run --debug
```

Then open:

- http://127.0.0.1:5000/

## Storage Backends

Backend selection is controlled by environment variables in the Flask app factory.

### Environment Variables

- `CRM_STORAGE_BACKEND`: `json` (default), `sqlite`, or `postgres`
- `DATABASE_URL`: required for postgres, optional for sqlite
- `CRM_AUTO_IMPORT`: set to `1` to auto-import from `data.json` at startup for db backends
- `SECRET_KEY`: Flask session secret (set a strong value outside local dev)
- `FLASK_DEBUG`: set to `1` for debug mode when running via `python crm/ui/web/app.py`

### JSON Backend (default)

No extra configuration required:

```powershell
$env:CRM_STORAGE_BACKEND="json"
python -m flask --app crm.ui.web.app:create_app run --debug
```

### SQLite Backend

Option A: let the app auto-create/use `project.db`:

```powershell
$env:CRM_STORAGE_BACKEND="sqlite"
Remove-Item Env:DATABASE_URL -ErrorAction SilentlyContinue
python -m flask --app crm.ui.web.app:create_app run --debug
```

Option B: specify a custom SQLite database file:

```powershell
$env:CRM_STORAGE_BACKEND="sqlite"
$env:DATABASE_URL="sqlite:///project.db"
python -m flask --app crm.ui.web.app:create_app run --debug
```

Optional auto-import on startup:

```powershell
$env:CRM_AUTO_IMPORT="1"
```

### PostgreSQL Backend

Set postgres backend and connection URL:

```powershell
$env:CRM_STORAGE_BACKEND="postgres"
$env:DATABASE_URL="postgresql://username:password@localhost:5432/alina_crm"
python -m flask --app crm.ui.web.app:create_app run --debug
```

Optional auto-import on startup:

```powershell
$env:CRM_AUTO_IMPORT="1"
```

At startup, the app ensures schema exists. Import is idempotent and can be triggered through Admin DB Dashboard as well.

## Import and Migration Behavior

- JSON backend runs JSON schema migration as needed before loading data.
- DB backends ensure relational schema exists.
- PostgreSQL import is idempotent:
  - if `roles` table already has rows, import is skipped.
- SQLite import follows equivalent idempotent behavior.

## Admin DB Dashboard

Route:

- `/admin/db`

Access:

- Requires authenticated user.
- Requires role name `Admin`.

What it shows:

- Active storage backend
- DB connectivity status (db backends)
- Row counts by table
- Table explorer (columns + paginated rows)
- Last import timestamp (postgres)

Actions:

- Import from `data.json` (idempotent)
- Admin-only user password reset from the `users` table view

Security notes:

- No arbitrary SQL execution UI is exposed.
- Connection strings are not displayed in dashboard output.

## Versioned API

The app exposes a small JSON API under `/api/v1` for authenticated clients.

Endpoints:

- `GET /api/v1/items` returns the authenticated user's scoped creator records as JSON.
- `GET /api/v1/items/<item_id>` returns one scoped creator record as JSON.

Responses:

- Unauthenticated requests return `401` with `{"error": "Unauthorized"}`.
- Missing or out-of-scope items return `404` with `{"error": "Not found"}`.

Example:

```powershell
GET /api/v1/items
```

## CLI Entry Point

CLI launcher:

```powershell
python app.py
```

## Database Bootstrap Helper (SQLite)

You can initialize and seed SQLite directly:

```powershell
python create_db.py
```

Optional variables for this script:

- `DATABASE_URL` (default: `sqlite:///project.db`)
- `DATA_JSON_PATH` (default: `./data.json`)

## Testing

Run all tests:

```powershell
pytest
```

Run targeted tests:

```powershell
pytest tests/test_admin_routes.py
pytest tests/test_postgres_import.py
pytest tests/test_postgres_schema.py
```

## Repository Layout (Top Level)

- `crm/domain`: domain models and validators
- `crm/persistence`: data stores, migration, repository helpers, import tools
- `crm/policies`: access control policy
- `crm/services`: application services
- `crm/ui/cli.py`: CLI interface
- `crm/ui/web`: Flask app, routes, templates, static assets
- `tests`: unit and route tests

## Notes for Deployment

- Default behavior is backward compatible with `data.json`.
- To switch environments safely:
  1. configure db backend in staging
  2. verify `/admin/db` connectivity
  3. run import from dashboard (or set `CRM_AUTO_IMPORT=1`)
  4. validate core entity pages and auth workflows


