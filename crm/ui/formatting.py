import pandas as pd


def display_table(data_list) -> None:
    """Print a list of dicts as a formatted table."""
    if not data_list:
        print("No data available.")
        return
    if isinstance(data_list, dict):
        data_list = [data_list]
    df = pd.DataFrame(data_list)
    print(df.to_string(index=False))


def select_item(items: list, display_func, prompt_text: str = "Select an item:"):
    """Present a numbered list and return the chosen item, or None on cancel."""
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


def find_and_select_item(items: list, search_key_func, display_func, item_type_name: str):
    """Search items by keyword and let the user pick from matches."""
    search_term = input(f"Enter {item_type_name} name/description to search: ").lower()
    matches = [item for item in items if search_term in search_key_func(item).lower()]

    if not matches:
        print(f"No {item_type_name} found matching '{search_term}'.")
        return None

    if len(matches) == 1:
        return matches[0]

    return select_item(matches, display_func, f"Multiple matches found for {item_type_name}:")
