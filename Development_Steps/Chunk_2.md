When a user adds a new item, the program must create a single Python dictionary to represent that item.
The keys of the dictionary must correspond to the fields defined in your project_plan.md.
This complete dictionary object must be added to a master list that holds all data.
The function responsible for listing items must be updated to iterate through the list of dictionaries.
The application's external behavior from the user's perspective should remain identical to the previous version.

# Objective
Modify the existing command line interface to do the following:
- Create a default admin user account
- After login in, show a main navigation. Main navigation should include the following pages:
  - Home
  - Search
  - Employees (only visable to users with a "Manager" role")
  - Clients (only visable to users with a "Employee" role or higher. No user access")
  - Brands
  - Deals
  - Contracts
  - Performance (a page for showing Goals, KPIs, and BI analytics)
  - Tasks (a page where users can keep track of all deals and contracts that are pending and need additional work done.)
  - Discover (This is a placeholder page for future AI social media webscrapping. you can just say, "Coming soon!")
  - Settings (a pages where users can edit their profile settings. i.e. update password, email, etc...)
- Add a global search option to the main navigation. This search should allow users to search any object type or key value pair in the main data within their role jurisdiction. Meaning, talent managers can see their influencer's data, but not vise versa. Influencers can see data related to them, but not other influencers. Users should have the option to navigate directly to where the searched item is stored.

The CLI should loop continuously. It should also prompt the user for next possible options/steps. Once the user has gotten to the home page, the user should always be able to navigate to the various pages via a main menu. It should only exit if the users chooses to.
  
## Casual Loop Diagram (Updated!)

### Welcome Page

prompt the user to either:
1. Create Account
2. Login
3. Exit

#### Create Account Page

1. Prompt user to type in all the required fields to create a user and associated person. Ensure each field is typed in correctly.
2. Add newly created user and person to gobal data variable. (all new accounts should default to a 'User' role
3. After creating the account, login the user in using the newly created credentials.

#### Login

1. Prompt the user for a username.
2. If username doesn't exist in data.users, then display invalid username message. Provide user with following options: try agagin, registrar, or forgot username.
3. If username does exist, prompt for password. If password doesn't match, then display incorrect password message. Provide user with the following options: try agagin, registrar, or forgot password.
4. If password does match, then display login success message. Then, route to Home Page based on user role.

#### Exit

1. Confirm user request to exit.
2. If confirmed, wish the user good bye, and end program.
3. If not confirmed, repeat last options.

### Home Page (for users with the role of: employee, manager, or admin)
1. Show the main navigation menu.
1. Print all direct reports (influencers for talent managers, talent managers for managers, and managers for admin)
2. Prompt user with:
3. Which direct report would they like to view/modify/delete
4. Would they like to add a new direct report?

### Home Page (for users with the role of: user, client, rep)
1. Print all Deals/Campaigns.
2. prompt user with:
3. Which deal/campaign would you like to view? (they don't have modify or delete permissions)

### Search

1. Ask the user what they would like to search for.
2. search the data dictionary for any item that matches. order them from closest match to least match.
3. Display each result with a number.
4. If the user types the coorespondng number, then navigate to the page where the object resides.
5. Have the very last number be a "return to home page" option.

### Employees

This page is only visible to users with the role of "Manager" or "Admin". Employees or users should not see this option in their main navigation menu.

1. List all the employees in table format.
2. Allow user to create a new employees.
3. Allow user to "select" any employee.
4. If an employee is selected, then provide modify or delete options.

### Clients 

This page is only visable to users with a "Admin", "Manager", and "Employee" roles. No user access.

1. List all the influencers in table format. (if a talent manager or "Employee" is logge in. Only show their influencers.)
2. Allow user to create a new influencers.
3. Allow user to "select" any influencers.
4. If an influencer is selected, then provide modify or delete options.

Create similar pages for the following:
  - Brands
  - Deals
  - Contracts
  - Performance 
  - Tasks 
  - Discover
  - Settings
