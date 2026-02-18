import pandas as pd
import sys
import json
import os

data = {
    "roles": [],
    "persons": [],
    "users": [],
    "employees": [],
    "clients": [],
    "social_media_accounts": [],
    "brands": [],
    "brand_representatives": [],
    "deals": [],
    "contracts": []
}

DATA_FILE = "data.json"

id_incrementer = 0

def save_data():
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving data: {e}")

def initialize_id_incrementer():
    global id_incrementer
    max_id = 0
    for key in data:
        for item in data[key]:
            for k, v in item.items():
                if k.endswith("_id") and isinstance(v, int):
                    if v > max_id:
                        max_id = v
    id_incrementer = max_id

def load_data():
    global data
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
            initialize_id_incrementer()
        except Exception as e:
            print(f"Error loading data: {e}")
    else:
        save_data()

def display_table(data_list):
    if not data_list:
        print("No data available.")
        return
    if isinstance(data_list, dict):
        data_list = [data_list]
    df = pd.DataFrame(data_list)
    print(df.to_string(index=False))

def get_person_name(person_id):
    person = next((p for p in data["persons"] if p["person_id"] == person_id), None)
    return person["full_name"] if person else "Unknown"

def select_item(items, display_func, prompt_text="Select an item:"):
    if not items:
        print("No items available to select.")
        return None
    
    print(f"\n{prompt_text}")
    for i, item in enumerate(items, 1):
        print(f"{i}. {display_func(item)}")
    
    while True:
        try:
            choice = input("Enter selection number (or press Enter to cancel): ")
            if choice == "":
                return None
            choice = int(choice)
            if 1 <= choice <= len(items):
                return items[choice - 1]
            print("Invalid selection.")
        except ValueError:
            print("Please enter a number.")

def find_and_select_item(items, search_key_func, display_func, item_type_name):
    search_term = input(f"Enter {item_type_name} name/description to search: ").lower()
    matches = [item for item in items if search_term in search_key_func(item).lower()]
    
    if not matches:
        print(f"No {item_type_name} found matching '{search_term}'.")
        return None
    
    if len(matches) == 1:
        return matches[0]
    
    return select_item(matches, display_func, f"Multiple matches found for {item_type_name}:")

def get_next_id():
    global id_incrementer
    id_incrementer += 1
    return id_incrementer

class Role:
    def __init__(self, role_name):
        self.role_id = get_next_id()
        self.role_name = role_name


class Person:
    def __init__(self, first_name, last_name, full_name, display_name, email, phone, address, city, state, zip_code):
        self.person_id = get_next_id()
        self.first_name = first_name
        self.last_name = last_name
        self.full_name = full_name
        self.display_name = display_name
        self.email = email
        self.phone = phone
        self.address = address
        self.city = city
        self.state = state
        self.zip = zip_code


class User:
    def __init__(self, username, password, role_id, person_id):
        self.user_id = get_next_id()
        self.username = username
        self.password = password
        self.role_id = role_id
        self.person_id = person_id

class Deal:
    def __init__(self, client_id, brand_id, brand_rep_id, pitch_date, is_active, is_successful):
        self.deal_id = get_next_id()
        self.client_id = client_id
        self.brand_id = brand_id
        self.brand_rep_id = brand_rep_id
        self.pitch_date = pitch_date
        self.is_active = is_active
        self.is_successful = is_successful


class Contract:
    def __init__(self, deal_id, details, payment, agency_percentage, start_date, end_date, status, is_approved):
        self.contract_id = get_next_id()
        self.deal_id = deal_id
        self.details = details
        self.payment = payment
        self.agency_percentage = agency_percentage
        self.start_date = start_date
        self.end_date = end_date
        self.status = status
        self.is_approved = is_approved

