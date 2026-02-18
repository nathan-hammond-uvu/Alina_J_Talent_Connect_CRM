import pandas as pd
import sys

data = {
    "roles": [],
    "persons": [],
    "users": [],
    "talent_managers": [],
    "influencers": [],
    "social_media_accounts": [],
    "brands": [],
    "brand_representatives": [],
    "deals": [],
    "contracts": []
}

id_incrementer = 0

def display_table(data_list):
    if not data_list:
        print("No data available.")
        return
    if isinstance(data_list, dict):
        data_list = [data_list]
    df = pd.DataFrame(data_list)
    print(df.to_string(index=False))

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
    def __init__(self, influencer_id, brand_id, brand_rep_id, pitch_date, is_active, is_successful):
        self.deal_id = get_next_id()
        self.influencer_id = influencer_id
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

class TalentManager:
    def __init__(self, person_id, position, title, manager_id, start_date, end_date, is_active):
        self.talent_manager_id = get_next_id()
        self.person_id = person_id
        self.position = position
        self.title = title
        self.manager_id = manager_id
        self.start_date = start_date
        self.end_date = end_date
        self.is_active = is_active

class Influencer:
    def __init__(self, talent_manager_id, description):
        self.influencer_id = get_next_id()
        self.talent_manager_id = talent_manager_id
        self.description = description

class SocialMediaAccount:
    def __init__(self, influencer_id, account_type, link):
        self.social_media_id = get_next_id()
        self.influencer_id = influencer_id
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
    influencer_id = int(input("Enter Influencer ID: "))
    brand_id = int(input("Enter Brand ID: "))
    brand_rep_id = int(input("Enter Brand Representative ID: "))
    pitch_date = input("Enter Pitch Date (YYYY-MM-DD): ")
    is_active = input("Is the deal active? (yes/no): ").lower() == "yes"
    is_successful = input("Is the deal successful? (yes/no): ").lower() == "yes"

    new_deal = Deal(influencer_id, brand_id, brand_rep_id, pitch_date, is_active, is_successful)
    data["deals"].append(new_deal.__dict__)
    print(f"Deal {new_deal.deal_id} created successfully!")

def view_contracts():
    print("\n------ Contracts ------")
    display_table(data["contracts"])
    print("\n-----------------------")

def create_contract():
    deal_id = int(input("Enter Deal ID: "))
    details = input("Enter Contract Details: ")
    payment = float(input("Enter Payment Amount: "))
    agency_percentage = float(input("Enter Agency Percentage: "))
    start_date = input("Enter Start Date (YYYY-MM-DD): ")
    end_date = input("Enter End Date (YYYY-MM-DD): ")
    status = input("Enter Contract Status (e.g., Sent, Pending, Accepted, Rejected): ")
    is_approved = input("Is the contract approved? (yes/no): ").lower() == "yes"

    new_contract = Contract(deal_id, details, payment, agency_percentage, start_date, end_date, status, is_approved)
    data["contracts"].append(new_contract.__dict__)
    print(f"Contract {new_contract.contract_id} created successfully!")

def view_entities(entity_name):
    print(f"\n------ {entity_name} ------")
    display_table(data[entity_name])
    print("----------------------------\n")

def add_talent_manager():
    person_id = int(input("Enter Person ID for the Talent Manager: "))
    position = input("Enter Position: ")
    title = input("Enter Title: ")
    manager_id = int(input("Enter Manager ID (or 0 if none): "))
    start_date = input("Enter Start Date (YYYY-MM-DD): ")
    end_date = input("Enter End Date (YYYY-MM-DD or leave blank): ") or None
    is_active = input("Is the Talent Manager active? (yes/no): ").lower() == "yes"

    new_talent_manager = TalentManager(person_id, position, title, manager_id, start_date, end_date, is_active)
    data["talent_managers"].append(new_talent_manager.__dict__)
    print(f"Talent Manager {new_talent_manager.talent_manager_id} added successfully!")

def modify_talent_manager():
    talent_manager_id = int(input("Enter Talent Manager ID to modify: "))
    talent_manager = next((tm for tm in data["talent_managers"] if tm["talent_manager_id"] == talent_manager_id), None)

    if not talent_manager:
        print("Talent Manager not found.")
        return

    print("Current data:")
    display_table(talent_manager)
    position = input("Enter new Position (leave blank to keep current): ") or talent_manager["position"]
    title = input("Enter new Title (leave blank to keep current): ") or talent_manager["title"]
    manager_id = input("Enter new Manager ID (leave blank to keep current): ") or talent_manager["manager_id"]
    start_date = input("Enter new Start Date (leave blank to keep current): ") or talent_manager["start_date"]
    end_date = input("Enter new End Date (leave blank to keep current): ") or talent_manager["end_date"]
    is_active = input("Is Active (leave blank to keep current, yes/no): ")
    is_active = talent_manager["is_active"] if is_active == "" else is_active.lower() == "yes"

    talent_manager.update({
        "position": position,
        "title": title,
        "manager_id": manager_id,
        "start_date": start_date,
        "end_date": end_date,
        "is_active": is_active
    })
    print("Talent Manager updated successfully!")

