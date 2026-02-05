"""Tests for MCP Resources registration and content."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import pytest

from uk_parliament_mcp.resources import (
    _extract_data_str,
    _safe_parse_data,
    register_resources,
)


class TestSafeParseData:
    """Tests for _safe_parse_data helper."""

    def test_extracts_data_field(self) -> None:
        result = json.dumps({"url": "test", "data": {"items": [1, 2]}})
        assert _safe_parse_data(result) == {"items": [1, 2]}

    def test_returns_full_parsed_if_no_data(self) -> None:
        result = json.dumps({"items": [1, 2]})
        assert _safe_parse_data(result) == {"items": [1, 2]}

    def test_handles_invalid_json(self) -> None:
        result = _safe_parse_data("not json")
        assert result == {"error": "Failed to parse response"}

    def test_handles_list_response(self) -> None:
        result = json.dumps([{"id": 1}, {"id": 2}])
        assert _safe_parse_data(result) == [{"id": 1}, {"id": 2}]


class TestExtractDataStr:
    """Tests for _extract_data_str helper."""

    def test_returns_json_string(self) -> None:
        result = json.dumps({"url": "test", "data": {"items": [1]}})
        output = _extract_data_str(result)
        parsed = json.loads(output)
        assert parsed == {"items": [1]}


class TestResourceRegistration:
    """Tests for resource registration."""

    def test_register_resources_calls_mcp(self) -> None:
        """Verify register_resources calls mcp.resource for each resource."""
        mock_mcp = AsyncMock()
        # Make resource() return a decorator that returns the function unchanged
        mock_mcp.resource = lambda uri: lambda fn: fn
        register_resources(mock_mcp)
        # No errors means all resources registered


class TestStaticResources:
    """Tests for static resource content."""

    @pytest.fixture
    def resources(self) -> dict[str, object]:
        """Register resources and capture the functions."""
        registered: dict[str, object] = {}

        class FakeMCP:
            def resource(self, uri: str):  # type: ignore[no-untyped-def]
                def decorator(fn):  # type: ignore[no-untyped-def]
                    registered[uri] = fn
                    return fn

                return decorator

        register_resources(FakeMCP())  # type: ignore[arg-type]
        return registered

    @pytest.mark.asyncio
    async def test_conventions_resource(self, resources: dict[str, object]) -> None:
        fn = resources["parliament://conventions"]
        result = await fn()  # type: ignore[misc]
        data = json.loads(result)
        assert "houses" in data
        assert data["houses"]["1"] == "House of Commons (MPs)"
        assert "dateFormat" in data
        assert "pagination" in data

    @pytest.mark.asyncio
    async def test_houses_resource(self, resources: dict[str, object]) -> None:
        fn = resources["parliament://houses"]
        result = await fn()  # type: ignore[misc]
        data = json.loads(result)
        assert len(data["houses"]) == 2
        assert data["houses"][0]["id"] == 1
        assert data["houses"][1]["id"] == 2

    @pytest.mark.asyncio
    async def test_tools_summary_resource(self, resources: dict[str, object]) -> None:
        fn = resources["parliament://tools/summary"]
        result = await fn()  # type: ignore[misc]
        assert "Composite Tools" in result
        assert "Members" in result or "members" in result

    @pytest.mark.asyncio
    async def test_member_types_resource(self, resources: dict[str, object]) -> None:
        fn = resources["parliament://member-types"]
        result = await fn()  # type: ignore[misc]
        data = json.loads(result)
        types = data["memberTypes"]
        assert len(types) == 2
        assert types[0]["type"] == "MP"
        assert types[1]["type"] == "Lord"

    @pytest.mark.asyncio
    async def test_all_expected_uris_registered(self, resources: dict[str, object]) -> None:
        expected = [
            "parliament://conventions",
            "parliament://houses",
            "parliament://tools/summary",
            "parliament://member-types",
            "parliament://parties",
            "parliament://bill-types",
            "parliament://bill-stages",
        ]
        for uri in expected:
            assert uri in resources, f"Missing resource: {uri}"


class TestDynamicResources:
    """Tests for dynamic resources that call APIs."""

    @pytest.fixture
    def resources(self) -> dict[str, object]:
        """Register resources and capture the functions."""
        registered: dict[str, object] = {}

        class FakeMCP:
            def resource(self, uri: str):  # type: ignore[no-untyped-def]
                def decorator(fn):  # type: ignore[no-untyped-def]
                    registered[uri] = fn
                    return fn

                return decorator

        register_resources(FakeMCP())  # type: ignore[arg-type]
        return registered

    @pytest.mark.asyncio
    async def test_parties_resource(self, resources: dict[str, object]) -> None:
        mock_commons = json.dumps({"url": "test", "data": [{"id": 1, "name": "Labour"}]})
        mock_lords = json.dumps({"url": "test", "data": [{"id": 2, "name": "Conservative"}]})

        async def mock_cached(url: str, cache_key: str | None = None) -> str:
            if "GetActive/1" in url:
                return mock_commons
            return mock_lords

        with patch("uk_parliament_mcp.resources.get_result_cached", side_effect=mock_cached):
            fn = resources["parliament://parties"]
            result = await fn()  # type: ignore[misc]
            data = json.loads(result)
            assert "commons" in data
            assert "lords" in data
            assert data["commons"][0]["name"] == "Labour"

    @pytest.mark.asyncio
    async def test_bill_types_resource(self, resources: dict[str, object]) -> None:
        mock_response = json.dumps(
            {"url": "test", "data": [{"id": 1, "name": "Public Bill"}]}
        )

        async def mock_cached(url: str, cache_key: str | None = None) -> str:
            return mock_response

        with patch("uk_parliament_mcp.resources.get_result_cached", side_effect=mock_cached):
            fn = resources["parliament://bill-types"]
            result = await fn()  # type: ignore[misc]
            data = json.loads(result)
            assert data[0]["name"] == "Public Bill"

    @pytest.mark.asyncio
    async def test_bill_stages_resource(self, resources: dict[str, object]) -> None:
        mock_response = json.dumps(
            {"url": "test", "data": [{"id": 1, "name": "First Reading"}]}
        )

        async def mock_cached(url: str, cache_key: str | None = None) -> str:
            return mock_response

        with patch("uk_parliament_mcp.resources.get_result_cached", side_effect=mock_cached):
            fn = resources["parliament://bill-stages"]
            result = await fn()  # type: ignore[misc]
            data = json.loads(result)
            assert data[0]["name"] == "First Reading"
