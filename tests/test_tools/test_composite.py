"""Tests for composite tools that combine multiple API calls."""

from __future__ import annotations

import json
from unittest.mock import patch

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
        member_response = {"items": [{"value": {"id": 4514, "nameDisplayAs": "Keir Starmer"}}]}
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

    def test_extract_member_id_from_pruned_response(self):
        """_extract_member_id handles search results after MCP response pruning.

        Pruning flattens the Members API value wrappers, which previously made
        get_my_mp report "No current MP found" for every postcode.
        """
        from uk_parliament_mcp.pruning import prune_response

        raw = json.dumps(
            {
                "url": "https://members-api.parliament.uk/api/Members/Search",
                "data": {
                    "items": [
                        {"value": {"id": 5257, "nameDisplayAs": "Rachel Blake"}, "links": []}
                    ],
                    "totalResults": 1,
                },
            }
        )
        member_data = composite._parse_response(prune_response(raw))

        assert composite._extract_member_id(member_data) == 5257
        assert composite._first_search_item(member_data)["nameDisplayAs"] == "Rachel Blake"


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


# ---------------------------------------------------------------------------
# Votes, bills, committee cross-reference and cross-API search
# ---------------------------------------------------------------------------


def _wrap(data: object) -> str:
    return json.dumps({"url": "https://test", "data": data})


def _router(routes: dict[str, object]):
    """Fake get_result that answers with the first route whose key is in the URL."""
    calls: list[str] = []

    async def fake(url: str, *args: object, **kwargs: object) -> str:
        calls.append(url)
        for key, data in routes.items():
            if key in url:
                return _wrap(data)
        return _wrap({})

    fake.calls = calls  # type: ignore[attr-defined]
    return fake


def _member(member_id: int, house: int, name: str) -> dict[str, object]:
    return {
        "value": {
            "id": member_id,
            "nameDisplayAs": name,
            "latestParty": {"name": "Party"},
            "latestHouseMembership": {"house": house, "membershipFrom": "Somewhere"},
        }
    }


def _commons_vote(division_id: int, aye: bool, title: str = "Division") -> dict[str, object]:
    return {
        "MemberVotedAye": aye,
        "MemberVotedNo": not aye,
        "MemberWasTeller": False,
        "PublishedDivision": {
            "DivisionId": division_id,
            "Date": f"2024-01-{division_id:02d}T00:00:00",
            "Title": title,
            "AyeCount": 10,
            "NoCount": 5,
        },
    }


class TestNewCompositeRegistration:
    async def test_all_ten_composite_tools(self) -> None:
        mcp = FastMCP(name="test")
        composite.register_tools(mcp)
        names = {t.name for t in await mcp.list_tools()}
        assert names == {
            "get_mp_profile",
            "check_mp_vote",
            "compare_member_votes",
            "get_bill_overview",
            "get_member_bills",
            "get_committee_summary",
            "get_bill_committees",
            "get_committee_bills",
            "search_parliament",
            "get_my_mp",
        }

    async def test_composite_docstrings_list_underlying_tools(self) -> None:
        mcp = FastMCP(name="test")
        composite.register_tools(mcp)
        for tool in await mcp.list_tools():
            assert "Combines:" in (tool.description or ""), tool.name


class TestNormaliseMemberVotes:
    def test_commons_records(self) -> None:
        votes = composite.normalise_member_votes(
            {"data": [_commons_vote(1, True, "A"), _commons_vote(2, False, "B")]}
        )
        assert [(v["division_id"], v["vote"]) for v in votes] == [(1, "Aye"), (2, "No")]
        assert votes[0]["date"] == "2024-01-01"

    def test_lords_records(self) -> None:
        record = {
            "memberWasContent": False,
            "memberWasTeller": False,
            "publishedDivision": {
                "divisionId": 7,
                "date": "2024-02-02T00:00:00",
                "title": "Lords vote",
                "authoritativeContentCount": 100,
                "authoritativeNotContentCount": 90,
            },
        }
        assert composite.normalise_member_votes({"data": [record]}) == [
            {
                "division_id": 7,
                "date": "2024-02-02",
                "title": "Lords vote",
                "vote": "Not Content",
                "ayes": 100,
                "noes": 90,
            }
        ]

    def test_skips_pruning_marker(self) -> None:
        records = [_commons_vote(1, True), {"_truncated": {"total": 30, "showing": 20}}]
        assert len(composite.normalise_member_votes({"data": records})) == 1


