# UK Parliament AI Assistant

[![PyPI version](https://badge.fury.io/py/uk-parliament-mcp.svg)](https://badge.fury.io/py/uk-parliament-mcp)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/ChrisBrooksbank/uk-parliament-mcp-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/ChrisBrooksbank/uk-parliament-mcp-lab/actions/workflows/ci.yml)

Access official UK Parliament data through AI assistants. Query MPs, Lords, bills, votes, committees, debates, and more.

## Table of Contents

- [Getting Started](#getting-started)
- [Claude Desktop Setup](#claude-desktop-setup)
- [VS Code Setup](#vs-code-setup)
- [What Can I Ask?](#what-can-i-ask)
- [Power Tools](#power-tools)
- [Prompting Tips](#prompting-tips)
- [Example Prompts](#example-prompts)
- [Alternative Installation Methods](#alternative-installation-methods)
- [Final Thoughts](#final-thoughts)

## Getting Started

**Step 1:** Configure your AI assistant (see [Claude Desktop](#claude-desktop-setup) or [VS Code](#vs-code-setup) below)

**Step 2:** Start a parliamentary research session:
- Use the `/parliament` slash command (in Claude Desktop or compatible MCP clients)
- Or say "Hello Parliament" to initialize the session

This gives your AI assistant the context it needs to effectively use the 92 available tools.

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

## Disconnecting from Parliament

Start a new chat session, or say "Goodbye Parliament" to end the parliamentary session while keeping context.

---

## Prompting Tips

> **Note**: Since AI is involved, some responses may be inaccurate. These tips help improve reliability.

### ✅ Initialize Your Session

Always begin your session with `/parliament` or "Hello Parliament". This ensures the AI assistant uses the correct tools and cites its sources properly.

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
- Who is Boris Johnson?
- Who is the member with ID 1471?
- Get the biography of member 172
- Show me contact details for member 4129
- What are the registered interests of member 3743?
- Show recent contributions from member 172
- What is the Commons voting record for member 4129?
- What is the Lords voting record for member 3743?
- Show the professional experience of member 1471
- What policy areas does member 172 focus on?
- Show early day motions submitted by member 1471
- Get the constituency election results for member 4129
- Show me the portrait and thumbnail images for member 172

</details>

<details>
<summary><strong>Bills and Legislation</strong> (14 examples)</summary>

- What recent bills are about fishing?
- What bills were updated recently?
- Show me details of bill 425
- What stages has bill 425 been through?
- What amendments were proposed for bill 425 at stage 15?
- Show me amendment 1234 for bill 425 stage 15
- What publications exist for bill 425?
- What news articles are there about bill 425?
- Show me all bill types available
- What are the different stages a bill can go through?
- Search for bills containing the word "environment"
- Get the RSS feed for all bills
- Get the RSS feed for public bills only
- Get the RSS feed for bill 425

</details>

<details>
<summary><strong>Voting and Divisions</strong> (6 examples)</summary>

- Search Commons Divisions for the keyword "refugee"
- Show details of Commons division 1234
- Show details of Lords division 5678
- Get Commons divisions grouped by party for keyword "climate"
- Get Lords divisions grouped by party for member 3743
- How many divisions match the search term "brexit"?

</details>

<details>
<summary><strong>Committees and Inquiries</strong> (9 examples)</summary>

- Which committees are focused on women's issues?
- List committee meetings scheduled for November 2024
- Show me details of committee 789
- What events has committee 789 held?
- Who are the members of committee 789?
- Search for committee publications about healthcare
- Show me written evidence submitted to committee 789
- Show me oral evidence from committee 789 hearings
- What are all the committee types?

</details>

<details>
<summary><strong>Parliamentary Procedures</strong> (9 examples)</summary>

- Search Erskine May for references to the Mace
- Show oral question times for questions tabled in November 2024
- Search Hansard for contributions on Brexit from November 2024
- What government departments exist?
- What are the answering bodies in Parliament?
- What parties are represented in the House of Commons?
- What parties are represented in the House of Lords?
- Show parliamentary calendar events for Commons in December 2024
- When is Parliament not sitting in January 2025?

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
- Show staff interests for Lords members
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
- Find all committee meetings about climate change between November and December 2024

</details>

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
