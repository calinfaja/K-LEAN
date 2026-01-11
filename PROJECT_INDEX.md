# Project Index: K-LEAN

**Generated:** 2026-01-11
**Package:** `kln-ai` v1.0.0b6
**Python:** >=3.9 | **License:** Apache-2.0

---

## Project Summary

Multi-model code review and persistent knowledge system for Claude Code. Get consensus from 3-5 LLMs, capture insights to a searchable knowledge base, and use 8 specialist agents for domain-specific analysis.

**Cross-platform:** Windows, Linux, macOS - no shell scripts required.

---

## Project Structure

```
k-lean/
├── src/klean/              # Main package (40 .py files)
│   ├── cli.py              # Click CLI entry point
│   ├── discovery.py        # LiteLLM model discovery
│   ├── reviews.py          # Async review engine (httpx)
│   ├── hooks.py            # Python hook entry points (4 hooks)
│   ├── platform.py         # Cross-platform utilities (psutil, platformdirs)
│   ├── config_generator.py # LiteLLM config generation
│   ├── smol/               # SmolKLN agent system (16 modules)
│   │   ├── executor.py         # Single agent execution
│   │   ├── multi_agent.py      # Multi-agent orchestration
│   │   ├── multi_config.py     # Agent configurations (3-agent, thorough)
│   │   ├── tools.py            # Agent tools (read, grep, git, etc.)
│   │   ├── loader.py           # Agent definition loader
│   │   ├── models.py           # LiteLLM model wrapper
│   │   ├── memory.py           # AgentMemory, SessionMemory
│   │   ├── context.py          # Git context extraction
│   │   ├── reflection.py       # Agent self-reflection
│   │   ├── async_executor.py   # Background async execution
│   │   ├── task_queue.py       # Persistent task queue
│   │   └── orchestrator.py     # Multi-agent coordination
│   ├── tools/              # Standalone tool implementations
│   └── data/               # Installable assets → ~/.claude/
│       ├── scripts/            # Knowledge DB Python scripts
│       ├── commands/kln/       # 9 slash commands
│       ├── agents/             # 8 SmolKLN agent definitions
│       ├── multi-agents/       # Multi-agent prompts (6 .md files)
│       └── config/             # LiteLLM config templates
├── tests/                  # 31 test files
│   ├── unit/               # Unit tests (28 files)
│   └── core/               # Integration tests (3 files)
├── docs/                   # Documentation
│   ├── architecture/       # OVERVIEW, COMPONENTS, DEVELOPMENT
│   └── roadmap/            # Future features
└── pyproject.toml          # Package configuration
```

---

## Entry Points

| Command | Module | Purpose |
|---------|--------|---------|
| `kln` | `klean.cli:main` | Main CLI (init, install, status, doctor, multi) |
| `kln-smol` | `klean.smol.cli:main` | SmolAgents executor |
| `kln-hook-session` | `klean.hooks:session_start` | SessionStart hook |
| `kln-hook-prompt` | `klean.hooks:prompt_handler` | UserPromptSubmit hook |
| `kln-hook-bash` | `klean.hooks:post_bash` | PostToolUse (Bash) hook |
| `kln-hook-web` | `klean.hooks:post_web` | PostToolUse (Web*) hook |

---

## Core Modules

### `src/klean/cli.py`
Primary CLI with Click commands:
- **Root:** `init`, `install`, `uninstall`, `status`, `doctor`, `start`, `stop`, `multi`
- **Model subgroup:** `list`, `add`, `remove`, `test`
- **Provider subgroup:** `list`, `add`, `set-key`, `remove`
- **Admin subgroup (hidden):** `sync`, `debug`, `test`

### `src/klean/discovery.py`
Dynamic model discovery from LiteLLM proxy:
- `list_models()` - All available models (TTL cached 60s)
- `get_model()` - First available model
- `is_available()` - Check LiteLLM status

### `src/klean/reviews.py`
Async code review engine:
- `quick_review()` - Single model async review
- `consensus_review()` - Multi-model parallel consensus
- `second_opinion()` - Alternative perspective
- Auto-handles thinking model responses (`content` OR `reasoning_content`)

### `src/klean/hooks.py`
Cross-platform hook entry points (JSON stdin → JSON stdout):
- `session_start()` - Auto-start LiteLLM + KB server
- `prompt_handler()` - FindKnowledge, SaveInfo, asyncReview keywords
- `post_bash()` - Git commit/push timeline logging
- `post_web()` - Auto-capture web content to KB

### `src/klean/platform.py`
Cross-platform utilities:
- `get_config_dir()`, `get_cache_dir()`, `get_runtime_dir()`
- `spawn_background()`, `kill_process_tree()`, `is_process_running()`
- `get_venv_python()`, `get_venv_pip()` - Venv path helpers

---

## SmolKLN Agent System

### Key Modules (`src/klean/smol/`)

