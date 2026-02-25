import os
import pytest

from crm.persistence.json_store import JsonDataStore
from crm.services.employee_service import EmployeeService
from crm.services.client_service import ClientService
from crm.services.deal_service import DealService
from crm.services.contract_service import ContractService


def _make_store(tmp_path: str) -> JsonDataStore:
    filepath = os.path.join(tmp_path, "test_data.json")
    return JsonDataStore(filepath)


@pytest.fixture
def store(tmp_path):
    return _make_store(str(tmp_path))


class TestEmployeeService:
    def test_add_employee_creates_record(self, store):
        svc = EmployeeService(store)
        emp = svc.add_employee(
            person_id=1, position="Dev", title="Developer",
            manager_id=0, start_date="2023-01-01", end_date=None,
            is_active=True, is_manager=False,
        )
        assert emp["person_id"] == 1
        assert emp["position"] == "Dev"
        assert emp["title"] == "Developer"
        assert emp["is_active"] is True
        assert emp["is_manager"] is False
        assert "employee_id" in emp

    def test_add_employee_persisted(self, store):
        svc = EmployeeService(store)
        emp = svc.add_employee(1, "Dev", "Developer", 0, "2023-01-01", None, True, False)
        data = store.load()
        assert any(e["employee_id"] == emp["employee_id"] for e in data["employees"])

    def test_list_employees(self, store):
        svc = EmployeeService(store)
        svc.add_employee(1, "Dev", "Developer", 0, "2023-01-01", None, True, False)
        svc.add_employee(2, "Mgr", "Manager", 0, "2022-01-01", None, True, True)
        assert len(svc.list_employees()) == 2

    def test_update_employee(self, store):
        svc = EmployeeService(store)
        emp = svc.add_employee(1, "Dev", "Developer", 0, "2023-01-01", None, True, False)
        updated = svc.update_employee(emp["employee_id"], title="Senior Developer")
        assert updated["title"] == "Senior Developer"

    def test_delete_employee(self, store):
        svc = EmployeeService(store)
        emp = svc.add_employee(1, "Dev", "Developer", 0, "2023-01-01", None, True, False)
        result = svc.delete_employee(emp["employee_id"])
        assert result is True
        assert svc.get_employee(emp["employee_id"]) is None

    def test_get_direct_reports(self, store):
        svc = EmployeeService(store)
        mgr = svc.add_employee(1, "Mgr", "Manager", 0, "2020-01-01", None, True, True)
        rep1 = svc.add_employee(2, "Dev", "Developer", mgr["employee_id"], "2021-01-01", None, True, False)
        rep2 = svc.add_employee(3, "Dev", "Designer", mgr["employee_id"], "2021-06-01", None, True, False)
        reports = svc.get_direct_reports(mgr["employee_id"])
        assert len(reports) == 2


class TestClientService:
    def test_add_client_creates_record(self, store):
        svc = ClientService(store)
        client = svc.add_client(employee_id=10, description="Influencer A")
        assert client["employee_id"] == 10
        assert client["description"] == "Influencer A"
        assert "client_id" in client

    def test_add_client_persisted(self, store):
        svc = ClientService(store)
        client = svc.add_client(10, "Influencer A")
        data = store.load()
        assert any(c["client_id"] == client["client_id"] for c in data["clients"])

    def test_get_clients_for_employee(self, store):
        svc = ClientService(store)
        svc.add_client(10, "Client A")
        svc.add_client(10, "Client B")
        svc.add_client(20, "Client C")
        results = svc.get_clients_for_employee(10)
        assert len(results) == 2
        assert all(c["employee_id"] == 10 for c in results)

    def test_delete_client(self, store):
        svc = ClientService(store)
        client = svc.add_client(10, "Delete Me")
        assert svc.delete_client(client["client_id"]) is True
        assert svc.get_client(client["client_id"]) is None


class TestDealService:
    def test_create_deal_creates_record(self, store):
        svc = DealService(store)
        deal = svc.create_deal(
            client_id=1, brand_id=2, brand_rep_id=3,
            pitch_date="2024-06-15", is_active=True, is_successful=False,
        )
        assert deal["client_id"] == 1
        assert deal["brand_id"] == 2
        assert deal["brand_rep_id"] == 3
        assert deal["pitch_date"] == "2024-06-15"
        assert deal["is_active"] is True
        assert deal["is_successful"] is False
        assert "deal_id" in deal

    def test_create_deal_persisted(self, store):
        svc = DealService(store)
        deal = svc.create_deal(1, 2, 3, "2024-06-15", True, False)
        data = store.load()
        assert any(d["deal_id"] == deal["deal_id"] for d in data["deals"])


class TestContractService:
    def test_create_contract_creates_record(self, store):
        svc = ContractService(store)
        contract = svc.create_contract(
            deal_id=5, details="Sponsorship deal", payment=10000.0,
            agency_percentage=15.0, start_date="2024-07-01", end_date="2024-12-31",
            status="Pending", is_approved=False,
        )
        assert contract["deal_id"] == 5
        assert contract["details"] == "Sponsorship deal"
        assert contract["payment"] == 10000.0
        assert contract["agency_percentage"] == 15.0
        assert contract["status"] == "Pending"
        assert contract["is_approved"] is False
        assert "contract_id" in contract

    def test_create_contract_persisted(self, store):
        svc = ContractService(store)
        contract = svc.create_contract(5, "Details", 5000.0, 10.0, "2024-01-01", "2024-06-30", "Sent", True)
        data = store.load()
        assert any(c["contract_id"] == contract["contract_id"] for c in data["contracts"])
