# Chunk 4: Web-Ready Refactor (Layered Architecture + Testable Core)

## Why this chunk exists
Chunk 5 will replace the CLI with a Flask web application. To make that transition smooth, this chunk focuses on **refining and restructuring the existing code** so that the “core CRM logic” is **framework-agnostic**.

Right now, `app.py` mixes:
- domain concepts (Role, User, Employee, Client, Deal, Contract...)
- persistence (JSON file reads/writes)
- business rules (who can see what, direct reports, create/modify/delete rules)
- UI concerns (printing tables, input prompts, navigation loops)

That coupling makes it harder to:
- reuse logic inside Flask routes
- write unit tests
- swap storage later (SQLite/Postgres) without rewriting everything

This chunk introduces a **layered architecture** while keeping behavior the same.

---

## Objectives
1. **Separate concerns** into modules:
   - Domain models / schemas
   - Persistence (JSON repository)
   - Service layer (use-cases)
   - Authorization + visibility policies (RBAC)
   - UI adapters (CLI now, Flask later)
2. **Eliminate global state dependence** where possible (or isolate it behind a repository object).
3. **Make core logic testable** without input()/print().
4. Keep the existing CLI operational (even if slightly reorganized), but with the CLI as a “thin adapter”.

---

## Target architecture (after Chunk 4)

### 1) Domain layer (pure Python, no I/O)
**Goal:** Represent CRM concepts and validate data consistently.

Recommended:
- `crm/domain/models.py`
  - dataclasses (or lightweight classes) for: Role, Person, User, Employee, Client, Brand, BrandRepresentative, Deal, Contract, SocialMediaAccount
- `crm/domain/validators.py`
  - email/phone validation, required fields, date parsing helpers, etc.

Notes:
- Use consistent ID field naming. In your current code, IDs are `*_id` (good).
- Prefer a single source of truth for allowed enum-like fields (e.g., contract status).

### 2) Persistence layer (JSON storage behind an interface)
**Goal:** Flask should not know about JSON structure or files.

Recommended:
- `crm/persistence/json_store.py`
  - `JsonDataStore` (responsible for reading/writing the file)
- `crm/persistence/repositories.py`
  - repository objects per entity (or a generic repository)

Key idea:
- Services should call repositories, not `open()` directly.
- `id_incrementer` should become a store concern (e.g., `store.next_id()`), not a global.

### 3) Service layer (use-cases)
**Goal:** Put business logic here so CLI and Flask can reuse it.

Recommended:
- `crm/services/auth_service.py`
  - register_user(), authenticate()
  - password hashing (see below)
- `crm/services/employee_service.py`, `client_service.py`, `deal_service.py`, etc.
  - create/update/delete/list functions
  - handle relationships (e.g., employee-manager, client-owner, deal relations)

Rule of thumb:
- Service functions accept **plain parameters** and return **objects/dicts**.
- They should not call `input()` or `print()`.

### 4) Authorization & visibility policies (RBAC)
**Goal:** Centralize “who can do what / who can see what” so it’s consistent in CLI and Flask.

Recommended:
- `crm/policies/access_control.py`
  - `can_view(entity, user)`
  - `can_edit(entity, user)`
  - `scope_query(user, entity_type)` -> returns filtered lists

This chunk should formalize the permission rules already implied by the CLI:
- Admin: full access
- Manager: can access Employees under them + associated Clients + deals/contracts under that hierarchy
- Employee: can access their own Clients and related deals/contracts
- User/Client/Rep: read-only access to deals/campaigns relevant to them (as designed)

### 5) Interface adapters
**Goal:** CLI becomes a wrapper around services.

Recommended:
- `crm/ui/cli.py`
  - handles menus and input prompts
  - calls service layer for actions
- Keep `display_table()` and selection helpers here (or in `crm/ui/formatting.py`)

Flask in Chunk 5 becomes another adapter:
- `crm/ui/web/routes.py` (later)
- Calls the same services

---

## Required refactors (high impact for Flask readiness)

### A) Replace plaintext passwords with hashing (now)
Your README states “Encrypted password storage.” Currently, the default admin uses `"admin"` password, and user registration stores plaintext.

In Chunk 4, implement:
- hash_password(password) using `werkzeug.security` or `bcrypt`
- verify_password(hash, password)

This is **not Flask-specific** and will carry directly into Chunk 5.

### B) Make data.json schema explicit and stable
Flask will rely on stable schema keys. Create a documented schema map for:
- top-level keys: roles, persons, users, employees, clients, social_media_accounts, brands, brand_representatives, deals, contracts
- required fields for each record
- foreign key relationships (person_id, employee_id, client_id, deal_id, etc.)

Add:
- `docs/data_schema.md` OR a section in README
- A migration strategy if schema changes (even if manual for now)

### C) Remove pandas dependency from the core
`pandas` is being used for CLI table formatting. That’s fine, but:
- keep it in the CLI adapter layer
- services and persistence should not require pandas

This reduces runtime weight and avoids unnecessary dependency issues later.

### D) Convert `app.py` into a thin entrypoint
By the end of chunk 4:
- `app.py` should ideally just call `crm/ui/cli.py:main()` (or similar).
- All logic should live in modules.

---

## Step-by-step task list

### Step 1: Create package structure
Create:
- `crm/`
  - `__init__.py`
  - `domain/`
  - `persistence/`
  - `services/`
  - `policies/`
  - `ui/`

### Step 2: Introduce a DataStore abstraction
Implement:
- `JsonDataStore.load() -> data`
- `JsonDataStore.save(data)`
- `JsonDataStore.next_id(data) -> int` (or maintain a stored counter)

Update code to:
- stop using global `data` directly inside services

### Step 3: Move models into domain
Implement models as dataclasses with:
- `.to_dict()` and `from_dict()` helpers (or keep dicts but define canonical keys)

### Step 4: Move business logic into services
Examples:
- AuthService.register_user(person_fields, username, password)
- DealService.create_deal(...)
- EmployeeService.add_employee(...)

### Step 5: Implement access control policy module
Add centralized rule checks and scoping filters.

### Step 6: Update CLI to call services
The CLI should:
- fetch the current user
- show menus
- call services
- render output

### Step 7: Add unit tests for services and policies
Create `tests/` and add tests for:
- password hashing/verification
- access control decisions
- create/update flows for a couple core entities

Even a small test suite will massively help when moving to Flask.

---

## Definition of Done (Chunk 4)
- Code is split into modules with clear responsibility boundaries.
- Core CRUD and business logic runs without any CLI dependency.
- `data.json` persistence still works.
- Passwords are hashed and verified.
- CLI still functions (even if not as polished), proving the refactor didn’t break behavior.
- A minimal test suite exists and can be run locally.

---

## What Chunk 5 will do (preview)
Chunk 5 will:
- replace the CLI adapter with Flask routes + templates (or API endpoints)
- reuse the same service layer, repositories, and policies from Chunk 4
- introduce sessions/login handling in a web context

Chunk 4’s job is to ensure Chunk 5 mostly becomes “wiring + HTML” instead of rewriting logic.
