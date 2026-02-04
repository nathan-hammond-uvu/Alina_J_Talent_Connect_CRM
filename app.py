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

# Similar functions for influencers and social media accounts can be created here (modify, delete)

def inside_welcome_page(user):
    role = next((r for r in data["roles"] if r["role_id"] == user["role_id"]), None)

    print(f"Welcome to the Inside Welcome Page, {user['username']}!")
    print(f"Your role: {role['role_name']}")

    while True:
        if role and role["role_name"] in ["Admin", "Manager", "Employee"]:
            print("1. View Talent Managers")
            print("2. Add Talent Manager")
            print("3. Modify Talent Manager")
            print("4. Delete Talent Manager")
            print("5. Log Out")
            
            choice = input("Enter your choice: ")

            if choice == "1":
                view_entities("talent_managers")
            elif choice == "2":
                add_talent_manager()
            elif choice == "3":
                modify_talent_manager()
            elif choice == "4":
                delete_talent_manager()
            elif choice == "5":
                print("Logging out...")
                break
            else:
                print("Invalid option. Please try again.")

if __name__ == "__main__":
    main()