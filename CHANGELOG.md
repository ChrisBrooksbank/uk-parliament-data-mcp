# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
