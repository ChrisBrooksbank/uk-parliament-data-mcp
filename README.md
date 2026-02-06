# UK Parliament AI Assistant

[![PyPI version](https://badge.fury.io/py/uk-parliament-mcp.svg)](https://badge.fury.io/py/uk-parliament-mcp)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/ChrisBrooksbank/uk-parliament-mcp-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/ChrisBrooksbank/uk-parliament-mcp-lab/actions/workflows/ci.yml)

> **Disclaimer:** This is an unofficial, independent project. It is not created, endorsed, or supported by UK Parliament. All data is sourced from the publicly available [parliament.uk APIs](https://developer.parliament.uk/).
>
> GitHub: [ChrisBrooksbank/uk-parliament-mcp-lab](https://github.com/ChrisBrooksbank/uk-parliament-mcp-lab)

An MCP (Model Context Protocol) server that gives AI assistants access to UK Parliament data. Query MPs, Lords, bills, votes, committees, debates, and more through AI assistants like Claude Desktop and VS Code Copilot. Also includes a CLI for terminal access.

## MCP Server for AI Assistants

Connect your AI assistant to 161 UK Parliament API tools for comprehensive parliamentary research.

## Table of Contents

- [MCP Server for AI Assistants](#mcp-server-for-ai-assistants)
  - [Getting Started](#getting-started)
  - [Starting a Session](#starting-a-session)
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
  - [Output Modes](#output-modes)
  - [Help System](#help-system)
- [Alternative Installation Methods](#alternative-installation-methods)
- [Final Thoughts](#final-thoughts)

## Getting Started

**Step 1:** Configure your AI assistant (see [Claude Desktop](#claude-desktop-setup) or [VS Code](#vs-code-setup) below)

**Step 2:** Start a parliamentary research session:
- Use the `/parliament` slash command (in Claude Desktop or compatible MCP clients)
- Or say **"Order Order"** (like the Speaker) to initialize the session

This gives your AI assistant the context it needs to effectively use the 161 available tools.

## Starting a Session

Say **"Order Order"** to initialize your parliamentary research session. This gives Claude the context needed to effectively use the 161 available tools.

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
| `get_mp_profile(name)` | Complete MP/Lord profile: bio, interests, voting record |
| `check_mp_vote(mp_name, topic)` | How an MP voted on a specific topic |
| `get_bill_overview(search_term)` | Full bill info: details, stages, publications |
| `get_committee_summary(topic)` | Committee overview: evidence, publications |

**Example:**
```
Tell me everything about Keir Starmer
```
The AI will use `get_mp_profile` to fetch biography, registered interests, and voting history in a single efficient call.

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

The package also includes a `parliament` CLI for terminal access to all 161 UK Parliament API tools. Perfect for developers, researchers, and automation scripts.

### Quick Start

```bash
# Install from PyPI
pip install uk-parliament-mcp

# Search for an MP
parliament members search "Keir Starmer"

# Get comprehensive MP profile
parliament composite mp-profile "Rishi Sunak" --pretty

# Check how an MP voted on a topic
parliament composite check-vote "Boris Johnson" "climate"

# Track bill progress
parliament bills search "Online Safety" --data-only | jq '.items[0]'

# What's happening now in Parliament?
parliament live commons-now --pretty
```

### Common Commands

The CLI organizes 161 tools into 12 command groups:

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
parliament live calendar
parliament live next-sitting-date --house 1

# Questions and statements
parliament questions search-edms "immigration"
parliament questions search-written "healthcare"

# Legislation and treaties
parliament legislation search-si "education"
parliament legislation search-treaties "trade"

# Erskine May procedure rules
parliament procedures search "closure"
```

**High-level composite tools** (combine multiple API calls):

```bash
# Get everything about an MP in one call
parliament composite mp-profile "Keir Starmer" --pretty

# Check how an MP voted on a topic
parliament composite check-vote "Johnson" "climate" --pretty

# Get comprehensive bill overview
parliament composite bill-overview "Online Safety" --pretty

# Get full committee summary
parliament composite committee-summary "Treasury" --pretty
```

### Output Modes

The CLI outputs JSON by default, making it easy to pipe to other tools:

```bash
# Default: compact JSON (for piping)
parliament members search "Starmer" | jq '.data[0].id'

# Pretty-printed JSON
parliament members search "Starmer" --pretty

# Just the data (strips url wrapper)
parliament members search "Starmer" --data-only | jq '.items[0]'

# Count results
parliament bills search "education" | jq '.items | length'

# Filter and extract
parliament votes search "climate" --house 1 | jq '.data[] | select(.ayes > 300)'

# Save to file
parliament composite mp-profile "Sunak" --pretty > profile.json
```

**Global flags:**
- `--pretty` / `-p` - Pretty-print JSON output
- `--data-only` / `-d` - Return only the data field, not the {url, data} wrapper

### Help System

```bash
# Show all command groups
parliament --help

# Show commands in a group
parliament members --help

# Show command details
parliament members search --help

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
| `uvx uk-parliament-mcp` | Most users | No install needed, always latest version | Requires uvx installed |
| `pip install uk-parliament-mcp` | Production use | Stable, version locked | Requires pip, manual updates |
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
git clone https://github.com/ChrisBrooksbank/uk-parliament-mcp-lab.git
cd uk-parliament-mcp-lab

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
      "command": "C:\\code\\uk-parliament-mcp-lab\\.venv\\Scripts\\python.exe",
      "args": ["-m", "uk_parliament_mcp"],
      "cwd": "C:\\code\\uk-parliament-mcp-lab"
    }
  }
}
```

**VS Code:** Use the full path to the virtual environment Python:
```bash
C:\code\uk-parliament-mcp-lab\.venv\Scripts\python.exe -m uk_parliament_mcp
```

---

## Final Thoughts

The project is under active development, with plans to increase data coverage and improve interaction quality. Contributions and feedback are welcome.
