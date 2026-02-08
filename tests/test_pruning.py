"""Tests for response pruning engine."""

from __future__ import annotations

import json
from unittest.mock import patch

from uk_parliament_mcp.pruning import (
    _compute_meta,
    _flatten_value_wrappers,
    _is_value_wrapper_array,
    _strip_nulls_and_empties,
    _truncate_arrays,
    prune_response,
)


class TestStripNullsAndEmpties:
    """Tests for _strip_nulls_and_empties."""

    def test_removes_null_values(self) -> None:
        data = {"name": "Starmer", "middleName": None, "title": "Rt Hon"}
        result = _strip_nulls_and_empties(data)
        assert result == {"name": "Starmer", "title": "Rt Hon"}

    def test_removes_empty_strings(self) -> None:
        data = {"name": "Test", "notes": "", "id": 1}
        result = _strip_nulls_and_empties(data)
        assert result == {"name": "Test", "id": 1}

    def test_removes_empty_lists(self) -> None:
        data = {"name": "Test", "items": [], "id": 1}
        result = _strip_nulls_and_empties(data)
        assert result == {"name": "Test", "id": 1}

    def test_removes_empty_dicts(self) -> None:
        data = {"name": "Test", "metadata": {}, "id": 1}
        result = _strip_nulls_and_empties(data)
        assert result == {"name": "Test", "id": 1}

    def test_recursive_stripping(self) -> None:
        data = {
            "member": {
                "name": "Test",
                "notes": None,
                "party": {"name": "Labour", "color": None},
            }
        }
        result = _strip_nulls_and_empties(data)
        assert result == {"member": {"name": "Test", "party": {"name": "Labour"}}}

    def test_preserves_false_and_zero(self) -> None:
        data = {"active": False, "count": 0, "name": "Test"}
        result = _strip_nulls_and_empties(data)
        assert result == {"active": False, "count": 0, "name": "Test"}

    def test_strips_nulls_in_lists(self) -> None:
        data = [None, {"id": 1}, None, {"id": 2}]
        result = _strip_nulls_and_empties(data)
        assert result == [{"id": 1}, {"id": 2}]

    def test_leaves_non_dict_non_list_values(self) -> None:
        assert _strip_nulls_and_empties("hello") == "hello"
        assert _strip_nulls_and_empties(42) == 42
        assert _strip_nulls_and_empties(True) is True

    def test_deeply_nested_empty_removal(self) -> None:
        """After stripping inner empties, outer dicts become empty too."""
        data = {"a": {"b": {"c": None}}}
        result = _strip_nulls_and_empties(data)
        assert result == {}


class TestTruncateArrays:
    """Tests for _truncate_arrays."""

    def test_no_truncation_under_limit(self) -> None:
        data = [1, 2, 3]
        result = _truncate_arrays(data, max_size=5)
        assert result == [1, 2, 3]

    def test_truncation_at_limit(self) -> None:
        data = list(range(25))
        result = _truncate_arrays(data, max_size=20)
        assert len(result) == 21  # 20 items + 1 metadata
        assert result[-1] == {"_truncated": {"total": 25, "showing": 20}}

    def test_truncation_in_nested_dict(self) -> None:
        data = {"items": list(range(30))}
        result = _truncate_arrays(data, max_size=10)
        assert len(result["items"]) == 11  # 10 + metadata
        assert result["items"][-1]["_truncated"]["total"] == 30

    def test_recursive_truncation(self) -> None:
        data = {"outer": [{"inner": list(range(25))}]}
        result = _truncate_arrays(data, max_size=5)
        inner = result["outer"][0]["inner"]
        assert len(inner) == 6  # 5 + metadata
        assert inner[-1]["_truncated"]["total"] == 25

    def test_uses_default_max_size(self) -> None:
        data = list(range(100))
        result = _truncate_arrays(data)
        # Should use MAX_ARRAY_SIZE (default 20)
        assert result[-1]["_truncated"]["showing"] == 20

    def test_non_list_non_dict_passthrough(self) -> None:
        assert _truncate_arrays("hello", max_size=5) == "hello"
        assert _truncate_arrays(42, max_size=5) == 42


