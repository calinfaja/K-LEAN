# Changelog

All notable changes to K-LEAN will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- Knowledge DB V3.1 schema: `timestamp` (ISO 8601), `branch` (git branch), `related_to` (linked entries)
- New entry types: `decision`, `discovery`, `journal` with auto-inference from signal words
- FindKnowledge filter syntax: `since:`, `until:`, `branch:`, `type:` inline filters
- `search_by_date()`, `get_timeline()`, `get_related()` query methods on KnowledgeDB
- Auto-capture: test failures, build errors, package installs, doc URLs, session starts
- Session journal entries created on startup with branch name
- Enhanced git commit capture: full 40-char hash, branch, changed files in insight
- `FindKnowledgeDetail <id>` keyword for fetching full KB entries by ID (progressive disclosure)
- `FindKnowledge` now returns compact index (title, type, date, score, short ID) for token efficiency
- `kln-hook-compact` (PreCompact hook) - automatic session log on context compaction
- Session log system: transcript + git log + KB entries summarized via Claude Haiku
- Session logs stored in `.serena/memories/session-log-YYYY-MM-DD.md` (Serena-discoverable)
- Searchable KB session entries with `related_to` graph links to full session log files
- `kln admin persist-session` CLI command for manual session log generation
- `_kb_send()` helper centralizing all KB TCP communication (11 call sites deduplicated)
- DRY `infer_type()` with signal-word matching, exponential time decay, semantic deduplication
- `kln init` - Unified initialization command with provider selection and multi-provider support
- `kln model` subgroup - Model management commands (list, add, remove, test)
- `kln provider` subgroup - Provider management commands (list, add, set-key, remove)
- `kln admin` subgroup (hidden) - Development tools (sync, debug, test)
- `model_utils.py` - Model name extraction and parsing utilities
- `model_defaults.py` - Default model configurations for NanoGPT (8) and OpenRouter (3)
- Multi-provider selection in `kln init` with model confirmation prompts
- Recommended models auto-installation when adding providers
- `configure_statusline()` - Automatic Claude Code statusline configuration
- Automatic statusline setup during installation
- Statusline validation in `doctor` command with auto-fix

### Fixed
- `make_executable()` now handles both `*.sh` and `*.py` files (statusline script was not executable)
- SuperClaude decoupling in status command
- Empty model_list YAML handling (None → [])
- CONFIG_DIR check in init command
- CLI error handling with proper sys.exit() usage
- 28 new comprehensive unit tests
- **Test fixes (v1.0.0b2)**: CLI integration tests now use new refactored CLI entry point
- **Code quality**: Ruff 100% pass (fixed unused imports, deprecated type hints, format strings)
- **Test coverage**: Updated test assertions to match new CLI structure and docstrings
- All 207 tests now passing (197 from b2 + 10 new)
- **QA fixes (v1.0.0b2)**:
  - `kln model test` now uses httpx with discovery endpoint (was importing non-existent LLMClient)
  - Slash commands (`/kln:quick`, `/kln:multi`, `/kln:rethink`, `/kln:status`) now use correct script path
  - Script count in `kln status` now includes both `.sh` and `.py` files (was showing 29 instead of 39)
  - Removed dead code checking for non-existent `thinking_transform.py` callback

### Changed
- Installation now includes zero-config statusline setup
- Doctor command enhanced with statusline validation
- Config merging now fully non-destructive
- **CLI reorganization:** 17 flat commands → 7 root + 3 subgroups for better UX
  - Model management now under `kln model` (list, add, remove, test)
  - Provider management now under `kln provider` (list, add, set-key, remove)
  - Development tools hidden under `kln admin` (sync, debug, test)
  - Removed redundant `setup` command (merged into `init`)
  - Removed `version` command (use `kln --version`)

### Removed
- `kln setup` - Now part of `kln init`
- `kln version` - Use `kln --version` flag
- `kln add-model` - Moved to `kln model add`
- `kln remove-model` - Moved to `kln model remove`
- `kln models` - Moved to `kln model list`
- `kln test-model` - Moved to `kln model test`
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
