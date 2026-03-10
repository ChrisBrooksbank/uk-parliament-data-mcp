# Gap Analysis: Missing Parliament API Endpoints

## Summary

| API | Spec Endpoints | Implemented | Missing (useful) | Coverage |
|-----|---------------|-------------|-------------------|----------|
| **bills** | 21 | 21 | 0 | 100% |
| **committees** | 38 | 26 | 8 | 68% |
| **commonsvotes** | 5 | 5 | 0 | 100% |
| **erskinemay** | 11 | 11 | 0 | 100% |
| **hansard** | 32 | 20 | 10 | 63% |
| **interests** | 8 | 3 | 3 | 38% |
| **lordsvotes** | 5 | 5 | 0 | 100% |
| **members** | 43 | 30 | 8 | 70% |
| **oralquestions** | 4 | 5 | 0 | 100% |
| **parliamentnow** | 2 | 2 | 1 | 50% |
| **statutoryinstruments** | 16 | 5 | 8 | 31% |
| **treaties** | 6 | 6 | 0 | 100% |
| **whatson** | 19 | 8 | 11 | 42% |
| **writtenquestions** | 7 | 7 | 0 | 100% |
| **TOTAL** | **217** | **163** | **~49** | **75%** |

*~5 endpoints excluded as binary downloads/images/redirects not suitable for MCP*

---

## Already Complete (no work needed)

- **bills** (21/21), **commonsvotes** (5/5), **lordsvotes** (5/5), **erskinemay** (11/11), **oralquestions** (4/4), **treaties** (6/6), **writtenquestions** (7/7)

---

## Phase 1: High-Value Gaps (28 endpoints across 4 APIs)

### 1A. Members API — 8 new tools + CLI commands

| Endpoint | Proposed Tool Name | Value |
|----------|-------------------|-------|
| `/api/Location/Constituency/Search` | `search_constituencies` | High — find constituency by name/postcode |
| `/api/Location/Constituency/{id}` | `get_constituency_by_id` | High — constituency details |
| `/api/Location/Constituency/{id}/ElectionResult/Latest` | `get_constituency_latest_election` | High — latest result for a constituency |
| `/api/Location/Constituency/{id}/ElectionResult/{electionId}` | `get_constituency_election_result` | Medium — specific election result |
| `/api/Location/Constituency/{id}/Representations` | `get_constituency_representations` | Medium — who has represented it |
| `/api/Location/Constituency/{id}/Synopsis` | `get_constituency_synopsis` | Medium — constituency summary |
| `/api/Location/Browse/{locationType}/{locationName}` | `browse_locations` | Medium — browse places |
| `/api/Members/SearchHistorical` | `search_historical_members` | High — former MPs |
| `/api/Posts/SpeakerAndDeputies/{forDate}` | `get_speaker_and_deputies` | Medium — current Speaker/Deputies |
| `/api/LordsInterests/Register` | `get_lords_interests_register` | Medium — Lords ROI |

*Skip: Portrait (binary), Thumbnail (binary), Departments/{id}/Logo (binary), Geometry (GeoJSON — niche), Departments/{type} (duplicates existing)*

### 1B. Hansard API — 10 new tools + CLI commands

| Endpoint | Proposed Tool Name | Value |
|----------|-------------------|-------|
| `/overview/currentlyprocessing.{format}` | `get_hansard_currently_processing` | High — what's being transcribed now |
| `/overview/firstyear.{format}` | `get_hansard_first_year` | Low — reference data |
| `/overview/pdfsforday.{format}` | `get_hansard_pdfs_for_day` | Medium — links to official PDFs |
| `/overview/speakerslist/{date}/{house}` | `get_hansard_speakers_for_day` | High — who spoke on a day |
| `/search/committeedebates.{format}` | `search_committee_debates` | High — committee Hansard |
| `/search/committees.{format}` | `search_hansard_committees` | Medium — committees in Hansard |
| `/search/debatebycolumn.{format}` | `get_debate_by_column` | Medium — lookup by column ref |
| `/search/debatebyexternalid.{format}` | `get_debate_by_external_id` | Medium — lookup by external ID |
| `/search/petitions.{format}` | `search_hansard_petitions` | Medium — petitions in Hansard |
| `/timeline-stats.{format}` | `get_hansard_timeline_stats` | Medium — contribution stats over time |

*Skip: `/search/parlisearchredirect` (redirect, not data), `/pdfs/pdf` (binary download)*

### 1C. What's On API — 11 new tools + CLI commands

| Endpoint | Proposed Tool Name | Value |
|----------|-------------------|-------|
| `/calendar/categories/list` | `get_calendar_categories` | Medium — reference data |
| `/calendar/events/EventTypeMetaData` | `get_event_type_metadata` | Low — reference data |
| `/calendar/events/diary` | `get_parliamentary_diary` | High — daily diary view |
| `/calendar/events/speakers` | `get_speaker_events` | Medium — Speaker's events |
| `/calendar/locations/list` | `get_calendar_locations` | Medium — locations reference |
| `/calendar/proceduraldates/annulmentdate/forDate` | `get_annulment_date` | Medium — SI annulment deadline |
| `/calendar/proceduraldates/{house}/lastsittingdate` | `get_last_sitting_date` | Medium — last sitting (whatson) |
| `/calendar/sessions/byid/{sessionId}` | `get_session_by_id` | Medium — session details |
| `/calendar/sessions/fordate/{date}` | `get_session_for_date` | Medium — what session a date falls in |
| `/calendar/tags/list` | `get_calendar_tags` | Low — reference data |
| `/calendar/types/list` | `get_calendar_types` | Low — reference data |

