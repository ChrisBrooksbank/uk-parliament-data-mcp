"""Auto-pagination for CLI commands that request more items than a single API page."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from uk_parliament_mcp.http_client import get_result

logger = logging.getLogger(__name__)

# Safety cap: never fetch more than 1000 items total
MAX_TOTAL_ITEMS = 1000


@dataclass(frozen=True)
class PaginationConfig:
    """Per-API pagination configuration.

    Different Parliament APIs use different parameter names and response keys.
    """

    skip_param: str  # e.g. "skip", "Skip", "queryParameters.skip"
    take_param: str  # e.g. "take", "Take", "queryParameters.take"
    items_key: str  # e.g. "items", "Results", "results"
    total_key: str  # e.g. "totalResults", "TotalResults"
    default_page_size: int  # e.g. 20, 25, 30


# Pre-defined configs for each API
MEMBERS_PAGINATION = PaginationConfig(
    skip_param="skip",
    take_param="take",
    items_key="items",
    total_key="totalResults",
    default_page_size=20,
)

BILLS_PAGINATION = PaginationConfig(
    skip_param="Skip",
    take_param="Take",
    items_key="items",
    total_key="totalResults",
    default_page_size=20,
)

COMMITTEES_PAGINATION = PaginationConfig(
    skip_param="Skip",
    take_param="Take",
    items_key="items",
    total_key="totalResults",
    default_page_size=30,
)

HANSARD_PAGINATION = PaginationConfig(
    skip_param="queryParameters.skip",
    take_param="queryParameters.take",
    items_key="Results",
    total_key="TotalResults",
    default_page_size=20,
)

HANSARD_MEMBER_SUMMARY_PAGINATION = PaginationConfig(
    skip_param="skip",
    take_param="take",
    items_key="Results",
    total_key="TotalResults",
    default_page_size=20,
)

WRITTEN_QUESTIONS_PAGINATION = PaginationConfig(
    skip_param="skip",
    take_param="take",
    items_key="results",
    total_key="totalResults",
    default_page_size=20,
)

ORAL_QUESTIONS_PAGINATION = PaginationConfig(
    skip_param="parameters.skip",
    take_param="parameters.take",
    items_key="Response",
    total_key="PagingInfo.Total",
    default_page_size=25,
)

LORDS_VOTES_PAGINATION = PaginationConfig(
    skip_param="skip",
    take_param="take",
    items_key="results",
    total_key="totalResults",
    default_page_size=25,
)

TREATIES_PAGINATION = PaginationConfig(
    skip_param="Skip",
    take_param="Take",
    items_key="items",
    total_key="totalResults",
    default_page_size=20,
)

ERSKINE_MAY_PAGINATION = PaginationConfig(
    skip_param="skip",
    take_param="take",
    items_key="items",
    total_key="totalResults",
    default_page_size=30,
)

DAILY_REPORTS_PAGINATION = PaginationConfig(
    skip_param="skip",
    take_param="take",
    items_key="results",
    total_key="totalResults",
    default_page_size=20,
)

WRITTEN_STATEMENTS_PAGINATION = PaginationConfig(
    skip_param="skip",
    take_param="take",
    items_key="results",
    total_key="totalResults",
    default_page_size=20,
)


def _replace_url_param(url: str, param_name: str, value: int) -> str:
    """Replace or add a query parameter in a URL.

    Args:
        url: The full URL with query string.
        param_name: The parameter name to replace (e.g. "skip", "queryParameters.skip").
        value: The new integer value.

    Returns:
        URL with the parameter updated.
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    # parse_qs returns lists; set single value
    params[param_name] = [str(value)]
    # Flatten lists back to single values for urlencode
    flat: dict[str, str] = {}
    for k, v_list in params.items():
        flat[k] = v_list[0]
    new_query = urlencode(flat)
    return urlunparse(parsed._replace(query=new_query))


def _get_nested(data: dict[str, Any], dotted_key: str) -> Any:
    """Get a value from a nested dict using dot notation."""
    keys = dotted_key.split(".")
    value: Any = data
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None
    return value


async def paginate_request(
    url: str,
    config: PaginationConfig,
    desired_total: int | None = None,
    start_skip: int = 0,
) -> str:
    """Make paginated requests, stitching results into a single response.

    If ``desired_total`` is within the API's default page size, this is a
    simple pass-through to ``get_result``.  Otherwise it fetches multiple
    pages sequentially and merges the item arrays.

    Args:
        url: The fully built URL (with skip/take already set for page 1).
        config: Pagination configuration for this API.
        desired_total: Total number of items the user wants (from --take).
            If None or <= page size, a single request is made.
        start_skip: The starting skip offset (from --skip).

    Returns:
        JSON string in standard ``{"url": "...", "data": {...}}`` format.
    """
    # Apply safety cap
    if desired_total is not None:
        desired_total = min(desired_total, MAX_TOTAL_ITEMS)

    # If desired_total fits in a single page, just pass through
    if desired_total is None or desired_total <= config.default_page_size:
        return await get_result(url)

    # --- Multi-page fetch ---
    # First request: use the page size as take, keeping user's skip
    page_size = config.default_page_size
    first_url = _replace_url_param(url, config.take_param, page_size)
    first_url = _replace_url_param(first_url, config.skip_param, start_skip)

    first_result_str = await get_result(first_url)
    first_parsed = json.loads(first_result_str)

    # If error, return as-is
    if "error" in first_parsed:
        return first_result_str

    first_data = first_parsed.get("data", {})
    if isinstance(first_data, str):
        first_data = json.loads(first_data)

    # Extract items and total from first response
    items = _get_nested(first_data, config.items_key)
    if items is None:
        items = []
    total_available = _get_nested(first_data, config.total_key)
    if total_available is None:
        total_available = len(items)

    # If first page returned nothing or we already have enough, return
    if not items or len(items) >= desired_total:
        # Trim to desired_total if we got more
        if items and len(items) > desired_total:
            _set_nested(first_data, config.items_key, items[:desired_total])
        return json.dumps({"url": first_parsed["url"], "data": first_data})

    # Calculate how many more items to fetch
    target = min(desired_total, total_available)
    all_items = list(items)

    current_skip = start_skip + page_size
    while len(all_items) < target:
        remaining = target - len(all_items)
        next_take = min(page_size, remaining)

        next_url = _replace_url_param(url, config.skip_param, current_skip)
        next_url = _replace_url_param(next_url, config.take_param, next_take)

        try:
            next_result_str = await get_result(next_url)
            next_parsed = json.loads(next_result_str)

            if "error" in next_parsed:
                logger.warning("Error on page at skip=%d, stopping pagination", current_skip)
                break

            next_data = next_parsed.get("data", {})
            if isinstance(next_data, str):
                next_data = json.loads(next_data)

            next_items = _get_nested(next_data, config.items_key)
            if not next_items:
                break  # No more items

            all_items.extend(next_items)
            current_skip += len(next_items)

        except Exception:
            logger.warning("Exception during pagination at skip=%d, stopping", current_skip)
            break

    # Trim to exact desired_total
    all_items = all_items[:target]

    # Build merged response
    _set_nested(first_data, config.items_key, all_items)
    return json.dumps({"url": first_parsed["url"], "data": first_data})


def _set_nested(data: dict[str, Any], dotted_key: str, value: Any) -> None:
    """Set a value in a nested dict using dot notation."""
    keys = dotted_key.split(".")
    obj = data
    for key in keys[:-1]:
        if isinstance(obj, dict):
            obj = obj.get(key, {})
        else:
            return
    if isinstance(obj, dict):
        obj[keys[-1]] = value
