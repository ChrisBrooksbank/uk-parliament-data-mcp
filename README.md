# UK Parliament AI Assistant

[![PyPI version](https://badge.fury.io/py/uk-parliament-mcp.svg)](https://badge.fury.io/py/uk-parliament-mcp)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/ChrisBrooksbank/uk-parliament-data-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/ChrisBrooksbank/uk-parliament-data-mcp/actions/workflows/ci.yml)

> **Disclaimer:** This is an unofficial, independent project. It is not created, endorsed, or supported by UK Parliament. All data is sourced from the publicly available [parliament.uk APIs](https://developer.parliament.uk/).
>
> GitHub: [ChrisBrooksbank/uk-parliament-data-mcp](https://github.com/ChrisBrooksbank/uk-parliament-data-mcp)

An MCP (Model Context Protocol) server that gives AI assistants access to UK Parliament data. Query MPs, Lords, bills, votes, committees, debates, and more through AI assistants like Claude Desktop and VS Code Copilot. Also includes a CLI for terminal access.

## MCP Server for AI Assistants

Connect your AI assistant to 209 UK Parliament API tools for comprehensive parliamentary research.

https://github.com/user-attachments/assets/30f2df13-dff9-44e6-b1f6-5eebfb665d9e


## Table of Contents

- [MCP Server for AI Assistants](#mcp-server-for-ai-assistants)
  - [Getting Started](#getting-started)
  - [Starting a Session](#starting-a-session)
  - [Parliament Research Skill (Claude Code)](#parliament-research-skill-claude-code)
  - [Claude Desktop Setup](#claude-desktop-setup)
  - [VS Code Setup](#vs-code-setup)
  - [What Can I Ask?](#what-can-i-ask)
  - [Power Tools](#power-tools)
  - [Ending Your Session](#ending-your-session)
  - [Prompting Tips](#prompting-tips)
  - [Example Prompts](#example-prompts)
- [CLI Usage](#cli-usage)
  - [Quick Start](#quick-start)
  - [Common Commands](#common-commands)
  - [Daily/Weekly Digest](#dailyweekly-digest)
  - [My MP Lookup](#my-mp-lookup)
  - [API Explorer](#api-explorer)
  - [CLI Reference](#cli-reference)
  - [Output Formats](#output-formats)
  - [URL Transparency](#url-transparency)
  - [Help System](#help-system)
- [Alternative Installation Methods](#alternative-installation-methods)
- [Final Thoughts](#final-thoughts)

## Getting Started

**Step 1:** Configure your AI assistant (see [Claude Desktop](#claude-desktop-setup) or [VS Code](#vs-code-setup) below)

**Step 2:** Start a parliamentary research session:
- Use the `/parliament` slash command (in Claude Desktop or compatible MCP clients)
- Or say **"Order Order"** (like the Speaker) to initialize the session

This gives your AI assistant the context it needs to effectively use the 209 available tools.

## Starting a Session

Say **"Order Order"** to initialize your parliamentary research session. This gives Claude the context needed to effectively use the 209 available tools.

If that doesn't work, copy and paste this system prompt:

```plaintext
You are a helpful assistant that answers questions using only data from UK Parliament MCP servers.

When the session begins, introduce yourself with a brief message such as:
"Hello! I'm a parliamentary data assistant. I can help answer questions using official data from the UK Parliament MCP APIs. Just ask me something, and I'll fetch what I can - and I'll always show you which sources I used."

When responding to user queries, you must:
Only retrieve and use data from the MCP API endpoints this server provides.
Avoid using any external sources or inferred knowledge.
After every response, append a list of all MCP API URLs used to generate the answer.
If no relevant data is available via the MCP API, state that clearly and do not attempt to fabricate a response.
Convert raw data into human-readable summaries while preserving accuracy, but always list the raw URLs used.
```

### Parliament Research Skill (Claude Code)

If you use [Claude Code](https://docs.anthropic.com/en/docs/claude-code), this repo includes a `/parliament-research` slash command that turns Claude into a Parliament research assistant.

Type `/parliament-research` followed by a natural language question:

```
/parliament-research How did Keir Starmer vote on climate?
/parliament-research When was Chelmsford mentioned in Hansard?
/parliament-research What bills about education are in progress?
```

Claude will pick the right CLI commands, run them, and present a sourced answer. The command file lives at `.claude/commands/parliament-research.md`.

## Claude Desktop Setup

1. Open Claude Desktop
2. Click **Settings** → **Developer** → **Edit Config**
3. Add the following configuration and save with UTF-8 encoding:

```json
{
  "mcpServers": {
    "uk-parliament": {
      "command": "uvx",
      "args": ["uk-parliament-mcp"]
    }
  }
}
```

4. Restart Claude Desktop
5. Open the Developer tab to verify the server is running

> **Note:** This uses `uvx` which runs the package directly without installation. It automatically uses the latest version from PyPI.
>
> Don't have uvx? Install it with: `pip install uv` or see [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/)

## VS Code Setup

1. Press `Ctrl+Shift+P` to open the Command Palette
2. Select **MCP: Add Server**
3. Choose **Command: Stdio**
4. Enter: `uvx uk-parliament-mcp`
5. Press **Enter**

### Start the Server

1. Press `Ctrl+Shift+P` again
2. Select **MCP: List Servers**
3. Click the server you just added and choose **Start server**

### First Interaction

1. Open **Copilot Chat** in VS Code
2. Set **Agent mode** using the dropdown in the bottom-left
3. Select your preferred model (e.g., Claude Sonnet 4)
4. Click **Configure Tools**, and select all tools from the newly added MCP server
5. Try a prompt such as: "What is happening now in the House of Commons?"
6. Accept any permission request to allow the MCP call

## What Can I Ask?

You can ask questions about virtually all aspects of UK Parliament data. Here are some key areas:

*   **Live Parliamentary Activity:** "What's happening in the House of Commons right now?" or "What's currently being debated in the Lords?"
*   **Members of Parliament:** "Tell me everything you know about Boris Johnson," "What are Sir Keir Starmer's registered interests?" or "Show me the voting record of member 4129"
*   **Bills & Legislation:** "Show me details of bill 425," "What amendments were proposed for bill 425?" or "What publications exist for the Environment Bill?"
*   **Voting Records:** "How did MPs vote on the climate change motion?" or "Show me Lords divisions on healthcare policy"
*   **Committees & Inquiries:** "Which committees are investigating economic issues?" or "Show me evidence submitted to the Treasury Committee"
*   **Parliamentary Procedures:** "Search Erskine May for references to Speaker's rulings" or "What are the oral question times this week?"
*   **Constituencies & Elections:** "Show me election results for Birmingham constituencies" or "List all constituencies in Scotland"
*   **Official Documents:** "Are there any statutory instruments about housing?" or "What treaties involve trade agreements?"
*   **Transparency Data:** "Show register of interests for Treasury ministers" or "What are the declared interests categories?"

## Power Tools

These high-level tools combine multiple API calls for common research tasks:

| Tool | What it does |
|------|--------------|
| `get_mp_profile(member_id)` | Complete MP/Lord profile: bio, interests, voting record |
| `check_mp_vote(member_id, topic)` | How an MP voted on a specific topic |
| `get_bill_overview(search_term)` | Full bill info: details, stages, publications |
| `get_committee_summary(topic)` | Committee overview: evidence, publications |
| `get_my_mp(postcode, topic)` | Find MP by UK postcode with full profile |

Note: `get_mp_profile` and `check_mp_vote` require a `member_id` (int). Search first with `get_member_by_name()`.

**Example:**
```
Tell me everything about Keir Starmer
```
The AI will use `get_member_by_name` to find the member_id, then `get_mp_profile` to fetch biography, registered interests, and voting history in a single efficient call.

## Ending Your Session

Start a new chat session to end the parliamentary research mode.

---

## Prompting Tips

> **Note**: Since AI is involved, some responses may be inaccurate. These tips help improve reliability.

### ✅ Initialize Your Session

Always begin your session with `/parliament` or say "Order Order". This ensures the AI assistant uses the correct tools and cites its sources properly.

### 🔄 Clear Context

Use the `+` icon (new chat) if:
- The AI seems stuck in a loop
- You want to reset the conversation context

### 🔗 Re-Display the API URL

While the AI is instructed to list source URLs automatically, you can ask for them again at any time. This is useful for troubleshooting or if you simply want to re-confirm the source for the last response.

You can ask:

```plaintext
Show me the API URL you just used.
```

Example response:
> The API URL just used to retrieve information about Boris Johnson is:
> `https://members-api.parliament.uk/api/Members/Search?Name=Boris%20Johnson`

### 🧠 Combine Data from Multiple Sources

Example:
```plaintext
Has Chelmsford been mentioned in either the Commons or Lords?
```

The AI may:
- Query both Commons and Lords Hansard
- Combine the results
- Offer more detail if requested

### 🧾 See the Raw JSON

For debugging or to inspect the raw data structure, you can ask the assistant to show you the full JSON response from its last API call. This is particularly useful for developers who want to understand exactly what information the AI is working with before it is summarized.

Example prompt:
```plaintext
Show me the JSON returned from the last MCP call.
```

## Example Prompts

<details>
<summary><strong>Live Parliamentary Activity</strong> (3 examples)</summary>

- What is happening now in both Houses?
- What's currently happening in the House of Commons?
- What's currently happening in the House of Lords?

</details>

<details>
<summary><strong>Members of Parliament</strong> (14 examples)</summary>

- Show me the interests of Sir Keir Starmer
- Tell me about Boris Johnson's parliamentary career
- Look up the MP with ID 1471
- Show me the biography for member 172
- Show me contact details for member 4129
- What are the registered interests of member 3743?
- What speeches has member 172 made recently?
- Show me how member 4129 has voted in the Commons
- Show me how member 3743 has voted in the Lords
- What was member 1471's career before Parliament?
- What policy areas does member 172 focus on?
- What early day motions has member 1471 signed?
- Get the constituency election results for member 4129
- Show me photos of member 172

</details>

<details>
<summary><strong>Bills and Legislation</strong> (14 examples)</summary>

- What bills about fishing are currently before Parliament?
- What bills were updated recently?
- Show me details of bill 425
- What stages has bill 425 been through?
- What amendments were proposed for bill 425 at stage 15?
- Show me amendment 1234 for bill 425 stage 15
- What publications exist for bill 425?
- What news articles are there about bill 425?
- Show me all bill types available
- What are the different stages a bill can go through?
- Find bills related to the environment
- Get the RSS feed to track all bills
- Get the RSS feed for public bills
- Get the RSS feed for bill 425

</details>

<details>
<summary><strong>Voting and Divisions</strong> (6 examples)</summary>

- How have MPs voted on refugee-related issues?
- Show details of Commons division 1234
- Show details of Lords division 5678
- Show how parties voted on climate issues in the Commons
- How did Lords vote by party on issues involving member 3743?
- How many votes have there been on Brexit?

</details>

<details>
<summary><strong>Written Questions & Statements</strong> (8 examples)</summary>

- What written questions have MPs asked about climate change?
- Show me unanswered written questions to the Home Office
- Find written questions about the NHS from the last month
- Get details of written question 12345
- What written ministerial statements were made about the budget?
- Search for written statements about housing policy
- Show me the daily report of written questions for this week
- Has any MP asked written questions about artificial intelligence?

</details>

<details>
<summary><strong>Committees and Inquiries</strong> (9 examples)</summary>

- Which committees are focused on women's issues?
- What committee meetings are scheduled this month?
- Show me details of committee 789
- What hearings has committee 789 held?
- Who are the members of committee 789?
- Find committee reports on healthcare
- What written evidence was submitted to committee 789?
- What oral evidence was given to committee 789?
- What are all the committee types?

</details>

<details>
<summary><strong>Hansard (Official Record)</strong> (8 examples)</summary>

- Search Hansard for recent debates on Brexit
- What was said about immigration in the Commons last month?
- Show me the full transcript of debate abc123-def456
- What did Keir Starmer say during the debate on the economy?
- Were there any votes during the NHS funding debate?
- What debates happened in the Commons on March 15th 2024?
- Which days in January 2024 had Commons sittings?
- Show me all speeches by member 4514 in debate xyz789

</details>

<details>
<summary><strong>Parliamentary Procedures</strong> (9 examples)</summary>

- Search Erskine May for references to the Mace
- What oral question times are coming up?
- What government departments exist?
- What are the answering bodies in Parliament?
- What parties are represented in the House of Commons?
- What parties are represented in the House of Lords?
- What's on the Commons calendar this month?
- When are the upcoming parliamentary recesses?
- What are the procedural rules for bill amendments?

</details>

<details>
<summary><strong>Constituencies and Elections</strong> (3 examples)</summary>

- List all UK constituencies
- Show the election results for constituency 4359
- Search for constituencies containing "london"

</details>

<details>
<summary><strong>Transparency and Interests</strong> (4 examples)</summary>

- List all categories of members' interests
- Get published registers of interests
- Show staff interests declared by Lords members
- Search the register of interests for member 1471

</details>

<details>
<summary><strong>Official Documents and Publications</strong> (5 examples)</summary>

- Are there any statutory instruments about harbours?
- Search Acts of Parliament that mention roads
- What treaties involve Spain?
- What publication types are available for bills?
- Show me document 123 from publication 456

</details>

<details>
<summary><strong>Advanced Queries</strong> (5 examples)</summary>

- Show the full data from this pasted API result: {PasteApiResultHere}
- Show me the JSON returned from the last MCP call
- Show me the API URL you just used
- Search for bills sponsored by member 172 from the Environment department
- Find committee meetings about climate change in the last few months

</details>

---

## CLI Usage

The package includes a `parliament` CLI for terminal access to all 209 UK Parliament API tools. Perfect for developers, researchers, and automation scripts.

### Install — Standalone Executable (Recommended)

**No Python required.** Download a single file, and you're ready to go:

| Platform | Download |
|----------|----------|
| Windows | [`parliament-windows-x64.exe`](https://github.com/ChrisBrooksbank/uk-parliament-data-mcp/releases/latest/download/parliament-windows-x64.exe) |
| macOS | [`parliament-macos-x64`](https://github.com/ChrisBrooksbank/uk-parliament-data-mcp/releases/latest/download/parliament-macos-x64) |
| Linux | [`parliament-linux-x64`](https://github.com/ChrisBrooksbank/uk-parliament-data-mcp/releases/latest/download/parliament-linux-x64) |

On macOS/Linux, make the binary executable after downloading:

```bash
chmod +x parliament-linux-x64
./parliament-linux-x64 members search "Starmer"
```

On Windows, just run the `.exe` directly:

```
parliament-windows-x64.exe members search "Starmer"
```

> **Tip:** Rename the download to `parliament` (or `parliament.exe`) and place it on your PATH for convenience.

### Install — pip (Alternative)

If you already have Python 3.11+, you can install from PyPI instead:

```bash
pip install uk-parliament-mcp
```

### Quick Start

```bash
# Search for an MP
parliament members search "Keir Starmer"

# Get comprehensive MP profile (use member_id)
parliament composite mp-profile 4514 --pretty

# Check how an MP voted on a topic (use member_id)
parliament composite check-vote 172 "climate"

# Track bill progress
parliament bills search "Online Safety" --data-only | jq '.items[0]'

# What's happening now in Parliament?
parliament live commons-now --pretty
```

### Common Commands

The CLI organizes 209 tools into 15 command groups:

```bash
# MP and Lords research
parliament members search "Starmer"
parliament members biography 4514
parliament interests search "Starmer"

# Bill tracking
parliament bills search "education"
parliament bills stages 123
parliament bills amendments 123

# Voting records
parliament votes search "climate" --house 1
parliament votes get-division 12345 --house 1

# Committee research
parliament committees search "Treasury"
parliament committees oral-evidence 456

# Parliamentary record
parliament hansard search-debates "NHS" --house 1

# Live activity
parliament live commons-now
parliament live calendar Commons 2025-01-15 2025-01-31
parliament live next-sitting-date Commons 2025-01-15

# Questions and statements
parliament questions search-edms "immigration"
parliament questions search-written "healthcare"

# Legislation and treaties
parliament legislation search-si "education"
parliament legislation search-treaties "trade"

# Erskine May procedure rules
parliament procedures search "closure"

# Daily/weekly parliamentary digest
parliament digest                          # Today's summary
parliament digest --date 2025-01-15        # Specific date
parliament digest --period week            # This week (Mon-Fri)
parliament digest --house 1                # Commons only

# Live dashboard with auto-refresh
parliament watch

# API explorer
parliament api list                        # List all Parliament APIs
parliament api search "bill"               # Search across APIs
```

**High-level composite tools** (combine multiple API calls):

```bash
# Find your MP by postcode
parliament my-mp "SW1A 1AA"
parliament my-mp "N1 9GU" --votes climate

# Get everything about an MP in one call (use member_id)
parliament composite mp-profile 4514 --pretty

# Check how an MP voted on a topic (use member_id)
parliament composite check-vote 172 "climate" --pretty

# Get comprehensive bill overview
parliament composite bill-overview "Online Safety" --pretty

# Get full committee summary
parliament composite committee-summary "Treasury" --pretty
```

### Daily/Weekly Digest

Get a quick overview of parliamentary activity without running multiple commands. The `digest` command aggregates 9 data sources (Hansard debates, Commons/Lords divisions, bills, committee meetings, written statements, oral questions, EDMs, and written questions) into a single summary with clickable links to parliament.uk:

```bash
# Today's digest (rich table output in terminal, JSON when piped)
parliament digest

# Pretty-printed for a specific date
parliament digest --date 2025-01-15 --pretty

# Weekly summary (Monday to Friday)
parliament digest --period week

# Filter to one house
parliament digest --house 1                # Commons only
parliament digest --house 2                # Lords only

# JSON output for scripting
parliament digest --format json | jq '.commons_divisions | length'
```

The rich output includes:
- **Divisions** with Ayes/Noes counts, linked to votes.parliament.uk
- **Bills** with titles and current stage, linked to bills.parliament.uk
- **Hansard debates** linked to hansard.parliament.uk
- **Committee meetings** with date, time, and topic, linked to committees.parliament.uk
- **Written statements**, **oral questions**, **EDMs**, and **written questions** summaries

### My MP Lookup

Find your MP by postcode with a single command:

```bash
# Basic lookup — constituency, MP bio, interests, election result, recent votes
parliament my-mp "SW1A 1AA"

# Filter votes by topic
parliament my-mp "N1 9GU" --votes climate

# JSON output for scripting
parliament my-mp "SW1A 1AA" --format json | jq '.basic_info'

# Pretty-printed
parliament my-mp "SW1A 1AA" --pretty
```

### API Explorer

Browse and search the Parliament API catalogue interactively:

```bash
# List all Parliament APIs
parliament api list

# Show endpoints for a specific API
parliament api endpoints members

# Get full details for an API
parliament api detail members

# Search across all APIs
parliament api search "bill"

# Show OpenAPI schema for an API
parliament api schema members

# Show parameters for a specific endpoint
parliament api params members "/api/Members/Search"
```

### CLI Reference

View the full command reference without leaving the terminal:

```bash
# Overview of all command groups
parliament reference

# Detailed view of a specific group
parliament reference members

# Search for commands by keyword
parliament reference --search vote

# Export as JSON
parliament reference --format json
```

### Output Formats

The CLI supports multiple output formats via the `--format` flag:

```bash
# Auto-detect: rich table in terminal, JSON when piped (default)
parliament members search "Starmer"

# Explicit formats
parliament members search "Starmer" --format table
parliament members search "Starmer" --format markdown
parliament members search "Starmer" --format csv
parliament members search "Starmer" --format json

# Select specific fields (case-insensitive matching)
parliament members search "Starmer" --fields "id,nameDisplayAs,latestParty.name"

# Raw JSON with full {url, data} wrapper
parliament members search "Starmer" --raw

# Pretty-printed JSON
parliament members search "Starmer" --pretty

# Just the data (strips url wrapper)
parliament members search "Starmer" --data-only | jq '.items[0]'
```

When using `--fields`, the CLI shows available fields on stderr if none match, so you can discover the correct field paths.

**Global flags:**
- `--format` / `-f` - Output format: `json`, `table`, `markdown`, `csv`, `auto` (default: `auto`)
- `--fields` - Comma-separated field paths for column selection (case-insensitive)
- `--raw` - Output full wrapper JSON (url + data), disabling auto-formatting
- `--pretty` / `-p` - Pretty-print JSON output
- `--data-only` / `-d` - Return only the data field, not the {url, data} wrapper

### URL Transparency

Every API request logs the source URL to stderr, so you can always see exactly which Parliament API endpoint was called:

```bash
# URL appears on stderr, data on stdout
parliament members search "Starmer"
# stderr: GET https://members-api.parliament.uk/api/Members/Search?Name=Starmer

# Capture just the data (URLs go to stderr, not stdout)
parliament members search "Starmer" > results.json
```

This makes it easy to verify data sources, debug issues, or construct your own API calls.

### Help System

```bash
# Show all command groups
parliament --help

# Show commands in a group
parliament members --help

# Show command details
parliament members search --help

# Full command reference (all groups and commands)
parliament reference
parliament reference members
parliament reference --search vote

# Browse the API catalogue
parliament api list
parliament api search "member"

# Get tool reference
parliament guide tools

# Get detailed domain guidance
parliament guide topic members

# Get research workflow
parliament guide workflow "How did my MP vote on X?"
```

**Available help topics:**
- `composite` - High-level tools combining multiple API calls
- `members` - MPs, Lords, constituencies, parties
- `bills` - Legislation, amendments, stages
- `votes` - Commons and Lords divisions
- `committees` - Committee info, meetings, evidence
- `hansard` - Parliamentary record
- `questions` - Oral questions, written questions, EDMs
- `interests` - Register of interests
- `live` - Current activity and calendar
- `legislation` - SIs and treaties
- `procedures` - Erskine May procedure rules

---

## Alternative Installation Methods

The `uvx` method shown above is recommended for most users. For specific use cases, here are alternative approaches:

### Which Method Should I Use?

| Method | Best For | Pros | Cons |
|--------|----------|------|------|
| **Standalone executable** | Non-technical users, quick setup | Zero prerequisites, single file download | Manual updates, larger file size |
| `uvx uk-parliament-mcp` | MCP server users | No install needed, always latest version | Requires uvx installed |
| `pip install uk-parliament-mcp` | Python developers | Stable, version locked, CLI + MCP server | Requires Python 3.11+ |
| Local development install | Contributors | Full source access, can modify | More complex setup |

### Using pip install

Install the package globally:

```bash
pip install uk-parliament-mcp
```

Then configure your AI client:

**Claude Desktop:**
```json
{
  "mcpServers": {
    "uk-parliament": {
      "command": "uk-parliament-mcp"
    }
  }
}
```

**VS Code:** Use `uk-parliament-mcp` as the command when adding the MCP server.

### Installation from Source

For development or to get the latest unreleased changes:

#### Prerequisites

- [Python](https://www.python.org/downloads/) (v3.11 or later)
- [Git](https://git-scm.com/downloads)

#### Clone and Install

```bash
git clone https://github.com/ChrisBrooksbank/uk-parliament-data-mcp.git
cd uk-parliament-data-mcp

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Install the package
pip install -e .
```

#### Configure for Local Development

**Claude Desktop:**
```json
{
  "mcpServers": {
    "uk-parliament": {
      "command": "C:\\code\\uk-parliament-data-mcp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "uk_parliament_mcp"],
      "cwd": "C:\\code\\uk-parliament-data-mcp"
    }
  }
}
```

**VS Code:** Use the full path to the virtual environment Python:
```bash
C:\code\uk-parliament-data-mcp\.venv\Scripts\python.exe -m uk_parliament_mcp
```

---

## Final Thoughts

The project is under active development, with plans to increase data coverage and improve interaction quality. Contributions and feedback are welcome.

