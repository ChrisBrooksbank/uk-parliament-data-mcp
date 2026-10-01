"""Centralized configuration for UK Parliament MCP Server."""

from typing import overload

# API Base URLs
MEMBERS_API_BASE = "https://members-api.parliament.uk/api"
BILLS_API_BASE = "https://bills-api.parliament.uk/api/v1"
COMMONS_VOTES_API_BASE = "https://commonsvotes-api.parliament.uk/data"
LORDS_VOTES_API_BASE = "https://lordsvotes-api.parliament.uk/data"
COMMITTEES_API_BASE = "https://committees-api.parliament.uk/api"
HANSARD_API_BASE = "https://hansard-api.parliament.uk"
INTERESTS_API_BASE = "https://interests-api.parliament.uk/api/v1"
NOW_API_BASE = "https://now-api.parliament.uk/api"
WHATSON_API_BASE = "https://whatson-api.parliament.uk/calendar"
STATUTORY_INSTRUMENTS_API_BASE = "https://statutoryinstruments-api.parliament.uk/api/v2"
TREATIES_API_BASE = "https://treaties-api.parliament.uk/api"
ERSKINE_MAY_API_BASE = "https://erskinemay-api.parliament.uk/api"
ORAL_QUESTIONS_API_BASE = "https://oralquestionsandmotions-api.parliament.uk"
WRITTEN_QUESTIONS_API_BASE = "https://questions-statements-api.parliament.uk/api"

# Common constants
HOUSE_COMMONS = 1
HOUSE_LORDS = 2

# House names as the string-based APIs (Hansard overview, What's On, Bills, ...) expect them
HOUSE_NAMES = {HOUSE_COMMONS: "Commons", HOUSE_LORDS: "Lords"}

_HOUSE_ALIASES = {
    "1": HOUSE_COMMONS,
    "commons": HOUSE_COMMONS,
    "house of commons": HOUSE_COMMONS,
    "2": HOUSE_LORDS,
    "lords": HOUSE_LORDS,
    "house of lords": HOUSE_LORDS,
}


def _parse_house(house: int | str) -> int | str:
    """Map a house given as 1/2, "1"/"2" or "Commons"/"Lords" (any case) to its ID.

    "Bicameral" (used by the written questions API) comes back as the string "Bicameral".
    """
    if isinstance(house, bool):
        raise ValueError(f"Invalid house: {house!r}")
    if isinstance(house, int):
        if house in HOUSE_NAMES:
            return house
        raise ValueError(f"Invalid house: {house!r}. Use 1 (Commons) or 2 (Lords).")
    key = house.strip().lower()
    if key in _HOUSE_ALIASES:
        return _HOUSE_ALIASES[key]
    if key == "bicameral":
        return "Bicameral"
    raise ValueError(f"Invalid house: {house!r}. Use 1/'Commons' or 2/'Lords'.")


@overload
def house_id(house: int | str) -> int: ...
@overload
def house_id(house: None) -> None: ...
def house_id(house: int | str | None) -> int | None:
    """Normalise a house to its numeric ID (1 = Commons, 2 = Lords) for numeric APIs."""
    if house is None or house == "":
        return None
    parsed = _parse_house(house)
    if isinstance(parsed, str):
        raise ValueError(f"Invalid house: {house!r}. Use 1/'Commons' or 2/'Lords'.")
    return parsed


@overload
def house_name(house: int | str) -> str: ...
@overload
def house_name(house: None) -> None: ...
def house_name(house: int | str | None) -> str | None:
    """Normalise a house to its name ("Commons"/"Lords"/"Bicameral") for name-based APIs."""
    if house is None or house == "":
        return None
    parsed = _parse_house(house)
    return parsed if isinstance(parsed, str) else HOUSE_NAMES[parsed]