class Employee:
    def __init__(self, person_id, position, title, manager_id, start_date, end_date, is_active, is_manager):
        self.employee_id = get_next_id()
        self.person_id = person_id
        self.position = position
        self.title = title
        self.manager_id = manager_id
        self.start_date = start_date
        self.end_date = end_date
        self.is_active = is_active
        self.is_manager = is_manager

class Client:
    def __init__(self, employee_id, description):
        self.client_id = get_next_id()
        self.employee_id = employee_id
        self.description = description

class SocialMediaAccount:
    def __init__(self, client_id, account_type, link):
        self.social_media_id = get_next_id()
        self.client_id = client_id
        self.account_type = account_type
        self.link = link

def login():
    while True:
        username = input("Enter your username: ")
        matching_user = next((user for user in data["users"] if user["username"] == username), None)

        if not matching_user:
            print("Invalid username.")
            choice = input("Options: (1) Try again, (2) Register: ")
            if choice == '2':
                register()
                return # register handles login and returns here, so we return to outside_welcome_page
            else:
                continue

        password = input("Enter your password: ")
        if matching_user["password"] == password:
            print(f"Login successful! Welcome, {matching_user['username']}.")
            main_navigation_page(matching_user)
            return # After logout, return to the outside_welcome_page
        else:
            print("Incorrect password. Please try again.")

def register():
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
    
    person = Person(first_name, last_name, full_name, display_name, email, phone, address, city, state, zip_code)
    data["persons"].append(person.__dict__)

    username = input("Choose a username: ")
    password = input("Choose a password: ")

    # Assign the "user" role by default
    role = next((r for r in data["roles"] if r["role_name"] == "User"), None)
    if not role:
        print("Error: 'user' role not found.")
        return

    user = User(username, password, role["role_id"], person.person_id)
    data["users"].append(user.__dict__)
    save_data()

    print("Registration successful! Logging you in.")
    main_navigation_page(user.__dict__)

def exit_system():
    print("Exiting Alina J Talent Management System. Goodbye!")
    sys.exit()

def outside_welcome_page():
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

def view_deals():
    print("\n------ Deals ------")
    display_table(data["deals"])
    print("\n-------------------")

def create_deal():
    print("--- Create New Deal ---")
    client = select_item(data["clients"], lambda x: f"{x['description']}", "Select Client")
    if not client: return

    brand = select_item(data["brands"], lambda x: str(x), "Select Brand")
    if not brand: return

    brand_rep = select_item(data["brand_representatives"], lambda x: str(x), "Select Brand Representative")
    if not brand_rep: return

    client_id, brand_id, brand_rep_id = client["client_id"], brand["brand_id"], brand_rep["brand_rep_id"]
    pitch_date = input("Enter Pitch Date (YYYY-MM-DD): ")
    is_active = input("Is the deal active? (yes/no): ").lower() == "yes"
    is_successful = input("Is the deal successful? (yes/no): ").lower() == "yes"

    new_deal = Deal(client_id, brand_id, brand_rep_id, pitch_date, is_active, is_successful)
    data["deals"].append(new_deal.__dict__)
    save_data()
    print(f"Deal {new_deal.deal_id} created successfully!")

def view_contracts():
    print("\n------ Contracts ------")
    display_table(data["contracts"])
    print("\n-----------------------")

def create_contract():
    print("--- Create New Contract ---")
    # Helper to display deal info
    deal = select_item(data["deals"], lambda x: f"Deal ID {x['deal_id']} (Date: {x['pitch_date']})", "Select Deal")
    if not deal: return
    deal_id = deal["deal_id"]
    details = input("Enter Contract Details: ")
    payment = float(input("Enter Payment Amount: "))
    agency_percentage = float(input("Enter Agency Percentage: "))
    start_date = input("Enter Start Date (YYYY-MM-DD): ")
    end_date = input("Enter End Date (YYYY-MM-DD): ")
    status = input("Enter Contract Status (e.g., Sent, Pending, Accepted, Rejected): ")
    is_approved = input("Is the contract approved? (yes/no): ").lower() == "yes"

    new_contract = Contract(deal_id, details, payment, agency_percentage, start_date, end_date, status, is_approved)
    data["contracts"].append(new_contract.__dict__)
    save_data()
    print(f"Contract {new_contract.contract_id} created successfully!")

