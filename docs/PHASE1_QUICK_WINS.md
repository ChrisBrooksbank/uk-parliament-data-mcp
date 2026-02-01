# Phase 1: Quick Wins

Low effort, immediate value improvements.

## 1.1 Add README Badges

**File:** `README.md` (line 1, after title)

Add these badges:
```markdown
[![PyPI version](https://badge.fury.io/py/uk-parliament-mcp.svg)](https://badge.fury.io/py/uk-parliament-mcp)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/ChrisBrooksbank/uk-parliament-mcp-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/ChrisBrooksbank/uk-parliament-mcp-lab/actions/workflows/ci.yml)
```

**Why:** Visual indicators of project health, version, and compatibility at a glance.

---

## 1.2 Add README Table of Contents

**File:** `README.md` (after badges)

The README is 325 lines with no navigation. Add a TOC:

```markdown
## Table of Contents

- [Quick Install](#quick-install)
- [Getting Started](#getting-started)
- [What Can I Ask?](#what-can-i-ask)
- [Full Installation Guide](#full-installation-guide)
  - [Installation from Source](#installation-from-source)
  - [Claude Desktop Configuration](#add-mcp-server-in-claude-desktop-application)
  - [VS Code Configuration](#add-mcp-server-in-vs-code)
- [Prompting Tips](#prompting-tips)
- [Example Prompts](#example-prompts)
```

**Why:** Improves navigation for a long README.

---

## 1.3 Verify Tool Count Consistency

**Files to check:**
- `README.md` - says "94 tools"
- `CLAUDE.md` - says "94 tools"
- `src/uk_parliament_mcp/tools/core.py` - SYSTEM_PROMPT mentions tool count

**Action:** Count actual tools in each module and ensure consistency.

Tool modules and expected counts:
| Module | Tools |
|--------|-------|
| core.py | 4 |
| composite.py | 4 |
| members.py | 26 |
| bills.py | 21 |
| committees.py | 12 |
| commons_votes.py | 5 |
| lords_votes.py | 5 |
| hansard.py | 1 |
| oral_questions.py | 3 |
| interests.py | 3 |
| now.py | 2 |
| whatson.py | 3 |
| statutory_instruments.py | 2 |
| treaties.py | 1 |
| erskine_may.py | 1 |
| **Total** | **93** |

**Note:** Verify this count matches documentation claims.

---

## 1.4 Remove Unused Import

**File:** `src/uk_parliament_mcp/tools/commons_votes.py`

Check if `from urllib.parse import quote` is used. If not, remove it.

**Verification:**
```bash
grep -n "quote" src/uk_parliament_mcp/tools/commons_votes.py
```

---

## Checklist

- [ ] 1.1 Add badges to README.md
- [ ] 1.2 Add table of contents to README.md
- [ ] 1.3 Verify and update tool count across all docs
- [ ] 1.4 Remove unused import if applicable

## Verification

```bash
# Check lint passes
ruff check src/

# Visual check README renders correctly
# Open README.md in GitHub or VS Code preview
```
