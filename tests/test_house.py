"""Tests for house normalisation: every tool accepts 1/2 or 'Commons'/'Lords'."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from uk_parliament_mcp.config import house_id, house_name
from uk_parliament_mcp.server import create_server
from uk_parliament_mcp.tools import hansard, whatson


class TestHouseId:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (1, 1),
            (2, 2),
            ("1", 1),
            ("2", 2),
            ("Commons", 1),
            ("lords", 2),
            ("LORDS", 2),
            (" House of Commons ", 1),
            ("house of lords", 2),
            (None, None),
            ("", None),
        ],
    )
    def test_valid(self, value: int | str | None, expected: int | None) -> None:
        assert house_id(value) == expected

    @pytest.mark.parametrize("value", [0, 3, "Senate", "Bicameral", True])
    def test_invalid(self, value: int | str) -> None:
        with pytest.raises(ValueError, match="Invalid house"):
            house_id(value)


class TestHouseName:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (1, "Commons"),
            (2, "Lords"),
            ("1", "Commons"),
            ("commons", "Commons"),
            ("Lords", "Lords"),
            ("bicameral", "Bicameral"),
            (None, None),
            ("", None),
        ],
    )
    def test_valid(self, value: int | str | None, expected: str | None) -> None:
        assert house_name(value) == expected

    @pytest.mark.parametrize("value", [3, "Senate"])
    def test_invalid(self, value: int | str) -> None:
        with pytest.raises(ValueError, match="Invalid house"):
            house_name(value)


class TestToolsAcceptEitherForm:
    @pytest.mark.asyncio
    async def test_numeric_api_accepts_name(self) -> None:
        """A tool for a numeric-house API turns 'Lords' into 2."""
        with patch("uk_parliament_mcp.tools.hansard.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'
            mcp = FastMCP(name="test")
            hansard.register_tools(mcp)
            await mcp.call_tool(
                "search_hansard",
                {
                    "house": "Lords",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "search_term": "x",
                },
            )
            assert "queryParameters.house=2" in mock.call_args[0][0]

    @pytest.mark.asyncio
    async def test_name_api_accepts_number(self) -> None:
        """A tool for a name-based API turns 1 into 'Commons'."""
        with patch("uk_parliament_mcp.tools.whatson.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'
            mcp = FastMCP(name="test")
            whatson.register_tools(mcp)
            await mcp.call_tool(
                "get_next_sitting_date", {"house": 1, "date_to_check": "2024-01-01"}
            )
            assert "/proceduraldates/Commons/" in mock.call_args[0][0]

    @pytest.mark.asyncio
    async def test_invalid_house_is_a_tool_error(self) -> None:
        mcp = FastMCP(name="test")
        hansard.register_tools(mcp)
        with pytest.raises(ToolError, match="Invalid house"):
            await mcp.call_tool(
                "search_hansard",
                {
                    "house": "Senate",
                    "start_date": "2024-01-01",
                    "end_date": "2024-01-31",
                    "search_term": "x",
                },
            )

    @pytest.mark.asyncio
    async def test_every_house_parameter_accepts_int_and_str(self) -> None:
        """No tool is left taking only one form of house."""
        tools = await create_server().list_tools()
        checked = 0
        for tool in tools:
            props = tool.inputSchema.get("properties", {})
            for name in ("house", "was_member_of_house"):
                if name not in props:
                    continue
                checked += 1
                schema = props[name]
                types = {s.get("type") for s in schema.get("anyOf", [schema])}
                assert {"integer", "string"} <= types, f"{tool.name}.{name}: {schema}"
        assert checked > 30
