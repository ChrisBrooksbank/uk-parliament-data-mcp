"""Tests for composite tools that combine multiple API calls."""

from __future__ import annotations

import json

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.tools import composite


class TestCompositeToolsRegistration:
    """Tests for composite tools registration."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with composite tools registered."""
        server = FastMCP(name="test-server")
        composite.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_get_mp_profile(self, mcp: FastMCP):
        """register_tools adds get_mp_profile tool."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        assert "get_mp_profile" in tool_names

    @pytest.mark.asyncio
    async def test_register_tools_adds_check_mp_vote(self, mcp: FastMCP):
        """register_tools adds check_mp_vote tool."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        assert "check_mp_vote" in tool_names

    @pytest.mark.asyncio
    async def test_register_tools_adds_get_bill_overview(self, mcp: FastMCP):
        """register_tools adds get_bill_overview tool."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        assert "get_bill_overview" in tool_names

    @pytest.mark.asyncio
    async def test_register_tools_adds_get_committee_summary(self, mcp: FastMCP):
        """register_tools adds get_committee_summary tool."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        assert "get_committee_summary" in tool_names

    @pytest.mark.asyncio
    async def test_all_composite_tools_have_descriptions(self, mcp: FastMCP):
        """All composite tools have descriptions."""
        tools = await mcp.list_tools()
        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 0


class TestHelperFunctions:
    """Tests for composite module helper functions."""

    def test_parse_response_valid_json(self):
        """_parse_response handles valid JSON response."""
        response = json.dumps({"url": "test", "data": '{"items": []}'})
        result = composite._parse_response(response)
        assert result == {"items": []}

    def test_parse_response_direct_data(self):
        """_parse_response handles direct data dict."""
        response = json.dumps({"url": "test", "data": {"items": []}})
        result = composite._parse_response(response)
        assert result == {"items": []}

    def test_parse_response_no_data_key(self):
        """_parse_response handles response without data key."""
        response = json.dumps({"items": [], "totalResults": 0})
        result = composite._parse_response(response)
        assert result == {"items": [], "totalResults": 0}

    def test_parse_response_invalid_json(self):
        """_parse_response handles invalid JSON."""
        result = composite._parse_response("not json")
        assert "error" in result

    def test_extract_member_id_valid(self):
        """_extract_member_id extracts ID from valid response."""
        member_response = {
            "items": [
                {
                    "value": {
                        "id": 4514,
                        "nameDisplayAs": "Keir Starmer"
                    }
                }
            ]
        }
        result = composite._extract_member_id(member_response)
        assert result == 4514

    def test_extract_member_id_empty_items(self):
        """_extract_member_id returns None for empty items."""
        member_response = {"items": []}
        result = composite._extract_member_id(member_response)
        assert result is None

    def test_extract_member_id_missing_value(self):
        """_extract_member_id returns None for missing value."""
        member_response = {"items": [{}]}
        result = composite._extract_member_id(member_response)
        assert result is None


class TestGetMpProfile:
    """Tests for get_mp_profile tool."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with composite tools registered."""
        server = FastMCP(name="test-server")
        composite.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_get_mp_profile_has_required_parameters(self, mcp: FastMCP):
        """get_mp_profile has required member_id parameter."""
        tools = await mcp.list_tools()
        mp_profile_tool = next(t for t in tools if t.name == "get_mp_profile")
        assert mp_profile_tool.inputSchema is not None
        schema = mp_profile_tool.inputSchema
        assert "member_id" in schema.get("required", [])


class TestCheckMpVote:
    """Tests for check_mp_vote tool."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with composite tools registered."""
        server = FastMCP(name="test-server")
        composite.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_check_mp_vote_has_required_parameters(self, mcp: FastMCP):
        """check_mp_vote has required member_id and topic parameters."""
        tools = await mcp.list_tools()
        vote_tool = next(t for t in tools if t.name == "check_mp_vote")
        assert vote_tool.inputSchema is not None
        schema = vote_tool.inputSchema
        required = schema.get("required", [])
        assert "member_id" in required
        assert "topic" in required


class TestGetBillOverview:
    """Tests for get_bill_overview tool."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with composite tools registered."""
        server = FastMCP(name="test-server")
        composite.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_get_bill_overview_has_required_parameters(self, mcp: FastMCP):
        """get_bill_overview has required search_term parameter."""
        tools = await mcp.list_tools()
        bill_tool = next(t for t in tools if t.name == "get_bill_overview")
        assert bill_tool.inputSchema is not None
        schema = bill_tool.inputSchema
        assert "search_term" in schema.get("required", [])


class TestGetCommitteeSummary:
    """Tests for get_committee_summary tool."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with composite tools registered."""
        server = FastMCP(name="test-server")
        composite.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_get_committee_summary_has_required_parameters(self, mcp: FastMCP):
        """get_committee_summary has required topic parameter."""
        tools = await mcp.list_tools()
        committee_tool = next(t for t in tools if t.name == "get_committee_summary")
        assert committee_tool.inputSchema is not None
        schema = committee_tool.inputSchema
        assert "topic" in schema.get("required", [])


class TestCompositeGuidance:
    """Tests for composite tools in guidance content."""

    def test_composite_topic_exists_in_guidance(self):
        """Composite topic exists in GUIDANCE_CONTENT."""
        from uk_parliament_mcp.tools.core import GUIDANCE_CONTENT
        assert "composite" in GUIDANCE_CONTENT

    def test_composite_guidance_mentions_all_tools(self):
        """Composite guidance mentions all 4 composite tools."""
        from uk_parliament_mcp.tools.core import GUIDANCE_CONTENT
        guidance = GUIDANCE_CONTENT["composite"]
        assert "get_mp_profile" in guidance
        assert "check_mp_vote" in guidance
        assert "get_bill_overview" in guidance
        assert "get_committee_summary" in guidance

    def test_quick_reference_mentions_composite(self):
        """Quick reference mentions composite tools."""
        from uk_parliament_mcp.tools.core import QUICK_REFERENCE
        assert "composite" in QUICK_REFERENCE.lower()
        assert "get_mp_profile" in QUICK_REFERENCE
