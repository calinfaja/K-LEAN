# Changelog

All notable changes to K-LEAN will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [1.0.0-beta] - 2025-12-21

### Added
- Initial open source release
- K-LEAN CLI (`kln status`, `kln doctor`, `kln start`)
- Knowledge DB with per-project semantic search
- Multi-model code review via LiteLLM proxy
- SmolKLN agents (8 specialist AI agents)
- `/kln:*` slash commands for Claude Code

### Changed
- Restructured for PyPI distribution (`pipx install k-lean`)
- All paths now relative/environment-based for portability

### Removed
- Legacy shell-based installation scripts
- Project-specific files
