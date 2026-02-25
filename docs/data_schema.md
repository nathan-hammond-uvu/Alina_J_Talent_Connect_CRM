# Data Schema — Alina J Talent Connect CRM

## Overview

All data is stored in `data.json` as a JSON object with top-level keys for each entity collection.

---

## Entities

### Role
Defines the access level of a user.

| Field | Type | Description |
|-------|------|-------------|
| `role_id` | int | Primary key |
| `role_name` | str | One of: `User`, `Employee`, `Manager`, `Admin`, `Client`, `Rep` |

---

### Person
Represents any real-world individual (employee, client contact, admin, etc.).

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
| `person_id` | int | FK → `Person.person_id` |
| `position` | str | Job position / department |
| `title` | str | Job title |
| `manager_id` | int | FK → `Employee.employee_id` (0 = no manager) |
| `start_date` | str | Employment start date (YYYY-MM-DD) |
| `end_date` | str \| null | Employment end date (YYYY-MM-DD), null if active |
| `is_active` | bool | Whether currently employed |
| `is_manager` | bool | Whether this employee manages others |

---

### Client
Represents a talent / influencer managed by an employee.

| Field | Type | Description |
|-------|------|-------------|
| `client_id` | int | Primary key |
| `employee_id` | int | FK → `Employee.employee_id` (assigned agent) |
| `description` | str | Short description / stage name of the client |

---

### SocialMediaAccount
A social-media profile linked to a `Client`.

| Field | Type | Description |
|-------|------|-------------|
| `social_media_id` | int | Primary key |
| `client_id` | int | FK → `Client.client_id` |
| `account_type` | str | Platform name (e.g., `Instagram`, `TikTok`) |
| `link` | str | Profile URL |

---

### Brand
A company or brand that may sponsor clients.

| Field | Type | Description |
|-------|------|-------------|
| `brand_id` | int | Primary key |
| `description` | str | Brand name / description |

---

### BrandRepresentative
A person who represents a `Brand` in deal negotiations.

| Field | Type | Description |
|-------|------|-------------|
| `brand_rep_id` | int | Primary key |
| `person_id` | int | FK → `Person.person_id` |
| `brand_id` | int | FK → `Brand.brand_id` |
| `notes` | str | Additional notes about this representative |
| `is_active` | bool | Whether this rep is currently active |

---

### Deal
A pitch / sponsorship deal between a `Client` and a `Brand`.

| Field | Type | Description |
|-------|------|-------------|
| `deal_id` | int | Primary key |
| `client_id` | int | FK → `Client.client_id` |
| `brand_id` | int | FK → `Brand.brand_id` |
| `brand_rep_id` | int | FK → `BrandRepresentative.brand_rep_id` |
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
Person ──< BrandRepresentative

Role ──< User

Employee ──< Client
Employee ──< Employee (self-referencing via manager_id)

Client ──< SocialMediaAccount
Client ──< Deal

Brand ──< BrandRepresentative
Brand ──< Deal

BrandRepresentative ──< Deal

Deal ──< Contract
```

---

## Internal Fields

| Field | Type | Description |
|-------|------|-------------|
| `_next_id` | int | Auto-increment counter stored in `data.json`. Managed by `JsonDataStore.next_id()`. Not an entity field. |
