# Project Index: K-LEAN

**Generated**: 2026-01-01
**Version**: 1.0.0-beta
**License**: Apache-2.0

---

## Project Summary

Multi-model code review and persistent knowledge system for Claude Code. Get consensus from 3-5 LLMs, capture insights to a searchable knowledge base, and use 8 specialist agents for domain-specific analysis.

---

## Project Structure

```
k-lean/
├── src/klean/              # Main package (16K lines Python)
│   ├── cli.py              # CLI entry point (k-lean command)
│   ├── discovery.py        # Model discovery from LiteLLM
│   ├── smol/               # SmolKLN agent system
│   │   ├── cli.py          # smol-kln command
│   │   ├── executor.py     # Single agent execution
│   │   ├── multi_agent.py  # Multi-agent orchestration
│   │   ├── tools.py        # Agent tools (read, grep, git)
│   │   └── loader.py       # Agent .md file parser
│   ├── knowledge/          # Knowledge DB integration
│   └── data/               # Installable assets
│       ├── scripts/        # 35 shell & Python scripts (5K lines)
│       ├── commands/kln/   # 9 slash commands
│       ├── hooks/          # 4 Claude Code hooks
│       ├── agents/         # 8 SmolKLN agent definitions
│       └── config/         # LiteLLM & provider templates
├── tests/                  # 6 unit tests + fixtures
├── docs/                   # User & architecture docs
├── CLAUDE.md               # Claude Code instructions
└── AGENTS.md               # Universal AI instructions
```

---

## Entry Points

| Command | Source | Description |
|---------|--------|-------------|
| `k-lean` | `src/klean/cli.py:main` | Main CLI (install, status, doctor, multi, etc.) |
| `smol-kln` | `src/klean/smol/cli.py:main` | SmolAgents executor |

---

## Core Modules

### `src/klean/cli.py` (2800+ lines)
Primary CLI with Click commands:
- `install` / `uninstall` - Component installation
- `status` / `doctor` - Health checks and auto-fix
- `start` / `stop` - Service management (LiteLLM, Knowledge server)
- `models` / `test-model` - Model discovery and testing
- `multi` - Multi-agent orchestrated review
- `setup` - Provider configuration (NanoGPT, OpenRouter)
- `debug` - Real-time monitoring dashboard

### `src/klean/discovery.py`
Dynamic model discovery from LiteLLM proxy:
- `list_models()` - Get all available models (TTL cached)
- `get_model()` - Get first available model
- `is_available()` - Check LiteLLM status

### `src/klean/data/core/klean_core.py` (1300+ lines)
Review engine for quick/multi commands:
- `LLMClient` - HTTP client for LiteLLM
- `ModelResolver` - Model name resolution
- `ReviewEngine` - Single and multi-model reviews
- `cli_quick()`, `cli_multi()`, `cli_rethink()` - CLI handlers

### `src/klean/smol/executor.py`
SmolAgents-based agent execution:
- `SmolKLNExecutor` - Single agent runner
- Supports tools: read_file, grep, git_diff, knowledge_search

### `src/klean/smol/multi_agent.py`
Multi-agent orchestration (3 or 4 agent configurations):
- Manager orchestrates file_scout + analyzer (3-agent)
- Or file_scout + code_analyzer + security_auditor + synthesizer (4-agent)

---

## Slash Commands (/kln:*)

| Command | File | Purpose |
|---------|------|---------|
| `/kln:quick` | commands/kln/quick.md | Fast single-model review |
| `/kln:multi` | commands/kln/multi.md | Multi-model consensus |
| `/kln:agent` | commands/kln/agent.md | SmolKLN specialist agents |
| `/kln:rethink` | commands/kln/rethink.md | Fresh perspective debugging |
| `/kln:learn` | commands/kln/learn.md | Context-aware learning extraction |
| `/kln:remember` | commands/kln/remember.md | End-of-session capture |
| `/kln:doc` | commands/kln/doc.md | Documentation generation |
| `/kln:status` | commands/kln/status.md | System status |
| `/kln:help` | commands/kln/help.md | Command reference |

---

## Hooks

