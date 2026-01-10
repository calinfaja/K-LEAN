# Project Index: K-LEAN

**Generated**: 2026-01-09
**Version**: 1.0.0b6
**License**: Apache-2.0

---

## Project Summary

Multi-model code review and persistent knowledge system for Claude Code. Get consensus from 3-5 LLMs, capture insights to a searchable knowledge base, and use 8 specialist agents for domain-specific analysis.

**Cross-platform**: Works natively on Windows, Linux, and macOS with no shell scripts required for core functionality.

---

## Project Structure

```
k-lean/
├── src/klean/              # Main package
│   ├── cli.py              # CLI entry point (kln command)
│   ├── hooks.py            # Python hook entry points (4 hooks)
│   ├── reviews.py          # Async review engine (httpx)
│   ├── platform.py         # Cross-platform utilities (psutil, platformdirs)
│   ├── discovery.py        # Model discovery from LiteLLM
│   ├── config_generator.py # LiteLLM config generation
│   ├── model_utils.py      # Model extraction and parsing
│   ├── model_defaults.py   # Default model configurations
│   ├── smol/               # SmolKLN agent system (16 modules)
│   ├── tools/              # Agent tools (grep, read, search)
│   └── data/               # Installable assets
│       ├── scripts/        # Python scripts for Knowledge DB
│       ├── commands/kln/   # 9 slash commands
│       ├── agents/         # 8 SmolKLN agent definitions
│       └── config/         # LiteLLM & provider templates
├── tests/                  # Unit tests
│   └── unit/               # Platform, hooks, reviews, KB tests
├── docs/                   # Documentation
│   └── architecture/       # OVERVIEW, COMPONENTS, DEVELOPMENT
└── pyproject.toml          # Package configuration
```

---

## Entry Points

| Command | Source | Description |
|---------|--------|-------------|
| `kln` | `cli.py:main` | Main CLI (init, install, status, doctor, multi, etc.) |
| `kln-smol` | `smol/cli.py:main` | SmolAgents executor |
| `kln-hook-session` | `hooks.py:session_start` | SessionStart hook |
| `kln-hook-prompt` | `hooks.py:prompt_handler` | UserPromptSubmit hook |
| `kln-hook-bash` | `hooks.py:post_bash` | PostToolUse (Bash) hook |
| `kln-hook-web` | `hooks.py:post_web` | PostToolUse (Web*) hook |

---

## Core Modules

### `src/klean/cli.py`
Primary CLI with Click commands:
- **Root commands**: `init`, `install`, `uninstall`, `status`, `doctor`, `start`, `stop`, `multi`
- **Model subgroup** (`kln model`): `list`, `add`, `remove`, `test`
- **Provider subgroup** (`kln provider`): `list`, `add`, `set-key`, `remove`
- **Admin subgroup** (`kln admin`, hidden): `sync`, `debug`, `test`

Key functions:
- `get_litellm_binary()` - Find litellm in pipx venv or system PATH
- `merge_klean_hooks()` - Register Python entry point hooks
- `start_litellm()`, `stop_litellm()` - Service management
- `start_knowledge_server()`, `stop_knowledge_server()` - KB server control

### `src/klean/hooks.py`
Cross-platform hook entry points (read JSON stdin, output JSON stdout):
- `session_start()` - Auto-start LiteLLM + KB server
- `prompt_handler()` - FindKnowledge, SaveInfo, InitKB, asyncReview keywords
- `post_bash()` - Git commit/push timeline logging
- `post_web()` - Auto-capture web content to KB

### `src/klean/reviews.py`
Async code review engine:
- `quick_review()` - Single model async review
- `consensus_review()` - Multi-model parallel consensus (5 models)
- `second_opinion()` - Alternative perspective
- `_extract_content()` - Handles thinking model responses (content OR reasoning_content)

### `src/klean/platform.py`
Cross-platform utilities:
- `get_config_dir()`, `get_cache_dir()`, `get_runtime_dir()` - platformdirs paths
- `spawn_background()` - Background process launch
- `kill_process_tree()` - Graceful termination via psutil
- `is_process_running()`, `find_process()` - Process management
- `cleanup_stale_files()` - Remove orphaned port/pid files

### `src/klean/config_generator.py`
LiteLLM configuration with non-destructive merging:
- `generate_litellm_config()` - Generate config.yaml
- `merge_models_into_config()` - Add models without duplicates
- `add_model_to_config()`, `remove_model_from_config()` - Model management

