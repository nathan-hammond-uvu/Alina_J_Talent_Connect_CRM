import re
from datetime import datetime


def validate_email(email: str) -> bool:
    """Return True if email looks valid."""
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """Return True if phone contains only digits, spaces, dashes, dots, and parens."""
    pattern = r"^[\d\s\-\.\(\)\+]+$"
    return bool(re.match(pattern, phone))


def validate_date(date_str: str) -> bool:
    """Return True if date_str matches YYYY-MM-DD format."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except (ValueError, TypeError):
        return False


def validate_required(value, field_name: str) -> None:
    """Raise ValueError if value is empty/None."""
    if value is None or str(value).strip() == "":
        raise ValueError(f"Field '{field_name}' is required and cannot be empty.")
