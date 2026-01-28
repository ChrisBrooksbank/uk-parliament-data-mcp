"""Core tools for Parliament data assistant session management and guidance."""

from typing import Any

from mcp.server.fastmcp import FastMCP

SYSTEM_PROMPT = """You are a helpful assistant that answers questions using only data from UK Parliament MCP servers.
When the session begins, introduce yourself with a brief message such as:
"Hello! I'm a parliamentary data assistant. I can help answer questions using official data from the UK Parliament MCP APIs. Just ask me something, and I'll fetch what I can - and I'll always show you which sources I used."
When responding to user queries, you must:
Only retrieve and use data from the MCP API endpoints this server provides.
Avoid using any external sources or inferred knowledge.
After every response, append a list of all MCP API URLs used to generate the answer.
If no relevant data is available via the MCP API, state that clearly and do not attempt to fabricate a response.
Convert raw data into human-readable summaries while preserving accuracy, but always list the raw URLs used."""

GOODBYE_PROMPT = """You are now interacting as a normal assistant. There are no special restrictions or requirements for using UK Parliament MCP data. You may answer questions using any available data or knowledge, and you do not need to append MCP API URLs or limit yourself to MCP sources. Resume normal assistant behavior."""

QUICK_REFERENCE = """## Quick Reference: UK Parliament MCP Tools (86 tools)

### Key Conventions
- House IDs: 1 = Commons, 2 = Lords
- Dates: YYYY-MM-DD format
- Pagination: skip/take parameters (typical defaults: 20-30)
- IDs: Use search tools first to get member_id, bill_id, etc.

### Tool Categories & Entry Points
| Module | Tools | Start With |
|--------|-------|------------|
| members | 25 | get_member_by_name(name) |
| bills | 21 | search_bills(search_term) |
| committees | 12 | search_committees(search_term) |
| commons_votes | 5 | search_commons_divisions(search_term) |
| lords_votes | 5 | search_lords_divisions(search_term) |
| hansard | 1 | search_hansard(search_term) |
| oral_questions | 3 | search_early_day_motions(search_term) |
| interests | 3 | search_roi(member_id) |
| now | 2 | happening_now_in_commons() |
| whatson | 3 | search_calendar(from_date, to_date) |
| statutory_instruments | 2 | search_statutory_instruments() |
| treaties | 1 | search_treaties(search_text) |
| erskine_may | 1 | search_erskine_may(search_term) |

### Common Patterns
1. Search by name/term -> Get by ID -> Get related data
2. For MP voting: get_member_by_name() -> get_commons_voting_record_for_member()
3. For bill progress: search_bills() -> get_bill_stages()

Use parliament_guide(topic) for detailed tool information.
Use parliament_workflow(query) for step-by-step research planning."""

