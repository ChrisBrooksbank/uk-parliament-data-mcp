"""Response pruning engine for optimizing Parliament API responses.

Strips nulls, empties, truncates large arrays, flattens value wrappers,
and adds metadata about the pruning. This reduces token usage when responses
are consumed by AI assistants via MCP.
"""

from __future__ import annotations

import json
import os
from typing import Any

# Configuration via environment variables
PRUNING_ENABLED = os.environ.get("PARLIAMENT_PRUNING", "true").lower() != "false"
MAX_ARRAY_SIZE = int(os.environ.get("PARLIAMENT_MAX_ARRAY", "20"))

# Runtime override — set to True to disable pruning (used by CLI)
_force_disabled = False


def is_pruning_enabled() -> bool:
    """Check if pruning is enabled, respecting runtime overrides."""
    return PRUNING_ENABLED and not _force_disabled


def disable_pruning() -> None:
    """Disable pruning at runtime (e.g. for CLI usage)."""
    global _force_disabled  # noqa: PLW0603
    _force_disabled = True


def prune_response(response_str: str) -> str:
    """Prune a JSON response string to reduce size.

    Skips pruning for error responses (those containing an "error" key).

    Args:
        response_str: JSON string from Parliament API.

    Returns:
        Pruned JSON string with _meta stats, or original if pruning disabled/errors.
    """
    if not PRUNING_ENABLED:
        return response_str

    try:
        parsed = json.loads(response_str)
    except (json.JSONDecodeError, TypeError):
        return response_str

    # Skip error responses
    if isinstance(parsed, dict) and "error" in parsed:
        return response_str

    original_bytes = len(response_str.encode("utf-8"))

    # Apply pruning to the data field only (preserve url/data wrapper structure)
    if isinstance(parsed, dict) and "data" in parsed:
        pruned_data = _strip_nulls_and_empties(parsed["data"])
        pruned_data = _flatten_value_wrappers(pruned_data)
        pruned_data = _truncate_arrays(pruned_data)
        pruned = dict(parsed.items())
        pruned["data"] = pruned_data
    else:
        pruned = _strip_nulls_and_empties(parsed)
        pruned = _flatten_value_wrappers(pruned)
        pruned = _truncate_arrays(pruned)

    # Add meta stats
    pruned_str = json.dumps(pruned, ensure_ascii=False)
    pruned_bytes = len(pruned_str.encode("utf-8"))
    meta = _compute_meta(original_bytes, pruned_bytes)

    # Re-serialize with meta
    if isinstance(pruned, dict):
        pruned["_meta"] = meta
    else:
        pruned = {"_data": pruned, "_meta": meta}

    return json.dumps(pruned, ensure_ascii=False)


def _strip_nulls_and_empties(obj: Any) -> Any:
    """Recursively remove keys with null, empty string, empty list, or empty dict values.

    Args:
        obj: Any JSON-compatible value.

    Returns:
        Cleaned value with nulls and empties removed.
    """
    if isinstance(obj, dict):
        cleaned = {}
        for key, value in obj.items():
            stripped = _strip_nulls_and_empties(value)
            if stripped is not None and stripped != "" and stripped != [] and stripped != {}:
                cleaned[key] = stripped
        return cleaned
    elif isinstance(obj, list):
        return [_strip_nulls_and_empties(item) for item in obj if item is not None]
    else:
        return obj


def _truncate_arrays(obj: Any, max_size: int | None = None) -> Any:
    """Recursively truncate arrays exceeding max_size.

    Truncated arrays get a trailing metadata dict:
    ``{"_truncated": {"total": N, "showing": max_size}}``

    Args:
        obj: Any JSON-compatible value.
        max_size: Maximum array size before truncation. Defaults to MAX_ARRAY_SIZE.

    Returns:
        Value with large arrays truncated.
    """
    if max_size is None:
        max_size = MAX_ARRAY_SIZE

    if isinstance(obj, dict):
        return {k: _truncate_arrays(v, max_size) for k, v in obj.items()}
    elif isinstance(obj, list):
        # Recurse into each element first
        processed = [_truncate_arrays(item, max_size) for item in obj]
        if len(processed) > max_size:
            truncated = processed[:max_size]
            truncated.append({"_truncated": {"total": len(processed), "showing": max_size}})
            return truncated
        return processed
    else:
        return obj


def _flatten_value_wrappers(obj: Any) -> Any:
    """Flatten ``[{"value": {...}}]`` patterns common in the Members API.

    Only applies to arrays where every dict element has a single "value" key
    containing a dict. This avoids incorrectly flattening other structures.

    Args:
        obj: Any JSON-compatible value.

    Returns:
        Value with value-wrapper arrays flattened.
    """
    if isinstance(obj, dict):
        return {k: _flatten_value_wrappers(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        # Check if this is a value-wrapper array
        if _is_value_wrapper_array(obj):
            return [_flatten_value_wrappers(item["value"]) for item in obj]
        # Otherwise just recurse
        return [_flatten_value_wrappers(item) for item in obj]
    else:
        return obj


def _is_value_wrapper_array(arr: list[Any]) -> bool:
    """Check if an array follows the value-wrapper pattern.

    Returns True if every dict element in the array has a "value" key
    whose value is a dict.

    Args:
        arr: List to check.

    Returns:
        True if this is a value-wrapper array.
    """
    if not arr:
        return False
    dict_items = [item for item in arr if isinstance(item, dict)]
    if not dict_items:
        return False
    return all("value" in item and isinstance(item["value"], dict) for item in dict_items)


def _compute_meta(original_bytes: int, pruned_bytes: int) -> dict[str, int]:
    """Compute pruning metadata.

    Args:
        original_bytes: Size of original response in bytes.
        pruned_bytes: Size of pruned response in bytes.

    Returns:
        Dict with originalBytes, prunedBytes, reductionPercent.
    """
    reduction = 0 if original_bytes == 0 else round((1 - pruned_bytes / original_bytes) * 100)
    return {
        "originalBytes": original_bytes,
        "prunedBytes": pruned_bytes,
        "reductionPercent": reduction,
    }
