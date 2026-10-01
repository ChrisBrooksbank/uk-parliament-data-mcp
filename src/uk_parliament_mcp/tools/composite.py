"""Composite tools that combine multiple API calls for common workflows.

The query logic lives in module-level ``async`` functions that return dicts, so
the CLI (``cli/composite.py``) can reuse it; the MCP tools wrap them and return JSON.
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

from uk_parliament_mcp.config import (
    BILLS_API_BASE,
    COMMITTEES_API_BASE,
    COMMONS_VOTES_API_BASE,
    HANSARD_API_BASE,
    HOUSE_COMMONS,
    HOUSE_LORDS,
    INTERESTS_API_BASE,
    LORDS_VOTES_API_BASE,
    MEMBERS_API_BASE,
    WRITTEN_QUESTIONS_API_BASE,
)
from uk_parliament_mcp.http_client import build_url, get_result

if TYPE_CHECKING:  # the standalone CLI uses this module without the mcp package
    from mcp.server.fastmcp import FastMCP

# Committee business type for scrutiny of a bill (see get_committee_business_types)
LEGISLATIVE_SCRUTINY_BUSINESS_TYPE = 3
_BILL_LINK_RE = re.compile(r"bills\.parliament\.uk/bills/(\d+)")

# Next steps to offer when a composite tool finds nothing
SUGGESTIONS: dict[str, list[str]] = {
    "member": [
        "Try the surname only (e.g. 'Starmer' rather than 'Sir Keir Starmer').",
        "Check the spelling, or drop titles such as 'Sir', 'Dame', 'Dr' or 'MP'.",
        "For a former member, use search_historical_members.",
        "For a peer, try the title (e.g. 'Lord Smith' or 'Baroness Smith').",
    ],
    "postcode": [
        "Check the postcode format (e.g. 'SW1A 1AA').",
        "Try the outward code only (e.g. 'SW1A').",
        "Use get_constituencies with a place name, then get_constituency_representations.",
    ],
    "bill": [
        "Use fewer or broader keywords (e.g. 'Renters' rather than 'Renters Rights Bill 2024').",
        "Drop words like 'Bill', 'Act' or the year.",
        "For legislation that has become law, try search_acts_of_parliament.",
    ],
    "committee": [
        "Try the department or subject (e.g. 'Treasury', 'Health').",
        "Use a shorter term; committee names are matched as a phrase.",
        "List committees with search_committees and no search term.",
    ],
    "votes": [
        "Use a broader topic word (e.g. 'climate' rather than 'climate change levy').",
        "Drop the topic to see the member's most recent votes.",
        "Ministers often vote less; check get_member_voting for their overall record.",
    ],
    "committee_business": [
        "The committee may have examined the bill under a different title; try search_committees or get_committee_business with a keyword.",
        "Public bill committees (the Commons committee stage) are listed in this tool's committee_stages, not as committee business.",
    ],
    "search": [
        "Use fewer words or a single distinctive keyword.",
        "Check the spelling.",
        "Search Hansard over a date range with search_hansard for older debates.",
    ],
}


def _parse_response(response: str) -> dict[str, Any]:
    """Parse JSON response and extract data."""
    try:
        parsed: dict[str, Any] = json.loads(response)
        if "data" in parsed:
            # Data is a JSON string, parse it
            data = parsed["data"]
            if isinstance(data, str):
                data = json.loads(data)
            return dict(data) if isinstance(data, dict) else {"data": data}
        return parsed
    except (json.JSONDecodeError, TypeError):
        return {"error": "Failed to parse response"}


def _items(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """Return the result list of a parsed response, whatever key it lives under."""
    for key in ("items", "results", "data", "_data"):
        value = parsed.get(key)
        if isinstance(value, list):
            # Skip the {"_truncated": ...} marker that pruning appends
            return [
                (item["value"] if isinstance(item.get("value"), dict) else item)
                for item in value
                if isinstance(item, dict) and "_truncated" not in item
            ]
    return []


def _first_search_item(search_response: dict[str, Any]) -> dict[str, Any]:
    """Return the first item of a Members API search, with or without its value wrapper.

    Raw responses look like ``{"items": [{"value": {...}, "links": [...]}]}``; with
    response pruning on (the MCP default) the wrapper is flattened to ``{"items": [{...}]}``.
    """
    items = search_response.get("items") or [{}]
    first = items[0] if isinstance(items[0], dict) else {}
    value = first.get("value")
    return value if isinstance(value, dict) else first


def _extract_member_id(member_response: dict[str, Any]) -> int | None:
    """Extract member_id from member search response."""
    member_id = _first_search_item(member_response).get("id")
    return member_id if isinstance(member_id, int) else None


def _member_house(basic_info: dict[str, Any]) -> int:
    membership = basic_info.get("latestHouseMembership") or {}
    return HOUSE_LORDS if membership.get("house") == HOUSE_LORDS else HOUSE_COMMONS


def _member_summary(basic_info: dict[str, Any]) -> dict[str, Any]:
    membership = basic_info.get("latestHouseMembership") or {}
    party = basic_info.get("latestParty") or {}
    return {
        "id": basic_info.get("id"),
        "name": basic_info.get("nameDisplayAs"),
        "party": party.get("name"),
        "house": "Lords" if _member_house(basic_info) == HOUSE_LORDS else "Commons",
        "constituency_or_title": membership.get("membershipFrom"),
    }


async def _fetch_member(member_id: int) -> tuple[str, dict[str, Any]]:
    url = f"{MEMBERS_API_BASE}/Members/{member_id}"
    data = _parse_response(await get_result(url))
    value = data.get("value")
    return url, value if isinstance(value, dict) else {}


def member_voting_url(member_id: int, house: int, topic: str | None = None, take: int = 25) -> str:
    """URL of a member's division votes (with how they voted) in their House's votes API."""
    if house == HOUSE_LORDS:
        return build_url(
            f"{LORDS_VOTES_API_BASE}/Divisions/membervoting",
            {"MemberId": member_id, "SearchTerm": topic, "take": take},
        )
    return build_url(
        f"{COMMONS_VOTES_API_BASE}/divisions.json/membervoting",
        {
            "queryParameters.memberId": member_id,
            "queryParameters.searchTerm": topic,
            "queryParameters.take": take,
        },
    )


def normalise_member_votes(parsed: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten Commons or Lords ``membervoting`` records into one shape.

    Commons records use ``MemberVotedAye``/``PublishedDivision``; Lords records use
    ``memberWasContent``/``publishedDivision``.
    """
    votes = []
    for record in _items(parsed):
        if "PublishedDivision" in record:
            division = record["PublishedDivision"] or {}
            if record.get("MemberWasTeller"):
                vote = "Teller"
            elif record.get("MemberVotedAye"):
                vote = "Aye"
            elif record.get("MemberVotedNo"):
                vote = "No"
            else:
                vote = "Unknown"
            votes.append(
                {
                    "division_id": division.get("DivisionId"),
                    "date": str(division.get("Date", ""))[:10],
                    "title": division.get("Title"),
                    "vote": vote,
                    "ayes": division.get("AyeCount"),
                    "noes": division.get("NoCount"),
                }
            )
        elif "publishedDivision" in record:
            division = record["publishedDivision"] or {}
            if record.get("memberWasTeller"):
                vote = "Teller"
            elif record.get("memberWasContent") is True:
                vote = "Content"
            elif record.get("memberWasContent") is False:
                vote = "Not Content"
            else:
                vote = "Unknown"
            votes.append(
                {
                    "division_id": division.get("divisionId"),
                    "date": str(division.get("date", ""))[:10],
                    "title": division.get("title"),
                    "vote": vote,
                    "ayes": division.get("authoritativeContentCount"),
                    "noes": division.get("authoritativeNotContentCount"),
                }
            )
    return votes


