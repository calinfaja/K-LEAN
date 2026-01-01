# K-LEAN Project Index

> Comprehensive cross-referenced documentation for the K-LEAN codebase

---

## Package Overview

**K-LEAN** (v1.0.0-beta) is a multi-model code review and knowledge capture system for Claude Code.

| Component | Purpose | Entry Point |
|-----------|---------|-------------|
| **kln** | Main CLI for installation and management | `klean.cli:main` |
| **smol-kln** | SmolKLN agent CLI | `klean.smol.cli:main` |

---

## Source Code Structure

```
src/klean/
├── __init__.py          # Package metadata, path constants
├── cli.py               # Main CLI (kln command)
├── discovery.py         # Model discovery from LiteLLM proxy
├── smol/                # SmolKLN agent system
├── tools/               # Agent tools
├── utils/               # Shared utilities
└── data/                # Installable assets (scripts, hooks, commands)
```

---

## Core Modules

### `klean/__init__.py`
Package entry point with path constants.

| Constant | Path | Purpose |
|----------|------|---------|
| `DATA_DIR` | `src/klean/data/` | Package data directory |
| `CLAUDE_DIR` | `~/.claude/` | Claude Code configuration |
| `VENV_DIR` | `~/.venvs/knowledge-db/` | Knowledge DB Python environment |
| `CONFIG_DIR` | `~/.config/litellm/` | LiteLLM configuration |
| `KLEAN_DIR` | `~/.klean/` | K-LEAN runtime data |
| `SMOL_AGENTS_DIR` | `~/.klean/agents/` | Agent definitions |

### `klean/cli.py`
Main CLI entry point. Implements all `kln` commands.

| Command | Function | Description |
|---------|----------|-------------|
| `install` | `install()` | Deploy components to ~/.claude/ |
| `uninstall` | `uninstall()` | Remove components |
| `status` | `status()` | Show component health |
| `doctor` | `doctor()` | Diagnose and auto-fix issues |
| `start` | `start()` | Start LiteLLM/services |
| `stop` | `stop()` | Stop all services |
| `debug` | `debug()` | Live monitoring dashboard |
| `models` | `models()` | List available models |
| `setup` | `setup()` | Interactive API configuration |
| `multi` | `multi()` | Multi-agent orchestrated review |
| `sync` | `sync_data()` | Sync data for PyPI packaging |
| `test` | `test()` | Run test suite |
| `version` | `version()` | Show version info |

### `klean/discovery.py`
Central model discovery from LiteLLM proxy.

| Function | Description |
|----------|-------------|
| `list_models()` | Get all available models (cached 5 min) |
| `get_model(override)` | Get model (explicit or first available) |
| `clear_cache()` | Force refresh on next call |
| `is_available()` | Check if LiteLLM is running |

---

## SmolKLN Agent System

