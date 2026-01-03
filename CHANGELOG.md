# Changelog

All notable changes to K-LEAN will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added
- `kln init` - Unified initialization command with provider selection
- `kln model` subgroup - Model management commands (list, add, remove, test)
- `kln admin` subgroup (hidden) - Development tools (sync, debug, test)
- `model_utils.py` - Model name extraction and parsing utilities
- `configure_statusline()` - Automatic Claude Code statusline configuration
- Automatic statusline setup during installation
- Statusline validation in `doctor` command with auto-fix

### Fixed
- SuperClaude decoupling in status command
- Empty model_list YAML handling (None → [])
- CONFIG_DIR check in init command
- CLI error handling with proper sys.exit() usage
- 28 new comprehensive unit tests

### Changed
- Installation now includes zero-config statusline setup
- Doctor command enhanced with statusline validation
- Config merging now fully non-destructive
- **CLI reorganization:** 17 flat commands → 7 root + 2 subgroups for better UX
  - Model management now under `kln model` (list, add, remove, test)
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