def view_entities(entity_name):
    print(f"\n------ {entity_name} ------")
    display_table(data[entity_name])
    print("----------------------------\n")

def add_employee():
    print("--- Add Employee ---")
    person = select_item(data["persons"], lambda x: f"{x['full_name']} ({x['email']})", "Select Person to promote to Employee")
    if not person: return
    person_id = person["person_id"]

    position = input("Enter Position: ")
    title = input("Enter Title: ")
    
    is_manager = input("Is this employee a Manager? (yes/no): ").lower() == "yes"
    manager_id = 0

    if not is_manager:
        # If not a manager, ask if they want to add a manager
        add_mgr = input("Would you like to assign a Manager to this employee? (yes/no): ").lower()
        if add_mgr == "yes":
            managers = [e for e in data["employees"] if e.get("is_manager")]
            manager = select_item(managers, lambda x: f"{get_person_name(x['person_id'])} - {x['title']}", "Select Manager")
            if manager:
                manager_id = manager["employee_id"]

    start_date = input("Enter Start Date (YYYY-MM-DD): ")
    end_date = input("Enter End Date (YYYY-MM-DD or leave blank): ") or None
    is_active = input("Is the Employee active? (yes/no): ").lower() == "yes"

    new_employee = Employee(person_id, position, title, manager_id, start_date, end_date, is_active, is_manager)
    data["employees"].append(new_employee.__dict__)
    save_data()
    print(f"Employee {new_employee.employee_id} added successfully!")

    # If they are a manager, ask to add direct reports (assign existing employees)
    if is_manager:
        add_reports = input("Would you like to add direct reports (assign existing employees)? (yes/no): ").lower()
        if add_reports == "yes":
            while True:
                # Filter employees who are not managers (or just anyone)
                candidates = [e for e in data["employees"] if e["employee_id"] != new_employee.employee_id]
                report = select_item(candidates, lambda x: f"{get_person_name(x['person_id'])} (Current Mgr ID: {x['manager_id']})", "Select Employee to assign (or cancel to finish)")
                if not report:
                    break
                report["manager_id"] = new_employee.employee_id
                print(f"Assigned {get_person_name(report['person_id'])} to {get_person_name(new_employee.person_id)}")
            save_data()

def modify_employee():
    employee = find_and_select_item(
        data["employees"], 
        lambda x: get_person_name(x["person_id"]), 
        lambda x: f"{get_person_name(x['person_id'])} - {x['title']}", 
        "Employee"
    )
    if not employee:
        return

    print("Current data:")
    display_table(employee)
    position = input("Enter new Position (leave blank to keep current): ") or employee["position"]
    title = input("Enter new Title (leave blank to keep current): ") or employee["title"]
    start_date = input("Enter new Start Date (leave blank to keep current): ") or employee["start_date"]
    end_date = input("Enter new End Date (leave blank to keep current): ") or employee["end_date"]
    is_active = input("Is Active (leave blank to keep current, yes/no): ")
    is_active = employee["is_active"] if is_active == "" else is_active.lower() == "yes"

    # Handle Manager ID change via selection
    manager_id = employee["manager_id"]
    if not employee.get("is_manager"):
        change_manager = input("Change Reporting Manager? (yes/no): ").lower()
        if change_manager == "yes":
            managers = [e for e in data["employees"] if e.get("is_manager")]
            new_manager = select_item(managers, lambda x: f"{get_person_name(x['person_id'])}", "Select New Manager")
            if new_manager:
                manager_id = new_manager["employee_id"]

    employee.update({
        "position": position,
        "title": title,
        "manager_id": manager_id,
        "start_date": start_date,
        "end_date": end_date,
        "is_active": is_active
    })
    save_data()
    print("Employee updated successfully!")

