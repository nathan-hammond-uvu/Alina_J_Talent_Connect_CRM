# Chunk 6: Database-Ready People Model + Editable Access Control Matrix + UX Polish + Performance/Routing Hardening

## Why this chunk exists
Chunk 5 successfully wired the CRM core into a Flask, server-rendered portal with CRUD pages, templates, and role-aware visibility. Now that the web UI exists, the next pain points become clear:

1) The **people-related entities** (persons, users, employees, clients, brand_representatives) are not modeled consistently enough for an eventual relational database migration.

2) RBAC rules exist, but they’re **implicit and code-defined**. We need an explicit, visible **Access Control Matrix (ACM)** that admins can inspect and edit.

3) The UI is already “good”, but we can make it feel more **professional**, more consistent, and easier to navigate without changing the existing color palette/typography.

4) As the app grows, we must **optimize loading/scoping/rendering** so we don’t regress (slow pages, repeated JSON loads, inconsistent scoping, or forgotten routes).

This chunk focuses on **data model alignment + policy modernization + UX polish + reliability/performance improvements** while preserving the core behavior delivered in Chunk 5.

---

## Objectives

### Objective 1: Restructure data for database readiness (People model normalization)
We will restructure `data.json` and related service/persistence logic to make “people” consistent and relational-friendly.

Required changes:
1. Rename `clients` -> `creators`.
2. Rename `brand_representatives` -> `brand_contacts`.
3. Ensure that **all** of these records reference a **Person**:
   - Employees
   - Creators
   - Brand Contacts
   - Users
4. When creating a new Employee/Creator/Brand Contact/User, the UI must allow either:
   - linking to an **existing Person**, or
   - creating a **new Person** during creation.

**Goal:** every “human” record has a single canonical identity row (`persons`) so it can map cleanly to normalized DB tables later.

---

### Objective 2: Implement an Access Control Matrix (ACM) for CRUD functionality and make it editable in Settings
We will define a formal **Access Control Matrix** that applies to all CRUD actions and scoping behavior in the app.

Requirements:
- The matrix is **visible and editable** on the Settings page under a section called: **Access Control**
- Defaults/hard rules:
  1) **Admin** role has full, unrestricted access.
  2) **Managers** can make any changes, **except for other managers**.
  3) **Employees** can:
     - make changes for themselves and their creators
     - NOT edit other employees or other employees’ creators
     - **can edit all brand_contacts**
  4) **Creators** can only see their ACM; they can’t edit anything.
- Hierarchy (for ordering + reasoning):
  **admins -> managers -> employees -> creators -> brand_contacts**

**Important:** UI hiding buttons is not sufficient. The **server must enforce** ACM decisions on every add/edit/delete route.

---

### Objective 3: Enhance overall UX/UI without changing palette/typography
We will improve layout, spacing, and interaction design while keeping:

**Color palette**
- Primary: `#454E45`
- Secondary: `#EDDFD3`
- Tertiary: `#D1D3D1`
- Background: `#FFFFFF`

**Typography**
- Titles and Headers: Times New Roman
- Body text: Arial

We want pages that feel:
- consistent
- clean
- confident
- easy to scan
- “happy to use”

---

### Objective 4: Optimize rendering, routing, and data loading
We will remove unnecessary repeated loads, reduce duplicated code, and ensure that after schema + policy changes:
- Search still works
- CRUD still works
- Scoping still works
- Templates still render
- No “forgotten” old routes/entities remain in a half-deprecated state

---

## Part A — Data Model v2 (Database-ready People Model)

### A1) Schema changes (top-level keys)
Update `data.json` keys:

- `clients` -> `creators`
- `brand_representatives` -> `brand_contacts`

Target top-level (example, not exhaustive):
```json
{
  "roles": [],
  "persons": [],
  "users": [],
  "employees": [],
  "creators": [],
  "brand_contacts": [],
  "brands": [],
  "deals": [],
  "contracts": []
}
```

### A2) Standardize “Person” as the shared identity object
`persons` is the single canonical identity table.

**Person record (recommended canonical fields)**
- `person_id` (int)
- `first_name`
- `last_name`
- `full_name` (optional cached field; can be derived)
- `display_name` (UI display fallback)
- `email`
- `phone`
- `address`
- `city`
- `state`
- `zip`

**Rule:** Employees/Creators/Brand Contacts/Users must reference `person_id`.

### A3) Entity records must reference person_id
**Employee**
- `employee_id`
- `person_id` (required)
- `role_id` (or role name mapping depending on existing implementation)
- any existing hierarchy fields (e.g., manager relationships)

