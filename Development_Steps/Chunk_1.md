# Objective
Create a command line interface that encorporates the data model that is established in the main README.md file and follows the outlined CLD. All data should be stored in a global variable called, data. data is an object with lists of classes. For example:
```
data = {
    "roles": [],
    "persons": [],
    "users": [],
    "talent_managers": []
    "Influencers": []
     etc... (continue for all tables in the data model in the readme.md)
}
The CLI should loop continuously. It should also prompt the user for next possible options/steps. It should only exit if the users chooses to. 

```
  
## Casual Loop Diagram (CLD)

### Outside Welcome Page

1. prompt the user to either:
2. Register
3. Login
4. Exit

#### Register

1. Prompt user to type in all the required fields to create a user and associated person. Ensure each field is typed in correctly
2. Add newly created user and person to gobal data variable.
3. Return to Outside Welcome Page

#### Login

1. Prompt the user for a username.
2. If username doesn't exist in data.users, then display invalid username message. Provide user with following options: try agagin, registrar, or forgot username.
3. If username does exist, prompt for password. If password doesn't match, then display incorrect password message. Provide user with the following options: try agagin, registrar, or forgot password.
4. If password does match, then display login success message. Route to Inside Welcome Page based on user role.

#### Exit

1. Confirm user request to exit.
2. If confirmed, wish the user good bye, and end program.
3. If not confirmed, repeat last options.

### Inside Welcome Page (for users with the role of: employee, manager, or admin)
1. Print all direct reports (influencers for talent managers, talent managers for managers, and managers for admin)
2. Prompt user with:
3. Which direct report would they like to view/modify/delete
4. Would they like to add a new direct report?

### Inside Welcome Page (for users with the role of: user, client, rep)
1. Print all Deals/Campaigns.
2. prompt user with:
3. Which deal/campaign would you like to view? (they don't have modify or delete permissions)

Continue with this shcema until you've completed the entire data model.

