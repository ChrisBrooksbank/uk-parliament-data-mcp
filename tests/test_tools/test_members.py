"""Tests for members tools."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.config import MEMBERS_API_BASE
from uk_parliament_mcp.tools import members


class TestMembersToolsRegistration:
    """Tests for members tools registration."""

    @pytest.fixture
    def mcp(self):
        """Create a FastMCP instance with members tools registered."""
        server = FastMCP(name="test-server")
        members.register_tools(server)
        return server

    @pytest.mark.asyncio
    async def test_register_tools_adds_all_24_tools(self, mcp: FastMCP):
        """register_tools adds all 24 member tools."""
        tools = await mcp.list_tools()
        tool_names = [t.name for t in tools]

        expected_tools = [
            "get_member_by_name",
            "get_answering_bodies",
            "get_member_by_id",
            "edms_for_member_id",
            "parties_list_by_house",
            "get_departments",
            "get_contributions",
            "get_constituencies",
            "get_election_results_for_constituency",
            "get_lords_interests_staff",
            "get_members_biography",
            "get_members_contact",
            "search_members",
            "get_member_experience",
            "get_member_focus",
            "get_member_registered_interests",
            "get_member_staff",
            "get_member_synopsis",
            "get_member_voting",
            "get_member_written_questions",
            "get_members_history",
            "get_member_latest_election_result",
            "get_member_portrait_url",
            "get_member_thumbnail_url",
        ]

        for tool_name in expected_tools:
            assert tool_name in tool_names

    @pytest.mark.asyncio
    async def test_all_members_tools_have_descriptions(self, mcp: FastMCP):
        """All members tools have descriptions."""
        tools = await mcp.list_tools()
        for tool in tools:
            assert tool.description is not None
            assert len(tool.description) > 0


class TestGetMemberByName:
    """Tests for get_member_by_name tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_member_by_name builds correct URL."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)
            tools_list = await mcp.list_tools()
            tool = next(t for t in tools_list if t.name == "get_member_by_name")

            await mcp.call_tool(tool.name, {"name": "Boris Johnson"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Members/Search?Name=Boris%20Johnson"

    @pytest.mark.asyncio
    async def test_url_encodes_special_characters(self):
        """get_member_by_name URL-encodes special characters."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_member_by_name", {"name": "O'Brien"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "O%27Brien" in call_url


class TestGetAnsweringBodies:
    """Tests for get_answering_bodies tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_answering_bodies builds correct URL."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_answering_bodies", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Reference/AnsweringBodies"


class TestGetMemberById:
    """Tests for get_member_by_id tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_member_by_id builds correct URL."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_member_by_id", {"member_id": 1423})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Members/1423"


class TestEdmsForMemberId:
    """Tests for edms_for_member_id tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """edms_for_member_id builds correct URL."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("edms_for_member_id", {"member_id": 4514})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Members/4514/Edms"


class TestPartiesListByHouse:
    """Tests for parties_list_by_house tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url_commons(self):
        """parties_list_by_house builds correct URL for Commons."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("parties_list_by_house", {"house": 1})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Parties/GetActive/1"

    @pytest.mark.asyncio
    async def test_builds_correct_url_lords(self):
        """parties_list_by_house builds correct URL for Lords."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("parties_list_by_house", {"house": 2})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Parties/GetActive/2"


class TestGetDepartments:
    """Tests for get_departments tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_departments builds correct URL."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_departments", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Reference/Departments"


class TestGetContributions:
    """Tests for get_contributions tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_contributions builds correct URL."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_contributions", {"member_id": 4514})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Members/4514/ContributionSummary?page=1"


class TestGetConstituencies:
    """Tests for get_constituencies tool."""

    @pytest.mark.asyncio
    async def test_builds_url_without_params(self):
        """get_constituencies builds URL without optional params."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_constituencies", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Location/Constituency/Search"

    @pytest.mark.asyncio
    async def test_builds_url_with_pagination(self):
        """get_constituencies builds URL with skip and take params."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_constituencies", {"skip": 20, "take": 50})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "skip=20" in call_url
            assert "take=50" in call_url


class TestGetElectionResultsForConstituency:
    """Tests for get_election_results_for_constituency tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_election_results_for_constituency builds correct URL."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_election_results_for_constituency", {"constituency_id": 143924})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Location/Constituency/143924/ElectionResults"


class TestGetLordsInterestsStaff:
    """Tests for get_lords_interests_staff tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_default_search(self):
        """get_lords_interests_staff builds URL with default search term."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_lords_interests_staff", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/LordsInterests/Staff?searchTerm=richard"

    @pytest.mark.asyncio
    async def test_builds_url_with_custom_search(self):
        """get_lords_interests_staff builds URL with custom search term."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_lords_interests_staff", {"search_term": "Smith"})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "searchTerm=Smith" in call_url


class TestGetMembersBiography:
    """Tests for get_members_biography tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_members_biography builds correct URL."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_members_biography", {"member_id": 4514})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Members/4514/Biography"


class TestGetMembersContact:
    """Tests for get_members_contact tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_members_contact builds correct URL."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_members_contact", {"member_id": 4514})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Members/4514/Contact"


