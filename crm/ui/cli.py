import sys

from crm.persistence.json_store import JsonDataStore
from crm.services.auth_service import AuthService
from crm.services.employee_service import EmployeeService
from crm.services.client_service import ClientService
from crm.services.deal_service import DealService
from crm.services.contract_service import ContractService
from crm.policies.access_control import AccessPolicy
from crm.ui.formatting import display_table, select_item, find_and_select_item

# ---------------------------------------------------------------------------
# Module-level singletons initialised inside main()
# ---------------------------------------------------------------------------
_store: JsonDataStore | None = None
_auth: AuthService | None = None
_emp_svc: EmployeeService | None = None
_client_svc: ClientService | None = None
_deal_svc: DealService | None = None
_contract_svc: ContractService | None = None
_policy: AccessPolicy | None = None


def _get_data() -> dict:
    return _store.load()


def _save_data(data: dict) -> None:
    _store.save(data)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_person_name(person_id: int) -> str:
    data = _get_data()
    person = next((p for p in data.get("persons", []) if p["person_id"] == person_id), None)
    return person["full_name"] if person else "Unknown"


# ---------------------------------------------------------------------------
# Auth pages
# ---------------------------------------------------------------------------

def login() -> None:
    while True:
        username = input("Enter your username: ")
        data = _get_data()
        matching_user = next((u for u in data.get("users", []) if u["username"] == username), None)

        if not matching_user:
            print("Invalid username.")
            choice = input("Options: (1) Try again, (2) Register: ")
            if choice == "2":
                register()
                return
            else:
                continue

        password = input("Enter your password: ")
        authenticated = _auth.authenticate(username, password)
        if authenticated:
            print(f"Login successful! Welcome, {authenticated['username']}.")
            main_navigation_page(authenticated)
            return
        else:
            print("Incorrect password. Please try again.")


def register() -> None:
    print("Registering a new user")

    first_name = input("First Name: ")
    last_name = input("Last Name: ")
    full_name = f"{first_name} {last_name}"
    display_name = input("Display Name: ")
    email = input("Email: ")
    phone = input("Phone: ")
    address = input("Address: ")
    city = input("City: ")
    state = input("State: ")
    zip_code = input("ZIP Code: ")

    person_fields = dict(
        first_name=first_name,
        last_name=last_name,
        full_name=full_name,
        display_name=display_name,
        email=email,
        phone=phone,
        address=address,
        city=city,
        state=state,
        zip=zip_code,
    )

    username = input("Choose a username: ")
    password = input("Choose a password: ")

    try:
        user = _auth.register_user(person_fields, username, password)
    except ValueError as exc:
        print(f"Registration error: {exc}")
        return

    print("Registration successful! Logging you in.")
    main_navigation_page(user)


def exit_system() -> None:
    print("Exiting Alina J Talent Management System. Goodbye!")
    sys.exit()


def outside_welcome_page() -> None:
    while True:
        print("Welcome to Alina J Talent Management System!")
        print("1. Login")
        print("2. Register")
        print("3. Exit")
        choice = input("Enter your choice (1-3): ")

        if choice == "1":
            login()
        elif choice == "2":
            register()
        elif choice == "3":
            exit_system()
        else:
            print("Invalid choice, please try again.")


# ---------------------------------------------------------------------------
# Deal / Contract pages
# ---------------------------------------------------------------------------

def view_deals() -> None:
    print("\n------ Deals ------")
    display_table(_deal_svc.list_deals())
    print("\n-------------------")


def create_deal() -> None:
    print("--- Create New Deal ---")
    data = _get_data()

    client = select_item(data.get("clients", []), lambda x: x["description"], "Select Client")
    if not client:
        return

    brand = select_item(data.get("brands", []), lambda x: str(x), "Select Brand")
    if not brand:
        return

    brand_rep = select_item(data.get("brand_representatives", []), lambda x: str(x), "Select Brand Representative")
    if not brand_rep:
        return

    pitch_date = input("Enter Pitch Date (YYYY-MM-DD): ")
    is_active = input("Is the deal active? (yes/no): ").lower() == "yes"
    is_successful = input("Is the deal successful? (yes/no): ").lower() == "yes"

    deal = _deal_svc.create_deal(
        client["client_id"], brand["brand_id"], brand_rep["brand_rep_id"],
        pitch_date, is_active, is_successful,
    )
    print(f"Deal {deal['deal_id']} created successfully!")


def view_contracts() -> None:
    print("\n------ Contracts ------")
    display_table(_contract_svc.list_contracts())
    print("\n-----------------------")