GUIDANCE_CONTENT = {
    "members": """## Members Tools (25 tools)

### Primary Search Tools
- search_members(name, location, party_id, house, is_current_member, skip, take) - Comprehensive member search with filters
- get_member_by_name(name) - Simple name search for MPs and Lords
- search_members_historical(name, date_to_search_for) - Find historical members at a point in time

### Member Details (require member_id from search)
- get_member_by_id(member_id) - Full member profile with party, constituency, status
- get_members_biography(member_id) - Education, career, background
- get_members_contact(member_id) - Phone, email, office addresses
- get_member_synopsis(member_id) - Brief summary
- get_member_experience(member_id) - Professional background
- get_member_focus(member_id) - Policy interests and expertise

### Member Activity
- get_member_voting(member_id, house) - Recent voting records (house: 1=Commons, 2=Lords)
- get_commons_voting_record_for_member(member_id) - All Commons votes by member
- get_lords_voting_record_for_member(member_id) - All Lords votes by member
- get_member_written_questions(member_id, skip, take) - Written questions submitted
- get_contributions(member_id, skip, take) - Speeches, questions, interventions
- edms_for_member_id(member_id) - Early Day Motions signed/sponsored

### Interests & Staff
- get_member_registered_interests(member_id, house) - Declared financial interests
- get_member_staff(member_id) - Office staff details

### Electoral Data
- get_member_latest_election_result(member_id) - Last election result
- get_constituencies(skip, take) - List all constituencies
- get_election_results_for_constituency(constituency_id, skip, take) - Historical results

### Reference Data
- parties_list_by_house(house) - Active parties (house: 1=Commons, 2=Lords)
- get_departments() - Government departments
- get_answering_bodies() - Which dept answers which questions

### Typical Workflow
1. Search: get_member_by_name("Keir Starmer") -> extract member_id
2. Profile: get_member_by_id(member_id) -> basic info
3. Details: get_members_biography(member_id) -> background
4. Activity: get_commons_voting_record_for_member(member_id) -> voting history""",
    "bills": """## Bills Tools (21 tools)

### Search & Discovery
- search_bills(search_term, skip, take) - Find bills by keyword
- get_recently_updated_bills(take) - Latest legislative activity
- get_bill_by_id(bill_id) - Full bill details with current stage
- get_bills_types() - Types of bills (Public, Private, Hybrid, etc.)

### Bill Progress & Stages
- get_bill_stages(bill_id) - Track legislative journey through Parliament
- get_stage_types() - Stage definitions (1st Reading, 2nd Reading, Committee, etc.)
- get_bill_stage_sittings(bill_id, stage_id) - When stage was debated

### Amendments
- get_bill_amendments(bill_id, skip, take) - All amendments proposed
- get_bill_stage_amendments(bill_id, stage_id) - Amendments at specific stage
- get_bill_amendment_by_id(amendment_id) - Detailed amendment info

### Publications & News
- get_bill_publications(bill_id) - Associated documents and papers
- get_publication_types() - Types of parliamentary publications
- get_bill_news(bill_id) - News articles about the bill

### Sponsors
- get_bill_sponsors(bill_id) - Who introduced/backs the bill

### RSS Feeds
- get_bills_rss() - RSS feed of recent bill updates
- get_rss_bill_stages() - RSS feed of stage changes

### Typical Workflow
1. Search: search_bills("climate") -> find bill_id
2. Overview: get_bill_by_id(bill_id) -> current status
3. Progress: get_bill_stages(bill_id) -> legislative journey
4. Details: get_bill_amendments(bill_id) -> proposed changes
5. Sponsors: get_bill_sponsors(bill_id) -> who supports it""",
    "votes": """## Voting Tools (10 tools: 5 Commons + 5 Lords)

### Commons Divisions
- search_commons_divisions(search_term, skip, take) - Find Commons votes by keyword
- get_commons_division_by_id(division_id) - Full voting details with lists
- get_commons_voting_record_for_member(member_id, skip, take) - All votes by MP
- get_commons_divisions_by_member_grouped_by_party(member_id) - Votes grouped by party alignment
- get_commons_divisions_by_member_vote_count(member_id) - Vote tallies

### Lords Divisions
- search_lords_divisions(search_term, skip, take) - Find Lords votes by keyword
- get_lords_division_by_id(division_id) - Full voting details with lists
- get_lords_voting_record_for_member(member_id, skip, take) - All votes by Lord
- get_lords_divisions_by_member_grouped_by_party(member_id) - Votes grouped by party alignment
- get_lords_divisions_by_member_vote_count(member_id) - Vote tallies

### Key Concepts
- Division: A formal recorded vote in Parliament
- Aye/Content: Voting yes (Commons uses Aye, Lords uses Content)
- No/Not Content: Voting no (Commons uses No, Lords uses Not Content)
- Teller: Member who counts votes

### Typical Workflow
1. Find division: search_commons_divisions("Rwanda") -> get division_id
2. Full results: get_commons_division_by_id(division_id) -> see all votes
3. Member record: get_commons_voting_record_for_member(member_id) -> voting history""",
    "committees": """## Committee Tools (12 tools)

### Search & Discovery
- search_committees(search_term, skip, take) - Find committees by topic
- get_committee_by_id(committee_id) - Full committee details

### Meetings & Events
- get_committee_meetings(from_date, to_date) - Find meetings by date range (YYYY-MM-DD)
- get_committee_event_by_id(committee_id, event_id) - Specific meeting details

### Members & Participants
- get_committee_members(committee_id, skip, take) - Current committee members
- get_committee_attendees_for_event(committee_id, event_id) - Who attended meeting

### Evidence & Publications
- get_oral_evidence(committee_id, skip, take) - Oral evidence transcripts
- get_written_evidence(committee_id, skip, take) - Written submissions
- get_committee_publications(committee_id, skip, take) - Reports and documents
- get_committee_publication_document_chapters(committee_id, publication_id) - Document sections

### Types
- get_committee_types() - Select Committee, Joint Committee, etc.

### Typical Workflow
1. Search: search_committees("health") -> find committee_id
2. Details: get_committee_by_id(committee_id) -> scope and membership
3. Activity: get_committee_meetings("2024-01-01", "2024-12-31") -> recent meetings
4. Evidence: get_oral_evidence(committee_id) -> witness testimonies
5. Reports: get_committee_publications(committee_id) -> published reports""",
    "hansard": """## Hansard Tools (1 tool)

### Search
- search_hansard(search_term, house, skip, take) - Search parliamentary record

### About Hansard
Hansard is the official verbatim record of everything said in Parliament:
- Debates in the Commons and Lords chambers
- Questions to ministers
- Statements and announcements
- Interventions and points of order

### Parameters
- search_term: Keywords to search for
- house: 1 = Commons, 2 = Lords (optional)
- skip/take: Pagination

### Tips
- Search for specific topics, MP names, or phrases
- Results include date, speaker, and context
- Use date ranges to narrow results
- Combine with member tools to find who said what""",
    "questions": """## Questions & Motions Tools (3 tools)

### Early Day Motions (EDMs)
- search_early_day_motions(search_term, skip, take) - Find EDMs by topic
- edms_for_member_id(member_id) - EDMs signed/sponsored by a member

### Oral Questions
- search_question_times(from_date, to_date, skip, take) - Find question sessions

### About EDMs
Early Day Motions are formal notices of a motion:
- Used to draw attention to issues
- MPs can sign EDMs to show support
- Rarely debated but show parliamentary sentiment

### About Oral Questions
Question Time sessions where MPs/Lords ask ministers:
- Prime Minister's Questions (PMQs) - Wednesdays
- Departmental questions - rotating schedule
- Urgent Questions - same-day topical issues""",
    "interests": """## Register of Interests Tools (3 tools)

### Search & Browse
- search_roi(member_id) - Get member's registered interests
- interests_categories() - List interest categories
- interests_registers() - Available registers

### About Register of Interests
MPs and Lords must declare:
- Employment and earnings
- Donations and gifts
- Shareholdings
- Property
- Family members' interests

### Interest Categories
1. Employment and earnings
2. Donations (property, goods, services)
3. Gifts, benefits, hospitality
4. Visits outside UK
5. Gifts and benefits from UK sources
6. Land and property
7. Shareholdings
8. Miscellaneous
9. Family members employed
10. Family members with interests

### Typical Workflow
1. Find member: get_member_by_name("Name") -> member_id
2. Get interests: search_roi(member_id) -> declared interests
3. Understand categories: interests_categories() -> what each means""",
    "live": """## Live Activity & Calendar Tools (5 tools)

### What's Happening Now
- happening_now_in_commons() - Current Commons chamber activity
- happening_now_in_lords() - Current Lords chamber activity

### Calendar & Schedule
- search_calendar(from_date, to_date, house, skip, take) - Find scheduled events
- get_session_days(from_date, to_date) - Parliamentary sitting days
- get_non_sitting_days() - Recesses, bank holidays, etc.

### Parameters
- Dates: YYYY-MM-DD format
- house: 1 = Commons, 2 = Lords (optional)

### What "Now" Tools Return
- Current business being debated
- Speaker/chair information
- Estimated timing
- Link to live stream

### Tips
- "Now" tools only work when Parliament is sitting
- Check get_non_sitting_days() for recess periods
- Calendar includes debates, questions, legislation""",
    "legislation": """## Legislation Tools (3 tools)

### Statutory Instruments
- search_statutory_instruments(search_term, skip, take) - Find SIs
- get_statutory_instruments_business_items(statutory_instrument_id) - SI progress

### Treaties
- search_treaties(search_text, skip, take) - Find international treaties

### About Statutory Instruments
SIs are secondary/delegated legislation:
- Made under powers in primary Acts
- Subject to affirmative or negative procedure
- Cover detailed regulations

### About Treaties
International agreements requiring parliamentary scrutiny:
- Trade agreements
- Extradition treaties
- Mutual legal assistance
- Environmental agreements

### Typical Workflow
1. Search: search_statutory_instruments("environment")
2. Details: get_statutory_instruments_business_items(si_id) -> parliamentary progress""",
    "procedures": """## Procedure Tools (3 tools)

### Erskine May
- search_erskine_may(search_term) - Search parliamentary procedure manual

### Bill Reference
- get_bills_types() - Types of bills (from bills module)
- get_stage_types() - Stage definitions (from bills module)

### About Erskine May
"Parliamentary Practice" - the authoritative guide to:
- House procedures and rules
- Precedents and conventions
- Powers and privileges
- Committee procedures

### Bill Types
- Public Bills: Change general law
- Private Bills: Affect specific individuals/organizations
- Hybrid Bills: Mix of public and private
- Private Members' Bills: Introduced by backbenchers

### Bill Stages
1. First Reading: Formal introduction
2. Second Reading: Debate on principles
3. Committee Stage: Line-by-line scrutiny
4. Report Stage: House considers amendments
5. Third Reading: Final debate
6. Lords/Commons stages: Mirror process in other House
7. Royal Assent: Becomes law""",
    "all": """## All UK Parliament MCP Tools (86 tools)

### Members (25 tools)
Search: search_members, get_member_by_name, search_members_historical
Details: get_member_by_id, get_members_biography, get_members_contact, get_member_synopsis, get_member_experience, get_member_focus
Activity: get_member_voting, get_commons_voting_record_for_member, get_lords_voting_record_for_member, get_member_written_questions, get_contributions, edms_for_member_id
Interests: get_member_registered_interests, get_member_staff
Electoral: get_member_latest_election_result, get_constituencies, get_election_results_for_constituency
Reference: parties_list_by_house, get_departments, get_answering_bodies

### Bills (21 tools)
Search: search_bills, get_recently_updated_bills, get_bill_by_id, get_bills_types
Stages: get_bill_stages, get_stage_types, get_bill_stage_sittings
Amendments: get_bill_amendments, get_bill_stage_amendments, get_bill_amendment_by_id
Publications: get_bill_publications, get_publication_types, get_bill_news
Sponsors: get_bill_sponsors
RSS: get_bills_rss, get_rss_bill_stages

### Votes (10 tools)
Commons: search_commons_divisions, get_commons_division_by_id, get_commons_voting_record_for_member, get_commons_divisions_by_member_grouped_by_party, get_commons_divisions_by_member_vote_count
Lords: search_lords_divisions, get_lords_division_by_id, get_lords_voting_record_for_member, get_lords_divisions_by_member_grouped_by_party, get_lords_divisions_by_member_vote_count

### Committees (12 tools)
Search: search_committees, get_committee_by_id
Meetings: get_committee_meetings, get_committee_event_by_id
Members: get_committee_members, get_committee_attendees_for_event
Evidence: get_oral_evidence, get_written_evidence
Publications: get_committee_publications, get_committee_publication_document_chapters
Types: get_committee_types

### Other Tools (18 tools)
Hansard: search_hansard
Questions: search_early_day_motions, edms_for_member_id, search_question_times
Interests: search_roi, interests_categories, interests_registers
Live: happening_now_in_commons, happening_now_in_lords
Calendar: search_calendar, get_session_days, get_non_sitting_days
Legislation: search_statutory_instruments, get_statutory_instruments_business_items, search_treaties
Procedures: search_erskine_may
Session: hello_parliament, goodbye_parliament, parliament_guide, parliament_workflow""",
    "conventions": """## UK Parliament MCP Conventions

### House Identification
- House 1 = House of Commons (MPs)
- House 2 = House of Lords (Lords/Peers)
- Some tools accept house as integer, others as string ("Commons"/"Lords")

### Date Format
- Always use YYYY-MM-DD (e.g., "2024-03-15")
- Date ranges: from_date/start_date and to_date/end_date

### Pagination
- skip: Number of records to skip (default: 0)
- take: Number of records to return (typical: 20-30, max: 100)
- Use skip/take for paging through large result sets

### IDs
- member_id: Unique identifier for MPs and Lords
- bill_id: Unique identifier for legislation
- division_id: Unique identifier for votes
- committee_id: Unique identifier for committees
- Always get IDs from search results first, then use in detail tools

### Response Format
- All tools return JSON from Parliament APIs
- Successful: {"url": "...", "data": {...}}
- Error: {"url": "...", "error": "...", "statusCode": N}

### Naming Conventions
- search_* : Search/discovery tools
- get_* : Retrieve specific item by ID or parameters
- *_by_id : Requires specific ID parameter
- *_for_member : Requires member_id parameter""",
    "workflows": """## Common Research Workflows

### MP Voting Research
Goal: Find how an MP voted on a topic
1. get_member_by_name(name) -> member_id
2. search_commons_divisions(topic) -> find relevant division_id
3. get_commons_division_by_id(division_id) -> check Ayes/Noes lists

### Bill Tracking
Goal: Track a bill's progress through Parliament
1. search_bills(topic) -> bill_id
2. get_bill_by_id(bill_id) -> current status
3. get_bill_stages(bill_id) -> full journey
4. get_bill_amendments(bill_id) -> proposed changes

### Committee Investigation
Goal: Find what a committee examined
1. search_committees(topic) -> committee_id
2. get_committee_by_id(committee_id) -> scope
3. get_oral_evidence(committee_id) -> witness testimony
4. get_committee_publications(committee_id) -> reports

### Conflict of Interest Research
Goal: Check MP's financial interests
1. get_member_by_name(name) -> member_id
2. search_roi(member_id) -> declared interests
3. interests_categories() -> understand categories

### Live Parliament Activity
Goal: See what's happening now
1. happening_now_in_commons() or happening_now_in_lords()
2. search_calendar(today, today) -> today's schedule

### Historical Voting
Goal: Research past votes on topic
1. search_commons_divisions(topic) -> list of votes
2. get_commons_division_by_id(division_id) -> full results
3. Repeat for key divisions

### MP Background Research
Goal: Full profile of an MP
1. get_member_by_name(name) -> member_id
2. get_member_by_id(member_id) -> basic info
3. get_members_biography(member_id) -> background
4. get_member_registered_interests(member_id, 1) -> interests
5. get_commons_voting_record_for_member(member_id) -> votes

### Hansard Search
Goal: Find what was said in Parliament
1. search_hansard(topic, house) -> speeches and debates
2. Filter by date, speaker, or house

### Electoral Research
Goal: Constituency election history
1. get_constituencies() -> find constituency_id
2. get_election_results_for_constituency(constituency_id) -> all results

### Legislation Search
Goal: Find regulations and treaties
1. search_statutory_instruments(topic) -> SIs
2. search_treaties(topic) -> international agreements""",
}

