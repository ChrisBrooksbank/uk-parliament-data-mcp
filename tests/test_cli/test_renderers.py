"""Tests for CLI rich renderers."""

from __future__ import annotations

import json
from io import StringIO
from unittest.mock import patch

from rich.console import Console

from uk_parliament_mcp.cli.formatters import OutputFormat
from uk_parliament_mcp.cli.renderers import (
    render_bill_overview,
    render_calendar,
    render_chamber_now,
    render_check_vote,
    render_committee_summary,
    render_mp_profile,
)
from uk_parliament_mcp.cli.utils import should_render_rich

# ---------------------------------------------------------------------------
# should_render_rich
# ---------------------------------------------------------------------------


class TestShouldRenderRich:
    """Tests for should_render_rich utility."""

    def test_raw_always_false(self) -> None:
        assert should_render_rich(OutputFormat.AUTO, raw=True) is False
        assert should_render_rich(OutputFormat.TABLE, raw=True) is False

    def test_json_format_always_false(self) -> None:
        with patch("uk_parliament_mcp.cli.utils.sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            assert should_render_rich(OutputFormat.JSON, raw=False) is False

    def test_csv_format_always_false(self) -> None:
        with patch("uk_parliament_mcp.cli.utils.sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            assert should_render_rich(OutputFormat.CSV, raw=False) is False

    def test_markdown_format_always_false(self) -> None:
        with patch("uk_parliament_mcp.cli.utils.sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            assert should_render_rich(OutputFormat.MARKDOWN, raw=False) is False

    def test_auto_tty_returns_true(self) -> None:
        with patch("uk_parliament_mcp.cli.utils.sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            assert should_render_rich(OutputFormat.AUTO, raw=False) is True

    def test_auto_pipe_returns_false(self) -> None:
        with patch("uk_parliament_mcp.cli.utils.sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = False
            assert should_render_rich(OutputFormat.AUTO, raw=False) is False

    def test_table_tty_returns_true(self) -> None:
        with patch("uk_parliament_mcp.cli.utils.sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = True
            assert should_render_rich(OutputFormat.TABLE, raw=False) is True

    def test_table_pipe_returns_false(self) -> None:
        with patch("uk_parliament_mcp.cli.utils.sys.stdout") as mock_stdout:
            mock_stdout.isatty.return_value = False
            assert should_render_rich(OutputFormat.TABLE, raw=False) is False


# ---------------------------------------------------------------------------
# render_chamber_now
# ---------------------------------------------------------------------------


class TestRenderChamberNow:
    """Tests for render_chamber_now."""

    def test_renders_debate(self) -> None:
        data = {
            "slides": [
                {
                    "type": "Debate",
                    "lines": [{"content": "Climate Change", "style": "Text100", "displayOrder": 1}],
                    "speakerTime": "2024-01-15T14:32:00",
                }
            ],
            "scrollingMessages": [],
            "annunciatorDisabled": False,
            "showCommonsBell": False,
            "showLordsBell": False,
        }
        response = json.dumps({"url": "test", "data": data})
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_chamber_now(response, "House of Commons")
        text = output.getvalue()
        assert "House of Commons" in text
        assert "Debate" in text

    def test_renders_error_gracefully(self) -> None:
        response = json.dumps({"url": "test", "error": "Not found"})
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_chamber_now(response, "House of Commons")
        text = output.getvalue()
        assert "House of Commons" in text
        assert "Not currently sitting" in text

    def test_renders_invalid_json(self) -> None:
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_chamber_now("not json", "House of Lords")
        text = output.getvalue()
        assert "House of Lords" in text


# ---------------------------------------------------------------------------
# render_calendar
# ---------------------------------------------------------------------------


class TestRenderCalendar:
    """Tests for render_calendar."""

    def test_renders_events(self) -> None:
        data = [
            {
                "StartTime": "2024-01-15T11:30:00",
                "House": "Commons",
                "Description": "Oral Questions",
            }
        ]
        response = json.dumps({"url": "test", "data": data})
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_calendar(response)
        text = output.getvalue()
        assert "Calendar" in text

    def test_renders_empty(self) -> None:
        response = json.dumps({"url": "test", "error": "Not found"})
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_calendar(response)
        text = output.getvalue()
        assert "Calendar" in text


# ---------------------------------------------------------------------------
# render_mp_profile
# ---------------------------------------------------------------------------


class TestRenderMpProfile:
    """Tests for render_mp_profile."""

    def test_renders_full_profile(self) -> None:
        data = {
            "member_id": 4514,
            "basic_info": {
                "nameDisplayAs": "Keir Starmer",
                "latestParty": {"name": "Labour"},
                "latestHouseMembership": {"membershipFrom": "Holborn and St Pancras"},
            },
            "biography": {
                "value": {
                    "biographyEntries": [
                        {"category": "Education", "entry": "Leeds University"}
                    ]
                }
            },
            "registered_interests": {"items": []},
            "recent_voting": {"items": []},
            "sources": {},
        }
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_mp_profile(json.dumps(data))
        text = output.getvalue()
        assert "Keir Starmer" in text
        assert "MP Profile" in text

    def test_renders_error(self) -> None:
        data = {"error": "No member found matching 'Nobody'"}
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_mp_profile(json.dumps(data))
        text = output.getvalue()
        assert "No member found" in text

    def test_renders_with_interests(self) -> None:
        data = {
            "member_id": 100,
            "basic_info": {"nameDisplayAs": "Test MP"},
            "biography": {},
            "registered_interests": {
                "items": [
                    {
                        "category": "Donations",
                        "interests": [{"interest": "Donation from X"}],
                    }
                ]
            },
            "recent_voting": {"items": []},
            "sources": {},
        }
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_mp_profile(json.dumps(data))
        text = output.getvalue()
        assert "Test MP" in text
        assert "Registered Interests" in text

    def test_renders_with_votes(self) -> None:
        data = {
            "member_id": 100,
            "basic_info": {"nameDisplayAs": "Test MP"},
            "biography": {},
            "registered_interests": {"items": []},
            "recent_voting": {
                "items": [
                    {
                        "value": {
                            "divisionId": 123,
                            "title": "Climate Bill",
                            "date": "2024-01-15T00:00:00",
                            "memberVotedAye": True,
                        }
                    }
                ]
            },
            "sources": {},
        }
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_mp_profile(json.dumps(data))
        text = output.getvalue()
        assert "Test MP" in text
        assert "Recent Votes" in text

    def test_handles_invalid_json(self) -> None:
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_mp_profile("not json")
        text = output.getvalue()
        assert "Failed to parse" in text


# ---------------------------------------------------------------------------
# render_check_vote
# ---------------------------------------------------------------------------


class TestRenderCheckVote:
    """Tests for render_check_vote."""

    def test_renders_divisions(self) -> None:
        data = {
            "member_id": 1234,
            "member_info": {"nameDisplayAs": "Test MP"},
            "topic_searched": "climate",
            "divisions": {
                "items": [
                    {
                        "DivisionId": 456,
                        "Title": "Climate Change Act",
                        "Date": "2024-01-15",
                        "AyeCount": 300,
                        "NoCount": 200,
                    }
                ]
            },
            "sources": {},
        }
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_check_vote(json.dumps(data))
        text = output.getvalue()
        assert "Test MP" in text
        assert "Vote Check" in text
        assert "Divisions" in text

    def test_renders_no_divisions(self) -> None:
        data = {
            "member_id": 1234,
            "member_info": {"nameDisplayAs": "Test MP"},
            "topic_searched": "obscure topic",
            "divisions": {"items": []},
            "sources": {},
        }
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_check_vote(json.dumps(data))
        text = output.getvalue()
        assert "Test MP" in text
        assert "No divisions found" in text

    def test_renders_error(self) -> None:
        data = {"error": "No member found matching 'Nobody'"}
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_check_vote(json.dumps(data))
        text = output.getvalue()
        assert "No member found" in text


# ---------------------------------------------------------------------------
# render_bill_overview
# ---------------------------------------------------------------------------


class TestRenderBillOverview:
    """Tests for render_bill_overview."""

    def test_renders_bill_with_stages(self) -> None:
        data = {
            "bill_id": 123,
            "search_summary": {
                "shortTitle": "Online Safety Bill",
                "currentStage": {"description": "Royal Assent"},
            },
            "details": {"value": {"shortTitle": "Online Safety Bill"}},
            "stages": {
                "items": [
                    {
                        "stageType": {"name": "1st reading"},
                        "house": "Commons",
                        "stageSittings": [{"date": "2024-01-10T00:00:00"}],
                    },
                    {
                        "stageType": {"name": "2nd reading"},
                        "house": "Commons",
                        "stageSittings": [{"date": "2024-02-15T00:00:00"}],
                    },
                ]
            },
            "publications": {"items": []},
            "other_matches": 2,
            "sources": {},
        }
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_bill_overview(json.dumps(data))
        text = output.getvalue()
        assert "Online Safety Bill" in text
        assert "Bill Overview" in text
        assert "Legislative Stages" in text

    def test_renders_error(self) -> None:
        data = {"error": "No bills found matching 'Nothing'"}
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_bill_overview(json.dumps(data))
        text = output.getvalue()
        assert "No bills found" in text

    def test_renders_with_publications(self) -> None:
        data = {
            "bill_id": 123,
            "search_summary": {"shortTitle": "Test Bill"},
            "details": {},
            "stages": {"items": []},
            "publications": {
                "items": [
                    {"title": "Impact Assessment", "publicationType": {"name": "Report"}}
                ]
            },
            "other_matches": 0,
            "sources": {},
        }
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_bill_overview(json.dumps(data))
        text = output.getvalue()
        assert "Test Bill" in text
        assert "Publications" in text


# ---------------------------------------------------------------------------
# render_committee_summary
# ---------------------------------------------------------------------------


class TestRenderCommitteeSummary:
    """Tests for render_committee_summary."""

    def test_renders_committee(self) -> None:
        data = {
            "committee_id": 42,
            "search_summary": {"name": "Treasury Committee", "isCommons": True},
            "details": {"value": {"name": "Treasury Committee"}},
            "oral_evidence": {"items": []},
            "written_evidence": {"items": []},
            "publications": {"items": []},
            "other_matches": 0,
            "sources": {},
        }
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_committee_summary(json.dumps(data))
        text = output.getvalue()
        assert "Treasury Committee" in text
        assert "Committee Summary" in text

    def test_renders_with_evidence(self) -> None:
        data = {
            "committee_id": 42,
            "search_summary": {"name": "Health Committee"},
            "details": {},
            "oral_evidence": {
                "items": [
                    {
                        "date": "2024-01-15T00:00:00",
                        "title": "NHS Funding",
                        "witnesses": [{"name": "Dr Smith"}],
                    }
                ]
            },
            "written_evidence": {
                "items": [
                    {
                        "dateReceived": "2024-01-10",
                        "title": "Evidence on NHS",
                        "authorName": "BMA",
                    }
                ]
            },
            "publications": {"items": []},
            "other_matches": 1,
            "sources": {},
        }
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_committee_summary(json.dumps(data))
        text = output.getvalue()
        assert "Health Committee" in text
        assert "Oral Evidence" in text
        assert "Written Evidence" in text

    def test_renders_error(self) -> None:
        data = {"error": "No committees found matching 'Nothing'"}
        output = StringIO()
        console = Console(file=output, force_terminal=True)
        with patch("uk_parliament_mcp.cli.renderers.Console", return_value=console):
            render_committee_summary(json.dumps(data))
        text = output.getvalue()
        assert "No committees found" in text


# ---------------------------------------------------------------------------
# CLI commands still output JSON when piped (CliRunner is non-TTY)
# ---------------------------------------------------------------------------


class TestCliRunnerOutputsJson:
    """Verify that CliRunner (non-TTY) produces JSON, not rich output."""

    def test_composite_mp_profile_json(self) -> None:
        """mp-profile should output JSON through CliRunner (non-TTY)."""
        from typer.testing import CliRunner

        from uk_parliament_mcp.cli.main import app

        runner = CliRunner()
        member_resp = json.dumps({
            "url": "test",
            "data": json.dumps({
                "value": {"id": 4514, "nameDisplayAs": "Keir Starmer",
                           "latestHouseMembership": {"house": 1}}
            }),
        })
        bio_resp = json.dumps({"url": "test", "data": json.dumps({"value": {"biographyEntries": []}})})
        interests_resp = json.dumps({"url": "test", "data": json.dumps({"items": []})})
        voting_resp = json.dumps({"url": "test", "data": json.dumps({"items": []})})

        call_count = [0]

        async def mock_get_result(url: str) -> str:
            responses = [member_resp, bio_resp, interests_resp, voting_resp]
            response = responses[call_count[0]]
            call_count[0] += 1
            return response

        with patch("uk_parliament_mcp.cli.composite.get_result", new=mock_get_result):
            result = runner.invoke(app, ["composite", "mp-profile", "4514"])

        assert result.exit_code == 0
        # Should be valid JSON (not rich markup)
        output = json.loads(result.stdout)
        assert "member_id" in output

    def test_live_commons_now_json(self) -> None:
        """commons-now should output JSON through CliRunner (non-TTY)."""
        from typer.testing import CliRunner

        from uk_parliament_mcp.cli.main import app

        runner = CliRunner()
        mock_response = json.dumps({
            "url": "test",
            "data": {"slides": [{"type": "Debate"}], "scrollingMessages": []},
        })

        async def mock_get_result(url: str) -> str:
            return mock_response

        with patch("uk_parliament_mcp.cli.live.get_result", new=mock_get_result):
            result = runner.invoke(app, ["live", "commons-now"])

        assert result.exit_code == 0
        # Should be valid JSON
        output = json.loads(result.stdout)
        assert isinstance(output, dict)

    def test_format_json_bypasses_rich(self) -> None:
        """--format json should bypass rich rendering even on TTY."""
        from typer.testing import CliRunner

        from uk_parliament_mcp.cli.main import app

        runner = CliRunner()
        mock_response = json.dumps({
            "url": "test",
            "data": {"slides": [{"type": "Debate"}], "scrollingMessages": []},
        })

        async def mock_get_result(url: str) -> str:
            return mock_response

        with patch("uk_parliament_mcp.cli.live.get_result", new=mock_get_result):
            result = runner.invoke(app, ["live", "commons-now", "--format", "json"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert isinstance(output, dict)

    def test_raw_flag_bypasses_rich(self) -> None:
        """--raw should bypass rich rendering."""
        from typer.testing import CliRunner

        from uk_parliament_mcp.cli.main import app

        runner = CliRunner()
        mock_response = json.dumps({
            "url": "test",
            "data": json.dumps({"slides": [{"type": "Debate"}]}),
        })

        async def mock_get_result(url: str) -> str:
            return mock_response

        with patch("uk_parliament_mcp.cli.live.get_result", new=mock_get_result):
            result = runner.invoke(app, ["live", "commons-now", "--raw"])

        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert "url" in output