class TestSearchMembers:
    """Tests for search_members tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_minimal_params(self):
        """search_members builds URL with default skip and take."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("search_members", {})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{MEMBERS_API_BASE}/Members/Search" in call_url
            assert "skip=0" in call_url
            assert "take=20" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_name_filter(self):
        """search_members builds URL with name filter."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("search_members", {"name": "Smith", "skip": 0, "take": 20})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "Name=Smith" in call_url

    @pytest.mark.asyncio
    async def test_filters_none_values(self):
        """search_members filters out None parameter values."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("search_members", {"name": "Test", "location": None, "skip": 0, "take": 20})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "Name=Test" in call_url
            assert "Location" not in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_all_params(self):
        """search_members builds URL with multiple filter parameters."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool(
                "search_members",
                {
                    "name": "Smith",
                    "house": 1,
                    "gender": "M",
                    "is_current_member": True,
                    "skip": 10,
                    "take": 50,
                },
            )

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "Name=Smith" in call_url
            assert "House=1" in call_url
            assert "Gender=M" in call_url
            assert "IsCurrentMember=true" in call_url
            assert "skip=10" in call_url
            assert "take=50" in call_url


class TestGetMemberExperience:
    """Tests for get_member_experience tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_member_experience builds correct URL."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_member_experience", {"member_id": 4514})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Members/4514/Experience"


class TestGetMemberFocus:
    """Tests for get_member_focus tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_member_focus builds correct URL."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_member_focus", {"member_id": 4514})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Members/4514/Focus"


class TestGetMemberRegisteredInterests:
    """Tests for get_member_registered_interests tool."""

    @pytest.mark.asyncio
    async def test_builds_url_without_house(self):
        """get_member_registered_interests builds URL without house param."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_member_registered_interests", {"member_id": 4514})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{MEMBERS_API_BASE}/Members/4514/RegisteredInterests" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_house(self):
        """get_member_registered_interests builds URL with house param."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_member_registered_interests", {"member_id": 4514, "house": 1})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "house=1" in call_url


class TestGetMemberStaff:
    """Tests for get_member_staff tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_member_staff builds correct URL."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_member_staff", {"member_id": 4514})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Members/4514/Staff"


class TestGetMemberSynopsis:
    """Tests for get_member_synopsis tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_member_synopsis builds correct URL."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_member_synopsis", {"member_id": 4514})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Members/4514/Synopsis"


class TestGetMemberVoting:
    """Tests for get_member_voting tool."""

    @pytest.mark.asyncio
    async def test_builds_url_without_page(self):
        """get_member_voting builds URL without page param."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_member_voting", {"member_id": 4514, "house": 1})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{MEMBERS_API_BASE}/Members/4514/Voting" in call_url
            assert "house=1" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_page(self):
        """get_member_voting builds URL with page param."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_member_voting", {"member_id": 4514, "house": 1, "page": 2})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "page=2" in call_url


class TestGetMemberWrittenQuestions:
    """Tests for get_member_written_questions tool."""

    @pytest.mark.asyncio
    async def test_builds_url_without_page(self):
        """get_member_written_questions builds URL without page param."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_member_written_questions", {"member_id": 4514})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{MEMBERS_API_BASE}/Members/4514/WrittenQuestions" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_page(self):
        """get_member_written_questions builds URL with page param."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_member_written_questions", {"member_id": 4514, "page": 3})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "page=3" in call_url


class TestGetMembersHistory:
    """Tests for get_members_history tool."""

    @pytest.mark.asyncio
    async def test_builds_url_with_single_id(self):
        """get_members_history builds URL with single member ID."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_members_history", {"member_ids": [4514]})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert f"{MEMBERS_API_BASE}/Members/History" in call_url
            assert "ids=4514" in call_url

    @pytest.mark.asyncio
    async def test_builds_url_with_multiple_ids(self):
        """get_members_history builds URL with multiple member IDs."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_members_history", {"member_ids": [4514, 1423, 4019]})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert "ids=4514%2C1423%2C4019" in call_url or "ids=4514,1423,4019" in call_url


class TestGetMemberLatestElectionResult:
    """Tests for get_member_latest_election_result tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_member_latest_election_result builds correct URL."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_member_latest_election_result", {"member_id": 4514})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Members/4514/LatestElectionResult"


class TestGetMemberPortraitUrl:
    """Tests for get_member_portrait_url tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_member_portrait_url builds correct URL."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_member_portrait_url", {"member_id": 4514})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Members/4514/PortraitUrl"


class TestGetMemberThumbnailUrl:
    """Tests for get_member_thumbnail_url tool."""

    @pytest.mark.asyncio
    async def test_builds_correct_url(self):
        """get_member_thumbnail_url builds correct URL."""
        with patch("uk_parliament_mcp.tools.members.get_result", new_callable=AsyncMock) as mock:
            mock.return_value = '{"url": "test", "data": "{}"}'

            mcp = FastMCP(name="test")
            members.register_tools(mcp)

            await mcp.call_tool("get_member_thumbnail_url", {"member_id": 4514})

            mock.assert_called_once()
            call_url = mock.call_args[0][0]
            assert call_url == f"{MEMBERS_API_BASE}/Members/4514/ThumbnailUrl"