class TestFlattenValueWrappers:
    """Tests for _flatten_value_wrappers."""

    def test_flattens_value_wrapper_array(self) -> None:
        data = {
            "items": [
                {"value": {"id": 1, "name": "Alice"}},
                {"value": {"id": 2, "name": "Bob"}},
            ]
        }
        result = _flatten_value_wrappers(data)
        assert result == {"items": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]}

    def test_does_not_flatten_non_wrapper_arrays(self) -> None:
        data = {"items": [{"id": 1, "name": "Test"}, {"id": 2, "name": "Test2"}]}
        result = _flatten_value_wrappers(data)
        assert result == data

    def test_does_not_flatten_mixed_arrays(self) -> None:
        """Array where not all items have value wrappers."""
        data = [{"value": {"id": 1}}, {"id": 2, "name": "Test"}]
        result = _flatten_value_wrappers(data)
        # The second item doesn't have "value" containing a dict, so no flattening
        assert result == data

    def test_does_not_flatten_non_dict_value(self) -> None:
        """Value key exists but isn't a dict."""
        data = [{"value": "string"}, {"value": "other"}]
        result = _flatten_value_wrappers(data)
        assert result == data

    def test_recursive_flattening(self) -> None:
        data = {"outer": {"items": [{"value": {"id": 1, "nested": [{"value": {"x": 10}}]}}]}}
        result = _flatten_value_wrappers(data)
        assert result["outer"]["items"] == [{"id": 1, "nested": [{"x": 10}]}]

    def test_empty_array_not_flattened(self) -> None:
        data = {"items": []}
        result = _flatten_value_wrappers(data)
        assert result == {"items": []}

    def test_non_dict_non_list_passthrough(self) -> None:
        assert _flatten_value_wrappers("hello") == "hello"
        assert _flatten_value_wrappers(42) == 42


class TestIsValueWrapperArray:
    """Tests for _is_value_wrapper_array."""

    def test_valid_wrapper_array(self) -> None:
        arr = [{"value": {"id": 1}}, {"value": {"id": 2}}]
        assert _is_value_wrapper_array(arr) is True

    def test_empty_array(self) -> None:
        assert _is_value_wrapper_array([]) is False

    def test_non_wrapper_array(self) -> None:
        arr = [{"id": 1}, {"id": 2}]
        assert _is_value_wrapper_array(arr) is False

    def test_mixed_array(self) -> None:
        arr = [{"value": {"id": 1}}, {"id": 2}]
        assert _is_value_wrapper_array(arr) is False

    def test_non_dict_value(self) -> None:
        arr = [{"value": "string"}]
        assert _is_value_wrapper_array(arr) is False

    def test_non_dict_items_ignored(self) -> None:
        """Non-dict items in the array are ignored."""
        arr = [{"value": {"id": 1}}, "string"]
        # The string is not a dict so dict_items only has the first
        assert _is_value_wrapper_array(arr) is True


class TestComputeMeta:
    """Tests for _compute_meta."""

    def test_computes_reduction(self) -> None:
        meta = _compute_meta(1000, 250)
        assert meta["originalBytes"] == 1000
        assert meta["prunedBytes"] == 250
        assert meta["reductionPercent"] == 75

    def test_zero_original_bytes(self) -> None:
        meta = _compute_meta(0, 0)
        assert meta["reductionPercent"] == 0

    def test_no_reduction(self) -> None:
        meta = _compute_meta(100, 100)
        assert meta["reductionPercent"] == 0

    def test_rounding(self) -> None:
        meta = _compute_meta(3, 1)
        assert meta["reductionPercent"] == 67  # 66.67 -> 67


class TestPruneResponse:
    """Tests for the main prune_response function."""

    def test_prunes_full_response(self) -> None:
        response = json.dumps(
            {
                "url": "https://api.parliament.uk/test",
                "data": {
                    "items": [{"value": {"id": 1, "name": "Test", "notes": None, "extra": ""}}]
                },
            }
        )
        result = json.loads(prune_response(response))
        # Should have _meta
        assert "_meta" in result
        assert result["_meta"]["reductionPercent"] >= 0
        # Data should be pruned: nulls stripped, value flattened
        items = result["data"]["items"]
        assert items[0] == {"id": 1, "name": "Test"}

    def test_skips_error_responses(self) -> None:
        response = json.dumps(
            {"url": "https://api.parliament.uk/test", "error": "Not found", "statusCode": 404}
        )
        result = prune_response(response)
        assert result == response  # Unchanged

    def test_handles_invalid_json(self) -> None:
        result = prune_response("not json")
        assert result == "not json"

    def test_handles_non_dict_top_level(self) -> None:
        response = json.dumps([1, 2, 3])
        result = json.loads(prune_response(response))
        assert "_meta" in result
        assert "_data" in result

    @patch("uk_parliament_mcp.pruning.PRUNING_ENABLED", False)
    def test_disabled_via_env(self) -> None:
        response = json.dumps({"url": "test", "data": {"key": None}})
        result = prune_response(response)
        assert result == response  # Unchanged when disabled

    def test_truncates_large_arrays(self) -> None:
        items = [{"id": i, "name": f"Item {i}"} for i in range(50)]
        response = json.dumps({"url": "test", "data": {"items": items}})
        result = json.loads(prune_response(response))
        data_items = result["data"]["items"]
        # Should be truncated to 20 + 1 metadata entry
        assert len(data_items) == 21
        assert "_truncated" in data_items[-1]
        assert data_items[-1]["_truncated"]["total"] == 50

    def test_meta_shows_reduction(self) -> None:
        """Response with lots of nulls should show meaningful reduction."""
        data = dict.fromkeys(range(50))
        data["name"] = "Test"  # type: ignore[assignment]
        response = json.dumps({"url": "test", "data": data})
        result = json.loads(prune_response(response))
        assert result["_meta"]["reductionPercent"] > 0
