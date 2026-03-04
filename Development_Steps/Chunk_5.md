# Chunk 5: Flask Web App Conversion (Auth + Role-Based Portal + CRUD Pages)

## Why this chunk exists
Chunk 4 reorganized the CRM into a layered, testable architecture so the CLI could be replaced without rewriting business logic.

This chunk **replaces the CLI UI** with a **fully functional Flask website** that:
- provides a public homepage with **login/register**
- uses **sessions** for logged-in state
- redirects authenticated users into a **role-based portal**
- provides a **left navigation menu** and separate pages for CRM entities
- enforces **RBAC visibility + edit permissions** consistently via the policies/services created in Chunk 4

**Important constraint:** Chunk 5 is about wiring services into Flask routes + templates. The **core logic remains in services/persistence/policies** (no business rules inside the routes).

---

## Objectives
1. Convert the existing CLI application into a Flask web app (server-rendered HTML).
2. Add authentication pages:
   - **Homepage** (welcome + login/register links)
   - **Register**
   - **Login**
   - **Logout**
3. Create an authenticated **Portal** area with:
   - a left-side navigation menu
   - role-aware page access
   - role-aware data visibility (scope filtering)
4. Implement pages matching the portal menu:
   1) Portal Home (Under construction)
   2) Search (global search of data.json, filtered by RBAC)
   3) Employees (CRUD)
   4) Clients (CRUD)
   5) Brands (CRUD)
   6) Deals (CRUD)
   7) Contracts (CRUD)
   8) Performance (Coming soon)
   9) Tasks (Coming soon)
   10) Discover (Coming soon)
   11) Settings (View/update current user + person + login data)
5. Use the provided `web_app.py` pattern as the baseline template style for entity pages (form + table, edit/delete).
6. Ensure every page is protected appropriately and uses services + access control rules.

---

## Target UX / Navigation
### Public pages (not logged in)
- `/` (Homepage)
  - greeting text
  - CTA buttons/links: **Login** and **Register**

- `/login`
- `/register`

After successful login/registration:
- redirect to `/portal`

### Portal (logged in)
- `/portal` layout includes:
  - left side menu with the following items, grouped like:

    1. Portal Home  
    2. Search  
    ------------  
    3. Employees  
    4. Clients  
    5. Brands  
    6. Deals  
    7. Contracts  
    -------------  
    8. Performance  
    9. Tasks  
    10. Discover  
    11. Settings  
    ------------  
    Profile pic | display name | role

- Profile section at bottom of sidebar shows:
  - profile pic (placeholder if not available)
  - display_name (or full_name fallback)
  - current role

### Page behavior requirements
- **Portal Home:** display “under construction”
- **Performance / Tasks / Discover:** display “coming soon!”
- Entity pages (Employees/Clients/Brands/Deals/Contracts):
  - show add form + table of records user can see
  - allow inline edit + save + delete where permitted by RBAC
- **Search page:** global search across permitted datasets in `data.json`
  - results show as a table of link-like rows to relevant detail views (or to the entity list page with highlight/anchor)
  - must not show items the user cannot view

---

## Architecture & Folder Structure (Web Adapter)
Build the Flask UI as a new adapter layer that depends on Chunk 4 services/policies.

Recommended structure:
- `crm/ui/web/`
  - `app.py` (Flask app factory or main Flask entry)
  - `routes/`
    - `auth_routes.py` (home, login, register, logout)
    - `portal_routes.py` (portal home, search, coming soon pages)
    - `entity_routes.py` (employees, clients, brands, deals, contracts CRUD)
    - `settings_routes.py` (settings/profile updates)
  - `templates/`
    - `base_public.html`
    - `base_portal.html` (sidebar + main content area)
    - `auth/` (home/login/register)
    - `portal/` (home/search/coming_soon)
    - `entities/` (employees/clients/brands/deals/contracts)
    - `settings/` (settings page)
  - `static/`
    - `styles.css` (extract CSS from the inline HTML in `web_app.py`)
    - optional `app.js` (extract table edit/delete JS)

**Do not** put business rules in Flask routes. Routes call:
- `crm/services/*`
- `crm/policies/access_control.py`
- `crm/persistence/*`

---

## Step-by-step task list

### Step 1: Add Flask dependencies + run entrypoint
1. Add/update dependencies (requirements file) to include Flask and any auth helpers already used in Chunk 4.
2. Create a Flask entrypoint:
   - `flask --app crm.ui.web.app run` should work, or
   - `python -m crm.ui.web.app`
3. Confirm `data.json` is still the single source of persistence through the JsonDataStore.

**Outcome:** You can start the server and hit `/`.

---

### Step 2: Implement session-based authentication (Login/Register/Logout)
1. Build `GET /login` and `POST /login`
   - call `AuthService.authenticate(username, password)`
   - on success:
     - store `user_id` (and/or username) in session
     - redirect to `/portal`
   - on failure:
     - render login with an error message

2. Build `GET /register` and `POST /register`
   - collect person fields + username + password
   - call `AuthService.register_user(...)`
   - on success:
     - either auto-login + redirect to `/portal`
     - or redirect to `/login` with “registration successful”

3. Add `/logout`
   - clear session
   - redirect to `/`

4. Add a `login_required` guard (decorator or before_request)
   - any `/portal*` route requires session auth

**Outcome:** Users can register, login, logout, and are redirected appropriately.

---

### Step 3: Create the Portal layout + Sidebar navigation
1. Create `base_portal.html` with:
   - left sidebar nav (menu structure above)
   - main content area block
   - bottom “profile strip” showing:
     - profile image placeholder
     - display_name + role

2. Add `/portal` route
   - loads current user context via service layer
   - renders portal home “under construction”

3. Ensure the sidebar highlights the active page.

