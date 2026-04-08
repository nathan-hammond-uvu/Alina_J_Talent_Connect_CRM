# Chunk 8 — Home Page UI Upgrade (Actionable Dashboard)

This chunk focuses on making the CRM home page feel like a real product “command center” instead of a static landing page. The goal is to give users **immediate value in the first 5 seconds** by showing what matters *today* (work in progress, deadlines, quick actions, and recent activity), while keeping the implementation aligned with the current Flask + server-rendered HTML approach in this repo.

> Context from the repo
> - Primary stack is **Python (Flask)** with server-rendered **HTML templates** and light CSS/JS.
> - Data is currently JSON-backed (`data.json`) via `JsonDataStore`, with a longer-term direction toward a DB-backed store (see `Development_Steps/Chunk_7.md`).
> - This chunk is designed to work *now* with the JSON store, while being future-friendly for Postgres.

---

## Goals

1. **Replace “bland” home page with a dashboard**
   - High-signal summary cards (counts + key KPIs)
   - “What needs attention” list (deadlines / missing fields / stalled deals)
   - Quick actions (create talent, create brand, add deal/contract, etc.)
   - Recent activity feed (recently edited/created entities)

2. **Improve perceived polish**
   - Consistent spacing + typography
   - Responsive layout (works on laptop + tablet)
   - Accessible color contrast, headings, landmarks

3. **Keep implementation incremental**
   - Add a dashboard route + template
   - Add a small “dashboard service” that computes stats from repositories
   - Avoid large refactors

---

## UX: What the Home Page Should Show

### A) Top summary (4–6 cards)
**Cards should be clickable**, taking the user to the underlying list page. Examples:

- **Talent**: total talent count
- **Brands**: total brands count
- **Deals in progress**: deals where status != closed
- **Contracts pending**: missing signature/date, or expiring soon
- **Campaigns active** (if campaigns exist)
- **Tasks due this week** (if tasks exist; otherwise show “Coming soon”)

Each card can show:
- primary number (count)
- a small secondary label (“+3 this week” if you can compute it; optional)

### B) “Needs attention” (high value)
A short list (5–10 items) that surfaces issues users would otherwise miss:

- Deals without a linked contract
- Contracts expiring within N days
- Talent missing contact info
- Brand reps missing email/phone
- Records missing required fields

This provides *real utility* even with minimal data modeling.

### C) Quick actions
A panel of buttons/links:

- Add Talent
- Add Brand
- Add Deal
- Add Contract
- Import data (admin-only if present)

### D) Recent activity
If the repo has any concept of timestamps or “last updated” fields, show a feed. If not, implement a minimal feed via one of:

- lightweight audit log table/collection (recommended)
- or “recently viewed” stored in session (cheap but less useful)

Start minimal: show “recently created” if those fields exist; otherwise skip and add in a later chunk.

---

## Implementation Plan (Flask + Templates)

### 1) Add a dashboard route
Create a dedicated dashboard route and make it the default landing page after login.

**Suggested files**
- `crm/ui/web/routes/dashboard_routes.py` (new blueprint)
- Register blueprint in `crm/ui/web/app.py`

**Routes**
- `GET /` or `GET /dashboard`
  - requires login
  - loads dashboard view-model
  - renders template

If `/` is currently used for a public landing page, use `/dashboard` after login and keep `/` public.

### 2) Add a dashboard “service” (view model builder)
Keep templates simple by preparing a structured dict in Python.

**Suggested file**
- `crm/services/dashboard_service.py`

**Responsibilities**
- Gather counts from repositories (talent, brands, deals, contracts)
- Compute “needs attention” items (simple rules)
- Provide “quick actions” links

**Interface**
```python
class DashboardService:
    def __init__(self, repos):
        self.repos = repos

    def build(self, user):
        return {
            "cards": [...],
            "needs_attention": [...],
            "quick_actions": [...],
            "recent_activity": [...],
        }
```

### 3) Create the dashboard template
**Suggested template**
- `crm/ui/web/templates/dashboard.html`

Template sections:
- `h1` + short intro
- Cards grid
- Needs attention list
- Quick actions
- Recent activity (optional)

### 4) Add styling improvements (minimal, consistent)
If the repo uses a global stylesheet, add dashboard classes there. Otherwise create a dedicated stylesheet and include it.

**Suggested**
- `crm/ui/web/static/css/dashboard.css`

Add:
- responsive grid (CSS grid/flex)
- card component styles
- subtle hover states
- empty states (“No items need attention”)

### 5) Accessibility + semantics
Checklist:
- Use landmarks (`main`, `nav`)
- Cards as links (`<a>` wrapping) or `button` where appropriate
- Visible focus states
- Color contrast
- Headings in order (`h1` → `h2`)

---

## “Needs Attention” Rules (Start Simple)

These rules should be fast to implement using existing data. Pick the ones that match the models you already have.

### Deals
- Deal exists but has no associated contract
- Deal missing brand
- Deal missing talent

### Contracts
- Contract missing start/end date
- Contract end date within 30 days

### Talent / Contacts
- Talent missing email OR phone
- Brand rep missing email

Represent each “attention item” as:
```json
{
  "type": "contract_expiring",
  "label": "Contract expiring soon",
  "detail": "Brand X – ends in 12 days",
  "url": "/contracts/123"
}
```

---

## Metrics/KPIs (Optional Enhancements)
If you have the data, add:
- Pipeline value (sum of open deals)
- Average contract length
- Win rate
- # new talent onboarded this month

If you don’t have the data yet, keep placeholders but hide them behind a feature flag or show “Not available”.

---

## Testing Plan

### Unit tests (Python)
Add tests around `DashboardService.build()`:
- returns expected counts with seeded repo data
- returns empty states when no data
- returns correct attention items for expiring contracts

### Route tests
- unauthenticated user is redirected to login
- authenticated user gets 200 and sees key sections

---

## Deliverables Checklist

- [ ] New route blueprint: `crm/ui/web/routes/dashboard_routes.py`
- [ ] New service: `crm/services/dashboard_service.py`
- [ ] New template: `crm/ui/web/templates/dashboard.html`
- [ ] Minimal dashboard CSS: `crm/ui/web/static/css/dashboard.css`
- [ ] Tests for dashboard service and route

---

## Notes

- This chunk intentionally avoids introducing a front-end framework. With Flask + templates you can still deliver a polished dashboard.
- When Postgres arrives (Chunk 7), the dashboard service should keep working as long as repository interfaces remain stable.