# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Repository URLs in package metadata, CLI help and CONTRIBUTING.md now point to `uk-parliament-data-mcp`

## [1.17.1] - 2026-03-10

### Fixed
- Stale tool counts (163 → 209) in CLI help text

## [1.17.0] - 2026-03-10

### Added
- 46 new Parliament API tools (163 → 209) with matching CLI commands and tests

## [1.16.0] - 2026-03-10

### Added
- PyInstaller packaging for standalone `parliament` executables
- `/parliament-research` slash command

## [1.15.3] - 2026-02-22

### Fixed
- Documentation drift in tool signatures, counts and CLI examples
- Test failures and lint warnings

## [1.15.2] - 2026-02-09

### Added
- Watch dashboard keyboard controls; Commons/Lords calendar panels with scroll indicators

### Fixed
- Cross-platform mypy and headless CI key-reader tests

## [1.15.0] - 2026-02-08

### Added
- Interactive `parliament api try` explorer and `parliament api explore` URL parser
- Truncation warning for human-friendly CLI output; striped table rows

### Changed
- `--json` flag standardised to `--format` across `api`, `guide` and main commands

### Removed
- Shell tab completion (broken)

## [1.14.0] - 2026-02-08

### Added
- `parliament api` commands for browsing Parliament API specs
- URL logging after every CLI command
- Case-insensitive `--fields` matching, with a hint listing available fields
- Performance tests for request counts and parallel execution

### Changed
- Duplicate search commands merged into a single `search` with optional filters
- Shared CLI type aliases and output helpers extracted across CLI modules

## [1.13.0] - 2026-02-07

### Added
- `parliament digest` daily/weekly summary with enriched bills and links

### Fixed
- Hansard debate links in digest

### Removed
- `daily-reports` CLI command (Parliament API returns broken blob URLs)

## [1.11.0] - 2026-02-06

### Added
- `parliament my-mp` postcode lookup

### Fixed
- Division number mismatch between `my-mp` and `votes get-division`

## [1.9.0] - 2026-02-06

### Added
- Watch dashboard house colours, time tracking and Parliament TV links
- Missing API parameters on CLI commands; `nameContains` filter for answering bodies and departments

### Changed
- Response pruning disabled for CLI output

## [1.8.0] - 2026-02-06

### Added
- Unofficial disclaimer and LICENSE file

## [1.6.0] - 2026-02-05

### Added
- MCP response pruning and MCP resources
- Watch dashboard, rich CLI output for live and composite commands
- CLI auto-pagination for `skip`/`take` commands

### Fixed
- Windows console encoding errors for Unicode output

## [1.5.0] - 2026-02-05

### Added
- `parliament` CLI for terminal access to the Parliament APIs, with table and markdown output
- `parliament reference` command

### Fixed
- Commons Votes API URL now uses HTTPS

## [1.4.0] - 2026-02-05

### Added
- 46 new tools for Erskine May, Hansard, Committees and Members, and advanced filtering on existing tools (161 total)

### Fixed
- Written Questions API 301 redirect; members tools corrected against the live API

## [1.3.0] - 2026-02-03

### Added
- 15 tools for government structure, EDM details, SI/treaty details and procedural dates

## [1.2.1] - 2026-02-03

### Fixed
- Hansard API base URL

## [1.1.0] - 2026-02-03

### Added
- Centralized API configuration in `config.py`
- TypedDict for HTTP client response types
- Expanded test coverage for all tool modules
- pytest-cov for code coverage tracking
- CHANGELOG.md and CONTRIBUTING.md
- README badges (PyPI version, Python 3.11+, MIT License, CI status)
- README table of contents
- Configuration decision matrix in README
- Collapsible example prompt sections in README

### Changed
- Restructured README with improved organization and navigation
- Corrected tool count from 94 to 92 in all documentation
- Safer dictionary access patterns in composite tools

### Removed
- Unused tenacity dependency

## [1.0.1] - 2026-02-01

### Added
- Server-level instructions for automatic context via MCP `instructions` parameter
- Composite tools documentation in CLAUDE.md
- Composite tools for common workflows (`get_mp_profile`, `check_mp_vote`, `get_bill_overview`, `get_committee_summary`)
- Agent guidance system with `/parliament` MCP prompt
- `parliament_guide()` and `parliament_workflow()` tools for navigating available tools

### Changed
- Improved documentation clarity in CLAUDE.md
- Enhanced LLM efficiency with high-level composite tools

### Fixed
- Getting Started section references to configuration steps

## [1.0.0] - 2026-01-28

### Added
- Initial Python release of UK Parliament MCP Server
- 92 tools covering 15 Parliament APIs (members, bills, votes, committees, Hansard, etc.)
- Support for Claude Desktop and VS Code via MCP protocol
- HTTP client with automatic retry logic and timeout protection
- Comprehensive documentation in CLAUDE.md and README.md
- CI/CD pipeline with GitHub Actions (linting, type checking, tests)
- PyPI publishing via Trusted Publishing
- Test infrastructure with pytest and pytest-asyncio
- Type checking with mypy
- Code quality enforcement with ruff

### Changed
- Migrated from C# implementation to Python 3.11+
- Adopted FastMCP framework for simplified MCP server development