**Outcome:** Logged-in users land in a consistent portal layout.

---

### Step 4: Role-based access to pages (RBAC in the web)
1. Define per-page access requirements:
   - Employees page: likely Admin/Manager (and maybe Employee read-only if required)
   - Clients/Brands/Deals/Contracts: scoped visibility per current rules
   - Settings: any logged-in user can access
2. Implement enforcement:
   - use `access_control.can_view(...)`, `can_edit(...)`, and/or `scope_query(user, entity_type)`
   - return 403 page (or redirect) if user cannot access a route at all
3. Ensure all list queries are filtered by scope:
   - never show records outside the user’s visibility scope

**Outcome:** Portal pages show only what the role allows.

---

### Step 5: Implement Search page (global search over RBAC-filtered data)
1. Create `GET /portal/search` with:
   - search input box (query param like `?q=...`)
   - results area below
2. Search behavior:
   - load datasets via services/repositories
   - apply `scope_query` per entity type
   - perform case-insensitive matching across string fields (and IDs as strings)
   - include record type in results: (Employee / Client / Brand / Deal / Contract / Person / User, depending on what is allowed)
3. Search result display:
   - table format
   - each row includes:
     - entity type
     - a label (display_name/full_name/name/title)
     - “link” to a target page:
       - simplest: link to that entity list page with an anchor or query param to highlight the record
       - optional later improvement: dedicated detail pages

**Outcome:** Users can search “anything” they are allowed to see in `data.json`, with clickable results.

---

### Step 6: Build CRUD pages for Employees, Clients, Brands, Deals, Contracts (Template from web_app.py)
For each entity page:
- `GET /portal/<entity>`: show form + table
- `POST /portal/<entity>/add`: create record
- `PUT /portal/<entity>/<id>`: update record
- `DELETE /portal/<entity>/<id>`: delete record

Implementation guidelines:
1. Reuse the `web_app.py` approach:
   - one “add” form at top
   - below, a table showing existing records
   - single-row selection with edit mode
   - save/delete buttons that appear only when a row is selected
2. Move inline HTML/CSS/JS out of python strings:
   - CSS into `static/styles.css`
   - JS into `static/app.js` (or page-level script blocks)
   - templates into `templates/entities/<entity>.html`
3. RBAC rules:
   - list: only records from `scope_query(user, entity_type)`
   - edit/delete controls only shown if `can_edit(record, user)` is true
   - server must still validate permissions on PUT/DELETE even if UI hides buttons
4. Field schema:
   - Each entity page should define its field list similarly to `FIELDS` in `web_app.py`
   - Do not allow editing of primary key IDs
   - Consider calculated fields (like full_name) as either derived or editable—choose one consistent rule
5. Persistence:
   - CRUD must call service layer methods, not write JSON directly in routes
   - services update JsonDataStore via repositories

**Outcome:** Pages 3–7 are functional CRUD screens with consistent UI/behavior.

---

### Step 7: Coming Soon pages (Performance, Tasks, Discover)
1. Add routes and templates:
   - `/portal/performance`
   - `/portal/tasks`
   - `/portal/discover`
2. Each renders:
   - “coming soon!” message in portal layout.

**Outcome:** Menu items work without 404s.

---

### Step 8: Settings page (Read/update user + person + login data)
1. Add `/portal/settings`:
   - shows current session user’s:
     - user account fields (username, role display, etc.)
     - person profile fields (first_name, last_name, display_name, email, phone, address, etc.)
     - login-related fields (password update workflow)
2. Allow updates:
   - Update person fields (profile)
   - Update username if allowed (optional, but if supported must validate uniqueness)
   - Update password:
     - require current password
     - validate new password rules
     - store hashed password (from Chunk 4 hashing)
3. RBAC:
   - user can update themselves
   - admins may optionally be allowed to update others later (not required in this chunk unless already part of CLI behavior)

**Outcome:** Users can manage their own profile and login credentials.

---

### Step 9: Error handling, flash messaging, and polish
1. Replace raw alerts with friendly UI messages:
   - success banners for saves/deletes
   - error banners for validation failures
2. Add pages for:
   - 403 Forbidden
   - 404 Not Found
   - 500 Server Error
3. Add basic form validation:
   - required fields
   - email format
   - safe handling for empty/invalid JSON bodies in PUT/DELETE

**Outcome:** The site behaves cleanly and predictably for common failures.

---

### Step 10: Minimal web-focused test coverage (optional but recommended)
Even if not exhaustive, add tests for:
- auth flow logic via service layer (already in chunk 4), plus
- web route smoke tests:
  - unauthenticated redirect to login
  - authenticated access to portal
  - 403 for disallowed routes
  - CRUD endpoints respect RBAC

**Outcome:** A small test safety net exists for future chunks.

---

## Definition of Done (Chunk 5)
- Flask app runs locally and replaces CLI as primary UI.
- Public homepage offers login/register.
- Users can register and login; sessions persist; logout works.
- Portal exists with sidebar menu and profile strip.
- Portal Home shows “under construction”.
- Search works globally across RBAC-scoped data and provides link-like results.
- Employees, Clients, Brands, Deals, Contracts pages are functional CRUD pages using the `web_app.py` UX as a baseline.
- Performance, Tasks, Discover show “coming soon!”.
- Settings page allows a logged-in user to view/update their person/user/login data (including password change with hashing).
- RBAC is enforced server-side on all portal routes and CRUD actions.

---

## Notes / Implementation strategy reminders
- **Routes are adapters**: They should translate HTTP requests -> service calls -> templates.
- **All role logic must live in policies/services** so the CLI and web remain consistent.
- Keep `data.json` schema stable (as documented in Chunk 4).
- Don’t add new complex features (like file uploads or full profile pictures) yet—use placeholders until later chunks.
