"""Tests for core tools (hello_parliament, goodbye_parliament, parliament_guide, parliament_workflow)."""

from __future__ import annotations

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.tools import core
from uk_parliament_mcp.tools.core import (
    GOODBYE_PROMPT,
    GUIDANCE_CONTENT,
    QUICK_REFERENCE,
    SYSTEM_PROMPT,
    WORKFLOW_PATTERNS,
)


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
    async def test_register_tools_adds_parliament_guide(self, mcp: FastMCP):
        """register_tools adds parliament_guide tool."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        assert "parliament_guide" in tool_names

    @pytest.mark.asyncio
    async def test_register_tools_adds_parliament_workflow(self, mcp: FastMCP):
        """register_tools adds parliament_workflow tool."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]
        assert "parliament_workflow" in tool_names

    @pytest.mark.asyncio
    async def test_hello_parliament_returns_system_prompt_and_quick_reference(
        self, mcp: FastMCP
    ):
        """hello_parliament returns system prompt with quick reference."""
        content_list, _ = await mcp.call_tool("hello_parliament", {})
        assert len(content_list) > 0
        text_content = content_list[0].text
        # Contains both system prompt and quick reference
        assert SYSTEM_PROMPT in text_content
        assert "Quick Reference" in text_content
        assert "parliament_guide" in text_content
        assert "parliament_workflow" in text_content

    @pytest.mark.asyncio
    async def test_goodbye_parliament_returns_goodbye_prompt(self, mcp: FastMCP):
        """goodbye_parliament returns the correct goodbye prompt."""
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


class TestQuickReference:
    """Tests for quick reference content."""

    def test_quick_reference_includes_conventions(self):
        """Quick reference includes key conventions."""
        assert "House IDs" in QUICK_REFERENCE
        assert "1 = Commons" in QUICK_REFERENCE
        assert "2 = Lords" in QUICK_REFERENCE
        assert "YYYY-MM-DD" in QUICK_REFERENCE

    def test_quick_reference_includes_tool_categories(self):
        """Quick reference includes tool category table."""
        assert "members" in QUICK_REFERENCE
        assert "bills" in QUICK_REFERENCE
        assert "committees" in QUICK_REFERENCE
        assert "votes" in QUICK_REFERENCE or "commons_votes" in QUICK_REFERENCE

    def test_quick_reference_mentions_guidance_tools(self):
        """Quick reference points to parliament_guide and parliament_workflow."""
        assert "parliament_guide" in QUICK_REFERENCE
        assert "parliament_workflow" in QUICK_REFERENCE


class TestParliamentGuide:
    """Tests for parliament_guide tool."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with core tools registered."""
        server = FastMCP(name="test-server")
        core.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_guide_members_returns_content(self, mcp: FastMCP):
        """parliament_guide returns content for members topic."""
        content_list, _ = await mcp.call_tool("parliament_guide", {"topic": "members"})
        text = content_list[0].text
        assert "Members Tools" in text
        assert "search_members" in text
        assert "get_member_by_id" in text
        assert "get_member_by_name" in text

    @pytest.mark.asyncio
    async def test_guide_bills_returns_content(self, mcp: FastMCP):
        """parliament_guide returns content for bills topic."""
        content_list, _ = await mcp.call_tool("parliament_guide", {"topic": "bills"})
        text = content_list[0].text
        assert "Bills Tools" in text
        assert "search_bills" in text
        assert "get_bill_stages" in text

    @pytest.mark.asyncio
    async def test_guide_votes_returns_content(self, mcp: FastMCP):
        """parliament_guide returns content for votes topic."""
        content_list, _ = await mcp.call_tool("parliament_guide", {"topic": "votes"})
        text = content_list[0].text
        assert "Voting Tools" in text
        assert "search_commons_divisions" in text
        assert "search_lords_divisions" in text

    @pytest.mark.asyncio
    async def test_guide_all_returns_comprehensive_list(self, mcp: FastMCP):
        """parliament_guide with 'all' returns comprehensive tool list."""
        content_list, _ = await mcp.call_tool("parliament_guide", {"topic": "all"})
        text = content_list[0].text
        assert "86 tools" in text
        assert "Members" in text
        assert "Bills" in text
        assert "Votes" in text
        assert "Committees" in text

    @pytest.mark.asyncio
    async def test_guide_conventions_returns_content(self, mcp: FastMCP):
        """parliament_guide returns conventions documentation."""
        content_list, _ = await mcp.call_tool(
            "parliament_guide", {"topic": "conventions"}
        )
        text = content_list[0].text
        assert "House 1" in text
        assert "House 2" in text
        assert "YYYY-MM-DD" in text
        assert "skip" in text
        assert "take" in text

    @pytest.mark.asyncio
    async def test_guide_invalid_topic_returns_error(self, mcp: FastMCP):
        """parliament_guide returns error for invalid topic."""
        content_list, _ = await mcp.call_tool(
            "parliament_guide", {"topic": "invalid_topic"}
        )
        text = content_list[0].text
        assert "not recognized" in text
        assert "Available topics" in text

    @pytest.mark.asyncio
    async def test_guide_case_insensitive(self, mcp: FastMCP):
        """parliament_guide handles case-insensitive topic names."""
        content_list, _ = await mcp.call_tool("parliament_guide", {"topic": "MEMBERS"})
        text = content_list[0].text
        assert "Members Tools" in text

    @pytest.mark.asyncio
    async def test_guide_has_description(self, mcp: FastMCP):
        """parliament_guide tool has a description."""
        tools = await mcp.list_tools()
        tools_dict = {t.name: t for t in tools}
        guide_tool = tools_dict["parliament_guide"]
        assert guide_tool.description is not None
        assert "guidance" in guide_tool.description.lower()


