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


def inside_welcome_page(user):
    role = next((r for r in data["roles"] if r["role_id"] == user["role_id"]), None)

    print(f"Welcome to the Inside Welcome Page, {user['username']}!")
    print(f"Your role: {role['role_name']}")

    if role["role_name"] in ["Employee", "Manager", "Admin"]:
        print("You have management tasks available here.")
        # Implementation for management tasks goes here
    elif role["role_name"] in ["User", "Client", "Rep"]:
        print("You can view deals/campaigns.")
        # Implementation for deal/campaign viewing goes here

def main():
    # Create sample data
    roles = ["user", "Employee", "Manager", "Admin"]
    for role_name in roles:
        role_instance = Role(role_name)
        data["roles"].append(role_instance.__dict__)

    outside_welcome_page()

if __name__ == "__main__":
    main()
```