def create_contract() -> None:
    print("--- Create New Contract ---")
    data = _get_data()

    deal = select_item(
        data.get("deals", []),
        lambda x: f"Deal ID {x['deal_id']} (Date: {x['pitch_date']})",
        "Select Deal",
    )
    if not deal:
        return

    details = input("Enter Contract Details: ")
    payment = float(input("Enter Payment Amount: "))
    agency_percentage = float(input("Enter Agency Percentage: "))
    start_date = input("Enter Start Date (YYYY-MM-DD): ")
    end_date = input("Enter End Date (YYYY-MM-DD): ")
    status = input("Enter Contract Status (e.g., Sent, Pending, Accepted, Rejected): ")
    is_approved = input("Is the contract approved? (yes/no): ").lower() == "yes"

    contract = _contract_svc.create_contract(
        deal["deal_id"], details, payment, agency_percentage,
        start_date, end_date, status, is_approved,
    )
    print(f"Contract {contract['contract_id']} created successfully!")


# ---------------------------------------------------------------------------
# Employee pages
# ---------------------------------------------------------------------------

def add_employee() -> None:
    print("--- Add Employee ---")
    data = _get_data()

    person = select_item(
        data.get("persons", []),
        lambda x: f"{x['full_name']} ({x['email']})",
        "Select Person to promote to Employee",
    )
    if not person:
        return

    position = input("Enter Position: ")
    title = input("Enter Title: ")
    is_manager = input("Is this employee a Manager? (yes/no): ").lower() == "yes"
    manager_id = 0

    if not is_manager:
        add_mgr = input("Would you like to assign a Manager to this employee? (yes/no): ").lower()
        if add_mgr == "yes":
            managers = [e for e in data.get("employees", []) if e.get("is_manager")]
            manager = select_item(
                managers,
                lambda x: f"{get_person_name(x['person_id'])} - {x['title']}",
                "Select Manager",
            )
            if manager:
                manager_id = manager["employee_id"]

    start_date = input("Enter Start Date (YYYY-MM-DD): ")
    end_date = input("Enter End Date (YYYY-MM-DD or leave blank): ") or None
    is_active = input("Is the Employee active? (yes/no): ").lower() == "yes"

    new_emp = _emp_svc.add_employee(
        person["person_id"], position, title, manager_id,
        start_date, end_date, is_active, is_manager,
    )
    print(f"Employee {new_emp['employee_id']} added successfully!")

    if is_manager:
        add_reports = input("Would you like to add direct reports? (yes/no): ").lower()
        if add_reports == "yes":
            while True:
                data = _get_data()
                candidates = [e for e in data.get("employees", []) if e["employee_id"] != new_emp["employee_id"]]
                report = select_item(
                    candidates,
                    lambda x: f"{get_person_name(x['person_id'])} (Current Mgr ID: {x['manager_id']})",
                    "Select Employee to assign (or cancel to finish)",
                )
                if not report:
                    break
                _emp_svc.update_employee(report["employee_id"], manager_id=new_emp["employee_id"])
                print(f"Assigned {get_person_name(report['person_id'])} to {get_person_name(new_emp['person_id'])}")


def modify_employee() -> None:
    data = _get_data()
    employee = find_and_select_item(
        data.get("employees", []),
        lambda x: get_person_name(x["person_id"]),
        lambda x: f"{get_person_name(x['person_id'])} - {x['title']}",
        "Employee",
    )
    if not employee:
        return

    print("Current data:")
    display_table(employee)
    position = input("Enter new Position (leave blank to keep current): ") or employee["position"]
    title = input("Enter new Title (leave blank to keep current): ") or employee["title"]
    start_date = input("Enter new Start Date (leave blank to keep current): ") or employee["start_date"]
    end_date = input("Enter new End Date (leave blank to keep current): ") or employee["end_date"]
    is_active_input = input("Is Active (leave blank to keep current, yes/no): ")
    is_active = employee["is_active"] if is_active_input == "" else is_active_input.lower() == "yes"

    manager_id = employee["manager_id"]
    if not employee.get("is_manager"):
        change_manager = input("Change Reporting Manager? (yes/no): ").lower()
        if change_manager == "yes":
            managers = [e for e in data.get("employees", []) if e.get("is_manager")]
            new_manager = select_item(managers, lambda x: get_person_name(x["person_id"]), "Select New Manager")
            if new_manager:
                manager_id = new_manager["employee_id"]

    _emp_svc.update_employee(
        employee["employee_id"],
        position=position,
        title=title,
        manager_id=manager_id,
        start_date=start_date,
        end_date=end_date,
        is_active=is_active,
    )
    print("Employee updated successfully!")


def delete_employee() -> None:
    data = _get_data()
    employee = find_and_select_item(
        data.get("employees", []),
        lambda x: get_person_name(x["person_id"]),
        lambda x: get_person_name(x["person_id"]),
        "Employee",
    )
    if not employee:
        return
    _emp_svc.delete_employee(employee["employee_id"])
    print("Employee deleted successfully!")


