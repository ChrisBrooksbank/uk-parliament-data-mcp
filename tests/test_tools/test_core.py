"""Tests for core tools (hello_parliament, goodbye_parliament)."""
from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.tools import core
from uk_parliament_mcp.tools.core import GOODBYE_PROMPT, SYSTEM_PROMPT


class TestCoreTools:
    """Tests for core session management tools."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with core tools registered."""
        server = FastMCP(name="test-server")
        core.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_hello_parliament(self, mcp: FastMCP):
        """register_tools adds hello_parliament tool."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        assert "hello_parliament" in tool_names

    @pytest.mark.asyncio
    async def test_register_tools_adds_goodbye_parliament(self, mcp: FastMCP):
        """register_tools adds goodbye_parliament tool."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        assert "goodbye_parliament" in tool_names

    @pytest.mark.asyncio
    async def test_hello_parliament_returns_system_prompt(self, mcp: FastMCP):
        """hello_parliament returns the correct system prompt."""
        # call_tool returns (content_list, raw_result)
        content_list, _ = await mcp.call_tool("hello_parliament", {})
        assert len(content_list) > 0
        text_content = content_list[0].text
        assert text_content == SYSTEM_PROMPT
        assert "parliamentary data assistant" in text_content

    @pytest.mark.asyncio
    async def test_goodbye_parliament_returns_goodbye_prompt(self, mcp: FastMCP):
        """goodbye_parliament returns the correct goodbye prompt."""
        # call_tool returns (content_list, raw_result)
        content_list, _ = await mcp.call_tool("goodbye_parliament", {})
        assert len(content_list) > 0
        text_content = content_list[0].text
        assert text_content == GOODBYE_PROMPT
        assert "normal assistant" in text_content

    @pytest.mark.asyncio
    async def test_hello_parliament_has_description(self, mcp: FastMCP):
        """hello_parliament tool has a description."""
        tools = await mcp.list_tools()
        tools_dict = {t.name: t for t in tools}
        hello_tool = tools_dict["hello_parliament"]
        assert hello_tool.description is not None
        assert len(hello_tool.description) > 0

    @pytest.mark.asyncio
    async def test_goodbye_parliament_has_description(self, mcp: FastMCP):
        """goodbye_parliament tool has a description."""
        tools = await mcp.list_tools()
        tools_dict = {t.name: t for t in tools}
        goodbye_tool = tools_dict["goodbye_parliament"]
        assert goodbye_tool.description is not None
        assert len(goodbye_tool.description) > 0


class TestSystemPromptContent:
    """Tests for system prompt content requirements."""

    def test_system_prompt_includes_mcp_instruction(self):
        """System prompt instructs to use MCP API endpoints."""
        assert "MCP" in SYSTEM_PROMPT

    def test_system_prompt_includes_url_requirement(self):
        """System prompt requires appending API URLs to responses."""
        assert "URL" in SYSTEM_PROMPT

    def test_goodbye_prompt_removes_restrictions(self):
        """Goodbye prompt removes MCP-specific restrictions."""
        assert "no special restrictions" in GOODBYE_PROMPT