**Creator**
- `creator_id`
- `person_id` (required)
- `owner_employee_id` (recommended: which employee “owns” this creator, for scoping)

**Brand Contact**
- `brand_contact_id`
- `person_id` (required)
- `brand_id` (recommended: who they represent)
  - If this is too much for now, at minimum keep person link; brand link can be added later.

**User**
- `user_id`
- `person_id` (required)
- `username`
- `password` (hashed)
- `role_id` (recommended) OR a `role` string key, but prefer role_id

### A4) Migration strategy (one-time migration step)
Create a migration routine that:
1) Loads current `data.json`
2) Produces a new structure with renamed keys
3) Ensures every employee/client/rep has a valid `person_id`
4) Writes the migrated data back safely (backup recommended)

**Rules for migration:**
- If an entity already has a `person_id`, keep it.
- If it has person-like fields embedded, create a new Person row and link it.
- If it references a person by other keys, normalize to `person_id`.

**Important constraint:** This migration must not break existing logins. Users must still authenticate after migration.

---

## Part B — Person assignment UX (Create/Link flows)

### B1) Pattern: Choose existing Person OR create a new Person
For each “create” form that results in an Employee/Creator/Brand Contact/User:
- Provide a small “Person” section at the top of the form with:
  - a dropdown / selector of existing persons (by display_name/full_name/email)
  - OR inputs to create a new person

**Expected UX:**
- Radio / toggle:
  - ( ) Use existing person
  - ( ) Create new person
- If “Use existing” selected:
  - show dropdown
- If “Create new” selected:
  - show person fields (first name, last name, email, phone, etc.)

### B2) Required updates to services
Add a shared helper flow in a dedicated service:
- `PersonService.find_or_create_person(...)`
- or a generic helper in `AuthService`/`EmployeeService`/`CreatorService` that:
  - validates `person_id` exists if provided
  - creates a Person record if “create new” payload provided

**Rule:** Routes should not directly manipulate `data["persons"]`. Keep it in services.

---

## Part C — Rename Clients -> Creators, Brand Representatives -> Brand Contacts

### C1) Rename in code and templates
Update all references across:
- persistence repositories
- service layer
- policy layer
- routes
- templates
- navigation labels

Portal nav changes:
- Clients -> Creators

Templates folder changes:
- `templates/entities/clients.html` -> `templates/entities/creators.html`
- route endpoints and url_for names update accordingly

---

## Part D — Access Control Matrix (ACM)

### D1) Data model for ACM
Store the ACM in `data.json` so it can be edited without code changes.

Recommended:
```json
"access_control_matrix": {
  "version": 1,
  "rules": [
    {
      "role": "admin",
      "entity": "*",
      "action": "*",
      "effect": "allow"
    }
  ]
}
```

But to keep editing simple in the Settings UI, an alternate structure is acceptable:
```json
"access_control_matrix": {
  "admin": { "employees": {"create": true, "read": true, "update": true, "delete": true}, ... },
  "manager": { ... },
  "employee": { ... },
  "creator": { ... },
  "brand_contact": { ... }
}
```

**Important:** even if the ACM is editable, we must still enforce **hard constraints**:
- Admin always has full access.
- Creator can never edit anything.
- Hierarchy rules must remain consistent (don’t allow “creator edits employees” by misconfiguration).

To handle this cleanly:
- Keep “base constraints” in code
- Allow ACM to refine/limit within allowed bounds

### D2) ACM actions and entities
Define standard actions:
- `create`, `read`, `update`, `delete`

Define entities:
- `persons`
- `users`
- `employees`
- `creators`
- `brand_contacts`
- `brands`
- `deals`
- `contracts`

### D3) Rules to implement exactly (defaults)
1) **Admin**: allow everything (CRUD on everything)
2) **Manager**:
   - can CRUD almost everything in scope
   - cannot update/delete **other managers**
3) **Employee**:
   - can update self (employee record + own person/user profile as applicable)
   - can CRUD creators that are “owned” by that employee
   - can edit all brand_contacts
   - cannot edit other employees nor other employees’ creators
4) **Creator**:
   - read-only view of ACM
   - cannot create/update/delete anything

**Scope rules** must be explicit:
- “Self” means matching employee_id or user_id / person_id links
- “Their creators” means creator.owner_employee_id == current_employee_id (or equivalent mapping)

### D4) Settings UI: Access Control section
In `/portal/settings`:
- Add a new section titled **Access Control**
- It displays:
  - the role list
  - entity list
  - checkboxes for CRUD actions

