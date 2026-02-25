from crm.persistence.json_store import JsonDataStore
from crm.persistence.repositories import ContractRepository


class ContractService:
    def __init__(self, store: JsonDataStore):
        self._store = store
        self._contracts = ContractRepository(store)

    def list_contracts(self) -> list:
        return self._contracts.all()

    def create_contract(
        self,
        deal_id: int,
        details: str,
        payment: float,
        agency_percentage: float,
        start_date: str,
        end_date: str,
        status: str,
        is_approved: bool,
    ) -> dict:
        return self._contracts.add({
            "deal_id": deal_id,
            "details": details,
            "payment": payment,
            "agency_percentage": agency_percentage,
            "start_date": start_date,
            "end_date": end_date,
            "status": status,
            "is_approved": is_approved,
        })