async def check_member_votes(member_id: int, topic: str, take: int = 25) -> dict[str, Any]:
    """How a member voted on divisions matching a topic, in whichever House they sit."""
    member_url, basic_info = await _fetch_member(member_id)
    votes_url = member_voting_url(member_id, _member_house(basic_info), topic, take)
    votes = normalise_member_votes(_parse_response(await get_result(votes_url)))
    result: dict[str, Any] = {
        "member_id": member_id,
        "member_info": basic_info,
        "topic_searched": topic,
        "votes": votes,
        "sources": {"member": member_url, "votes": votes_url},
    }
    if not votes:
        result["suggestions"] = SUGGESTIONS["votes"]
    return result


async def compare_votes(
    member_id_a: int, member_id_b: int, topic: str | None = None, take: int = 50
) -> dict[str, Any]:
    """Compare two members' votes on the divisions both voted in."""
    (url_a, info_a), (url_b, info_b) = await asyncio.gather(
        _fetch_member(member_id_a), _fetch_member(member_id_b)
    )
    house_a, house_b = _member_house(info_a), _member_house(info_b)
    members = {"a": _member_summary(info_a), "b": _member_summary(info_b)}
    if house_a != house_b:
        return {
            "error": "The two members sit in different Houses, so they never vote in the same divisions.",
            "members": members,
            "suggestions": ["Compare two MPs, or two members of the Lords."],
        }

    votes_url_a = member_voting_url(member_id_a, house_a, topic, take)
    votes_url_b = member_voting_url(member_id_b, house_b, topic, take)
    response_a, response_b = await asyncio.gather(get_result(votes_url_a), get_result(votes_url_b))
    votes_a = {v["division_id"]: v for v in normalise_member_votes(_parse_response(response_a))}
    votes_b = {v["division_id"]: v for v in normalise_member_votes(_parse_response(response_b))}

    common = []
    for division_id, vote_a in votes_a.items():
        if division_id not in votes_b:
            continue
        vote_b = votes_b[division_id]["vote"]
        common.append(
            {
                "division_id": division_id,
                "date": vote_a["date"],
                "title": vote_a["title"],
                "a_vote": vote_a["vote"],
                "b_vote": vote_b,
                "agree": vote_a["vote"] == vote_b,
            }
        )
    common.sort(key=lambda d: d["date"], reverse=True)
    agreed = sum(1 for d in common if d["agree"])

    def only(mine: dict[Any, dict[str, Any]], theirs: dict[Any, Any]) -> list[dict[str, Any]]:
        return [
            {k: v[k] for k in ("division_id", "date", "title", "vote")}
            for division_id, v in mine.items()
            if division_id not in theirs
        ][:10]

    result: dict[str, Any] = {
        "members": members,
        "topic_searched": topic,
        "summary": {
            "divisions_both_voted_in": len(common),
            "agreed": agreed,
            "disagreed": len(common) - agreed,
            "agreement_rate": round(agreed / len(common), 2) if common else None,
            "note": f"Based on each member's {take} most recent matching divisions.",
        },
        "divisions": common,
        "only_a_voted": only(votes_a, votes_b),
        "only_b_voted": only(votes_b, votes_a),
        "sources": {
            "member_a": url_a,
            "member_b": url_b,
            "votes_a": votes_url_a,
            "votes_b": votes_url_b,
        },
    }
    if not common:
        result["suggestions"] = [
            "Increase take to look further back.",
            *SUGGESTIONS["votes"][:2],
        ]
    return result


