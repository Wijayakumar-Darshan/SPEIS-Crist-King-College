"""validators.py – Input validation helpers."""
import re
from datetime import date


def validate_reg_no(val: str) -> tuple[bool, str]:
    val = val.strip()
    if not val:
        return False, "Registration number is required."
    if len(val) > 30:
        return False, "Registration number too long (max 30 chars)."
    return True, ""


def validate_name(val: str) -> tuple[bool, str]:
    val = val.strip()
    if not val:
        return False, "Name is required."
    if len(val) < 2:
        return False, "Name must be at least 2 characters."
    if len(val) > 100:
        return False, "Name too long (max 100 chars)."
    return True, ""


def validate_grade(val) -> tuple[bool, str]:
    try:
        g = int(val)
        if 6 <= g <= 13:
            return True, ""
        return False, "Grade must be between 6 and 13."
    except (TypeError, ValueError):
        return False, "Invalid grade."


def validate_marks(val) -> tuple[bool, str]:
    try:
        m = float(val)
        if 0 <= m <= 100:
            return True, ""
        return False, "Marks must be between 0 and 100."
    except (TypeError, ValueError):
        return False, "Invalid marks value."


def validate_password(val: str) -> tuple[bool, str]:
    if len(val) < 6:
        return False, "Password must be at least 6 characters."
    return True, ""


def validate_year(val) -> tuple[bool, str]:
    try:
        y = int(val)
        if 2000 <= y <= 2050:
            return True, ""
        return False, "Year must be between 2000 and 2050."
    except (TypeError, ValueError):
        return False, "Invalid year."


def sanitize_text(val: str) -> str:
    """Strip leading/trailing whitespace; remove control characters."""
    return re.sub(r"[\x00-\x1f\x7f]", "", val.strip())
