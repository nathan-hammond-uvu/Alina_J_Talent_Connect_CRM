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

def inside_welcome_page(user):
    role = next((r for r in data["roles"] if r["role_id"] == user["role_id"]), None)

    print(f"Welcome to the Inside Welcome Page, {user['username']}!")
    print(f"Your role: {role['role_name']}")

    while True:
        if role and role["role_name"] in ["Admin", "Manager", "Employee"]:
            print("1. View Deals")
            print("2. Create Deal")
            print("3. View Contracts")
            print("4. Create Contract")
            print("5. Log Out")
            
            choice = input("Enter your choice: ")

            if choice == "1":
                view_deals()
            elif choice == "2":
                create_deal()
            elif choice == "3":
                view_contracts()
            elif choice == "4":
                create_contract()
            elif choice == "5":
                print("Logging out...")
                break
            else:
                print("Invalid option. Please try again.")


def main():
    # Create sample data
    roles = ["user", "Employee", "Manager", "Admin"]
    for role_name in roles:
        role_instance = Role(role_name)
        data["roles"].append(role_instance.__dict__)

    outside_welcome_page()


if __name__ == "__main__":
    main()