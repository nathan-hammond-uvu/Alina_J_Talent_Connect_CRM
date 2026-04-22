### Deployment Prep (Render + WSGI + Env Vars)

**Goal:** Prepare this repo for deployment on **Render** with a **WSGI** entrypoint (e.g., **Gunicorn**), environment-based configuration, and documented dependencies.

#### Requirements
1. **Create `requirements.txt`**
   - Add all Python dependencies required to run the app in production.
   - Ensure versions are pinned (recommended) or otherwise stable.
   - Include **Gunicorn** as a dependency.
   - If the project uses a framework (Flask/Django/FastAPI+WSGI wrapper/etc.), ensure it’s included.

2. **Move all configuration to environment variables**
   - Identify every configuration value currently hard-coded or stored in local config files (examples: secret keys, database URLs, API keys, debug flags, host/port, allowed hosts, etc.).
   - Refactor the app so these values are read from `os.environ`.
   - Provide sensible defaults *only* for non-sensitive values (if appropriate), but **do not** default secrets.
   - Fail fast with a clear error message if required environment variables are missing.

3. **Add `.env.example`**
   - Create a `.env.example` file at the repo root.
   - Include **all** environment variables the application expects, with placeholder values.
   - Do **not** include real secrets.
   - Add brief inline comments where helpful (e.g., what format a value should be in).

4. **Ensure the project runs under a WSGI server (Gunicorn)**
   - Provide a WSGI entrypoint that Gunicorn can import, commonly:
     - `wsgi.py` exporting `app`, or
     - `<package>.wsgi:application` (Django style), or
     - `app:app` for Flask if the module is named `app.py`
   - Validate that the app starts successfully with a command like:
     - `gunicorn wsgi:app` (or the correct import path for this project)
   - Do not rely on `flask run` / development servers for deployment.

5. **Render deployment readiness**
   - Add Render-friendly startup guidance:
     - Provide the correct **Start Command** for Render using Gunicorn.
     - Ensure the app binds to the port provided by Render (typically via `PORT` env var).
   - If needed, add a `render.yaml` blueprint **or** document manual setup steps (whichever best matches the repo’s conventions).
   - Confirm the app can run in a clean environment using only:
     - `pip install -r requirements.txt`
     - environment variables set in Render
     - `gunicorn ...` start command

#### Deliverables
- `requirements.txt`
- `.env.example`
- A working WSGI entrypoint (new file like `wsgi.py` if needed)
- Any necessary refactors so **all config comes from environment variables**
- Render deployment instructions (and `render.yaml` if appropriate)

#### Acceptance Criteria
- Fresh install succeeds with `pip install -r requirements.txt`.
- App starts with Gunicorn in production mode (no dev server).
- No secrets are hard-coded in the repository.
- `.env.example` fully documents required environment variables.
- App uses the Render-provided `PORT` (or equivalent) and runs successfully on Render.