def delete_talent_manager():
    talent_manager_id = int(input("Enter Talent Manager ID to delete: "))
    data["talent_managers"] = [tm for tm in data["talent_managers"] if tm["talent_manager_id"] != talent_manager_id]
    print("Talent Manager deleted successfully!")

def add_influencer():
    talent_manager_id = int(input("Enter Talent Manager ID: "))
    description = input("Enter Influencer Description: ")
    new_influencer = Influencer(talent_manager_id, description)
    data["influencers"].append(new_influencer.__dict__)
    print(f"Influencer {new_influencer.influencer_id} added successfully!")

def modify_influencer():
    influencer_id = int(input("Enter Influencer ID to modify: "))
    influencer = next((i for i in data["influencers"] if i["influencer_id"] == influencer_id), None)

    if not influencer:
        print("Influencer not found.")
        return

    print("Current data:")
    display_table(influencer)
    description = input("Enter new Description (leave blank to keep current): ") or influencer["description"]
    talent_manager_id = input("Enter new Talent Manager ID (leave blank to keep current): ") or influencer["talent_manager_id"]

    influencer.update({
        "description": description,
        "talent_manager_id": int(talent_manager_id)
    })
    print("Influencer updated successfully!")

def delete_influencer():
    influencer_id = int(input("Enter Influencer ID to delete: "))
    initial_len = len(data["influencers"])
    data["influencers"] = [i for i in data["influencers"] if i["influencer_id"] != influencer_id]
    if len(data["influencers"]) < initial_len:
        print("Influencer deleted successfully!")
    else:
        print("Influencer not found.")

def home_page(user, role):
    role_name = role["role_name"]
    print(f"Welcome to the Home Page, {user['username']}!")

    if role_name in ["Employee", "Manager", "Admin"]:
        print("\n--- Direct Reports ---")
        direct_reports = []
        if role_name == "Admin":
            direct_reports = data["talent_managers"]
        elif role_name == "Manager":
            direct_reports = [tm for tm in data["talent_managers"] if tm.get("manager_id") == user["person_id"]]
        elif role_name == "Employee":
            # Assuming an "Employee" is a Talent Manager, find their TM record to find their influencers
            tm_record = next((tm for tm in data["talent_managers"] if tm.get("person_id") == user["person_id"]), None)
            if tm_record:
                direct_reports = [i for i in data["influencers"] if i.get("talent_manager_id") == tm_record["talent_manager_id"]]

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
    print("--- All Employees (Talent Managers) ---")
    display_table(data["talent_managers"])

    while True:
        print("\nEmployee Menu:")
        print("1. Add New Employee")
        print("2. Modify Employee")
        print("3. Delete Employee")
        print("4. Return to Main Menu")
        choice = input("Enter your choice: ")

        if choice == '1':
            add_talent_manager()
        elif choice == '2':
            modify_talent_manager()
        elif choice == '3':
            delete_talent_manager()
        elif choice == '4':
            return
        else:
            print("Invalid choice.")

def clients_page(user, role):
    role_name = role["role_name"]
    print("--- Clients (Influencers) ---")
    
    influencers_to_show = []
    if role_name == "Employee":
        talent_manager = next((tm for tm in data["talent_managers"] if tm["person_id"] == user["person_id"]), None)
        if talent_manager:
            influencers_to_show = [i for i in data["influencers"] if i["talent_manager_id"] == talent_manager["talent_manager_id"]]
        else:
            print("You are not registered as a Talent Manager.")
    elif role_name in ["Manager", "Admin"]:
        influencers_to_show = data["influencers"]

    display_table(influencers_to_show)

    while True:
        print("\nClient Menu:")
        print("1. Add New Client (Influencer)")
        print("2. Modify Client (Influencer)")
        print("3. Delete Client (Influencer)")
        print("4. Return to Main Menu")
        choice = input("Enter your choice: ")

        if choice == '1':
            add_influencer()
        elif choice == '2':
            modify_influencer()
        elif choice == '3':
            delete_influencer()
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

    outside_welcome_page()


if __name__ == "__main__":
    main()