def _bill_summary(bill: dict[str, Any]) -> dict[str, Any]:
    stage = bill.get("currentStage") or {}
    return {
        "bill_id": bill.get("billId"),
        "short_title": bill.get("shortTitle"),
        "current_house": bill.get("currentHouse"),
        "current_stage": stage.get("description"),
        "is_act": bill.get("isAct"),
        "is_defeated": bill.get("isDefeated"),
        "withdrawn": bill.get("billWithdrawn"),
        "last_update": str(bill.get("lastUpdate", ""))[:10],
    }


async def member_bills(member_id: int, take: int = 20) -> dict[str, Any]:
    """Bills a member has sponsored, most recently updated first."""
    bills_url = build_url(
        f"{BILLS_API_BASE}/Bills",
        {"MemberId": member_id, "SortOrder": "DateUpdatedDescending", "Take": take},
    )
    (member_url, basic_info), bills_response = await asyncio.gather(
        _fetch_member(member_id), get_result(bills_url)
    )
    parsed = _parse_response(bills_response)
    bills = [_bill_summary(b) for b in _items(parsed)]
    result: dict[str, Any] = {
        "member": _member_summary(basic_info),
        "total_bills": parsed.get("totalResults", len(bills)),
        "bills": bills,
        "sources": {"member": member_url, "bills": bills_url},
    }
    if not bills:
        result["suggestions"] = [
            "Most bills are sponsored by ministers; backbench sponsorship is mostly Private Members' Bills.",
            "For a member's legislative activity more broadly, try get_member_hansard_contributions or search_early_day_motions.",
        ]
    return result


def _normalise_title(title: str) -> str:
    """'Renters’ Rights Act 2025' and "Renter's Rights Bill [HL]" -> 'renters rights'."""
    text = re.sub(r"\[.*?\]|\(.*?\)", " ", title.lower())
    text = re.sub(r"['’‘`]", "", text)
    text = re.sub(r"\b(bill|act|\d{4})\b", " ", text)
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return " ".join(text.split())


def _linked_bill_ids(detail: dict[str, Any]) -> list[int]:
    """Bill IDs in a committee business item's relatedInformation links."""
    ids = set()
    for link in detail.get("relatedInformation") or []:
        if isinstance(link, dict) and (m := _BILL_LINK_RE.search(str(link.get("url", "")))):
            ids.add(int(m.group(1)))
    return sorted(ids)


def _committee_summary(committee: dict[str, Any]) -> dict[str, Any] | None:
    if not committee:
        return None
    return {
        "id": committee.get("id"),
        "name": committee.get("name"),
        "house": committee.get("house"),
    }


def _business_summary(business: dict[str, Any]) -> dict[str, Any]:
    return {
        "business_id": business.get("id"),
        "title": business.get("title"),
        "type": (business.get("type") or {}).get("name"),
        "open_date": str(business.get("openDate") or "")[:10] or None,
        "close_date": str(business.get("closeDate") or "")[:10] or None,
    }


async def _business_with_committee(business: dict[str, Any]) -> dict[str, Any]:
    """Add the examining committee and any linked bill IDs to a committee business item."""
    business_id = business.get("id")
    detail_url = f"{COMMITTEES_API_BASE}/CommitteeBusiness/{business_id}"
    publications_url = build_url(
        f"{COMMITTEES_API_BASE}/Publications", {"CommitteeBusinessId": business_id, "Take": 1}
    )
    detail_response, publications_response = await asyncio.gather(
        get_result(detail_url), get_result(publications_url)
    )
    publications = _items(_parse_response(publications_response))
    committee = publications[0].get("committee") if publications else None
    return {
        **_business_summary(business),
        "committee": _committee_summary(committee) if isinstance(committee, dict) else None,
        "linked_bill_ids": _linked_bill_ids(_parse_response(detail_response)),
    }