class TestCheckMemberVotes:
    async def test_lords_member_uses_lords_api(self) -> None:
        fake = _router({"Members/3743": _member(3743, 2, "Lord X"), "membervoting": []})
        with patch("uk_parliament_mcp.tools.composite.get_result", fake):
            result = await composite.check_member_votes(3743, "climate")
        assert "lordsvotes-api" in result["sources"]["votes"]
        assert "MemberId=3743" in result["sources"]["votes"]
        assert result["suggestions"]  # nothing found -> next steps

    async def test_commons_member_filter_is_applied(self) -> None:
        fake = _router(
            {"Members/4514": _member(4514, 1, "MP"), "membervoting": [_commons_vote(3, True)]}
        )
        with patch("uk_parliament_mcp.tools.composite.get_result", fake):
            result = await composite.check_member_votes(4514, "climate")
        assert "queryParameters.memberId=4514" in result["sources"]["votes"]
        assert result["votes"][0]["vote"] == "Aye"
        assert "suggestions" not in result


class TestCompareMemberVotes:
    async def test_agreement(self) -> None:
        fake = _router(
            {
                "Members/1": _member(1, 1, "A"),
                "Members/2": _member(2, 1, "B"),
                "memberId=1&": [
                    _commons_vote(1, True),
                    _commons_vote(2, True),
                    _commons_vote(3, True),
                ],
                "memberId=2&": [
                    _commons_vote(1, True),
                    _commons_vote(2, False),
                    _commons_vote(4, True),
                ],
            }
        )
        with patch("uk_parliament_mcp.tools.composite.get_result", fake):
            result = await composite.compare_votes(1, 2)
        summary = result["summary"]
        assert summary["divisions_both_voted_in"] == 2
        assert summary["agreed"] == 1 and summary["disagreed"] == 1
        assert summary["agreement_rate"] == 0.5
        assert [d["division_id"] for d in result["divisions"]] == [2, 1]  # newest first
        assert [d["division_id"] for d in result["only_a_voted"]] == [3]
        assert [d["division_id"] for d in result["only_b_voted"]] == [4]

    async def test_different_houses(self) -> None:
        fake = _router({"Members/1": _member(1, 1, "MP"), "Members/2": _member(2, 2, "Peer")})
        with patch("uk_parliament_mcp.tools.composite.get_result", fake):
            result = await composite.compare_votes(1, 2)
        assert "different Houses" in result["error"]
        assert not any("membervoting" in url for url in fake.calls)  # type: ignore[attr-defined]


class TestMemberBills:
    async def test_lists_sponsored_bills(self) -> None:
        fake = _router(
            {
                "Members/4514": _member(4514, 1, "MP"),
                "Bills?": {
                    "totalResults": 1,
                    "items": [
                        {
                            "billId": 9,
                            "shortTitle": "Test Bill",
                            "currentStage": {"description": "2nd reading"},
                        }
                    ],
                },
            }
        )
        with patch("uk_parliament_mcp.tools.composite.get_result", fake):
            result = await composite.member_bills(4514)
        assert result["bills"][0]["short_title"] == "Test Bill"
        assert result["bills"][0]["current_stage"] == "2nd reading"
        assert "MemberId=4514" in result["sources"]["bills"]


