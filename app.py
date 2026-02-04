```python
import pandas as pd

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
            print("Invalid username. Please try again.")
            continue

        password = input("Enter your password: ")
        if matching_user["password"] == password:
            print(f"Login successful! Welcome, {matching_user['username']}.")
            inside_welcome_page(matching_user)
            break
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
    role = next((r for r in data["roles"] if r["role_name"] == "user"), None)
    if not role:
        print("Error: 'user' role not found.")
        return

    user = User(username, password, role["role_id"], person.person_id)
    data["users"].append(user.__dict__)

    print("Registration successful! You can now log in.")

def exit_system():
    print("Exiting Alina J Talent Management System. Goodbye!")
    exit()

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
    for deal in data["deals"]:
        print(deal)
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
    for contract in data["contracts"]:
        print(contract)
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
    for entity in data[entity_name]:
        print(entity)
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

    print(f"Current data: {talent_manager}")
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


def inside_welcome_page(user):
    """Main entry point for the Inside Welcome Page based on the user role."""
    role = next((r for r in data["roles"] if r["role_id"] == user["role_id"]), None)

    if not role:
        print("Role not found for user.")
        return

    print(f"Welcome to the Inside Welcome Page, {user['username']}!")
    print(f"Your role: {role['role_name']}")

    while True:
        role_name = role["role_name"]

        if role_name in ["Employee", "Manager", "Admin"]:
            handle_employee_manager_admin(user, role)
        elif role_name in ["User", "Client", "Rep"]:
            handle_user_client_rep(user, role)
        else:
            print("Role not recognized. Logging out.")
            break


def handle_employee_manager_admin(user, role):
    """Handle actions for Employee, Manager, and Admin roles."""
    while True:
        print("\nYour Direct Reports:")
        if role["role_name"] == "Admin":
            direct_reports = [m for m in data["talent_managers"]]
        elif role["role_name"] == "Manager":
            direct_reports = [tm for tm in data["talent_managers"] if tm["manager_id"] == user["person_id"]]
        elif role["role_name"] == "Employee":
            direct_reports = [i for i in data["influencers"] if i["talent_manager_id"] == user["person_id"]]
        else:
            direct_reports = []

        for i, report in enumerate(direct_reports, start=1):
            print(f"{i}. {report}")

        print("\nOptions:")
        print("1. View a Direct Report")
        print("2. Modify a Direct Report")
        print("3. Delete a Direct Report")
        print("4. Add a New Direct Report")
        print("5. Log Out")

        choice = input("Enter your choice: ")

        if choice == "1":
            view_entity(direct_reports)
        elif choice == "2":
            modify_entity(direct_reports)
        elif choice == "3":
            delete_entity(direct_reports)
        elif choice == "4":
            add_entity(user, role)
        elif choice == "5":
            print("Logging out...")
            break
        else:
            print("Invalid option. Please try again.")


def handle_user_client_rep(user, role):
    """Handle actions for User, Client, and Rep roles."""
    while True:
        print("\nYour Deals/Campaigns:")
        campaigns = [c for c in data["campaigns"] if c["user_id"] == user["user_id"]]

        for i, campaign in enumerate(campaigns, start=1):
            print(f"{i}. {campaign}")

        print("\nOptions:")
        print("1. View a Deal/Campaign")
        print("2. Log Out")

        choice = input("Enter your choice: ")

        if choice == "1":
            view_entity(campaigns)
        elif choice == "2":
            print("Logging out...")
            break
        else:
            print("Invalid option. Please try again.")


def view_entity(entities):
    """View details of a specific entity."""
    entity_index = int(input("Enter the number of the entity to view: ")) - 1
    if 0 <= entity_index < len(entities):
        print(f"Details: {entities[entity_index]}")
    else:
        print("Invalid selection.")


def modify_entity(entities):
    """Modify details of a specific entity."""
    entity_index = int(input("Enter the number of the entity to modify: ")) - 1
    if 0 <= entity_index < len(entities):
        print(f"Current details: {entities[entity_index]}")
        # Collect updated fields here, similar to the `modify_talent_manager` function.
        print("Modification not implemented yet.")  # Placeholder
    else:
        print("Invalid selection.")


def delete_entity(entities):
    """Delete a specific entity."""
    entity_index = int(input("Enter the number of the entity to delete: ")) - 1
    if 0 <= entity_index < len(entities):
        entity_to_delete = entities.pop(entity_index)
        print(f"Deleted: {entity_to_delete}")
    else:
        print("Invalid selection.")


def add_entity(user, role):
    """Add a new entity based on user role."""
    print("Adding a new entity is not implemented yet.")  # Placeholder

def main():
    # Create sample data
    roles = ["user", "Employee", "Manager", "Admin"]
    for role_name in roles:
        role_instance = Role(role_name)
        data["roles"].append(role_instance.__dict__)

    outside_welcome_page()


if __name__ == "__main__":
    main()