### `src/klean/discovery.py`
Dynamic model discovery from LiteLLM proxy:
- `list_models()` - Get all available models (TTL cached)
- `get_model()` - Get first available model
- `is_available()` - Check LiteLLM status

---

## SmolKLN Agent System (`src/klean/smol/`)

| Module | Purpose |
|--------|---------|
| `executor.py` | `SmolKLNExecutor` - Single agent execution with tool use |
| `orchestrator.py` | `SmolKLNOrchestrator` - Multi-agent coordination |
| `memory.py` | `AgentMemory`, `SessionMemory` - Context management |
| `tools.py` | Agent tools: read_file, search_files, grep, knowledge_search |
| `models.py` | LiteLLM model wrapper, thinking model support |
| `loader.py` | Agent definition loading from markdown (YAML + system prompt) |
| `context.py` | Git context extraction (status, diff, log) |
| `reflection.py` | Agent self-reflection and retry |
| `async_executor.py` | Background async execution |
| `task_queue.py` | Persistent task queue |
| `mcp_tools.py` | MCP tool integration |

---

## Slash Commands (/kln:*)

| Command | Purpose |
|---------|---------|
| `/kln:quick` | Fast single-model review (~30s) |
| `/kln:multi` | Multi-model consensus (~60s) |
| `/kln:agent` | SmolKLN specialist agents (~2min) |
| `/kln:rethink` | Contrarian debugging (4 techniques) |
| `/kln:learn` | Context-aware learning extraction |
| `/kln:remember` | End-of-session capture |
| `/kln:doc` | Documentation generation |
| `/kln:status` | System status |
| `/kln:help` | Command reference |

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

**Storage**: `.knowledge-db/` per project
**Backend**: fastembed-hybrid (ONNX-based)
**Search**: RRF fusion (dense BGE + sparse BM42 + cross-encoder reranking)
**Server**: TCP localhost (cross-platform), port 14000 + hash offset

| Script | Purpose |
|--------|---------|
| `knowledge-server.py` | TCP server with "add" command for immediate indexing |
| `knowledge_db.py` | Core hybrid search |
| `knowledge-capture.py` | Entry creation (TCP-first with fallback) |
| `kb_utils.py` | Cross-platform utilities |

**Server-Owned Writes**: Entries added via TCP are immediately searchable (no rebuild needed).

---

## Hooks (Python Entry Points)

| Entry Point | Trigger | Purpose |
|-------------|---------|---------|
| `kln-hook-session` | SessionStart | Auto-start LiteLLM + KB server |
| `kln-hook-prompt` | UserPromptSubmit | Keyword detection (FindKnowledge, SaveInfo, etc.) |
| `kln-hook-bash` | PostToolUse (Bash) | Git timeline logging |
| `kln-hook-web` | PostToolUse (Web*) | Auto-capture web content |

**Protocol**: Read JSON from stdin, output JSON to stdout. Exit 0=success, 2=block.

---

## Tests

| Test File | Coverage |
|-----------|----------|
| `test_platform.py` | Cross-platform utilities |
| `test_hooks.py` | Hook entry points |
| `test_reviews.py` | Review engine |
| `test_knowledge_server.py` | KB server TCP protocol |
| `test_cli_integration.py` | CLI end-to-end |
| `test_discovery.py` | Model discovery |
| `test_loader.py` | Agent file parsing |

---

## Dependencies

**Core**:
- click, rich - CLI framework
- pyyaml, httpx - Config & HTTP
- psutil, platformdirs - Cross-platform utilities
- fastembed, numpy - Knowledge DB embeddings
- smolagents[litellm] - Agent framework
- lizard, ddgs, markdownify - Agent tools

**Optional**:
- `[telemetry]` - arize-phoenix, opentelemetry
- `[agent-sdk]` - anthropic (Claude Agent SDK)
- `[dev]` - pytest, black, ruff

---

## Quick Start

```bash
# Install
pipx install kln-ai

# Initialize (provider selection + install)
kln init

# Start services
kln start

# Check status
kln status
kln doctor -f

# Run reviews (in Claude Code)
/kln:quick security
/kln:multi "security review"
/kln:agent security-auditor "audit auth"
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
| Overview | `docs/architecture/OVERVIEW.md` |
| Components | `docs/architecture/COMPONENTS.md` |
| Development | `docs/architecture/DEVELOPMENT.md` |
| Migration | `docs/shell-to-python-migration.md` |

---

*Index size: ~5KB | Full codebase: ~60K tokens | Savings: 92%*
