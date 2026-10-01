"""Per-topic tool counts in the guide text match what each module registers.

test_consistency.py checks the overall total; this checks the breakdown in
QUICK_REFERENCE's module table and the parliament_guide topic headings.
"""

from __future__ import annotations

import re
from types import ModuleType

import pytest
from mcp.server.fastmcp import FastMCP

from uk_parliament_mcp.server import create_server
from uk_parliament_mcp.tools import (
    bills,
    committees,
    composite,
    core,
    erskine_may,
    hansard,
    interests,
    members,
    now,
    oral_questions,
    statutory_instruments,
    treaties,
    votes,
    whatson,
    written_questions,
)

MODULES: dict[str, ModuleType] = {
    "bills": bills,
    "committees": committees,
    "composite": composite,
    "core": core,
    "erskine_may": erskine_may,
    "hansard": hansard,
    "interests": interests,
    "members": members,
    "now": now,
    "oral_questions": oral_questions,
    "statutory_instruments": statutory_instruments,
    "treaties": treaties,
    "votes": votes,
    "whatson": whatson,
    "written_questions": written_questions,
}

# parliament_guide topic -> (modules it covers, tools it lists from other modules)
TOPIC_MODULES: dict[str, tuple[list[str], int]] = {
    "composite": (["composite"], 0),
    "members": (["members"], 0),
    "bills": (["bills"], 0),
    "votes": (["votes"], 0),
    "committees": (["committees"], 0),
    "hansard": (["hansard"], 0),
    "questions": (["oral_questions"], 0),
    "interests": (["interests"], 0),
    "live": (["now", "whatson"], 0),
    "legislation": (["statutory_instruments", "treaties"], 0),
    # Erskine May plus bill_types and bill_stages from the bills module
    "procedures": (["erskine_may"], 2),
}

# "### <section> (N tools)" in the "all" guide and the legislation guide
SECTION_MODULES: dict[str, list[str]] = {
    "Composite": ["composite"],
    "Members": ["members"],
    "Bills": ["bills"],
    "Votes": ["votes"],
    "Committees": ["committees"],
    "Hansard": ["hansard"],
    "Erskine May": ["erskine_may"],
    "Questions & Motions": ["oral_questions"],
    "Written Questions & Statements": ["written_questions"],
    "Interests": ["interests"],
    "Live & Calendar": ["now", "whatson"],
    "Legislation": ["statutory_instruments", "treaties"],
    "Session & Guidance": ["core"],
    "Statutory Instruments": ["statutory_instruments"],
    "Treaties": ["treaties"],
}

HEADING_COUNT_RE = re.compile(r"^#+ (.+?) \((\d+) tools", re.MULTILINE)


@pytest.fixture(scope="module")
async def module_counts() -> dict[str, int]:
    counts = {}
    for name, module in MODULES.items():
        mcp = FastMCP(name=name)
        module.register_tools(mcp)
        counts[name] = len(await mcp.list_tools())
    return counts


async def test_modules_cover_every_registered_tool(module_counts: dict[str, int]) -> None:
    assert sum(module_counts.values()) == len(await create_server().list_tools())


def test_quick_reference_table(module_counts: dict[str, int]) -> None:
    rows = dict(re.findall(r"^\| (\w+) \| (\d+) \|", core.QUICK_REFERENCE, re.MULTILINE))
    assert {k: int(v) for k, v in rows.items()} == module_counts


@pytest.mark.parametrize("topic", sorted(TOPIC_MODULES))
def test_topic_heading_count(topic: str, module_counts: dict[str, int]) -> None:
    modules, extra = TOPIC_MODULES[topic]
    heading = core.GUIDANCE_CONTENT[topic].splitlines()[0]
    match = re.search(r"\((\d+) tools", heading)
    assert match, f"no count in {topic} heading: {heading!r}"
    assert int(match.group(1)) == sum(module_counts[m] for m in modules) + extra


@pytest.mark.parametrize("topic", ["all", "legislation"])
def test_section_counts(topic: str, module_counts: dict[str, int]) -> None:
    sections = HEADING_COUNT_RE.findall(core.GUIDANCE_CONTENT[topic])[1:]  # skip the title
    assert sections
    for name, count in sections:
        assert name in SECTION_MODULES, f"unknown section {name!r}; add it to SECTION_MODULES"
        expected = sum(module_counts[m] for m in SECTION_MODULES[name])
        assert int(count) == expected, (
            f"{topic} guide: {name} says {count}, modules have {expected}"
        )


def test_all_guide_sections_add_up(module_counts: dict[str, int]) -> None:
    sections = HEADING_COUNT_RE.findall(core.GUIDANCE_CONTENT["all"])[1:]
    assert sum(int(n) for _, n in sections) == sum(module_counts.values())
