# Agent Guidance System Specification

## Overview

This specification describes the agent guidance system implemented in the UK Parliament MCP Server. The system helps AI assistants effectively navigate and use the 86 tools across 14 modules.

## Problem Statement

With 86 tools available, AI assistants need guidance to:
- Understand which tools exist for different domains
- Know the correct sequence of tools for common research tasks
- Understand conventions (house IDs, date formats, pagination)
- Discover relationships between tools (search -> detail -> related data)

## Solution: Tiered Guidance System

### Tier 1: Enhanced `hello_parliament()`

**Purpose**: Session initialization with quick reference

**Changes**:
- Appends a `QUICK_REFERENCE` section to the existing system prompt
- Provides tool category overview with entry points
- Documents key conventions
- Points to detailed guidance tools

**Output includes**:
- Original system prompt (data source transparency, URL citation requirements)
- Tool categories table (14 modules with tool counts)
- Entry point functions for each category
- Common usage patterns
- References to `parliament_guide()` and `parliament_workflow()`

### Tier 2: `parliament_guide(topic: str)`

**Purpose**: Detailed, topic-focused guidance

**Parameters**:
- `topic`: One of 13 topics

**Available Topics**:
| Topic | Description |
|-------|-------------|
| members | 25 tools for MPs, Lords, constituencies, parties |
| bills | 21 tools for legislation, amendments, stages |
| votes | 10 tools for Commons and Lords divisions |
| committees | 12 tools for committee info, meetings, evidence |
| hansard | 1 tool for parliamentary record search |
| questions | 3 tools for EDMs, oral questions |
| interests | 3 tools for Register of Interests |
| live | 5 tools for current activity, calendar |
| legislation | 3 tools for SIs, treaties |
| procedures | 3 tools for Erskine May, bill types |
| all | Condensed reference of all 86 tools |
| conventions | Date formats, house IDs, pagination |
| workflows | Overview of common research patterns |

**Output includes**:
- Tool list with parameters
- Categorization by function
- Typical workflow steps
- Key parameter documentation

### Tier 3: `parliament_workflow(query: str)`

**Purpose**: Query-driven workflow suggestions

**Matching**: Keyword-based pattern matching against user query

**Workflow Patterns**:
1. **MP Voting Research** - Keywords: vote, voted, voting, division, aye, noes
2. **Bill Tracking** - Keywords: bill, legislation, law, act, progress, stage
3. **Committee Research** - Keywords: committee, inquiry, evidence, witness, hearing
4. **Interests/Conflicts Research** - Keywords: interest, conflict, financial, donation, declare
5. **Live Parliament Activity** - Keywords: now, today, happening, live, current, sitting
6. **MP Background Research** - Keywords: background, biography, profile, who is, about
7. **Hansard Search** - Keywords: said, speech, debate, hansard, parliament said
8. **Electoral Research** - Keywords: election, constituency, result, majority, swing
9. **Early Day Motion Research** - Keywords: edm, early day motion, support, signed
10. **Treaty Research** - Keywords: treaty, international, agreement, trade deal

**Output includes**:
- Step-by-step workflow
- Tool names with parameters
- Purpose of each step
- Expected output at each step
- Alternative approaches where applicable

**Fallback**: When no pattern matches, provides general research approach guidance.

## Implementation

### File Structure

All guidance code is in `src/uk_parliament_mcp/tools/core.py`:

```python
# Constants
SYSTEM_PROMPT = "..."      # Original session prompt
GOODBYE_PROMPT = "..."     # Session end prompt
QUICK_REFERENCE = "..."    # Tool overview (appended to hello)
GUIDANCE_CONTENT = {...}   # Dict of topic -> detailed content
WORKFLOW_PATTERNS = [...]  # List of workflow pattern dicts

# Helper functions
def _format_workflow(pattern: dict[str, Any]) -> str
def _suggest_general_approach(query: str) -> str

# Tools (registered via register_tools)
async def hello_parliament() -> str
async def goodbye_parliament() -> str
async def parliament_guide(topic: str) -> str
async def parliament_workflow(query: str) -> str
```

### No Server.py Changes Required

The new tools are automatically registered because `core.register_tools(mcp)` is already called in `server.py`.

## Testing

Tests are in `tests/test_tools/test_core.py`:

- `TestCoreTools`: Tool registration and basic functionality
- `TestSystemPromptContent`: System prompt content validation
- `TestQuickReference`: Quick reference content validation
- `TestParliamentGuide`: Topic guidance for each topic
- `TestParliamentWorkflow`: Workflow matching for each pattern
- `TestGuidanceContent`: Content completeness validation

## Usage Examples

### Starting a Session
```
User: "I want to research UK Parliament data"
AI calls: hello_parliament()
AI receives: System prompt + Quick reference
```

### Exploring a Domain
```
User: "What tools are available for researching MPs?"
AI calls: parliament_guide(topic="members")
AI receives: 25 tools with parameters, categories, workflows
```

### Planning Research
```
User: "How can I find how my MP voted on the climate bill?"
AI calls: parliament_workflow(query="how did my MP vote on climate bill")
AI receives: Step-by-step workflow: get_member_by_name -> search_commons_divisions -> get_commons_division_by_id
```

## Design Decisions

1. **Static content, no API calls**: Guidance returns pre-defined text, ensuring fast responses and no external dependencies.

2. **Keyword matching for workflows**: Simple substring matching provides good coverage without complexity. First matching pattern wins.

3. **Integrated into core.py**: Keeps all guidance/session tools together for discoverability.

4. **Tool count accuracy**: The "86 tools" claim includes the 4 core tools (hello, goodbye, guide, workflow) in the total.

5. **Fallback for unmatched queries**: `parliament_workflow` provides general guidance when no specific pattern matches.