Behavior:
- Admin users can edit and save ACM (POST)
- Non-admin users can view only (especially creators)
- Creators see ACM section, but no other editable settings (per requirement “they can’t edit anything”)

---

## Part E — UX/UI Improvements (keep palette + typography)

### E1) Portal layout improvements
Enhance `base_portal.html` + CSS:
- consistent spacing system (8px/16px/24px rhythm)
- improved sidebar:
  - clearer active state
  - grouped sections with headings
- page headers:
  - consistent title + optional subtitle
- cards:
  - subtle border using tertiary palette
  - consistent shadows (very light)

### E2) Forms
- Better label alignment
- Required fields indicator
- Inline error summaries
- Disable “Save” unless row is selected (where inline-edit pattern exists)
- Improve empty-state visuals (“No creators found yet. Add your first creator.”)

### E3) Tables
- Sticky header on long pages (optional)
- zebra striping using `#EDDFD3` at very low opacity
- more consistent “Actions” column styling
- accessible focus states

### E4) Confirmations and messaging
- Use flash messages consistently:
  - success
  - warning
  - danger
- Add a small global flash container in base templates

---

## Part F — Rendering, routing, and data-loading optimization

### F1) Reduce repeated data loads
Current pattern often loads `store.load()` per route, sometimes multiple times.

Target:
- Load once per request where possible.
- Services accept the loaded data or provide “unit of work” methods (if architecture supports it).
- Avoid reading/writing JSON repeatedly inside the same request.

### F2) Centralize “current user context”
Ensure there is exactly one canonical helper that builds portal context:
- display name resolution
- role resolution
- permission booleans
- nav visibility booleans
- ACM visibility/editability flags

### F3) Route consistency + deprecation cleanup
After renames:
- Ensure `/portal/clients` no longer exists (or redirects to `/portal/creators` temporarily)
- Ensure templates and url_for calls match new blueprint endpoints
- Ensure search results route to the correct new entity pages

### F4) Search correctness after schema change
Update search to:
- search over `creators` and `brand_contacts` (instead of old keys)
- still respect scoping rules
- still return links that work

---

## Step-by-step task list (Implementation Plan)

### Step 1: Add schema documentation + decide canonical field sets
1. Update or create `docs/data_schema.md` to include:
   - `persons`, `users`, `employees`, `creators`, `brand_contacts`
   - ID fields + relationship keys
2. Document the migration plan and the exact rename rules.

**Outcome:** the new schema is explicit and stable.

---

### Step 2: Implement migration and data compatibility helpers
1. Create a migration function (manual run or automatic on startup):
   - Renames keys (`clients`->`creators`, `brand_representatives`->`brand_contacts`)
   - Ensures person_id links exist
2. Add safety:
   - backup `data.json` to something like `data.backup.<timestamp>.json` (optional but recommended)

**Outcome:** existing environments can upgrade without losing data.

---

### Step 3: Implement Person linking for create flows
1. Add `PersonService` and shared “choose/create person” helper.
2. Update CRUD create handlers for:
   - users
   - employees
   - creators
   - brand contacts
3. Update templates to include the new person selector / creator UI.

**Outcome:** all new records are database-ready and normalized.

---

### Step 4: Introduce Access Control Matrix storage + enforcement layer
1. Create ACM structure in `data.json`
2. Add policy code:
   - `acm.can(role, entity, action, target=None, user=None, data=None)`
   - Must apply hard constraints + hierarchy rules
3. Replace scattered permission checks with ACM evaluation.

**Outcome:** one permission engine drives the entire app.

---

### Step 5: Settings page “Access Control” section
1. Add ACM section UI
2. Save edits (admin-only)
3. Show read-only for creators and non-admin roles
4. Ensure creators cannot edit anything (including profile) per requirement.

**Outcome:** ACM is visible and editable where allowed.

---

### Step 6: Rename Clients to Creators and Brand Representatives to Brand Contacts everywhere
1. Update routes, template names, nav labels
2. Update services/repositories
3. Ensure old routes don’t break the app (either remove or redirect)

**Outcome:** terminology matches the new data model.

---

### Step 7: UX/UI polish pass
1. Improve CSS while keeping palette/typography
2. Normalize:
   - headings
   - cards
   - forms
   - tables
   - flash messages
3. Improve empty states and page clarity.

**Outcome:** app feels more professional and cohesive.

---

### Step 8: Performance + reliability audit
1. Ensure no route loads `store.load()` multiple times unnecessarily
2. Ensure every add/edit/delete results in a single save
3. Add a few “smoke tests” (optional but strongly](#)