| Hook | File | Trigger |
|------|------|---------|
| UserPromptSubmit | hooks/user-prompt-handler.sh | SaveThis, FindKnowledge, async* |
| PostToolUse (Bash) | hooks/post-bash-handler.sh | Post-commit docs, timeline |
| PostToolUse (Web*) | hooks/post-web-handler.sh | Auto-capture URLs |
| SessionStart | hooks/session-start.sh | Session initialization |

---

## SmolKLN Agents

| Agent | File | Specialty |
|-------|------|-----------|
| code-reviewer | agents/code-reviewer.md | OWASP, SOLID, code quality |
| security-auditor | agents/security-auditor.md | Vulnerabilities, auth, crypto |
| debugger | agents/debugger.md | Root cause analysis |
| performance-engineer | agents/performance-engineer.md | Profiling, optimization |
| rust-expert | agents/rust-expert.md | Ownership, lifetimes, unsafe |
| c-pro | agents/c-pro.md | C99/C11, POSIX, embedded |
| arm-cortex-expert | agents/arm-cortex-expert.md | ARM MCU, real-time |
| orchestrator | agents/orchestrator.md | Multi-agent coordination |

**Agent Tools**: `read_file`, `search_files`, `grep`, `knowledge_search`, `get_complexity`

---

## Knowledge Database

**Storage**: `.knowledge-db/` per project
**Server**: Unix socket, auto-starts on first use

| Script | Purpose |
|--------|---------|
| knowledge-server.py | Persistent server daemon |
| knowledge-search.py | Semantic search (txtai) |
| knowledge-hybrid-search.py | BM25 + semantic hybrid |
| knowledge-capture.py | Entry creation |
| knowledge-query.sh | CLI query interface |

---

## Configuration

| File | Purpose |
|------|---------|
| `pyproject.toml` | Package metadata, dependencies |
| `data/config/klean-config.yaml` | K-LEAN defaults |
| `data/config/litellm/config.yaml` | LiteLLM model routing |
| `data/config/nanogpt.yaml` | NanoGPT template |
| `data/config/litellm/openrouter.yaml` | OpenRouter template |
| `.serena/project.yml` | Serena MCP project config |

---

## Dependencies

**Core** (always installed):
- click>=8.0.0 - CLI framework
- rich>=13.0.0 - Terminal formatting
- pyyaml>=6.0.0 - YAML parsing
- httpx>=0.27.0 - HTTP client

**Optional extras**:
- `[knowledge]` - txtai, sentence-transformers
- `[smolagents]` - smolagents, ddgs, markdownify
- `[telemetry]` - arize-phoenix, opentelemetry
- `[all]` - Everything

---

## Tests

**Location**: `tests/`
**Framework**: pytest

| Test File | Coverage |
|-----------|----------|
| test_discovery.py | Model discovery |
| test_loader.py | Agent file parsing |
| test_context.py | Project context |
| test_memory.py | Session memory |
| test_tools_citations.py | Citation validation |
| test_doctor_hooks.py | Hook installation |

**Core tests**: `src/klean/data/core/tests/` (27 tests)

---

## Quick Start

```bash
# Install
pipx install k-lean

# Configure provider
k-lean setup

# Start services
k-lean start

# Check status
k-lean status
k-lean doctor -f  # Auto-fix issues

# Run reviews
k-lean multi "security review"
smol-kln security-auditor "audit auth"
```

---

## Key Patterns

1. **Dynamic model discovery**: All models from LiteLLM, no hardcoding
2. **First-available model**: User controls priority via config order
3. **Agent definitions**: YAML frontmatter + markdown system prompt
4. **Per-project knowledge**: `.knowledge-db/` isolated per repo
5. **Hook system**: Shell scripts for Claude Code integration

---

## File Count Summary

| Type | Count | Lines |
|------|-------|-------|
| Python | 53 | 16,438 |
| Shell | 35 | 5,421 |
| Markdown | 100+ | - |
| YAML/TOML | 12 | - |
| Tests | 6 | - |

---

## Documentation

| Document | Path |
|----------|------|
| Installation | `docs/installation.md` |
| Usage | `docs/usage.md` |
| Reference | `docs/reference.md` |
| Architecture | `docs/architecture/OVERVIEW.md` |
| Components | `docs/architecture/COMPONENTS.md` |
| Development | `docs/architecture/DEVELOPMENT.md` |

---

*Index size: ~4KB | Full codebase: ~60K tokens | Savings: 94%*