WORKFLOW_PATTERNS: list[dict[str, Any]] = [
    {
        "keywords": ["vote", "voted", "voting", "division", "aye", "noes"],
        "name": "MP Voting Research",
        "description": "Find how an MP voted on a specific topic or bill",
        "steps": [
            {
                "step": 1,
                "tool": "get_member_by_name(name)",
                "purpose": "Get the member_id for the MP",
                "output": "member_id (integer)",
            },
            {
                "step": 2,
                "tool": "search_commons_divisions(search_term)",
                "purpose": "Find divisions (votes) on the topic",
                "output": "List of divisions with division_id",
            },
            {
                "step": 3,
                "tool": "get_commons_division_by_id(division_id)",
                "purpose": "Get full voting list including how members voted",
                "output": "Aye and No lists with member names",
            },
        ],
        "alternative": "Use get_commons_voting_record_for_member(member_id) for all votes by an MP",
    },
    {
        "keywords": ["bill", "legislation", "law", "act", "progress", "stage"],
        "name": "Bill Tracking",
        "description": "Track a bill's progress through Parliament",
        "steps": [
            {
                "step": 1,
                "tool": "search_bills(search_term)",
                "purpose": "Find the bill by keyword",
                "output": "bill_id and current status",
            },
            {
                "step": 2,
                "tool": "get_bill_by_id(bill_id)",
                "purpose": "Get full bill details",
                "output": "Title, summary, sponsors, current stage",
            },
            {
                "step": 3,
                "tool": "get_bill_stages(bill_id)",
                "purpose": "See the legislative journey",
                "output": "All stages with dates and houses",
            },
            {
                "step": 4,
                "tool": "get_bill_amendments(bill_id)",
                "purpose": "See proposed changes",
                "output": "List of amendments with sponsors",
            },
        ],
    },
    {
        "keywords": ["committee", "inquiry", "evidence", "witness", "hearing"],
        "name": "Committee Research",
        "description": "Find what a committee examined on a topic",
        "steps": [
            {
                "step": 1,
                "tool": "search_committees(search_term)",
                "purpose": "Find relevant committee",
                "output": "committee_id",
            },
            {
                "step": 2,
                "tool": "get_committee_by_id(committee_id)",
                "purpose": "Get committee details and scope",
                "output": "Committee info and current inquiries",
            },
            {
                "step": 3,
                "tool": "get_oral_evidence(committee_id)",
                "purpose": "Find witness testimonies",
                "output": "Oral evidence transcripts",
            },
            {
                "step": 4,
                "tool": "get_committee_publications(committee_id)",
                "purpose": "Find reports and conclusions",
                "output": "Published reports",
            },
        ],
    },
    {
        "keywords": ["interest", "conflict", "financial", "donation", "declare"],
        "name": "Interests/Conflicts Research",
        "description": "Check an MP's declared financial interests",
        "steps": [
            {
                "step": 1,
                "tool": "get_member_by_name(name)",
                "purpose": "Get the member_id",
                "output": "member_id",
            },
            {
                "step": 2,
                "tool": "search_roi(member_id)",
                "purpose": "Get all declared interests",
                "output": "List of registered interests",
            },
            {
                "step": 3,
                "tool": "interests_categories()",
                "purpose": "Understand what each category means",
                "output": "Category definitions",
            },
        ],
    },
    {
        "keywords": ["now", "today", "happening", "live", "current", "sitting"],
        "name": "Live Parliament Activity",
        "description": "See what's happening in Parliament right now",
        "steps": [
            {
                "step": 1,
                "tool": "happening_now_in_commons() or happening_now_in_lords()",
                "purpose": "Get current chamber activity",
                "output": "Current business, speaker, timing",
            },
            {
                "step": 2,
                "tool": "search_calendar(today_date, today_date)",
                "purpose": "See full day's schedule",
                "output": "All scheduled events for today",
            },
        ],
        "note": "Only works when Parliament is sitting - check get_non_sitting_days() for recesses",
    },
    {
        "keywords": ["background", "biography", "profile", "who is", "about"],
        "name": "MP Background Research",
        "description": "Get comprehensive information about an MP",
        "steps": [
            {
                "step": 1,
                "tool": "get_member_by_name(name)",
                "purpose": "Find the member",
                "output": "member_id and basic info",
            },
            {
                "step": 2,
                "tool": "get_member_by_id(member_id)",
                "purpose": "Get full profile",
                "output": "Party, constituency, status",
            },
            {
                "step": 3,
                "tool": "get_members_biography(member_id)",
                "purpose": "Get background",
                "output": "Education, career, personal",
            },
            {
                "step": 4,
                "tool": "get_member_registered_interests(member_id, house=1)",
                "purpose": "Get declared interests",
                "output": "Financial interests",
            },
        ],
    },
    {
        "keywords": ["said", "speech", "debate", "hansard", "parliament said"],
        "name": "Hansard Search",
        "description": "Find what was said in Parliament about a topic",
        "steps": [
            {
                "step": 1,
                "tool": "search_hansard(search_term, house)",
                "purpose": "Search parliamentary record",
                "output": "Speeches and debates matching topic",
            },
        ],
        "tips": [
            "Use specific phrases for better results",
            "Filter by house (1=Commons, 2=Lords) if needed",
            "Results include speaker, date, and context",
        ],
    },
    {
        "keywords": ["election", "constituency", "result", "majority", "swing"],
        "name": "Electoral Research",
        "description": "Find election results for a constituency",
        "steps": [
            {
                "step": 1,
                "tool": "get_constituencies()",
                "purpose": "Find constituency ID",
                "output": "List of constituencies with IDs",
            },
            {
                "step": 2,
                "tool": "get_election_results_for_constituency(constituency_id)",
                "purpose": "Get historical results",
                "output": "All election results with votes and majorities",
            },
        ],
    },
    {
        "keywords": ["edm", "early day motion", "support", "signed"],
        "name": "Early Day Motion Research",
        "description": "Find EDMs on a topic or signed by an MP",
        "steps": [
            {
                "step": 1,
                "tool": "search_early_day_motions(search_term)",
                "purpose": "Find EDMs by topic",
                "output": "List of EDMs with signatories",
            },
        ],
        "alternative": "Use edms_for_member_id(member_id) to find EDMs signed by a specific MP",
    },
    {
        "keywords": ["treaty", "international", "agreement", "trade deal"],
        "name": "Treaty Research",
        "description": "Find international treaties and agreements",
        "steps": [
            {
                "step": 1,
                "tool": "search_treaties(search_text)",
                "purpose": "Find treaties by keyword",
                "output": "Treaty details and status",
            },
        ],
    },
]


