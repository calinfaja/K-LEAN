# Project Index: K-LEAN

**Generated**: 2026-01-01
**Version**: 1.0.0b1
**License**: Apache-2.0

---

## Project Summary

Multi-model code review and persistent knowledge system for Claude Code. Get consensus from 3-5 LLMs, capture insights to a searchable knowledge base, and use 8 specialist agents for domain-specific analysis.

---

## Project Structure

```
k-lean/
├── src/klean/              # Main package (7.8K lines Python)
│   ├── cli.py              # CLI entry point (kln command)
│   ├── discovery.py        # Model discovery from LiteLLM
│   ├── smol/               # SmolKLN agent system (16 modules)
│   │   ├── cli.py          # smol-kln command
│   │   ├── executor.py     # Single agent execution
│   │   ├── multi_agent.py  # Multi-agent orchestration
│   │   ├── tools.py        # Agent tools (read, grep, git)
│   │   ├── models.py       # LiteLLM model wrapper
│   │   └── loader.py       # Agent .md file parser
│   ├── tools/              # Agent tools (grep, read, search)
│   └── data/               # Installable assets
│       ├── scripts/        # 39 shell & Python scripts
│       ├── commands/kln/   # 9 slash commands
│       ├── hooks/          # 4 Claude Code hooks
│       ├── agents/         # 8 SmolKLN agent definitions
│       └── config/         # LiteLLM & provider templates
├── tests/                  # 10 test files
├── docs/                   # User & architecture docs
├── CLAUDE.md               # Claude Code instructions
└── AGENTS.md               # Universal AI instructions
```

---

## Entry Points

| Command | Source | Description |
|---------|--------|-------------|
| `kln` | `src/klean/cli.py:main` | Main CLI (install, status, doctor, multi, etc.) |
| `smol-kln` | `src/klean/smol/cli.py:main` | SmolAgents executor |

---

## Core Modules

### `src/klean/cli.py`
Primary CLI with Click commands:
- `install` / `uninstall` - Component installation
- `status` / `doctor` - Health checks and auto-fix
- `start` / `stop` - Service management (LiteLLM, Knowledge server)
- `models` / `test-model` - Model discovery and testing
- `multi` - Multi-agent orchestrated review
- `setup` - Provider configuration (NanoGPT, OpenRouter)
- `debug` - Real-time monitoring dashboard
- `sync` - Sync package data for PyPI
- `version` - Show version information

### `src/klean/discovery.py`
Dynamic model discovery from LiteLLM proxy:
- `list_models()` - Get all available models (TTL cached)
- `get_model()` - Get first available model
- `is_available()` - Check LiteLLM status

### `src/klean/smol/` (16 modules)
SmolAgents-based agent system:
| Module | Purpose |
|--------|---------|
| `cli.py` | SmolKLN CLI entry point |
| `executor.py` | Single agent execution with tool use |
| `multi_agent.py` | Multi-agent orchestration and consensus |
| `tools.py` | Agent tools: read_file, search_files, grep |
| `models.py` | LiteLLM model wrapper, thinking model support |
| `orchestrator.py` | Agent coordination and task delegation |
| `memory.py` | Agent memory and context management |
| `context.py` | Git context extraction (status, diff, log) |
| `prompts.py` | System prompts and templates |
| `loader.py` | Agent definition loading from markdown |
| `async_executor.py` | Async agent execution |
| `multi_config.py` | Multi-agent configuration |
| `task_queue.py` | Task queue for parallel execution |
| `reflection.py` | Agent self-reflection |
| `mcp_tools.py` | MCP tool integration |

### `src/klean/tools/` (Agent Tools)
| Module | Purpose |
|--------|---------|
| `read_tool.py` | File reading with line limits |
| `grep_tool.py` | Pattern search in files |
| `search_knowledge_tool.py` | Knowledge DB semantic search |

---

## Slash Commands (/kln:*)

| Command | File | Purpose |
|---------|------|---------|
| `/kln:quick` | commands/kln/quick.md | Fast single-model review (~30s) |
| `/kln:multi` | commands/kln/multi.md | Multi-model consensus (~60s) |
| `/kln:agent` | commands/kln/agent.md | SmolKLN specialist agents (~2min) |
| `/kln:rethink` | commands/kln/rethink.md | Contrarian debugging |
| `/kln:learn` | commands/kln/learn.md | Context-aware learning extraction |
| `/kln:remember` | commands/kln/remember.md | End-of-session capture |
| `/kln:doc` | commands/kln/doc.md | Documentation generation |
| `/kln:status` | commands/kln/status.md | System status |
| `/kln:help` | commands/kln/help.md | Command reference |

---

## Hooks

| Hook | File | Trigger |
|------|------|---------|
| SessionStart | hooks/session-start.sh | Auto-start LiteLLM + Knowledge Server |
| UserPromptSubmit | hooks/user-prompt-handler.sh | FindKnowledge, SaveInfo, async reviews |
| PostToolUse (Bash) | hooks/post-bash-handler.sh | Post-commit docs, timeline |
| PostToolUse (Web*) | hooks/post-web-handler.sh | Auto-capture URLs |

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
| kb-init.sh | Initialize project KB |

---

## Key Scripts (39 total)

### Review Scripts
- `quick-review.sh` - Single model quick review
- `consensus-review.sh` - Multi-model consensus
- `second-opinion.sh` - Alternative perspective

### Service Scripts
- `setup-litellm.sh` - LiteLLM proxy setup
- `start-litellm.sh` - Start proxy
- `health-check.sh` - Service health
- `session-helper.sh` - Session management

### Utility Scripts
- `timeline-query.sh` - Query timeline log
- `smart-capture.sh` - Smart URL capture
- `fact-extract.sh` - Extract facts from text
- `async-dispatch.sh` - Async task dispatch

---

## Configuration

| File | Purpose |
|------|---------|
| `pyproject.toml` | Package metadata, dependencies |
| `config/litellm/config.yaml` | LiteLLM model routing (NanoGPT) |
| `config/litellm/openrouter.yaml` | LiteLLM model routing (OpenRouter) |
| `config/CLAUDE.md` | K-LEAN command reference |
| `.serena/project.yml` | Serena MCP project config |

---

## Dependencies

**Core** (always installed):
- click>=8.0.0 - CLI framework
- rich>=13.0.0 - Terminal formatting
- pyyaml>=6.0.0 - YAML parsing
- httpx>=0.27.0 - HTTP client
- txtai>=7.0.0 - Semantic embeddings
- sentence-transformers>=2.0.0 - Embedding models
- smolagents[litellm]>=1.17.0 - Agent framework
- lizard>=1.17.0 - Code complexity analysis

**Optional extras**:
- `[agent-sdk]` - anthropic (Claude Agent SDK)
- `[telemetry]` - arize-phoenix, opentelemetry
- `[toon]` - python-toon
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

**Core tests**: `src/klean/data/core/tests/` (run_all_tests.py)

---

## Quick Start

```bash
# Install
pipx install .

# Configure provider
kln install
kln setup

# Start services
kln start

# Check status
kln status
kln doctor -f  # Auto-fix issues

# Run reviews (in Claude Code)
/kln:quick security
/kln:multi "security review"
/kln:agent security-auditor "audit auth"
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

| Type | Count |
|------|-------|
| Python | 37 |
| Shell | 29 |
| Markdown (agents, commands, docs) | 50+ |
| YAML/TOML | 14 |
| Tests | 10 |

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