class TestParliamentWorkflow:
    """Tests for parliament_workflow tool."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with core tools registered."""
        server = FastMCP(name="test-server")
        core.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_workflow_voting_query(self, mcp: FastMCP):
        """parliament_workflow returns voting workflow for vote-related queries."""
        content_list, _ = await mcp.call_tool(
            "parliament_workflow", {"query": "How did my MP vote on climate?"}
        )
        text = content_list[0].text
        assert "Workflow" in text
        assert "get_member_by_name" in text
        assert "division" in text.lower()

    @pytest.mark.asyncio
    async def test_workflow_bill_tracking(self, mcp: FastMCP):
        """parliament_workflow returns bill workflow for legislation queries."""
        content_list, _ = await mcp.call_tool(
            "parliament_workflow", {"query": "Track the progress of the Online Safety Bill"}
        )
        text = content_list[0].text
        assert "Workflow" in text
        assert "search_bills" in text
        assert "get_bill_stages" in text

    @pytest.mark.asyncio
    async def test_workflow_committee_research(self, mcp: FastMCP):
        """parliament_workflow returns committee workflow for inquiry queries."""
        content_list, _ = await mcp.call_tool(
            "parliament_workflow", {"query": "What committee examined NHS funding?"}
        )
        text = content_list[0].text
        assert "Workflow" in text
        assert "search_committees" in text
        assert "evidence" in text.lower()

    @pytest.mark.asyncio
    async def test_workflow_interests_research(self, mcp: FastMCP):
        """parliament_workflow returns interests workflow for conflict queries."""
        content_list, _ = await mcp.call_tool(
            "parliament_workflow", {"query": "Does this MP have financial interests?"}
        )
        text = content_list[0].text
        assert "Workflow" in text
        assert "search_roi" in text

    @pytest.mark.asyncio
    async def test_workflow_live_activity(self, mcp: FastMCP):
        """parliament_workflow returns live workflow for current activity queries."""
        content_list, _ = await mcp.call_tool(
            "parliament_workflow", {"query": "What's happening in Parliament now?"}
        )
        text = content_list[0].text
        assert "Workflow" in text
        assert "happening_now" in text

    @pytest.mark.asyncio
    async def test_workflow_general_fallback(self, mcp: FastMCP):
        """parliament_workflow returns general approach for unmatched queries."""
        content_list, _ = await mcp.call_tool(
            "parliament_workflow", {"query": "Something completely unrelated xyz123"}
        )
        text = content_list[0].text
        assert "Research Approach" in text
        assert "parliament_guide" in text

    @pytest.mark.asyncio
    async def test_workflow_has_description(self, mcp: FastMCP):
        """parliament_workflow tool has a description."""
        tools = await mcp.list_tools()
        tools_dict = {t.name: t for t in tools}
        workflow_tool = tools_dict["parliament_workflow"]
        assert workflow_tool.description is not None
        assert "workflow" in workflow_tool.description.lower()


class TestGuidanceContent:
    """Tests for guidance content completeness."""

    def test_all_topics_have_content(self):
        """All documented topics have content."""
        expected_topics = [
            "members",
            "bills",
            "votes",
            "committees",
            "hansard",
            "questions",
            "interests",
            "live",
            "legislation",
            "procedures",
            "all",
            "conventions",
            "workflows",
        ]
        for topic in expected_topics:
            assert topic in GUIDANCE_CONTENT, f"Missing topic: {topic}"
            assert len(GUIDANCE_CONTENT[topic]) > 0, f"Empty content for: {topic}"

    def test_workflow_patterns_have_required_fields(self):
        """All workflow patterns have required fields."""
        for pattern in WORKFLOW_PATTERNS:
            assert "keywords" in pattern, "Pattern missing keywords"
            assert "name" in pattern, "Pattern missing name"
            assert "description" in pattern, "Pattern missing description"
            assert "steps" in pattern, "Pattern missing steps"
            assert len(pattern["keywords"]) > 0, "Pattern has empty keywords"
            assert len(pattern["steps"]) > 0, "Pattern has empty steps"

    def test_workflow_steps_have_required_fields(self):
        """All workflow steps have required fields."""
        for pattern in WORKFLOW_PATTERNS:
            for step in pattern["steps"]:
                assert "step" in step, f"Step missing step number in {pattern['name']}"
                assert "tool" in step, f"Step missing tool in {pattern['name']}"
                assert "purpose" in step, f"Step missing purpose in {pattern['name']}"
                assert "output" in step, f"Step missing output in {pattern['name']}"