# ---------------------------------------------------------------------------
# Client pages
# ---------------------------------------------------------------------------

def add_client() -> None:
    print("--- Add Client ---")
    data = _get_data()
    emp = select_item(
        data.get("employees", []),
        lambda x: get_person_name(x["person_id"]),
        "Select Employee (Manager) for this Client",
    )
    if not emp:
        return
    description = input("Enter Client Description: ")
    new_client = _client_svc.add_client(emp["employee_id"], description)
    print(f"Client {new_client['client_id']} added successfully!")


def modify_client() -> None:
    data = _get_data()
    client = find_and_select_item(
        data.get("clients", []),
        lambda x: x["description"],
        lambda x: x["description"],
        "Client",
    )
    if not client:
        return

    print("Current data:")
    display_table(client)
    description = input("Enter new Description (leave blank to keep current): ") or client["description"]

    employee_id = client["employee_id"]
    change_emp = input("Change Employee? (yes/no): ").lower()
    if change_emp == "yes":
        emp = select_item(
            data.get("employees", []),
            lambda x: get_person_name(x["person_id"]),
            "Select New Employee",
        )
        if emp:
            employee_id = emp["employee_id"]

    _client_svc.update_client(client["client_id"], description=description, employee_id=int(employee_id))
    print("Client updated successfully!")


def delete_client() -> None:
    data = _get_data()
    client = find_and_select_item(
        data.get("clients", []),
        lambda x: x["description"],
        lambda x: x["description"],
        "Client",
    )
    if not client:
        return
    _client_svc.delete_client(client["client_id"])
    print("Client deleted successfully!")


# ---------------------------------------------------------------------------
# Navigation pages
# ---------------------------------------------------------------------------

def home_page(user: dict, role: dict) -> None:
    role_name = role["role_name"]
    print(f"Welcome to the Home Page, {user['username']}!")

    if role_name in {"Employee", "Manager", "Admin"}:
        print("\n--- Direct Reports ---")
        direct_reports = []
        data = _get_data()
        if role_name == "Admin":
            direct_reports = data.get("employees", [])
        elif role_name == "Manager":
            mgr_record = next(
                (e for e in data.get("employees", []) if e.get("person_id") == user["person_id"]), None
            )
            if mgr_record:
                direct_reports = [
                    e for e in data.get("employees", []) if e.get("manager_id") == mgr_record["employee_id"]
                ]
        elif role_name == "Employee":
            emp_record = next(
                (e for e in data.get("employees", []) if e.get("person_id") == user["person_id"]), None
            )
            if emp_record:
                direct_reports = [c for c in data.get("clients", []) if c.get("employee_id") == emp_record["employee_id"]]

        display_table(direct_reports)
        print("\n(Management for reports is handled on the Employees/Clients pages)")

    elif role_name in {"User", "Client", "Rep"}:
        print("\n--- Your Deals/Campaigns ---")
        display_table(_deal_svc.list_deals())
    else:
        print("No specific home page view for your role.")


def search_page(user: dict, role: dict) -> None:
    search_term = input("Enter search term: ").lower()
    data = _get_data()
    results = []
    for entity_type, entity_list in data.items():
        if not isinstance(entity_list, list):
            continue
        for item in entity_list:
            if not isinstance(item, dict):
                continue
            for value in item.values():
                if search_term in str(value).lower():
                    results.append((entity_type, item))
                    break

    if not results:
        print("No results found.")
        return

    print("\n--- Search Results ---")
    display_results = [
        {"Option": i, "Type": entity_type.replace("_", " ").title(), "Data": str(item)}
        for i, (entity_type, item) in enumerate(results, start=1)
    ]
    display_table(display_results)
    print(f"\n{len(results) + 1}. Return to Main Menu")

    while True:
        try:
            choice = int(input("Select a result to view details (or return to menu): "))
            if 1 <= choice <= len(results):
                print("\n--- Detailed View ---")
                print(results[choice - 1])
                print("---------------------\n")
            elif choice == len(results) + 1:
                return
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a number.")


def employees_page(user: dict, role: dict) -> None:
    print("--- All Employees ---")
    display_table(_emp_svc.list_employees())

    while True:
        print("\nEmployee Menu:")
        print("1. Add New Employee")
        print("2. Modify Employee")
        print("3. Delete Employee")
        print("4. Return to Main Menu")
        choice = input("Enter your choice: ")

        if choice == "1":
            add_employee()
        elif choice == "2":
            modify_employee()
        elif choice == "3":
            delete_employee()
        elif choice == "4":
            return
        else:
            print("Invalid choice.")