def delete_employee():
    employee = find_and_select_item(
        data["employees"], 
        lambda x: get_person_name(x["person_id"]), 
        lambda x: f"{get_person_name(x['person_id'])}", 
        "Employee"
    )
    if not employee: return

    data["employees"] = [e for e in data["employees"] if e["employee_id"] != employee["employee_id"]]
    save_data()
    print("Employee deleted successfully!")

def add_client():
    print("--- Add Client ---")
    emp = select_item(data["employees"], lambda x: f"{get_person_name(x['person_id'])}", "Select Employee (Manager) for this Client")
    if not emp: return
    employee_id = emp["employee_id"]

    description = input("Enter Client Description: ")
    new_client = Client(employee_id, description)
    data["clients"].append(new_client.__dict__)
    save_data()
    print(f"Client {new_client.client_id} added successfully!")

def modify_client():
    client = find_and_select_item(data["clients"], lambda x: x["description"], lambda x: x["description"], "Client")
    if not client:
        return

    print("Current data:")
    display_table(client)
    description = input("Enter new Description (leave blank to keep current): ") or client["description"]
    
    employee_id = client["employee_id"]
    change_emp = input("Change Employee? (yes/no): ").lower()
    if change_emp == "yes":
        emp = select_item(data["employees"], lambda x: f"{get_person_name(x['person_id'])}", "Select New Employee")
        if emp:
            employee_id = emp["employee_id"]

    client.update({
        "description": description,
        "employee_id": int(employee_id)
    })
    save_data()
    print("Client updated successfully!")

def delete_client():
    client = find_and_select_item(data["clients"], lambda x: x["description"], lambda x: x["description"], "Client")
    if not client: return

    data["clients"] = [c for c in data["clients"] if c["client_id"] != client["client_id"]]
    save_data()
    print("Client deleted successfully!")

def home_page(user, role):
    role_name = role["role_name"]
    print(f"Welcome to the Home Page, {user['username']}!")

    if role_name in ["Employee", "Manager", "Admin"]:
        print("\n--- Direct Reports ---")
        direct_reports = []
        if role_name == "Admin":
            direct_reports = data["employees"]
        elif role_name == "Manager":
            # Find the employee record for this user
            mgr_record = next((e for e in data["employees"] if e.get("person_id") == user["person_id"]), None)
            if mgr_record:
                direct_reports = [e for e in data["employees"] if e.get("manager_id") == mgr_record["employee_id"]]
        elif role_name == "Employee":
            # Find the employee record
            emp_record = next((e for e in data["employees"] if e.get("person_id") == user["person_id"]), None)
            if emp_record:
                direct_reports = [c for c in data["clients"] if c.get("employee_id") == emp_record["employee_id"]]

        display_table(direct_reports)
        print("\n(Management for reports is handled on the Employees/Clients pages)")

    elif role_name in ["User", "Client", "Rep"]:
        print("\n--- Your Deals/Campaigns ---")
        # NOTE: The data model doesn't directly link a "User" to a "Deal".
        # This is a placeholder showing all deals. A real implementation would need a clear link.
        display_table(data["deals"])
    else:
        print("No specific home page view for your role.")

def search_page(user, role):
    search_term = input("Enter search term: ").lower()
    results = []
    # This is a simplified search. A real implementation would need more sophisticated matching and ranking.
    # TODO: Add role-based access control to filter search results based on user jurisdiction.
    for entity_type, entity_list in data.items():
        for item in entity_list:
            for value in item.values():
                if search_term in str(value).lower():
                    results.append((entity_type, item))
                    break # Move to next item once a match is found in the current one

    if not results:
        print("No results found.")
        return

    print("\n--- Search Results ---")
    display_results = []
    for i, (entity_type, item) in enumerate(results, start=1):
        display_results.append({"Option": i, "Type": entity_type.replace('_', ' ').title(), "Data": str(item)})
    
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