class TestBillCommitteeCrossReference:
    def test_normalise_title(self) -> None:
        assert composite._normalise_title("Renters’ Rights Act 2025") == "renters rights"
        assert composite._normalise_title("Renter's Rights Bill [HL]") == "renters rights"

    async def test_bill_committees(self) -> None:
        fake = _router(
            {
                "Bills/5/Stages": {
                    "items": [
                        {
                            "description": "Committee stage",
                            "house": "Commons",
                            "stageSittings": [{"date": "2024-01-01T00:00:00"}],
                        },
                        {"description": "2nd reading", "house": "Commons"},
                    ]
                },
                "Bills/5": {"shortTitle": "Renters’ Rights Act 2025"},
                "CommitteeBusiness/11": {
                    "relatedInformation": [{"url": "https://bills.parliament.uk/bills/5"}]
                },
                "CommitteeBusiness?": {
                    "items": [
                        {"id": 11, "title": "Renter's Rights Bill", "openDate": "2024-02-01"},
                        {"id": 12, "title": "Unrelated inquiry", "openDate": "2024-03-01"},
                    ]
                },
                "Publications?CommitteeBusinessId=11": {
                    "items": [{"committee": {"id": 172, "name": "Constitution Committee"}}]
                },
            }
        )
        with patch("uk_parliament_mcp.tools.composite.get_result", fake):
            result = await composite.bill_committees(5)
        assert result["committee_stages"] == [
            {"stage": "Committee stage", "house": "Commons", "sittings": ["2024-01-01"]}
        ]
        assert [b["business_id"] for b in result["committee_business"]] == [11]
        assert result["committee_business"][0]["linked_bill_ids"] == [5]
        assert result["committee_business"][0]["committee"]["name"] == "Constitution Committee"
        assert "SearchTerm=renters+rights" in result["sources"]["committee_business"]

    async def test_bill_committees_unknown_bill(self) -> None:
        fake = _router({})
        with patch("uk_parliament_mcp.tools.composite.get_result", fake):
            result = await composite.bill_committees(1)
        assert "No bill found" in result["error"]
        assert result["suggestions"]

    async def test_committee_bills_matches_by_link_or_title(self) -> None:
        fake = _router(
            {
                "Committees/172": {"id": 172, "name": "Constitution Committee", "house": "Lords"},
                "CommitteeBusiness/21": {
                    "relatedInformation": [{"url": "https://bills.parliament.uk/bills/40"}]
                },
                "CommitteeBusiness/22": {"relatedInformation": []},
                "CommitteeBusiness?": {
                    "totalResults": 2,
                    "items": [
                        {"id": 21, "title": "Linked Bill", "openDate": "2024-05-01"},
                        {"id": 22, "title": "Railways Bill", "openDate": "2024-04-01"},
                    ],
                },
                "SearchTerm=linked": {"items": [{"billId": 40, "shortTitle": "Linked Bill"}]},
                "SearchTerm=railways": {
                    "items": [
                        {"billId": 1, "shortTitle": "Railways Bill", "lastUpdate": "2010-01-01"},
                        {"billId": 2, "shortTitle": "Railways Bill", "lastUpdate": "2024-09-01"},
                        {"billId": 3, "shortTitle": "Railways (Other) Bill"},
                    ]
                },
            }
        )
        with patch("uk_parliament_mcp.tools.composite.get_result", fake):
            result = await composite.committee_bills(172)
        examined = {i["business_id"]: i for i in result["bills_examined"]}
        assert examined[21]["match"] == "link" and examined[21]["bill"]["bill_id"] == 40
        # The 2010 bill predates the committee's business; the 2024 one is chosen
        assert examined[22]["match"] == "title" and examined[22]["bill"]["bill_id"] == 2
        assert "BusinessTypeId=3" in result["sources"]["committee_business"]


class TestSearchParliament:
    async def test_combines_categories(self) -> None:
        fake = _router(
            {
                "Members/Search": {"totalResults": 1, "items": [_member(1, 2, "Lord Y")]},
                "bills-api": {"totalResults": 1, "items": [{"billId": 3, "shortTitle": "Z Bill"}]},
                "Committees?": {"totalResults": 0, "items": []},
                "search.json": {
                    "TotalDebates": 1,
                    "Debates": [{"Title": "Debate", "SittingDate": "2024-01-01T00:00:00"}],
                },
                "writtenquestions": {
                    "totalResults": 1,
                    "results": [{"value": {"id": 5, "heading": "Housing"}}],
                },
            }
        )
        with patch("uk_parliament_mcp.tools.composite.get_result", fake):
            result = await composite.search_everything("z y")
        assert result["members"][0]["house"] == "Lords"
        assert result["bills"][0]["bill_id"] == 3
        assert result["hansard_debates"][0]["title"] == "Debate"
        assert result["totals"]["committees"] == 0
        assert result["written_questions"][0]["heading"] == "Housing"
        # Multi-word written question searches are quoted as a phrase
        assert "searchTerm=%22z+y%22" in result["sources"]["written_questions"]
        assert "suggestions" not in result

    async def test_suggestions_when_nothing_found(self) -> None:
        fake = _router({})
        with patch("uk_parliament_mcp.tools.composite.get_result", fake):
            result = await composite.search_everything("qqqq")
        assert result["suggestions"] == composite.SUGGESTIONS["search"]


class TestNotFoundSuggestions:
    async def test_bill_overview(self) -> None:
        mcp = FastMCP(name="test")
        composite.register_tools(mcp)
        with patch(
            "uk_parliament_mcp.tools.composite.get_result", _router({"Bills": {"items": []}})
        ):
            result = await mcp.call_tool("get_bill_overview", {"search_term": "nothing"})
        text = result[0][0].text if isinstance(result, tuple) else result[0].text
        assert json.loads(text)["suggestions"] == composite.SUGGESTIONS["bill"]

    async def test_my_mp(self) -> None:
        mcp = FastMCP(name="test")
        composite.register_tools(mcp)
        with patch("uk_parliament_mcp.tools.composite.get_result", _router({})):
            result = await mcp.call_tool("get_my_mp", {"postcode": "ZZ1"})
        text = result[0][0].text if isinstance(result, tuple) else result[0].text
        assert json.loads(text)["suggestions"] == composite.SUGGESTIONS["postcode"]