def _format_workflow(pattern: dict[str, Any]) -> str:
    """Format a workflow pattern into readable text."""
    lines = [
        f"## Workflow: {pattern['name']}",
        "",
        pattern["description"],
        "",
        "### Steps",
    ]

    for step in pattern["steps"]:
        lines.append(f"**Step {step['step']}**: `{step['tool']}`")
        lines.append(f"- Purpose: {step['purpose']}")
        lines.append(f"- Output: {step['output']}")
        lines.append("")

    if "alternative" in pattern:
        lines.append(f"**Alternative**: {pattern['alternative']}")
        lines.append("")

    if "note" in pattern:
        lines.append(f"**Note**: {pattern['note']}")
        lines.append("")

    if "tips" in pattern:
        lines.append("**Tips**:")
        for tip in pattern["tips"]:
            lines.append(f"- {tip}")
        lines.append("")

    return "\n".join(lines)


def _suggest_general_approach(query: str) -> str:
    """Suggest a general approach when no specific workflow matches."""
    return f"""## Research Approach for: "{query}"

No specific workflow pattern matched. Here's a general approach:

### Step 1: Identify What You Need
- **People**: Use get_member_by_name() to find MPs/Lords
- **Legislation**: Use search_bills() to find bills
- **Votes**: Use search_commons_divisions() or search_lords_divisions()
- **Committees**: Use search_committees()
- **Debates**: Use search_hansard()

### Step 2: Get IDs from Search Results
Most detail tools require an ID (member_id, bill_id, etc.) from search results.

### Step 3: Drill Down
Use specific tools like get_member_by_id(), get_bill_stages(), etc.

### Available Topics for Detailed Guidance
Use parliament_guide(topic) with one of:
- members, bills, votes, committees, hansard
- questions, interests, live, legislation, procedures
- all, conventions, workflows"""


