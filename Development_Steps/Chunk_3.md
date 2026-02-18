# Chunk 3: Persistence, Refactoring, and UI Polish

## Overview
In this development chunk, we focused on transitioning the application from in-memory storage to persistent file storage using JSON. We also performed a significant schema refactor to better align with business terminology, renaming "Talent Managers" to "Employees" and "Influencers" to "Clients". Additionally, we enhanced the Command Line Interface (CLI) to be more user-friendly by implementing tabular data views and interactive selection menus, removing the need for users to manually memorize and enter IDs.

## Objectives
1.  **Data Persistence**: Ensure data is saved to and loaded from a file (`data.json`) so that records are not lost when the program exits.
2.  **Schema Refactoring**: 
    *   Rename `talent_managers` to `employees` and introduce an `is_manager` flag to distinguish roles.
    *   Rename `influencers` to `clients`.
    *   Update all relationships (Deals, Social Media) to reference the new entity names.
3.  **UI/UX Improvements**:
    *   Replace raw dictionary printing with readable tables using `pandas`.
    *   Replace manual ID input with interactive list selection and search functionality.
4.  **Robust Startup**: Handle the initialization of the data file and default admin account automatically.

## Results
The application now persists state across sessions. The user experience is significantly smoother; users can search for entities by name or select them from numbered lists. The data model now supports a hierarchical structure where Employees can be Managers, and Clients are assigned to specific Employees.

## Change Log

### File System
- **Created**: `data.json` to serve as the persistent data store.

### `app.py` Modifications
- **Persistence Layer**:
    - Added `load_data()` and `save_data()` functions.
    - Added `initialize_id_incrementer()` to ensure unique IDs continue correctly after a restart.
    - Updated `main()` to check for `data.json` existence and create a default boilerplate with an Admin user if missing.

- **Schema Changes**:
    - Renamed `TalentManager` class to `Employee`.
    - Added `is_manager` boolean to `Employee` class.
    - Renamed `Influencer` class to `Client`.
    - Updated `Deal` and `SocialMediaAccount` classes to reference `client_id` instead of `influencer_id`.
    - Refactored `data` dictionary keys (`talent_managers` -> `employees`, `influencers` -> `clients`).

- **Helper Functions**:
    - Added `display_table(data_list)`: Uses pandas to render ASCII tables.
    - Added `select_item(items, ...)`: Allows users to pick an object from a list.
    - Added `find_and_select_item(...)`: Allows users to search for an object by string matching.
    - Added `get_person_name(person_id)`: Helper to resolve names for display.

- **CRUD & Logic Updates**:
    - Updated `add_employee`: Now handles "Manager" logic and assigning direct reports.
    - Updated `home_page`: Logic for "Direct Reports" now filters based on `is_manager` status and `employee_id`.
    - Updated all creation/modification functions (`create_deal`, `modify_client`, etc.) to use `select_item` instead of asking for raw IDs.
    - Added `save_data()` calls after every successful state change.