Located in `src/klean/smol/`. Built on [smolagents](https://github.com/huggingface/smolagents).

### Module Index

| Module | Lines | Purpose |
|--------|-------|---------|
| `executor.py` | ~400 | Main agent execution engine |
| `tools.py` | ~1500 | Custom agent tools |
| `orchestrator.py` | ~340 | Multi-agent coordination |
| `memory.py` | ~350 | Session and agent memory |
| `context.py` | - | Project context gathering |
| `loader.py` | - | Agent definition loading |
| `models.py` | - | LiteLLM model wrapper |
| `prompts.py` | - | System prompts |
| `cli.py` | ~120 | SmolKLN CLI entry point |
| `multi_agent.py` | - | Multi-agent execution |
| `multi_config.py` | - | Multi-agent configuration |
| `task_queue.py` | - | Async task management |
| `async_executor.py` | - | Async agent execution |
| `reflection.py` | - | Agent reflection/improvement |
| `mcp_tools.py` | - | MCP tool integration |

### `smol/executor.py`
Primary agent execution engine.

```python
class SmolKLNExecutor:
    def __init__(agents_dir, api_base, project_path)
    def execute(agent_name, task, model_override) -> AgentResult
```

**Features:**
- Project-aware context (CLAUDE.md, git info)
- Knowledge DB integration
- Citation validation
- Step awareness callbacks

### `smol/tools.py`
Custom tools available to agents.

| Tool | Description |
|------|-------------|
| `read_file` | Read file contents with line numbers |
| `search_files` | Glob pattern file search |
| `grep` | Content search with regex |
| `grep_with_context` | Grep with surrounding lines |
| `knowledge_search` | Query Knowledge DB |
| `web_search` | DuckDuckGo web search |
| `visit_webpage` | Fetch and parse web pages |
| `git_diff` | Show git differences |
| `git_status` | Repository status |
| `git_log` | Commit history |
| `git_show` | Show commit details |
| `scan_secrets` | Detect hardcoded secrets |
| `get_complexity` | Code complexity (Python/C/C++) |
| `analyze_test_coverage` | Test coverage analysis |

### `smol/orchestrator.py`
Multi-agent task coordination.

```python
class TaskPlan:
    subtasks: List[SubTask]
    dependencies: Dict[str, List[str]]

class Orchestrator:
    def plan(task) -> TaskPlan
    def execute(plan) -> OrchestratorResult
```

---

## Agent Definitions

Located in `src/klean/data/agents/`. Markdown files with YAML frontmatter.

| Agent | File | Expertise |
|-------|------|-----------|
| code-reviewer | `code-reviewer.md` | OWASP, SOLID, code quality |
| security-auditor | `security-auditor.md` | Vulnerabilities, auth, crypto |
| debugger | `debugger.md` | Root cause analysis |
| performance-engineer | `performance-engineer.md` | Profiling, optimization |
| rust-expert | `rust-expert.md` | Ownership, lifetimes, unsafe |
| c-pro | `c-pro.md` | C99/C11, POSIX, memory |
| arm-cortex-expert | `arm-cortex-expert.md` | Embedded ARM, real-time |
| orchestrator | `orchestrator.md` | Multi-agent coordination |

**Agent Format:**
```yaml
---
name: agent-name
description: Agent description
model: inherit  # or specific model
tools: ["tool1", "tool2", ...]
---

System prompt content...
```

---

## Slash Commands

Located in `src/klean/data/commands/kln/`. 9 commands total.

| Command | File | Description |
|---------|------|-------------|
| `/kln:quick` | `quick.md` | Single model fast review |
| `/kln:multi` | `multi.md` | 3-5 model consensus |
| `/kln:agent` | `agent.md` | SmolKLN specialist agents |
| `/kln:rethink` | `rethink.md` | Contrarian debugging |
| `/kln:doc` | `doc.md` | Session documentation |
| `/kln:learn` | `learn.md` | Context-aware knowledge capture |
| `/kln:remember` | `remember.md` | End-of-session capture |
| `/kln:status` | `status.md` | System health check |
| `/kln:help` | `help.md` | Command reference |

---

## Hooks

Located in `src/klean/data/hooks/`. 4 handlers.

| Hook | File | Trigger |
|------|------|---------|
| User Prompt | `user-prompt-handler.sh` | FindKnowledge, SaveInfo, asyncReview |
| Post Bash | `post-bash-handler.sh` | Git commit documentation |
| Post Web | `post-web-handler.sh` | Auto-capture web content |
| Session Start | `session-start.sh` | Start LiteLLM, Knowledge server |

---

## Scripts

Located in `src/klean/data/scripts/`. 39 scripts total.

### Review Scripts
| Script | Purpose |
|--------|---------|
| `quick-review.sh` | Single model review |
| `consensus-review.sh` | Multi-model consensus |
| `second-opinion.sh` | Alternative perspective |
| `async-dispatch.sh` | Background review dispatch |

### Knowledge DB Scripts
| Script | Purpose |
|--------|---------|
| `knowledge_db.py` | Main Knowledge DB implementation (~24K) |
| `knowledge-capture.py` | Add entries to KB |
| `knowledge-search.py` | Direct KB search |
| `knowledge-query.sh` | Query via server |
| `knowledge-server.py` | Unix socket server |
| `knowledge-hybrid-search.py` | Hybrid search (semantic + keyword) |
| `kb_utils.py` | Shared KB utilities |
| `kb-doctor.sh` | KB diagnostics |
| `kb-init.sh` | Initialize KB for project |
| `kb-root.sh` | Find project root |

### Infrastructure Scripts
| Script | Purpose |
|--------|---------|
| `setup-litellm.sh` | Configure LiteLLM |
| `start-litellm.sh` | Start LiteLLM proxy |
| `health-check.sh` | Service health check |
| `health-check-model.sh` | Individual model check |
| `get-models.sh` | List available models |
| `get-healthy-models.sh` | List healthy models |
| `validate-model.sh` | Validate model config |
| `test-system.sh` | Run system tests |

### Utility Scripts
| Script | Purpose |
|--------|---------|
| `timeline-query.sh` | Query chronological log |
| `smart-capture.py` | Intelligent content capture |
| `smart-web-capture.sh` | Web content capture |
| `fact-extract.sh` | Extract facts from text |
| `post-commit-docs.sh` | Document commits |
| `session-helper.sh` | Session utilities |
| `sync-check.sh` | Verify file sync |
| `sync-serena-kb.py` | Sync KB with Serena |
| `prepare-release.sh` | Release preparation |

---

## Configuration

### pyproject.toml Dependencies

| Group | Packages |
|-------|----------|
| **core** | click, rich, pyyaml, httpx |
| **knowledge** | txtai, sentence-transformers |
| **agent-sdk** | anthropic |
| **smolagents** | smolagents[litellm], txtai, ddgs, markdownify, lizard |
| **telemetry** | arize-phoenix, opentelemetry-*, openinference-* |
| **toon** | python-toon |
| **dev** | pytest, pytest-cov, black, ruff |

### LiteLLM Configuration

Located at `~/.config/litellm/config.yaml`.

Supports:
- NanoGPT (12+ models, $15/mo flat)
- OpenRouter (pay-per-use)
- Ollama (local models)
- Any OpenAI-compatible API

---

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures
├── __init__.py
├── test_doctor_hooks.py     # Hook diagnostics
└── unit/
    ├── test_context.py      # Context gathering
    ├── test_discovery.py    # Model discovery
    ├── test_loader.py       # Agent loading
    ├── test_memory.py       # Memory system
    └── test_tools_citations.py  # Citation validation
```

Run with: `kln test` or `pytest tests/`

---

## Documentation Map

```
docs/
├── README.md                    # Quick reference
├── installation.md              # Setup guide
├── usage.md                     # Commands and workflows
├── reference.md                 # Complete config reference
├── architecture/
│   ├── OVERVIEW.md              # System architecture
│   ├── COMPONENTS.md            # Module breakdown
│   └── DEVELOPMENT.md           # Contributing guide
└── roadmap/
    ├── README.md                # Roadmap overview
    ├── future-features.md       # Planned features
    ├── mem0-style-memory.md     # Memory enhancement
    ├── swe-bench-integration.md # Benchmark integration
    └── toon/                    # Token compression
```

---

## Key Paths Summary

| Path | Purpose |
|------|---------|
| `~/.claude/` | Claude Code config (hooks, commands, scripts) |
| `~/.claude/scripts/` | Installed scripts |
| `~/.klean/` | K-LEAN runtime |
| `~/.klean/agents/` | SmolKLN agent definitions |
| `~/.klean/logs/` | Service logs |
| `~/.klean/pids/` | Service PIDs |
| `~/.venvs/knowledge-db/` | Knowledge DB Python env |
| `~/.config/litellm/` | LiteLLM configuration |
| `.knowledge-db/` | Per-project knowledge base |
| `.claude/kln/agentExecute/` | Agent output directory |

---

## Cross-References

### Knowledge DB Flow
```
/kln:learn → knowledge-capture.py → .knowledge-db/entries.jsonl
FindKnowledge → user-prompt-handler.sh → knowledge-query.sh → knowledge-server.py
```

### Review Flow
```
/kln:quick → quick.md → quick-review.sh → LiteLLM → NanoGPT/OpenRouter
/kln:multi → multi.md → consensus-review.sh → 3-5 models → consensus scoring
/kln:agent → agent.md → smol/executor.py → smolagents → tools
```

### Hook Flow
```
Session Start → session-start.sh → start LiteLLM, KB server
User Prompt → user-prompt-handler.sh → keyword matching → dispatch
Post Bash → post-bash-handler.sh → git commit → timeline logging
Post Web → post-web-handler.sh → auto-capture → knowledge-capture.py
```

---

*Generated: 2026-01-01 | K-LEAN v1.0.0-beta*
