# Changelog

All notable changes to K-LEAN will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

## [1.0.0b11] - 2026-02-09

### Removed
- Dead code: async_executor.py, orchestrator.py, reflection.py, task_queue.py (never wired into CLI)
- 3 test files for dead modules (74 tests)

### Fixed
- CHANGELOG.md rewritten with proper release sections (was single Unreleased blob)
- Orchestrator agent definition rewritten (was 773-line Factory.ai copy-paste)
- Stale version references across 5 documentation files
- CLAUDE.md: added missing modules and data directories
- COMPONENTS.md: fixed SaveThis -> SaveInfo, V2 -> V3.1 schema
- CONTRIBUTING.md: added Python 3.9+ requirement, removed stale shellcheck reference
- DEVELOPMENT.md: fixed hook count (4->5), added 4 missing data directories
- future-features.md: replaced shell script refs with Python equivalents
- shell-to-python-migration.md: added 5th hook entry
- PROJECT_INDEX files: updated version, modules, test counts

### Changed
- Prevent Haiku refusals in session log generation by refining prompt structure
- Improve session log quality: fix double-truncation (500->2000 char cap), async PreCompact, cross-midnight git window fix, TCP recv loop for knowledge capture
- Updated CLAUDE.md and README with recent knowledge system changes

## [1.0.0b10] - 2026-02-08

### Added
- Show KB entry count in statusline even when knowledge server is stopped

## [1.0.0b9] - 2026-02-08

### Added
- Knowledge-only install path (`kln init --provider skip`): deploys scripts, commands, hooks, rules, knowledge venv, statusline without smolkln/litellm
- PreCompact hook fires on both auto and manual `/compact` triggers for session log generation
- KB entry count display in statusline (`kb:42` format) via single TCP status round-trip
- Auto-pinning: critical entries pinned at capture, others after 3 retrievals (1.3x search boost, cap 15)

### Fixed
- Remove hardcoded model names across CLI, reviews, help docs, agent executors
- Add retry logic for LiteLLM health check with fallback
- Two-pass project root discovery for edge cases
- Non-interactive mode for provider setup
- Ruff formatting fixes across 4 files

## [1.0.0b8] - 2026-02-08

### Added
- `kln-hook-compact` (PreCompact hook) - automatic session log on context compaction via Claude Haiku
- Session logs stored in `.serena/memories/session-log-YYYY-MM-DD.md` (Serena-discoverable)
- Searchable KB session entries with `related_to` graph links
- `kln admin persist-session` CLI command for manual session log generation
- `FindKnowledgeDetail <id>` keyword for fetching full KB entries by ID (progressive disclosure)
- `FindKnowledge` returns compact index (title, type, date, score, short ID) for token efficiency
- `_kb_send()` helper centralizing all KB TCP communication (11 call sites deduplicated)
- Knowledge DB V3.1 schema: `timestamp` (ISO 8601), `branch` (git branch), `related_to` (linked entries)
- New entry types: `decision`, `discovery`, `journal` with auto-inference from signal words
- FindKnowledge filter syntax: `since:`, `until:`, `branch:`, `type:` inline filters
- `search_by_date()`, `get_timeline()`, `get_related()` query methods on KnowledgeDB
- Auto-capture: test failures, build errors, package installs, doc URLs, session starts
- DRY `infer_type()` with signal-word matching, exponential time decay, semantic deduplication

### Fixed
- Model name `deepseek-v3.2-speciale` renamed to `deepseek-v3.2`

## [1.0.0b7] - 2026-01-11

### Added
- Native Windows support with hypercorn proxy (no uvloop dependency)
- Comprehensive test coverage for smol modules
- Server-owned writes for immediate Knowledge DB searchability

### Fixed
- Windows compatibility for platform and init tests
- Unicode symbols replaced with ASCII for cp1252 encoding (Windows terminals)
- Uninstall backup collision on repeated runs
- Model command references from `kln models` to `kln model list`
- Pydantic serialization warnings from smolagents/LiteLLM suppressed

### Changed
- Full cross-platform support (Windows/Linux/macOS) via platform.py, psutil, platformdirs
- Architecture docs updated for cross-platform migration
- Codebase cleanup: removed dead code and fixed documentation

## [1.0.0b5] - 2026-01-05

### Fixed
- Pydantic serialization warnings from smolagents/LiteLLM suppressed

## [1.0.0b4] - 2026-01-05

### Fixed
- Sync `__version__` to 1.0.0b4
- Remove unused `Dict` import (CI fix)
- stdin/context-file support for `cli_quick` and `cli_multi`

## [1.0.0b3] - 2026-01-04

### Fixed
- Statusline permission and docs accuracy
- Remove duplicate docs, fix PROJECT_INDEX, improve README flow

### Changed
- Move Quick Start after value proposition in README for better UX
- Add "What You Get" section to README

## [1.0.0b2] - 2026-01-04

### Added
- `kln init` - Unified initialization command with provider selection and multi-provider support
- `kln model` subgroup - Model management commands (list, add, remove, test)
- `kln provider` subgroup - Provider management commands (list, add, set-key, remove)
- `kln admin` subgroup (hidden) - Development tools (sync, debug, test)
- `model_utils.py` - Model name extraction and parsing utilities
- `model_defaults.py` - Default model configurations for NanoGPT and OpenRouter
- Multi-provider selection in `kln init` with model confirmation prompts
- `configure_statusline()` - Automatic Claude Code statusline configuration

### Fixed
- CLI integration tests updated for refactored CLI entry point
- Ruff 100% pass (unused imports, deprecated type hints, format strings)
- All 207 tests passing
- `kln model test` now uses httpx with discovery endpoint
- Slash commands use correct script paths
- Script count includes both `.sh` and `.py` files

### Changed
- CLI reorganization: 17 flat commands -> 7 root + 3 subgroups
- Installation includes zero-config statusline setup
- Doctor command enhanced with statusline validation
- Config merging now fully non-destructive

### Removed
- `kln setup` - Now part of `kln init`
- `kln version` - Use `kln --version` flag
- `kln add-model`, `kln remove-model`, `kln models`, `kln test-model` - Moved to `kln model` subgroup
- `kln sync`, `kln debug`, `kln test` - Moved to `kln admin` (hidden)

## [1.0.0b1] - 2025-12-30

### Added
- Initial open source release
- K-LEAN CLI (`kln install`, `kln setup`, `kln doctor`, `kln start`)
- Knowledge DB with per-project semantic search
- Multi-model code review via LiteLLM proxy
- SmolKLN agents (8 specialist AI agents)
- `/kln:*` slash commands for Claude Code (9 commands)
- PyPI package distribution (`pipx install kln-ai`)

### Changed
- Restructured for PyPI distribution
- All paths now relative/environment-based for portability

### Removed
- Legacy shell-based installation scripts
