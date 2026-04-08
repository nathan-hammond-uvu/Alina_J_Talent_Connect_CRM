"""Dashboard service – builds the view-model for the CRM command-centre dashboard."""
from __future__ import annotations

from datetime import date, datetime, timedelta


def _parse_date(value: str | None) -> date | None:
    """Parse an ISO-8601 date string (YYYY-MM-DD) or return None."""
    if not value:
        return None
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(value[:10], fmt).date()
        except (ValueError, TypeError):
            continue
    return None


class DashboardService:
    """Builds a structured view-model dict used by the dashboard template.

    Works with any store that exposes a ``load()`` method returning the
    standard data dict (json / sqlite / postgres backends all qualify).
    """

    EXPIRY_WINDOW_DAYS = 30

    def __init__(self, store):
        self._store = store

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(self, user: dict) -> dict:
        """Return the complete dashboard view-model for *user*."""
        data = self._store.load()
        today = date.today()

        return {
            "cards": self._build_cards(data, today),
            "needs_attention": self._build_needs_attention(data, today),
            "quick_actions": self._build_quick_actions(),
            "recent_activity": self._build_recent_activity(data),
        }

    # ------------------------------------------------------------------
    # Cards (summary KPIs)
    # ------------------------------------------------------------------

    def _build_cards(self, data: dict, today: date) -> list[dict]:
        creators = data.get("creators", [])
        brands = data.get("brands", [])
        deals = data.get("deals", [])
        contracts = data.get("contracts", [])

        active_deals = [d for d in deals if d.get("is_active")]
        expiring = [
            c for c in contracts
            if self._days_until(c.get("end_date"), today) is not None
            and 0 <= self._days_until(c.get("end_date"), today) <= self.EXPIRY_WINDOW_DAYS
        ]

        return [
            {
                "id": "talent",
                "label": "Talent / Creators",
                "value": len(creators),
                "icon": "\U0001f31f",
                "url": "/portal/creators",
                "color_class": "card-stat--blue",
            },
            {
                "id": "brands",
                "label": "Brands",
                "value": len(brands),
                "icon": "\U0001f381",
                "url": "/portal/brands",
                "color_class": "card-stat--purple",
            },
            {
                "id": "active_deals",
                "label": "Active Deals",
                "value": len(active_deals),
                "icon": "\U0001f91d",
                "url": "/portal/deals",
                "color_class": "card-stat--green",
            },
            {
                "id": "contracts",
                "label": "Contracts",
                "value": len(contracts),
                "icon": "\U0001f4c4",
                "url": "/portal/contracts",
                "color_class": "card-stat--orange",
                "secondary": (
                    f"{len(expiring)} expiring soon"
                    if expiring
                    else None
                ),
            },
        ]

    # ------------------------------------------------------------------
    # Needs-attention items
    # ------------------------------------------------------------------

    def _build_needs_attention(self, data: dict, today: date) -> list[dict]:
        items: list[dict] = []

        persons = {p["person_id"]: p for p in data.get("persons", [])}
        brands_map = {b["brand_id"]: b for b in data.get("brands", [])}
        creators_map = {c["creator_id"]: c for c in data.get("creators", [])}
        deals = data.get("deals", [])
        contracts = data.get("contracts", [])

        # Contracts with a missing start or end date
        for c in contracts:
            if not c.get("start_date") or not c.get("end_date"):
                items.append({
                    "type": "contract_missing_dates",
                    "label": "Contract missing dates",
                    "detail": f"Contract #{c['contract_id']} — start or end date not set",
                    "url": "/portal/contracts",
                })

        # Contracts expiring within EXPIRY_WINDOW_DAYS
        for c in contracts:
            days = self._days_until(c.get("end_date"), today)
            if days is not None and 0 <= days <= self.EXPIRY_WINDOW_DAYS:
                deal = next((d for d in deals if d.get("deal_id") == c.get("deal_id")), None)
                brand_name = ""
                if deal:
                    brand = brands_map.get(deal.get("brand_id"))
                    if brand:
                        brand_desc = brand.get("description") or f"Brand #{deal['brand_id']}"
                        brand_name = f" ({brand_desc})"
                items.append({
                    "type": "contract_expiring",
                    "label": "Contract expiring soon",
                    "detail": f"Contract #{c['contract_id']}{brand_name} — ends in {days} day{'s' if days != 1 else ''}",
                    "url": "/portal/contracts",
                })

        # Deals without any linked contract
        contract_deal_ids = {c.get("deal_id") for c in contracts}
        for d in deals:
            if d.get("deal_id") not in contract_deal_ids:
                creator = creators_map.get(d.get("client_id"))
                brand = brands_map.get(d.get("brand_id"))
                creator_label = ""
                if creator:
                    person = persons.get(creator.get("person_id"), {})
                    creator_label = person.get("display_name") or person.get("full_name") or f"Creator #{creator['creator_id']}"
                brand_label = brand.get("description") or f"Brand #{d['brand_id']}" if brand else ""
                detail = f"Deal #{d['deal_id']}"
                if creator_label or brand_label:
                    detail += f" — {creator_label}" + (" × " + brand_label if brand_label else "")
                items.append({
                    "type": "deal_no_contract",
                    "label": "Deal has no contract",
                    "detail": detail,
                    "url": "/portal/deals",
                })

        # Creators (talent) missing email or phone
        for creator in data.get("creators", []):
            person = persons.get(creator.get("person_id"), {})
            if not person.get("email") and not person.get("phone"):
                label = person.get("display_name") or person.get("full_name") or f"Creator #{creator['creator_id']}"
                items.append({
                    "type": "creator_missing_contact",
                    "label": "Talent missing contact info",
                    "detail": f"{label} — no email or phone on record",
                    "url": "/portal/creators",
                })

        # Brand contacts missing email
        bc_persons = {p["person_id"]: p for p in data.get("persons", [])}
        for contact in data.get("brand_contacts", []):
            person = bc_persons.get(contact.get("person_id"), {})
            if not person.get("email"):
                label = person.get("display_name") or person.get("full_name") or f"Brand Contact #{contact['brand_contact_id']}"
                items.append({
                    "type": "brand_contact_missing_email",
                    "label": "Brand contact missing email",
                    "detail": f"{label} — no email on record",
                    "url": "/portal/brand_contacts",
                })

        # Cap to keep the list scannable
        return items[:10]

    # ------------------------------------------------------------------
    # Quick actions
    # ------------------------------------------------------------------

    def _build_quick_actions(self) -> list[dict]:
        return [
            {"label": "Add Talent",        "url": "/portal/creators",       "icon": "\U0001f31f"},
            {"label": "Add Brand",         "url": "/portal/brands",         "icon": "\U0001f381"},
            {"label": "Add Brand Contact", "url": "/portal/brand_contacts", "icon": "\U0001f4de"},
            {"label": "Add Deal",          "url": "/portal/deals",          "icon": "\U0001f91d"},
            {"label": "Add Contract",      "url": "/portal/contracts",      "icon": "\U0001f4c4"},
        ]

    # ------------------------------------------------------------------
    # Recent activity (created-order; most-recent first)
    # ------------------------------------------------------------------

    def _build_recent_activity(self, data: dict) -> list[dict]:
        persons = {p["person_id"]: p for p in data.get("persons", [])}
        items: list[dict] = []

        for creator in data.get("creators", []):
            person = persons.get(creator.get("person_id"), {})
            label = person.get("display_name") or person.get("full_name") or f"Creator #{creator['creator_id']}"
            items.append({
                "type": "Creator",
                "label": label,
                "url": "/portal/creators",
                "sort_key": creator.get("creator_id", 0),
            })

        for brand in data.get("brands", []):
            items.append({
                "type": "Brand",
                "label": brand.get("description") or brand.get("name") or f"Brand #{brand['brand_id']}",
                "url": "/portal/brands",
                "sort_key": brand.get("brand_id", 0),
            })

        for deal in data.get("deals", []):
            items.append({
                "type": "Deal",
                "label": f"Deal #{deal['deal_id']}",
                "url": "/portal/deals",
                "sort_key": deal.get("deal_id", 0),
            })

        for contract in data.get("contracts", []):
            items.append({
                "type": "Contract",
                "label": f"Contract #{contract['contract_id']}",
                "url": "/portal/contracts",
                "sort_key": contract.get("contract_id", 0),
            })

        # Sort by descending id (proxy for "most recently created")
        items.sort(key=lambda x: x.get("sort_key", 0), reverse=True)
        # Remove internal sort key before returning
        for item in items:
            item.pop("sort_key", None)
        return items[:8]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _days_until(date_str: str | None, today: date) -> int | None:
        """Return the number of days until *date_str*, or None if unparseable."""
        d = _parse_date(date_str)
        if d is None:
            return None
        return (d - today).days
