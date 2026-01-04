# Project Index: K-LEAN

**Generated**: 2026-01-03
**Version**: 1.0.0b2
**License**: Apache-2.0

---

## Project Summary

Multi-model code review and persistent knowledge system for Claude Code. Get consensus from 3-5 LLMs, capture insights to a searchable knowledge base, and use 8 specialist agents for domain-specific analysis.

---

## Project Structure

```
k-lean/
├── src/klean/              # Main package (~5.4K lines Python)
│   ├── cli.py              # CLI entry point (kln command)
│   ├── model_utils.py      # Model extraction and parsing utilities
│   ├── config_generator.py # LiteLLM config generation and merging
│   ├── discovery.py        # Model discovery from LiteLLM
│   ├── smol/               # SmolKLN agent system (16 modules)
│   │   ├── cli.py          # kln-smol command
│   │   ├── executor.py     # Single agent execution
│   │   ├── multi_agent.py  # Multi-agent orchestration
│   │   ├── tools.py        # Agent tools (read, grep, git)
│   │   ├── models.py       # LiteLLM model wrapper
│   │   └── loader.py       # Agent .md file parser
│   ├── tools/              # Agent tools (grep, read, search)
│   └── data/               # Installable assets
│       ├── scripts/        # 35 shell & Python scripts
│       ├── commands/kln/   # 9 slash commands
│       ├── hooks/          # 4 Claude Code hooks
│       ├── agents/         # 8 SmolKLN agent definitions
│       └── config/         # LiteLLM & provider templates
├── tests/                  # 11 test files
├── docs/                   # User & architecture docs
├── config/litellm/         # LiteLLM proxy configuration
└── pyproject.toml          # Package configuration
```

---

## Entry Points

| Command | Source | Description |
|---------|--------|-------------|
| `kln` | `src/klean/cli.py:main` | Main CLI (install, status, doctor, multi, etc.) |
| `kln-smol` | `src/klean/smol/cli.py:main` | SmolAgents executor |

---

## Core Modules

### `src/klean/cli.py`
Primary CLI with Click commands (reorganized in this session):
- **Root commands** (8): `init`, `install`, `uninstall`, `status`, `doctor`, `start`, `stop`, `multi`
- **Model subgroup** (`kln model`): `list`, `add`, `remove`, `test`
- **Provider subgroup** (`kln provider`): `list`, `add`, `set-key`, `remove`
- **Admin subgroup** (`kln admin`, hidden): `sync`, `debug`, `test`

Key helper functions:
- `get_litellm_binary()` - Find litellm in pipx venv or system PATH
- `configure_statusline()` - Configure Claude Code statusline

Key improvements:
- 65% fewer visible commands (17 flat -> 7 root + 3 groups)
- Noun-verb pattern (`kln model add` vs `kln add-model`)
- Admin tools hidden from main help
- Cognitive load reduced ~60%
- pipx-compatible binary detection (v1.0.0b2)

### `src/klean/model_utils.py`
Model extraction and parsing utilities:
- `extract_model_name()` - Extract short name from model ID
- `parse_model_id()` - Parse provider and model from ID
- `is_thinking_model()` - Detect thinking/extended-thinking models

### `src/klean/config_generator.py`
LiteLLM configuration generation with non-destructive merging:
- `generate_litellm_config()` - Generate config.yaml content
- `load_config_yaml()` - Load existing config
- `merge_models_into_config()` - Add models without duplicates
- `add_model_to_config()` - Add single model to config
- `remove_model_from_config()` - Remove model from config
- `list_models_in_config()` - List all configured models

### `src/klean/model_defaults.py`
Default model configurations for each provider:
- `get_nanogpt_models()` - Returns 10 recommended NanoGPT models
- `get_openrouter_models()` - Returns 6 recommended OpenRouter models
- `NANOGPT_MODELS` - Static list of NanoGPT model definitions
- `OPENROUTER_MODELS` - Static list of OpenRouter model definitions

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
| `async_executor.py` | Async agent execution |
| `multi_agent.py` | Multi-agent orchestration and consensus |
| `tools.py` | Agent tools: read_file, search_files, grep |
| `models.py` | LiteLLM model wrapper, thinking model support |
| `orchestrator.py` | Agent coordination and task delegation |
| `memory.py` | Agent memory and context management |
| `context.py` | Git context extraction (status, diff, log) |
| `prompts.py` | System prompts and templates |
| `loader.py` | Agent definition loading from markdown |
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
| `testing_tool.py` | Test execution tool |

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
**Backend**: fastembed-hybrid (ONNX-based, ~313MB models)
**Search**: RRF fusion (dense BGE + sparse BM42 + cross-encoder reranking)
**Server**: Unix socket, auto-starts on first use

| Script | Purpose |
|--------|---------|
| knowledge-server.py | Persistent server daemon |
| knowledge_db.py | Core hybrid search implementation (dense + sparse + reranking) |
| knowledge-search.py | Semantic search |
| knowledge-capture.py | Entry creation |
| knowledge-query.sh | CLI query interface |
| kb-init.sh | Initialize project KB |

---

## Key Scripts (35 total)

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
| `.serena/project.yml` | Serena MCP project config |

---

## Dependencies

**Core** (always installed):
- click>=8.0.0 - CLI framework
- rich>=13.0.0 - Terminal formatting
- pyyaml>=6.0.0 - YAML parsing
- httpx>=0.27.0 - HTTP client
- fastembed>=0.3.0 - Semantic embeddings (ONNX-based)
- numpy>=1.24.0 - Numerical operations
- smolagents[litellm]>=1.17.0 - Agent framework
- lizard>=1.17.0 - Code complexity analysis
- ddgs>=6.0.0 - Web search
- markdownify>=0.11.0 - HTML to markdown

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
| test_async_completion.py | Async model calls |
| test_llm_client.py | LLM client integration |
| test_cli_integration.py | CLI end-to-end |
| test_init_command.py | Init command (new in this session) |
| test_model_management.py | Model management commands (new in this session) |

---

## Quick Start

```bash
# Install
pipx install kln-ai

# Initialize with provider selection (includes install + setup)
kln init                  # NanoGPT, OpenRouter, or skip LiteLLM

# Start services
kln start

# Check status
kln status
kln doctor -f            # Auto-fix issues

# Manage models (new subgroup structure)
kln model list           # List available models
kln model list --health  # Check model health
kln model add --provider openrouter "anthropic/claude-3.5-sonnet"
kln model remove "claude-3-sonnet"
kln model test "gpt-4"   # Test a specific model

# Manage providers
kln provider list        # Show configured providers
kln provider add openrouter --api-key $KEY  # Add provider with models
kln provider set-key nanogpt --key $NEWKEY  # Update API key
kln provider remove openrouter              # Remove provider

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
| Python | ~51 |
| Shell | 35 |
| Markdown (agents, commands, docs) | 50+ |
| YAML/TOML | 12 |
| Tests | 11 |

---

## Documentation

| Document | Path |
|----------|------|
| Installation | `docs/installation.md` |
| Usage | `docs/usage.md` |
| Reference | `docs/reference.md` |
| Architecture | `docs/architecture/OVERVIEW.md` |

---

*Index size: ~4KB | Full codebase: ~60K tokens | Savings: 94%*
