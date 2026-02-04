import pandas as pd

data = {
    "roles": [],
    "persons": [],
    "users": []
    
}

id_incrementer = 0

class role:   
    def __init__(self, role_name: str):
        self.role_id = id_incrementer + 1
        id_incrementer += 1
        self.role_name = role_name
        self.permissions = []

class person:
    def __init__(self, first_name: str, last_name: str, full_name: str, display_name: str, email: str, phone: str, address: str, city: str, state: str, zip: int):
        self.person_id = id_incrementer + 1
        id_incrementer += 1
        self.first_name = first_name
        self.last_name = last_name
        self.full_name = full_name
        self.display_name = display_name
        self.email = email
        self.phone = phone
        self.address = address
        self.city = city
        self.state = state
        self.zip = zip

class user:
    def __init__(self, username: str, password: str, role_id: int, person_id: int):
        self.user_id = id_incrementer + 1
        id_incrementer += 1
        self.username = username
        self.password = password
        self.role_id = role_id
        self.person_id = person_id


def login():
    username = input("Enter your username: ")
    # look for a user with this username
    # if found, prompt for password
    # if not found, print error message
    # if password matches, print welcome message and prompt main menu options.
    # if password does not match, print error message

def register():
    print("Register a new user")
    first_name = input("First Name: ")
    last_name = input("Last Name: ")
    full_name = f"{first_name} {last_name}"
    display_name = input("Display Name: ")
    email = input("Email: ")
    phone = input("Phone: ")
    address = input("Address: ")
    city = input("City: ")
    state = input("State: ")
    zip_code = int(input("Zip Code: "))
    username = input("Choose a username: ")
    password = input("Choose a password: ")

    new_person = person(first_name, last_name, full_name, display_name, email, phone, address, city, state, zip_code)
    
    # get role id for new user from data.roles where role_name is "user"
    role_id = None
    for r in data["roles"]:
        if r["role_name"] == "user":
            role_id = r["role_id"]
            break
    if role_id is None:
        print("Error: Could not find role with name 'user'")
        return

    new_user = user(username, password, role_id, new_person.person_id)

    print(f"User {username} registered successfully!")

    # After registration, prompt to login
    login()

def exit_system():
    print("Exiting Alina J Talent Management System. Goodbye!")
    exit()



def main():
    print("Welcome to Alina J Talent Management System!")

    # create some default roles, persons, and users.
    role_user = role("user")
    role_employee = role("Employee")
    role_manager = role("Manager")
    role_admin = role("Admin")
    person_admin = person("Admin", "User", "Admin User", "Admin", "admin@alinajtalent.com", "123-456-7890", "Fake street", "Salt Lake City", "UT", 84101)
    user_admin = user("admin", "adminpass", role_admin.role_id, person_admin.person_id)
    data["roles"].append(role_user.__dict__)
    data["roles"].append(role_employee.__dict__)
    data["roles"].append(role_manager.__dict__)
    data["roles"].append(role_admin.__dict__)
    data["persons"].append(person_admin.__dict__)
    data["users"].append(user_admin.__dict__)

    print("Choose an option:")
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


if __name__ == "__main__":
    main()