from crm.persistence.json_store import JsonDataStore
from crm.persistence.repositories import DealRepository


class DealService:
    def __init__(self, store: JsonDataStore):
        self._store = store
        self._deals = DealRepository(store)

    def list_deals(self) -> list:
        return self._deals.all()

    def create_deal(
        self,
        client_id: int,
        brand_id: int,
        brand_rep_id: int,
        pitch_date: str,
        is_active: bool,
        is_successful: bool,
    ) -> dict:
        return self._deals.add({
            "client_id": client_id,
            "brand_id": brand_id,
            "brand_rep_id": brand_rep_id,
            "pitch_date": pitch_date,
            "is_active": is_active,
            "is_successful": is_successful,
        })
