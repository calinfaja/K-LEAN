# Changelog

All notable changes to K-LEAN will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

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