async def bill_committees(bill_id: int, max_items: int = 5) -> dict[str, Any]:
    """Committees that examined a bill: select committee business plus committee stages."""
    bill_url = f"{BILLS_API_BASE}/Bills/{bill_id}"
    stages_url = f"{BILLS_API_BASE}/Bills/{bill_id}/Stages"
    bill_response, stages_response = await asyncio.gather(
        get_result(bill_url), get_result(stages_url)
    )
    bill = _parse_response(bill_response)
    short_title = bill.get("shortTitle")
    if not short_title:
        return {
            "error": f"No bill found with ID {bill_id}",
            "bill": bill,
            "suggestions": ["Find the bill ID with search_bills or get_bill_overview."],
        }

    committee_stages = [
        {
            "stage": stage.get("description"),
            "house": stage.get("house"),
            "sittings": [
                str(s.get("date", ""))[:10]
                for s in stage.get("stageSittings") or []
                if isinstance(s, dict)
            ],
        }
        for stage in _items(_parse_response(stages_response))
        if "committee" in str(stage.get("description", "")).lower()
    ]

    search_term = _normalise_title(short_title)
    business_url = build_url(
        f"{COMMITTEES_API_BASE}/CommitteeBusiness", {"SearchTerm": search_term, "Take": 20}
    )
    candidates = [
        b
        for b in _items(_parse_response(await get_result(business_url)))
        if search_term and search_term in _normalise_title(str(b.get("title", "")))
    ]
    examined = await asyncio.gather(*(_business_with_committee(b) for b in candidates[:max_items]))
    # Business that links to this bill first, each group most recent first
    examined = sorted(examined, key=lambda b: b["open_date"] or "", reverse=True)
    examined.sort(key=lambda b: bill_id not in b["linked_bill_ids"])

    result: dict[str, Any] = {
        "bill_id": bill_id,
        "short_title": short_title,
        "committee_stages": committee_stages,
        "committee_business": examined,
        "other_business_matches": max(len(candidates) - max_items, 0),
        "notes": "committee_business is matched on the bill's title; items whose linked_bill_ids include this bill are confirmed links.",
        "sources": {"bill": bill_url, "stages": stages_url, "committee_business": business_url},
    }
    if not examined:
        result["suggestions"] = SUGGESTIONS["committee_business"]
    return result


async def _resolve_business_bill(business: dict[str, Any]) -> dict[str, Any]:
    """Find the bill a legislative-scrutiny item examined: by link if present, else by title."""
    business_id = business.get("id")
    title = _normalise_title(str(business.get("title", "")))
    detail_url = f"{COMMITTEES_API_BASE}/CommitteeBusiness/{business_id}"
    search_url = build_url(
        f"{BILLS_API_BASE}/Bills",
        {"SearchTerm": title, "SortOrder": "DateUpdatedDescending", "Take": 10},
    )
    detail_response, search_response = await asyncio.gather(
        get_result(detail_url), get_result(search_url)
    )
    linked = _linked_bill_ids(_parse_response(detail_response))
    bills = [b for b in _items(_parse_response(search_response)) if b.get("billId")]

    bill: dict[str, Any] | None = None
    match = None
    if linked:
        bill = next((b for b in bills if b.get("billId") == linked[0]), {"billId": linked[0]})
        match = "link"
    else:
        # Same title; a bill named like this may recur across sessions, so take the
        # earliest-updated one still active after the committee opened the business.
        opened = str(business.get("openDate") or "")[:10]
        same = [
            b for b in bills if title and _normalise_title(str(b.get("shortTitle", ""))) == title
        ]
        after = [b for b in same if str(b.get("lastUpdate", ""))[:10] >= opened]
        chosen = min(after, key=lambda b: str(b.get("lastUpdate", ""))) if after else None
        if chosen or same:
            bill = chosen or same[0]
            match = "title"
    return {
        **_business_summary(business),
        "bill": _bill_summary(bill) if bill else None,
        "match": match,
    }


async def committee_bills(committee_id: int, take: int = 10) -> dict[str, Any]:
    """Bills a committee has examined, from its legislative scrutiny business."""
    committee_url = f"{COMMITTEES_API_BASE}/Committees/{committee_id}"
    business_url = build_url(
        f"{COMMITTEES_API_BASE}/CommitteeBusiness",
        {
            "CommitteeId": committee_id,
            "BusinessTypeId": LEGISLATIVE_SCRUTINY_BUSINESS_TYPE,
            "SortOrder": "DateOpenedNewest",
            "Take": min(take, 20),
        },
    )
    committee_response, business_response = await asyncio.gather(
        get_result(committee_url), get_result(business_url)
    )
    committee = _parse_response(committee_response)
    parsed_business = _parse_response(business_response)
    business = _items(parsed_business)
    items = await asyncio.gather(*(_resolve_business_bill(b) for b in business))

    result: dict[str, Any] = {
        "committee": _committee_summary(committee),
        "total_legislative_scrutiny": parsed_business.get("totalResults", len(items)),
        "bills_examined": items,
        "notes": "match is 'link' when the committee linked the bill, 'title' when matched by bill title, null when no bill was found.",
        "sources": {"committee": committee_url, "committee_business": business_url},
    }
    if not items:
        result["suggestions"] = [
            "This committee has no legislative scrutiny on record; departmental committees mostly run inquiries.",
            "The Constitution Committee, Delegated Powers Committee and Joint Committee on Human Rights scrutinise many bills.",
            "Use get_committee_business to see all of this committee's work.",
        ]
    return result


