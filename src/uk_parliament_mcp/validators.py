"""Parameter validation helpers."""

import re
from typing import Literal

HouseId = Literal[1, 2]


def validate_house_id(house: int) -> HouseId:
    """Validate house ID is 1 (Commons) or 2 (Lords).

    Args:
        house: House identifier to validate

    Returns:
        Validated house ID

    Raises:
        ValueError: If house is not 1 or 2
    """
    if house not in (1, 2):
        raise ValueError(f"House must be 1 (Commons) or 2 (Lords), got {house}")
    return house  # type: ignore[return-value]


def validate_date(date_str: str) -> str:
    """Validate date is YYYY-MM-DD format.

    Args:
        date_str: Date string to validate

    Returns:
        Validated date string

    Raises:
        ValueError: If date format is invalid
    """
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", date_str):
        raise ValueError(f"Date must be YYYY-MM-DD format, got {date_str}")
    return date_str


def validate_positive_int(value: int, name: str) -> int:
    """Validate integer is positive.

    Args:
        value: Integer to validate
        name: Parameter name for error message

    Returns:
        Validated integer

    Raises:
        ValueError: If value is not positive
    """
    if value < 1:
        raise ValueError(f"{name} must be positive, got {value}")
    return value
