# Chunk 9 — Versioned API Layer (`/api/v1`) + Protected JSON Endpoints (List + Detail)

This chunk adds a minimal, production-shaped API surface to the existing Flask app—**without replacing** the server-rendered portal. The goal is to introduce a clean `/api/v1` namespace, reuse the existing **services + policies + datastore** patterns, and return **JSON** responses that are safe (auth-protected + scoped) and predictable (proper HTTP status codes).

> Context from the repo
> - Primary stack is **Python (Flask)** with server-rendered templates (Chunk 5+), but the architecture emphasizes “routes are adapters” and core logic belongs in **services/policies**.
> - Data is currently JSON-backed via `JsonDataStore` and repository/service layers (see `crm/persistence/*`, `crm/services/*`, and `crm/policies/*`).
> - RBAC/scoping is enforced server-side; API endpoints must follow the same rules.

---

## Goals

1. **Introduce a versioned API namespace**
   - All API endpoints live under `/api/v1/*`
   - API routes are grouped in a dedicated blueprint/module

2. **Ship two protected endpoints**
   - List endpoint: return all items for the authenticated user
   - Detail endpoint: return one specific item (scoped to user)

3. **Enforce security + correctness**
   - API endpoints require authentication
   - Responses are JSON (not HTML templates)
   - Missing/unauthorized resources return `404 Not Found` (no data leakage)

---

## API UX (What the client should see)

### A) `GET /api/v1/items`
Returns a JSON list of all items visible to the authenticated user.

Example response:
```json
{
  "items": [
    { "id": 123, "name": "..." },
    { "id": 124, "name": "..." }
  ]
}
```
### B) GET /api/v1/items/<item_id>
Returns a single item object (JSON) if:

- it exists and
- it is within the authenticated user’s allowed scope

Example response:
```json
{
  "item": { "id": 123, "name": "..." }
}
```

If not found (or not allowed), return:

- HTTP 404
- JSON body:

```json
{ "error": "Not found" }
```
## “Item” definition (pick an existing entity)
Preferred: implement the endpoints for a real CRM entity that already exists and has ownership/scoping rules. Choose one of:

- creators (formerly clients)
- deals
- contracts
- brands
Rule: The list endpoint must return only records in the authenticated user’s scope (via existing policy/service scoping). The detail endpoint must not expose existence of out-of-scope records (return 404).

If there is no clear ownership/scoping mechanism on a chosen entity yet, add the smallest possible scoping logic in the policy/service layer (not the route).

## Implementation Plan (Flask + Blueprints + Services)
---

### Step 1) Add an API blueprint
Create a new blueprint dedicated to the API v1 namespace.

Suggested files

- crm/ui/web/routes/api_v1_routes.py (or crm/ui/web/routes/api/v1.py if an api/ folder already exists)
- Register the blueprint in crm/ui/web/app.py with:
  - url_prefix="/api/v1"

Outcome: /api/v1/* endpoints exist and are grouped cleanly.
---

### Step 2) Authentication protection (reuse existing auth)
All API routes must require authentication using the repo’s existing mechanism (for example: @login_required + current_user).

Rules

- Do not invent a new auth system (no new JWT layer) unless the repo already uses it.
- If the current app redirects unauthenticated users to login (HTML behavior), prefer returning JSON 401 for API routes if the repo already has a pattern for this. Otherwise, keep it consistent with existing auth behavior.

Outcome: API endpoints are protected.
---

### Step 3) Add service-layer methods (or reuse existing ones)
Routes must act as adapters:

- parse request
- call service layer
- return JSON
Suggested

- Add an API-focused service wrapper if needed, but prefer reusing existing services:
  - SomeEntityService.list_for_user(user)
  - SomeEntityService.get_for_user(user, entity_id)
Outcome: Business rules and scoping live in services/policies, not in routes.
---

### Step 4) Serialization (to_dict() / view-model)
Return JSON-safe dicts only. Do not return ORM objects (not applicable yet) or raw internal structures if they include sensitive fields.

Approach

- If domain models already have .to_dict(), use it.
- Otherwise create a small serializer/helper that builds a stable API shape.

Outcome: Predictable JSON responses.
---

### Step 5) Error handling + status codes
Implement consistent API error responses.

Minimum

- Not found or out-of-scope: 404 with {"error":"Not found"}
- Invalid item_id (non-int) if applicable: return 404 or 400 (match repo’s patterns; 404 is acceptable to avoid leaking details)
Outcome: Clean, consistent failure modes.
---

### Testing Plan (minimal but valuable)
If the repo already uses pytest/unittest, add tests for:

1. Auth
  - unauthenticated GET /api/v1/items is blocked (redirect or 401 depending on existing app behavior)
2. List
  - authenticated user receives 200 and a JSON array
3. Detail
  - authenticated user can fetch an in-scope item (200)
  - missing item returns 404
  - out-of-scope item returns 404
Outcome: API behavior stays stable as the project evolves.
---

## Deliverables Checklist
- New API blueprint registered under /api/v1
- GET /api/v1/items implemented (auth + scoped + JSON)
- GET /api/v1/items/<item_id> implemented (auth + scoped + JSON + 404)
- Serialization method(s) in an appropriate layer
- Minimal tests (if test framework exists)
- Short documentation note (README or docs) describing how to call the endpoints
---

## Definition of Done
- /api/v1/items returns only the authenticated user’s scoped items as JSON.
- /api/v1/items/<item_id> returns the scoped item as JSON, otherwise 404.
- All endpoints require authentication.
- Routes remain thin adapters; logic lives in services/policies.