async def search_everything(query: str, take: int = 5) -> dict[str, Any]:
    """Search members, bills, committees, Hansard and written questions at once."""
    urls = {
        "members": build_url(f"{MEMBERS_API_BASE}/Members/Search", {"Name": query, "take": take}),
        "bills": build_url(f"{BILLS_API_BASE}/Bills", {"SearchTerm": query, "Take": take}),
        "committees": build_url(
            f"{COMMITTEES_API_BASE}/Committees", {"SearchTerm": query, "Take": take}
        ),
        "hansard": build_url(
            f"{HANSARD_API_BASE}/search.json",
            {"queryParameters.searchTerm": query, "queryParameters.take": take},
        ),
        "written_questions": build_url(
            f"{WRITTEN_QUESTIONS_API_BASE}/writtenquestions/questions",
            # Unquoted words match any of them; quote a multi-word query as a phrase
            {
                "searchTerm": f'"{query}"' if " " in query and '"' not in query else query,
                "take": take,
            },
        ),
    }
    responses = dict(
        zip(urls, await asyncio.gather(*(get_result(u) for u in urls.values())), strict=True)
    )
    parsed = {k: _parse_response(v) for k, v in responses.items()}

    members = [
        {
            "member_id": m.get("id"),
            "name": m.get("nameDisplayAs"),
            "party": (m.get("latestParty") or {}).get("name"),
            "house": "Lords" if _member_house(m) == HOUSE_LORDS else "Commons",
        }
        for m in _items(parsed["members"])
    ]
    bills = [_bill_summary(b) for b in _items(parsed["bills"])]
    committees = [_committee_summary(c) for c in _items(parsed["committees"])]
    hansard = parsed["hansard"]
    debates = [
        {
            "title": d.get("Title"),
            "date": str(d.get("SittingDate", ""))[:10],
            "house": d.get("House"),
            "debate_section_ext_id": d.get("DebateSectionExtId"),
        }
        for d in hansard.get("Debates") or []
        if isinstance(d, dict)
    ][:take]  # the Hansard search ignores take for debates
    questions = [
        {
            "id": q.get("id"),
            "uin": q.get("uin"),
            "date_tabled": str(q.get("dateTabled", ""))[:10],
            "heading": q.get("heading"),
            "answering_body": q.get("answeringBodyName"),
        }
        for q in _items(parsed["written_questions"])
    ]

    totals = {
        "members": parsed["members"].get("totalResults", len(members)),
        "bills": parsed["bills"].get("totalResults", len(bills)),
        "committees": parsed["committees"].get("totalResults", len(committees)),
        "hansard_debates": hansard.get("TotalDebates", len(debates)),
        "hansard_contributions": hansard.get("TotalContributions"),
        "written_questions": parsed["written_questions"].get("totalResults", len(questions)),
    }
    result: dict[str, Any] = {
        "query": query,
        "totals": totals,
        "members": members,
        "bills": bills,
        "committees": committees,
        "hansard_debates": debates,
        "written_questions": questions,
        "next_steps": {
            "members": "get_mp_profile(member_id)",
            "bills": "get_bill_overview(search_term) or get_bill_by_id(bill_id)",
            "committees": "get_committee_summary(topic) or get_committee_by_id(committee_id)",
            "hansard_debates": "get_debate_by_id(debate_section_ext_id) or search_hansard_contributions",
            "written_questions": "get_written_question(question_id)",
        },
        "errors": {k: v["error"] for k, v in parsed.items() if "error" in v} or None,
        "sources": urls,
    }
    if not any((members, bills, committees, debates, questions)):
        result["suggestions"] = SUGGESTIONS["search"]
    return result