def register_tools(mcp: FastMCP) -> None:
    """Register core tools with the MCP server."""

    @mcp.tool()
    async def hello_parliament() -> str:
        """Initialize Parliament data assistant with system prompt | setup, configuration, start session, getting started, how to use, instructions | Use FIRST when beginning parliamentary research to get proper assistant behavior and data handling guidelines | Returns system prompt for optimal parliamentary data interaction"""
        return f"{SYSTEM_PROMPT}\n\n---\n\n{QUICK_REFERENCE}"

    @mcp.tool()
    async def goodbye_parliament() -> str:
        """End Parliament session and restore normal assistant behavior | exit, quit, finish session, reset, normal mode, end parliamentary mode | Use when finished with parliamentary research to return to standard assistant behavior | Removes parliamentary data restrictions and requirements"""
        return GOODBYE_PROMPT

    @mcp.tool()
    async def parliament_guide(topic: str) -> str:
        """Get detailed guidance for a specific Parliament data domain | tool help, API reference, how to use tools, available tools | Use when you need detailed information about tools in a specific area | Returns comprehensive guidance including tool names, parameters, and typical workflows

        Args:
            topic: Domain to get guidance for. Options: members, bills, votes, committees, hansard, questions, interests, live, legislation, procedures, all, conventions, workflows
        """
        topic_lower = topic.lower().strip()

        if topic_lower not in GUIDANCE_CONTENT:
            available = ", ".join(sorted(GUIDANCE_CONTENT.keys()))
            return f"Topic '{topic}' not recognized.\n\nAvailable topics: {available}"

        return GUIDANCE_CONTENT[topic_lower]

    @mcp.tool()
    async def parliament_workflow(query: str) -> str:
        """Get step-by-step workflow guidance for a parliamentary research task | workflow planning, multi-step tasks, research planning, how to find | Use when you have a specific research question and need to plan which tools to use in sequence | Returns recommended sequence of tools with parameters and expected data flow

        Args:
            query: Research question or task description. Examples: "How did my MP vote on climate?", "Track a bill's progress", "Find committee evidence on NHS"
        """
        query_lower = query.lower()

        # Find matching workflow pattern
        for pattern in WORKFLOW_PATTERNS:
            if any(keyword in query_lower for keyword in pattern["keywords"]):
                return _format_workflow(pattern)

        # No match - provide general guidance
        return _suggest_general_approach(query)