| Module | Purpose |
|--------|---------|
| `executor.py` | `SmolKLNExecutor` - Single agent execution with tool use |
| `multi_agent.py` | `MultiAgentExecutor` - Multi-agent orchestration |
| `multi_config.py` | `get_3_agent_config()`, `get_thorough_agent_config()` |
| `tools.py` | Agent tools: read_file, search_files, grep, knowledge_search |
| `models.py` | LiteLLM model wrapper, thinking model support |
| `loader.py` | Agent definition loading (YAML frontmatter + markdown) |
| `memory.py` | `AgentMemory`, `SessionMemory` - Context management |
| `context.py` | Git context extraction (status, diff, log) |
| `reflection.py` | Agent self-reflection and retry |
| `async_executor.py` | Background async execution |
| `task_queue.py` | Persistent task queue (JSON-based) |

### Agent Configurations

| Config | Agents | Use Case |
|--------|--------|----------|
| `get_3_agent_config()` | manager, file_scout, analyzer | Default, faster |
| `get_thorough_agent_config()` | manager, file_scout, code_analyzer, security_auditor, synthesizer | Thorough analysis |

---

## Slash Commands (/kln:*)

| Command | Purpose | Time |
|---------|---------|------|
| `/kln:quick` | Fast single-model review | ~30s |
| `/kln:multi` | 3-5 model consensus | ~60s |
| `/kln:agent` | SmolKLN specialist agents | ~2min |
| `/kln:rethink` | Contrarian debugging (4 techniques) | ~20s |
| `/kln:learn` | Extract learnings mid-session | ~30s |
| `/kln:remember` | End-of-session capture | ~20s |
| `/kln:doc` | Generate documentation | ~30s |
| `/kln:status` | System health check | ~2s |
| `/kln:help` | Command reference | instant |

---

## SmolKLN Agents

| Agent | Specialty |
|-------|-----------|
| `code-reviewer` | OWASP, SOLID, code quality |
| `security-auditor` | Vulnerabilities, auth, crypto |
| `debugger` | Root cause analysis |
| `performance-engineer` | Profiling, optimization |
| `rust-expert` | Ownership, lifetimes, unsafe |
| `c-pro` | C99/C11, POSIX, embedded |
| `arm-cortex-expert` | ARM MCU, real-time |
| `orchestrator` | Multi-agent coordination |

---

## Knowledge Database

**Storage:** `.knowledge-db/` per project
**Backend:** fastembed-hybrid (ONNX-based, ~200MB)
**Search:** RRF fusion (dense BGE + sparse BM42 + cross-encoder reranking)
**Server:** TCP localhost, port 14000 + hash offset

| Script | Purpose |
|--------|---------|
| `knowledge-server.py` | TCP server with immediate indexing |
| `knowledge_db.py` | Core hybrid search |
| `knowledge-capture.py` | Entry creation (TCP-first with fallback) |
| `kb_utils.py` | Cross-platform utilities |

---

## Tests

**31 test files** across unit/ and core/:

| Category | Files | Coverage |
|----------|-------|----------|
| Unit tests | 28 | CLI, hooks, reviews, KB, agents |
| Integration | 3 | End-to-end CLI, async |

Key test files:
- `test_platform.py` - Cross-platform utilities
- `test_hooks.py` - Hook entry points
- `test_reviews.py` - Review engine
- `test_smol_executor.py` - Agent execution
- `test_smol_multi_agent.py` - Multi-agent orchestration
- `test_multi_config.py` - Agent configurations
- `test_task_queue.py` - Task queue persistence

---

## Dependencies

**Core:**
- click, rich - CLI framework
- httpx - Async HTTP client
- pyyaml - Config parsing
- psutil, platformdirs - Cross-platform utilities
- fastembed, numpy - Knowledge DB embeddings
- smolagents[litellm] - Agent framework
- litellm[proxy] - LLM proxy server

**Optional:**
- `[telemetry]` - arize-phoenix, opentelemetry
- `[agent-sdk]` - anthropic (Claude Agent SDK)
- `[dev]` - pytest, black, ruff

---

## Quick Start

```bash
# Install
pipx install kln-ai

# Setup
kln init             # Configure provider + install
kln start            # Start LiteLLM proxy
kln doctor -f        # Verify and auto-fix

# Use in Claude Code
/kln:quick security
/kln:multi "error handling"
/kln:agent security-auditor "audit auth"
```

---

## Development

```bash
# Editable install
pipx install -e .

# Run tests
pytest tests/ -v

# Lint + format
ruff check src/ --fix
black src/

# Sync data files
kln admin sync
```

---

## Key Patterns

1. **Cross-platform first**: Python entry points, TCP IPC, platformdirs
2. **Dynamic model discovery**: All models from LiteLLM, no hardcoding
3. **Server-owned writes**: KB entries immediately searchable via TCP
4. **Thinking model handling**: Both `content` and `reasoning_content` supported
5. **Agent definitions**: YAML frontmatter + markdown system prompt
6. **Per-project isolation**: `.knowledge-db/` and `.claude/kln/` per repo

---

## Documentation

| Document | Path |
|----------|------|
| Claude Code guide | `CLAUDE.md` |
| Architecture overview | `docs/architecture/OVERVIEW.md` |
| Components detail | `docs/architecture/COMPONENTS.md` |
| Development guide | `docs/architecture/DEVELOPMENT.md` |
| Installation | `docs/installation.md` |
| Usage | `docs/usage.md` |

---

*Index updated: 2026-01-11 | ~4KB | Full codebase: ~60K tokens | Savings: 93%*