def register_tools(mcp: FastMCP) -> None:
    """Register composite tools with the MCP server."""

    @mcp.tool()
    async def get_mp_profile(member_id: int) -> str:
        """Get comprehensive MP/Lord profile in one call - combines member details, biography, interests, and voting summary | complete MP info, full member profile, MP background, politician details, comprehensive member data | Use when you need a complete picture of an MP or Lord without multiple tool calls | Returns combined data: basic info, biography, registered interests, and recent voting activity. Combines: get_member_by_id, get_members_biography, search_roi, get_member_voting. See also: get_my_mp (by postcode), get_member_by_name (to find member_id).

        Args:
            member_id: Parliament member ID. Get from member search first. Example: 4514

        Returns:
            Combined profile with basic info, biography, interests, and voting summary.
        """
        # Step 1: Fetch member directly by ID
        member_url = f"{MEMBERS_API_BASE}/Members/{member_id}"
        member_response = await get_result(member_url)
        member_data = _parse_response(member_response)

        basic_info = member_data.get("value", {})
        latest_membership = basic_info.get("latestHouseMembership") or {}
        house = latest_membership.get("house", 1)

        # Step 2: Parallel requests for details
        biography_url = f"{MEMBERS_API_BASE}/Members/{member_id}/Biography"
        interests_url = f"{INTERESTS_API_BASE}/Interests/?MemberId={member_id}"
        voting_url = build_url(
            f"{MEMBERS_API_BASE}/Members/{member_id}/Voting", {"house": house, "page": 1}
        )

        biography_response, interests_response, voting_response = await asyncio.gather(
            get_result(biography_url), get_result(interests_url), get_result(voting_url)
        )

        result: dict[str, Any] = {
            "member_id": member_id,
            "basic_info": basic_info,
            "biography": _parse_response(biography_response),
            "registered_interests": _parse_response(interests_response),
            "recent_voting": _parse_response(voting_response),
            "sources": {
                "member": member_url,
                "biography": biography_url,
                "interests": interests_url,
                "voting": voting_url,
            },
        }
        if not basic_info:
            result["suggestions"] = [
                "Check the member_id; find it with get_member_by_name or search_members.",
                *SUGGESTIONS["member"][:2],
            ]
        return json.dumps(result)

    @mcp.tool()
    async def check_mp_vote(member_id: int, topic: str, take: int = 25) -> str:
        """Check how an MP or Lord voted on a topic - combines member lookup and their division votes | MP voting stance, how did MP vote, voting record on topic, division lookup, aye or no | Use when you need to know how a specific member voted on a particular issue | Returns member details and each matching division with their vote (Aye/No, or Content/Not Content in the Lords). Combines: get_member_by_id, get_commons_voting_record_for_member or get_lords_voting_record_for_member (by the member's House). See also: compare_member_votes, search_commons_divisions.

        Args:
            member_id: Parliament member ID. Get from member search first. Example: 4514
            topic: Topic or keyword to search for in division titles (e.g., 'climate', 'NHS', 'brexit').
            take: Number of matching divisions to return (default 25, max 100).

        Returns:
            Member info and divisions matching the topic with the member's vote.
        """
        return json.dumps(await check_member_votes(member_id, topic, take))

    @mcp.tool()
    async def compare_member_votes(
        member_id_a: int,
        member_id_b: int,
        topic: str | None = None,
        take: int = 50,
    ) -> str:
        """Compare how two MPs (or two Lords) voted - lines up their votes division by division | compare voting records, do they agree, voting similarity, rebels, party loyalty, head to head | Use when asked whether two members vote the same way, overall or on a topic | Returns both members, agreement counts and rate, each shared division with both votes, and divisions only one of them voted in. Combines: get_member_by_id (x2), get_commons_voting_record_for_member or get_lords_voting_record_for_member (x2). See also: check_mp_vote, get_commons_divisions_grouped_by_party.

        Args:
            member_id_a: First member's Parliament ID. Get from get_member_by_name. Example: 4514
            member_id_b: Second member's Parliament ID; must sit in the same House as the first.
            topic: Optional: only divisions whose title matches this topic (e.g. 'climate', 'Rwanda').
            take: Number of each member's most recent matching divisions to compare (default 50, max 100).

        Returns:
            Agreement summary and division-by-division comparison.
        """
        return json.dumps(await compare_votes(member_id_a, member_id_b, topic, take))

    @mcp.tool()
    async def get_bill_overview(search_term: str) -> str:
        """Get comprehensive bill overview in one call - combines search, details, stages, and publications | complete bill info, legislation overview, bill progress, full bill details | Use when you need complete information about a bill without multiple tool calls | Returns bill details, legislative stages, and associated publications. Combines: search_bills, get_bill_by_id, get_bill_stages, get_bill_publications. See also: get_bill_committees, get_member_bills.

        Args:
            search_term: Search term for bill title or content (e.g., 'Online Safety', 'Environment', 'Finance').

        Returns:
            Combined bill data: details, stages, and publications.
        """
        # Step 1: Search for bills
        search_url = f"{BILLS_API_BASE}/Bills?SearchTerm={quote(search_term)}"
        search_response = await get_result(search_url)
        bills_data = _parse_response(search_response)

        items = bills_data.get("items", [])
        if not items:
            return json.dumps(
                {
                    "error": f"No bills found matching '{search_term}'",
                    "search_result": bills_data,
                    "suggestions": SUGGESTIONS["bill"],
                }
            )

        # Get first matching bill
        bill = items[0]
        bill_id = bill.get("billId")
        if not bill_id:
            return json.dumps({"error": "Could not extract bill ID", "search_result": bills_data})

        # Step 2: Parallel requests for details, stages, publications
        details_url = f"{BILLS_API_BASE}/Bills/{bill_id}"
        stages_url = f"{BILLS_API_BASE}/Bills/{bill_id}/Stages"
        publications_url = f"{BILLS_API_BASE}/Bills/{bill_id}/Publications"

        details_task = get_result(details_url)
        stages_task = get_result(stages_url)
        publications_task = get_result(publications_url)

        details_response, stages_response, publications_response = await asyncio.gather(
            details_task, stages_task, publications_task
        )

        return json.dumps(
            {
                "bill_id": bill_id,
                "search_summary": bill,
                "details": _parse_response(details_response),
                "stages": _parse_response(stages_response),
                "publications": _parse_response(publications_response),
                "other_matches": len(items) - 1,
                "sources": {
                    "search": search_url,
                    "details": details_url,
                    "stages": stages_url,
                    "publications": publications_url,
                },
            }
        )

    @mcp.tool()
    async def get_member_bills(member_id: int, take: int = 20) -> str:
        """Get the bills a member has sponsored | bills introduced by MP, Private Members' Bills, sponsored legislation, member's bills | Use when asked which bills an MP or Lord has introduced or sponsored | Returns the member and their sponsored bills with current stage, most recently updated first. Combines: get_member_by_id, search_bills (member filter). See also: get_bill_overview, get_bill_committees.

        Args:
            member_id: Parliament member ID. Get from get_member_by_name. Example: 4514
            take: Number of bills to return (default 20).

        Returns:
            Member summary, total sponsored bills and bill summaries.
        """
        return json.dumps(await member_bills(member_id, take))

    @mcp.tool()
    async def get_committee_summary(topic: str) -> str:
        """Get comprehensive committee summary in one call - combines search, details, evidence, and publications | complete committee info, inquiry overview, committee research, full committee details | Use when you need complete information about a committee's work without multiple tool calls | Returns committee details, oral/written evidence, and publications. Combines: search_committees, get_committee_by_id, get_oral_evidence, get_written_evidence, get_publications. See also: get_committee_bills.

        Args:
            topic: Search term for committee name or subject area (e.g., 'Treasury', 'Health', 'Defence').

        Returns:
            Combined committee data: details, evidence, and publications.
        """
        # Step 1: Search for committees
        search_url = f"{COMMITTEES_API_BASE}/Committees?SearchTerm={quote(topic)}"
        search_response = await get_result(search_url)
        committees_data = _parse_response(search_response)

        items = committees_data.get("items", [])
        if not items:
            return json.dumps(
                {
                    "error": f"No committees found matching '{topic}'",
                    "search_result": committees_data,
                    "suggestions": SUGGESTIONS["committee"],
                }
            )

        # Get first matching committee
        committee = items[0]
        committee_id = committee.get("id")
        if not committee_id:
            return json.dumps(
                {"error": "Could not extract committee ID", "search_result": committees_data}
            )

        # Step 2: Parallel requests for details, evidence, publications
        details_url = f"{COMMITTEES_API_BASE}/Committees/{committee_id}"
        oral_evidence_url = build_url(
            f"{COMMITTEES_API_BASE}/OralEvidence", {"CommitteeId": committee_id, "Take": 10}
        )
        written_evidence_url = build_url(
            f"{COMMITTEES_API_BASE}/WrittenEvidence", {"CommitteeId": committee_id, "Take": 10}
        )
        publications_url = build_url(
            f"{COMMITTEES_API_BASE}/Publications", {"CommitteeId": committee_id, "Take": 10}
        )

        details_task = get_result(details_url)
        oral_task = get_result(oral_evidence_url)
        written_task = get_result(written_evidence_url)
        publications_task = get_result(publications_url)

        (
            details_response,
            oral_response,
            written_response,
            publications_response,
        ) = await asyncio.gather(details_task, oral_task, written_task, publications_task)

        return json.dumps(
            {
                "committee_id": committee_id,
                "search_summary": committee,
                "details": _parse_response(details_response),
                "oral_evidence": _parse_response(oral_response),
                "written_evidence": _parse_response(written_response),
                "publications": _parse_response(publications_response),
                "other_matches": len(items) - 1,
                "sources": {
                    "search": search_url,
                    "details": details_url,
                    "oral_evidence": oral_evidence_url,
                    "written_evidence": written_evidence_url,
                    "publications": publications_url,
                },
            }
        )

    @mcp.tool()
    async def get_bill_committees(bill_id: int) -> str:
        """Find the committees that examined a bill | which committee scrutinised this bill, legislative scrutiny, committee stage, select committee reports on a bill | Use when asked which committees looked at a bill, or to find committee evidence and reports on it | Returns the bill's committee stages (with sitting dates) and select committee business on it with the examining committee; items whose linked_bill_ids include the bill are confirmed links. Combines: get_bill_by_id, get_bill_stages, get_committee_business, get_committee_business_by_id, get_publications. See also: get_committee_bills (the reverse), get_bill_overview.

        Args:
            bill_id: Bill ID. Get from search_bills or get_bill_overview. Example: 3764

        Returns:
            Committee stages and committee business for the bill.
        """
        return json.dumps(await bill_committees(bill_id))

    @mcp.tool()
    async def get_committee_bills(committee_id: int, take: int = 10) -> str:
        """Find the bills a committee has examined | committee legislative scrutiny, bills scrutinised by committee, committee's bill work | Use when asked which bills a committee has looked at | Returns the committee and its legislative-scrutiny business, newest first, each with the bill it examined (current stage) and how the bill was matched (committee link or title). Combines: get_committee_by_id, get_committee_business, get_committee_business_by_id, get_bill_by_id. See also: get_bill_committees (the reverse), get_committee_summary.

        Args:
            committee_id: Committee ID. Get from search_committees or get_committee_summary. Example: 172 (Lords Constitution Committee)
            take: Number of most recent legislative scrutiny items to return (default 10, max 20).

        Returns:
            Committee summary and the bills it examined.
        """
        return json.dumps(await committee_bills(committee_id, take))

    @mcp.tool()
    async def search_parliament(query: str, take: int = 5) -> str:
        """Search across Parliament in one call - members, bills, committees, Hansard debates and written questions | search everything, find anything, cross-search, where is this mentioned, general search | Use as a starting point when you don't know which kind of record holds the answer | Returns the top matches and total counts for each kind of record, with the tool to call next for each. Combines: search_members, search_bills, search_committees, search_hansard_full, search_written_questions. See also: parliament_workflow (to plan a research approach).

        Args:
            query: Search text (e.g. 'Renters Rights', 'Starmer', 'Treasury', 'net zero').
            take: Number of top matches per kind of record (default 5).

        Returns:
            Per-category matches and totals.
        """
        return json.dumps(await search_everything(query, take))

    @mcp.tool()
    async def get_my_mp(postcode: str, topic: str | None = None) -> str:
        """Find your MP by postcode and get their full profile - combines postcode lookup, biography, interests, election result, and voting | who is my MP, postcode lookup, constituency MP, local representative | Use when someone wants to find their MP from a postcode | Returns MP profile with constituency, biography, interests, election results, and recent votes (and how they voted on a topic, if given). Combines: search_members (location), get_members_biography, search_roi, get_member_latest_election_result, get_member_voting, get_commons_voting_record_for_member. See also: get_mp_profile, check_mp_vote.

        Args:
            postcode: UK postcode to look up (e.g., 'SW1A 1AA', 'N1 9GU').
            topic: Optional topic keyword to filter votes (e.g., 'climate', 'NHS').

        Returns:
            Combined MP profile with constituency, biography, interests, election result, and voting data.
        """
        # Step 1: Search for MP by postcode (Location parameter)
        search_url = build_url(
            f"{MEMBERS_API_BASE}/Members/Search",
            {
                "Location": postcode,
                "IsCurrentMember": "true",
                "House": 1,
            },
        )
        search_response = await get_result(search_url)
        member_data = _parse_response(search_response)

        member_id = _extract_member_id(member_data)
        if not member_id:
            return json.dumps(
                {
                    "error": f"No current MP found for postcode '{postcode}'",
                    "search_result": member_data,
                    "suggestions": SUGGESTIONS["postcode"],
                }
            )

        basic_info = _first_search_item(member_data)

        # Step 2: Parallel detail fetches
        biography_url = f"{MEMBERS_API_BASE}/Members/{member_id}/Biography"
        interests_url = f"{INTERESTS_API_BASE}/Interests/?MemberId={member_id}"
        election_url = f"{MEMBERS_API_BASE}/Members/{member_id}/LatestElectionResult"
        voting_url = build_url(
            f"{MEMBERS_API_BASE}/Members/{member_id}/Voting",
            {"house": 1, "page": 1},
        )

        tasks = [
            get_result(biography_url),
            get_result(interests_url),
            get_result(election_url),
            get_result(voting_url),
        ]

        # Optionally fetch how the MP voted on the topic
        topic_votes_url = None
        if topic:
            topic_votes_url = member_voting_url(member_id, HOUSE_COMMONS, topic)
            tasks.append(get_result(topic_votes_url))

        results = await asyncio.gather(*tasks)

        biography_response = results[0]
        interests_response = results[1]
        election_response = results[2]
        voting_response = results[3]

        output: dict[str, Any] = {
            "postcode": postcode,
            "member_id": member_id,
            "basic_info": basic_info,
            "biography": _parse_response(biography_response),
            "registered_interests": _parse_response(interests_response),
            "latest_election": _parse_response(election_response),
            "recent_voting": _parse_response(voting_response),
            "sources": {
                "search": search_url,
                "biography": biography_url,
                "interests": interests_url,
                "election": election_url,
                "voting": voting_url,
            },
        }

        if topic and len(results) > 4:
            output["topic_votes"] = normalise_member_votes(_parse_response(results[4]))
            output["topic_searched"] = topic
            output["sources"]["topic_votes"] = topic_votes_url

        return json.dumps(output)