def employees_page(user, role):
    print("--- All Employees ---")
    display_table(data["employees"])

    while True:
        print("\nEmployee Menu:")
        print("1. Add New Employee")
        print("2. Modify Employee")
        print("3. Delete Employee")
        print("4. Return to Main Menu")
        choice = input("Enter your choice: ")

        if choice == '1':
            add_employee()
        elif choice == '2':
            modify_employee()
        elif choice == '3':
            delete_employee()
        elif choice == '4':
            return
        else:
            print("Invalid choice.")

def clients_page(user, role):
    role_name = role["role_name"]
    print("--- Clients ---")
    
    clients_to_show = []
    if role_name == "Employee":
        employee = next((e for e in data["employees"] if e["person_id"] == user["person_id"]), None)
        if employee:
            clients_to_show = [c for c in data["clients"] if c["employee_id"] == employee["employee_id"]]
        else:
            print("You are not registered as an Employee.")
    elif role_name in ["Manager", "Admin"]:
        clients_to_show = data["clients"]

    display_table(clients_to_show)

    while True:
        print("\nClient Menu:")
        print("1. Add New Client")
        print("2. Modify Client")
        print("3. Delete Client")
        print("4. Return to Main Menu")
        choice = input("Enter your choice: ")

        if choice == '1':
            add_client()
        elif choice == '2':
            modify_client()
        elif choice == '3':
            delete_client()
        elif choice == '4':
            return
        else:
            print("Invalid choice.")

def brands_page(user, role):
    view_entities("brands")

def deals_page(user, role):
    view_deals()
    choice = input("\n1. Create a new deal\n2. Return to menu\nEnter choice: ")
    if choice == '1':
        create_deal()

def contracts_page(user, role):
    view_contracts()
    choice = input("\n1. Create a new contract\n2. Return to menu\nEnter choice: ")
    if choice == '1':
        create_contract()

def performance_page(user, role):
    print("Performance metrics, Goals, and KPIs coming soon!")

def tasks_page(user, role):
    print("A list of pending deals and contracts will be shown here.")

def discover_page(user, role):
    print("AI-powered social media discovery coming soon!")

def settings_page(user, role):
    print("User profile settings page coming soon.")

def main_navigation_page(user):
    role = next((r for r in data["roles"] if r["role_id"] == user["role_id"]), None)
    if not role:
        print("Role not found for user.")
        return

    role_name = role["role_name"]

    while True:
        print("\n--- Main Menu ---")
        menu_options = {}
        current_option = 1

        # Build menu dynamically
        def add_option(name, func):
            nonlocal current_option
            print(f"{current_option}. {name}")
            menu_options[str(current_option)] = (name, func)
            current_option += 1

        add_option("Home", home_page)
        add_option("Search", search_page)
        if role_name in ["Employee", "Manager", "Admin"]:
            add_option("Clients", clients_page)
        if role_name in ["Manager", "Admin"]:
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

def main():
    load_data()

    if not data["roles"]:
        # Create sample data
        roles = ["User", "Employee", "Manager", "Admin"]
        for role_name in roles:
            role_instance = Role(role_name)
            data["roles"].append(role_instance.__dict__)

        # Create a default admin user
        admin_role = next((r for r in data["roles"] if r["role_name"] == "Admin"), None)
        if admin_role:
            admin_person = Person("Admin", "User", "Admin User", "Admin", "admin@example.com", "N/A", "N/A", "N/A", "N/A", "N/A")
            data["persons"].append(admin_person.__dict__)
            admin_user = User("admin", "admin", admin_role["role_id"], admin_person.person_id)
            data["users"].append(admin_user.__dict__)
            print("Default admin user created with username 'admin' and password 'admin'.")
        save_data()

    outside_welcome_page()


if __name__ == "__main__":
    main()
