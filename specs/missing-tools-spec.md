# Missing Parliament API Endpoints

## Overview

Add ~49 missing API endpoints across 7 APIs to increase coverage from 163 to ~212 tools. Each tool needs an MCP tool function, CLI command, and test.

## Source

Full gap analysis in `AddMissingTools.md` at project root.

## Requirements

### Phase 1: High-Value Gaps (29 endpoints)

#### 1A. Members API — 8 new tools
- [ ] `search_constituencies` — `/api/Location/Constituency/Search`
- [ ] `get_constituency_by_id` — `/api/Location/Constituency/{id}`
- [ ] `get_constituency_latest_election` — `/api/Location/Constituency/{id}/ElectionResult/Latest`
- [ ] `get_constituency_election_result` — `/api/Location/Constituency/{id}/ElectionResult/{electionId}`
- [ ] `get_constituency_representations` — `/api/Location/Constituency/{id}/Representations`
- [ ] `get_constituency_synopsis` — `/api/Location/Constituency/{id}/Synopsis`
- [ ] `search_historical_members` — `/api/Members/SearchHistorical`
- [ ] `get_speaker_and_deputies` — `/api/Posts/SpeakerAndDeputies/{forDate}`

#### 1B. Hansard API — 10 new tools
- [ ] `get_hansard_currently_processing` — `/overview/currentlyprocessing.json`
- [ ] `get_hansard_first_year` — `/overview/firstyear.json`
- [ ] `get_hansard_pdfs_for_day` — `/overview/pdfsforday.json`
- [ ] `get_hansard_speakers_for_day` — `/overview/speakerslist/{date}/{house}`
- [ ] `search_committee_debates` — `/search/committeedebates.json`
- [ ] `search_hansard_committees` — `/search/committees.json`
- [ ] `get_debate_by_column` — `/search/debatebycolumn.json`
- [ ] `get_debate_by_external_id` — `/search/debatebyexternalid.json`
- [ ] `search_hansard_petitions` — `/search/petitions.json`
- [ ] `get_hansard_timeline_stats` — `/timeline-stats.json`

#### 1C. What's On API — 11 new tools
- [ ] `get_calendar_categories` — `/calendar/categories/list`
- [ ] `get_event_type_metadata` — `/calendar/events/EventTypeMetaData`
- [ ] `get_parliamentary_diary` — `/calendar/events/diary`
- [ ] `get_speaker_events` — `/calendar/events/speakers`
- [ ] `get_calendar_locations` — `/calendar/locations/list`
- [ ] `get_annulment_date` — `/calendar/proceduraldates/annulmentdate/forDate`
- [ ] `get_last_sitting_date` — `/calendar/proceduraldates/{house}/lastsittingdate`
- [ ] `get_session_by_id` — `/calendar/sessions/byid/{sessionId}`
- [ ] `get_session_for_date` — `/calendar/sessions/fordate/{date}`
- [ ] `get_calendar_tags` — `/calendar/tags/list`
- [ ] `get_calendar_types` — `/calendar/types/list`

### Phase 2: Medium-Value Gaps (20 endpoints)

#### 2A. Statutory Instruments API — 8 new tools
- [ ] `get_si_business_item` — `/api/v1/BusinessItem/{id}`
- [ ] `get_laying_bodies` — `/api/v1/LayingBody`
- [ ] `get_si_procedures` — `/api/v1/Procedure`
- [ ] `get_si_procedure` — `/api/v1/Procedure/{id}`
- [ ] `search_proposed_negative_sis` — `/api/v1/ProposedNegativeStatutoryInstrument`
- [ ] `get_proposed_negative_si` — `/api/v1/ProposedNegativeStatutoryInstrument/{id}`
- [ ] `get_proposed_negative_si_business_items` — `/api/v1/ProposedNegativeStatutoryInstrument/{id}/BusinessItems`
- [ ] `get_si_timeline_business_items` — `/api/v2/Timeline/{timelineId}/BusinessItems`

#### 2B. Interests API — 3 new tools
- [ ] `get_interest_category` — `/api/v1/Categories/{id}`
- [ ] `get_interest_by_id` — `/api/v1/Interests/{id}`
- [ ] `get_register_by_id` — `/api/v1/Registers/{id}`

#### 2C. Committees API — 5 new tools
- [ ] `get_bill_petition_by_id` — `/api/BillPetitions/{id}`
- [ ] `get_broadcast_meetings` — `/api/Broadcast/Meetings`
- [ ] `get_archived_publication_links` — `/api/Committees/{id}/ArchivedPublicationLinks`
- [ ] `search_event_activities` — `/api/Events/Activities`
- [ ] `get_submission_period` — `/api/SubmissionPeriod/{id}`

#### 2D. Parliament Now API — 1 new tool
- [ ] `get_annunciator_by_date` — `/api/Message/message/{annunciator}/{date}`

## Per-Tool Work

For each tool:
1. Add `@mcp.tool()` in `tools/<module>.py`
2. Add `@app.command()` in `cli/<module>.py`
3. Add test(s) in `tests/`
4. Follow existing patterns in each file

## Post-Implementation

- Update tool count in `CLAUDE.md` (163 → ~212)
- Update tool count in `tools/core.py` guidance text
- Update CLI command counts in `CLAUDE.md`
- Update `__init__.py` version
- Run full validation: `ruff check src/ && ruff format --check src/ && mypy src/ && pytest`

## Acceptance Criteria

- [ ] All ~49 new tools registered and callable via MCP
- [ ] All ~49 new CLI commands working
- [ ] Tests pass for all new tools
- [ ] `ruff check`, `mypy`, `pytest` all green
- [ ] CLAUDE.md counts updated

## Out of Scope

- Binary download endpoints (portraits, PDFs, documents)
- GeoJSON endpoints
- Redirect endpoints
- Duplicate/overlapping endpoints