---

## Phase 2: Medium-Value Gaps (16 endpoints across 3 APIs)

### 2A. Statutory Instruments API — 8 new tools + CLI commands

| Endpoint | Proposed Tool Name | Value |
|----------|-------------------|-------|
| `/api/v1/BusinessItem/{id}` | `get_si_business_item` | Medium — specific business item |
| `/api/v1/LayingBody` | `get_laying_bodies` | Medium — who lays SIs |
| `/api/v1/Procedure` | `get_si_procedures` | Medium — procedure types |
| `/api/v1/Procedure/{id}` | `get_si_procedure` | Medium — specific procedure |
| `/api/v1/ProposedNegativeStatutoryInstrument` | `search_proposed_negative_sis` | High — proposed negatives |
| `/api/v1/ProposedNegativeStatutoryInstrument/{id}` | `get_proposed_negative_si` | High — specific proposed negative |
| `/api/v1/ProposedNegativeStatutoryInstrument/{id}/BusinessItems` | `get_proposed_negative_si_business_items` | Medium — tracking |
| `/api/v2/Timeline/{timelineId}/BusinessItems` | `get_si_timeline_business_items` | Medium — timeline view |

### 2B. Interests API — 3 new tools + CLI commands

| Endpoint | Proposed Tool Name | Value |
|----------|-------------------|-------|
| `/api/v1/Categories/{id}` | `get_interest_category` | Low — specific category |
| `/api/v1/Interests/{id}` | `get_interest_by_id` | Medium — specific interest entry |
| `/api/v1/Registers/{id}` | `get_register_by_id` | Medium — specific register |

*Skip: `/api/v1/Interests/csv` (CSV export), `/api/v1/Registers/{id}/document` (binary)*

### 2C. Committees API — 5 new tools + CLI commands

| Endpoint | Proposed Tool Name | Value |
|----------|-------------------|-------|
| `/api/BillPetitions/{id}` | `get_bill_petition_by_id` | Medium — specific petition |
| `/api/Broadcast/Meetings` | `get_broadcast_meetings` | High — live/recorded committee broadcasts |
| `/api/Committees/{id}/ArchivedPublicationLinks` | `get_archived_publication_links` | Medium — archived reports |
| `/api/Committees/{id}/Members/{personId}` | `get_committee_member` | Low — specific membership |
| `/api/Countries` | `get_countries` | Low — country reference data |
| `/api/Events/Activities` | `search_event_activities` | Medium — search all activities |
| `/api/SubmissionPeriod/{id}` | `get_submission_period` | Medium — evidence submission windows |

*Skip: Document download endpoints (3), Messaging Banners, SubmissionPeriodTemplate doc*

### 2D. Parliament Now API — 1 new tool + CLI command

| Endpoint | Proposed Tool Name | Value |
|----------|-------------------|-------|
| `/api/Message/message/{annunciator}/{date}` | `get_annunciator_by_date` | Medium — historical chamber display |

---

## Implementation Plan

### Work per phase

| Phase | New MCP Tools | New CLI Commands | Files Modified |
|-------|--------------|-----------------|----------------|
| **Phase 1** | 29 | 29 | 6 tool files + 5 CLI files |
| **Phase 2** | 20 | 20 | 5 tool files + 4 CLI files |
| **Total** | **~49** | **~49** | — |

### Execution order (by impact and file grouping)

1. **members.py** — 8 new tools + CLI (constituency search/details, historical members, Speaker)
2. **hansard.py** — 10 new tools + CLI (currently processing, speakers list, committee debates, petitions, stats)
3. **whatson.py / cli/live.py** — 11 new tools + CLI (diary, sessions, reference data)
4. **statutory_instruments.py / cli/legislation.py** — 8 new tools + CLI (proposed negatives, laying bodies, procedures)
5. **committees.py** — 5 new tools + CLI (broadcast meetings, archived pubs, bill petitions)
6. **interests.py** — 3 new tools + CLI (individual lookups)
7. **now.py / cli/live.py** — 1 new tool + CLI (historical annunciator)

### For each tool, the work is

1. Add `@mcp.tool()` function in `tools/<module>.py`
2. Add `@app.command()` function in `cli/<module>.py`
3. Add test(s) in `tests/`
4. Update tool count in CLAUDE.md and core.py guidance text
5. Update CLI command counts in CLAUDE.md

### Post-implementation

- Run `ruff check` + `ruff format`
- Run `mypy src/`
- Run `pytest`
- Update version number
- Update `CLAUDE.md` counts (163 → ~212)