def clients_page(user: dict, role: dict) -> None:
    role_name = role["role_name"]
    print("--- Clients ---")

    clients_to_show: list = []
    data = _get_data()
    if role_name == "Employee":
        employee = next(
            (e for e in data.get("employees", []) if e["person_id"] == user["person_id"]), None
        )
        if employee:
            clients_to_show = _client_svc.get_clients_for_employee(employee["employee_id"])
        else:
            print("You are not registered as an Employee.")
    elif role_name in {"Manager", "Admin"}:
        clients_to_show = _client_svc.list_clients()

    display_table(clients_to_show)

    while True:
        print("\nClient Menu:")
        print("1. Add New Client")
        print("2. Modify Client")
        print("3. Delete Client")
        print("4. Return to Main Menu")
        choice = input("Enter your choice: ")

        if choice == "1":
            add_client()
        elif choice == "2":
            modify_client()
        elif choice == "3":
            delete_client()
        elif choice == "4":
            return
        else:
            print("Invalid choice.")


def brands_page(user: dict, role: dict) -> None:
    data = _get_data()
    print("\n------ Brands ------")
    display_table(data.get("brands", []))
    print("----------------------------\n")


def deals_page(user: dict, role: dict) -> None:
    view_deals()
    choice = input("\n1. Create a new deal\n2. Return to menu\nEnter choice: ")
    if choice == "1":
        create_deal()


def contracts_page(user: dict, role: dict) -> None:
    view_contracts()
    choice = input("\n1. Create a new contract\n2. Return to menu\nEnter choice: ")
    if choice == "1":
        create_contract()


def performance_page(user: dict, role: dict) -> None:
    print("Performance metrics, Goals, and KPIs coming soon!")


def tasks_page(user: dict, role: dict) -> None:
    print("A list of pending deals and contracts will be shown here.")


def discover_page(user: dict, role: dict) -> None:
    print("AI-powered social media discovery coming soon!")


def settings_page(user: dict, role: dict) -> None:
    print("User profile settings page coming soon.")


def main_navigation_page(user: dict) -> None:
    data = _get_data()
    role = next((r for r in data.get("roles", []) if r["role_id"] == user["role_id"]), None)
    if not role:
        print("Role not found for user.")
        return

    role_name = role["role_name"]

    while True:
        print("\n--- Main Menu ---")
        menu_options: dict = {}
        current_option = 1

        def add_option(name: str, func) -> None:
            nonlocal current_option
            print(f"{current_option}. {name}")
            menu_options[str(current_option)] = (name, func)
            current_option += 1

        add_option("Home", home_page)
        add_option("Search", search_page)
        if role_name in {"Employee", "Manager", "Admin"}:
            add_option("Clients", clients_page)
        if role_name in {"Manager", "Admin"}:
            add_option("Employees", employees_page)
        add_option("Brands", brands_page)
        add_option("Deals", deals_page)
        add_option("Contracts", contracts_page)
        add_option("Performance", performance_page)
        add_option("Tasks", tasks_page)
        add_option("Discover", discover_page)
        add_option("Settings", settings_page)
        print("0. Log Out")

        choice = input("Enter your choice: ")

        if choice == "0":
            print("Logging out...")
            break
        elif choice in menu_options:
            page_name, page_function = menu_options[choice]
            print(f"\n>>> Navigating to {page_name}...")
            page_function(user, role)
        else:
            print("Invalid choice, please try again.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    global _store, _auth, _emp_svc, _client_svc, _deal_svc, _contract_svc, _policy

    _store = JsonDataStore()
    _auth = AuthService(_store)
    _emp_svc = EmployeeService(_store)
    _client_svc = ClientService(_store)
    _deal_svc = DealService(_store)
    _contract_svc = ContractService(_store)
    _policy = AccessPolicy(_store)

    data = _store.load()

    if not data.get("roles"):
        for role_name in ["User", "Employee", "Manager", "Admin"]:
            role_id = _store.next_id(data)
            data.setdefault("roles", []).append({"role_id": role_id, "role_name": role_name})

        admin_role = next((r for r in data["roles"] if r["role_name"] == "Admin"), None)
        if admin_role:
            person_id = _store.next_id(data)
            data.setdefault("persons", []).append({
                "person_id": person_id,
                "first_name": "Admin", "last_name": "User",
                "full_name": "Admin User", "display_name": "Admin",
                "email": "admin@example.com", "phone": "N/A",
                "address": "N/A", "city": "N/A", "state": "N/A", "zip": "N/A",
            })
            user_id = _store.next_id(data)
            from werkzeug.security import generate_password_hash
            data.setdefault("users", []).append({
                "user_id": user_id,
                "username": "admin",
                "password": generate_password_hash("admin"),
                "role_id": admin_role["role_id"],
                "person_id": person_id,
            })
            print("Default admin user created with username 'admin' and password 'admin'.")
        _store.save(data)

    outside_welcome_page()
