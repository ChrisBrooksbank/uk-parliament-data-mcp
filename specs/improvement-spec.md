# UK Parliament MCP - Improvement Specification

## Overview

This specification covers code quality improvements, test coverage expansion, and documentation enhancements for the UK Parliament MCP Server.

## User Stories

- As a developer, I want centralized API configuration so that I can update URLs in one place
- As a contributor, I want comprehensive test coverage so that I can confidently make changes
- As a user, I want clear documentation so that I can quickly understand how to use the server

## Requirements

### Phase 1: Quick Wins
- [ ] README badges (PyPI, Python, License, CI)
- [ ] Table of contents for navigation
- [ ] Consistent tool count across all documentation

### Phase 2: Code Quality
- [ ] Centralized API base URLs in config.py
- [ ] TypedDict for response types
- [ ] Fix unsafe dictionary access patterns
- [ ] Remove unused dependencies

### Phase 3: Testing
- [ ] Test coverage for all 15 tool modules
- [ ] Coverage reporting configuration
- [ ] Target: 80%+ code coverage

### Phase 4: Documentation
- [ ] Collapsible example prompts sections
- [ ] Configuration decision matrix
- [ ] CHANGELOG.md with version history
- [ ] CONTRIBUTING.md with development guide

### Phase 5: CI/CD
- [ ] pip caching for faster CI
- [ ] Coverage reporting in CI
- [ ] Dependabot for dependency updates

## Acceptance Criteria

- [ ] All tests pass: `pytest`
- [ ] Type checking passes: `mypy src/`
- [ ] Linting passes: `ruff check src/`
- [ ] README renders correctly on GitHub
- [ ] Coverage > 80%

## Out of Scope

- New API integrations
- Breaking changes to existing tools
- Performance optimizations (except caching in Phase 5.3)
