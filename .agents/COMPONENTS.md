# K-LEAN Components Reference

> Consolidated documentation for all K-LEAN components: CLI, Hooks, Knowledge DB, LiteLLM, Review System, and SmolKLN Agents.

---

## Table of Contents

1. [CLI Commands](#1-cli-commands)
2. [Hooks System](#2-hooks-system)
3. [Knowledge Database](#3-knowledge-database)
4. [LiteLLM Integration](#4-litellm-integration)
5. [Review System](#5-review-system)
6. [SmolKLN Agents](#6-smolkln-agents)
7. [Quick Reference](#7-quick-reference)

---

## 1. CLI Commands

The K-LEAN CLI provides 14 commands for managing the system.

### Command Overview

| Command | Purpose | Speed |
|---------|---------|-------|
| `k-lean doctor` | Validate config (.env, subscription, services) | ~3s |
| `k-lean doctor -f` | Auto-fix issues | ~5s |
| `k-lean status` | Show installed components and services | ~2s |
| `k-lean models` | List available models | ~1s |
| `k-lean models --health` | Check model health | ~60s |
| `k-lean models --test` | Test each model with latency | Slow |
| `k-lean start` | Start LiteLLM proxy | ~3s |
| `k-lean stop` | Stop services | ~1s |
| `k-lean install` | Install components | Varies |
| `k-lean setup` | Configure API provider (interactive) | ~30s |
| `k-lean uninstall` | Remove components | ~5s |
| `k-lean sync` | Sync package data (dev) | ~2s |
| `k-lean test` | Run test suite | ~10s |
| `k-lean test-model` | Test specific model | ~5s |
| `k-lean version` | Show version info | Instant |
| `k-lean debug` | Live monitoring dashboard | Continuous |

### User Mental Model

```
"Is my SYSTEM configured?" --> k-lean doctor
"What's RUNNING now?"      --> k-lean status
"Are my MODELS working?"   --> k-lean models --health
```

---

### 1.1 doctor

Validates configuration and services.

```bash
k-lean doctor             # Check everything
k-lean doctor --auto-fix  # Fix issues automatically
k-lean doctor -f          # Short form
```

**Checks performed:**
- `.env` file exists with `NANOGPT_API_KEY`
- `NANOGPT_API_BASE` configured (auto-detects subscription vs pay-per-use)
- NanoGPT subscription status + remaining quota
- LiteLLM proxy running
- Knowledge server running
- Hardcoded API keys (security check)

---

### 1.2 status

Shows installed components and running services.

```bash
k-lean status
```

**Output includes:**
- Scripts count (symlinked status)
- KLN commands (9)
- SuperClaude availability (optional)
- Hooks (5)
- SmolKLN Agents (8)
- Knowledge DB (per-project status + entry count)
- LiteLLM Proxy (model count + provider)
- K-LEAN CLI version

---

### 1.3 models

Lists and tests available LLM models.

```bash
k-lean models           # List all models
k-lean models --health  # Check health (calls each model)
k-lean models --test    # Full latency test
```

**Dynamic Discovery:** Models are discovered from LiteLLM at runtime, not hardcoded.

---

### 1.4 start / stop

Controls K-LEAN services.

```bash
k-lean start                    # Start LiteLLM (default)
k-lean start -s knowledge       # Start Knowledge server
k-lean start -s all             # Start both services
k-lean start -p 4001            # Custom port
k-lean stop                     # Stop for current project
k-lean stop --all-projects      # Stop all KB servers
k-lean stop -s litellm          # Stop specific service
```

---

### 1.5 install / uninstall

Manages K-LEAN components.

```bash
k-lean install                      # Full installation
k-lean install --component scripts  # Specific component
k-lean install --dev                # Dev mode (symlinks)

k-lean uninstall                    # Remove all
k-lean uninstall --yes              # Skip confirmation
```

**Components:** all, scripts, commands, hooks, smolkln, config, core, knowledge

---

### 1.6 setup

Configures LiteLLM API provider (interactive wizard).

```bash
k-lean setup                # Interactive menu
k-lean setup -p nanogpt     # Direct NanoGPT setup
k-lean setup -p openrouter  # Direct OpenRouter setup
```

**Features:**
- Provider selection (NanoGPT/OpenRouter)
- Secure API key input (hidden)
- Auto-detects NanoGPT subscription endpoint
- Backs up existing config before overwriting
- Creates `~/.config/litellm/.env` (chmod 600)
- Copies appropriate config.yaml template

---

### 1.7 sync

Syncs data files (development tool).

```bash
k-lean sync           # Sync all data
k-lean sync --check   # Verify sync status (CI mode)
k-lean sync --clean   # Remove stale files
```

---

### 1.8 test

Runs comprehensive test suite.

```bash
k-lean test
```

**Tests across 8 categories:**
1. Installation Structure
2. Scripts Executable
3. KLN Commands
4. Hooks
5. LiteLLM Service
6. Knowledge System
7. Nano Profile
8. SmolKLN Agents

**Exit code:** 0 = all pass, 1 = failures (CI-friendly)

---

### 1.9 debug

Live monitoring dashboard.

```bash
k-lean debug              # Full dashboard
k-lean debug --compact    # Minimal output (for hooks)
```

---

### 1.10 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error / test failures |
| 2 | Configuration error |

---

### 1.11 Environment Variables

| Variable | Purpose |
|----------|---------|
| `KLEAN_KB_PYTHON` | Override Python path |
| `KLEAN_SCRIPTS_DIR` | Override scripts location |
| `KLEAN_SOCKET_DIR` | Override socket directory |
| `KLEAN_CONFIG_DIR` | Override config directory |

---

### 1.12 Implementation

Main CLI: `src/klean/cli.py` (~2766 lines)

Uses:
- `click` for CLI framework
- `rich` for terminal output
- `httpx` for async HTTP

---

## 2. Hooks System

K-LEAN integrates with Claude Code via **5 hooks** that trigger on specific events.

### Hook Overview

| Hook | Trigger | Purpose |
|------|---------|---------|
| `session-start.sh` | SessionStart | Auto-start LiteLLM + per-project KB |
| `user-prompt-handler.sh` | UserPromptSubmit | Keyword detection (7 keywords) |
| `post-bash-handler.sh` | PostToolUse (Bash) | Git events -> timeline + fact extraction |
| `post-web-handler.sh` | PostToolUse (Web*) | Auto-capture web content to KB |
| `async-review.sh` | UserPromptSubmit | Background async reviews |

---

### 2.1 session-start.sh

**Trigger:** Claude Code session starts

**Actions:**
1. Start LiteLLM proxy (if not running)
2. Start per-project KB server
3. Show configuration warnings

---

### 2.2 user-prompt-handler.sh

**Trigger:** User submits a prompt

**Keywords detected:**

| Keyword | Action |
|---------|--------|
| `SaveThis: <text>` | Capture insight to KB |
| `SaveInfo: <text>` | Smart save with LLM evaluation |
| `FindKnowledge: <query>` | Search KB |
| `InitKB` | Initialize project KB |
| `asyncReview` | Background quick review |
| `asyncDeepReview` | Background deep review |
| `asyncConsensus` | Background consensus review |

---

### 2.3 post-bash-handler.sh

**Trigger:** After any Bash command

**Detects:**
- `git commit` -> Log to timeline + extract facts
- `git push` -> Log to timeline
- Other git operations

---

### 2.4 post-web-handler.sh

**Trigger:** After WebFetch/WebSearch/Tavily tools

**Action:** Smart capture of web content to KB

---

### 2.5 Hook File Location

```
src/klean/data/hooks/
|-- session-start.sh
|-- user-prompt-handler.sh
|-- post-bash-handler.sh
|-- post-web-handler.sh
`-- async-review.sh
```

---

### 2.6 Hook Structure

```bash
#!/usr/bin/env bash

# Source path utilities (with fallback)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../scripts/kb-root.sh" 2>/dev/null || {
    # Inline fallbacks if kb-root.sh not found
    KB_PYTHON="${KLEAN_KB_PYTHON:-$HOME/.venvs/knowledge-db/bin/python}"
}

# Hook logic here...

# Exit codes:
# 0 = success, continue
# 1 = error (logged)
# 2 = block operation (with stderr message to Claude)
```

---

### 2.7 Hook Registration

Hooks are registered in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": ["~/.claude/hooks/session-start.sh"]
      }
    ],
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": ["~/.claude/hooks/user-prompt-handler.sh"]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": ["~/.claude/hooks/post-bash-handler.sh"]
      },
      {
        "matcher": "^(WebFetch|WebSearch|mcp__tavily)",
        "hooks": ["~/.claude/hooks/post-web-handler.sh"]
      }
    ]
  }
}
```

---

### 2.8 Exit Code Behavior

| Code | Behavior |
|------|----------|
| 0 | Success, continue |
| 1 | Error (logged, operation continues) |
| 2 | **Block operation** (stderr shown to Claude) |

**Blocking Example:**

```bash
# Block dangerous commands
if [[ "$command" =~ "rm -rf /" ]]; then
    echo "Blocked: Dangerous command" >&2
    exit 2
fi
```

---

### 2.9 Important Rules

1. **No blocking operations** - Hooks run synchronously
2. **Handle errors gracefully** - Hooks run silently
3. **Use inline fallbacks** - In case kb-root.sh missing
4. **Check exit codes** - For proper error reporting

---

### 2.10 Debugging Hooks

```bash
# Live monitoring
k-lean debug

# Compact mode (shows hook output)
k-lean debug --compact

# Manual test
~/.claude/hooks/session-start.sh
echo $?  # Check exit code
```

---

## 3. Knowledge Database

The Knowledge DB provides **persistent semantic memory** across Claude Code sessions using txtai embeddings.

### Key Features

- **Per-project isolation**: Each git repo gets its own KB
- **Semantic search**: Find related knowledge by meaning, not just keywords
- **Fast queries**: Unix socket server with 1hr idle timeout (~30ms latency)
- **V2 schema**: Rich metadata for quality and provenance

---

### 3.1 Architecture

```
+-----------------------------------------------------+
|                   Claude Code                        |
|  "SaveThis: important insight"                       |
+---------------------+-------------------------------+
                      | user-prompt-handler.sh
                      v
+-----------------------------------------------------+
|               knowledge-capture.py                   |
|  Parse -> V2 Schema -> Append to entries.jsonl      |
+---------------------+-------------------------------+
                      |
                      v
+-----------------------------------------------------+
|                 .knowledge-db/                       |
|  |-- entries.jsonl     # All captured knowledge     |
|  `-- index/            # Semantic embeddings        |
+-----------------------------------------------------+
                      ^
                      | Unix socket query
+---------------------+-------------------------------+
|              knowledge-server.py                     |
|  Socket: /tmp/kb-{md5_hash}.sock                    |
|  Idle timeout: 1 hour                               |
+-----------------------------------------------------+
```

---

### 3.2 V2 Schema

Each knowledge entry contains:

```json
{
  "id": "uuid",
  "found_date": "ISO8601",
  "title": "Brief title",
  "summary": "Detailed description",
  "type": "lesson|finding|solution|pattern",
  "atomic_insight": "Single clear insight",
  "key_concepts": ["concept1", "concept2"],
  "tags": ["tag1", "tag2"],
  "quality": "high|medium|low",
  "source": "manual|conversation|web|file",
  "source_path": "path/to/source",
  "relevance_score": 0.85,
  "confidence_score": 0.9
}
```

| Field | Purpose |
|-------|---------|
| `type` | Entry category (lesson/finding/solution/pattern) |
| `atomic_insight` | Single, self-contained insight |
| `key_concepts` | Searchable concept tags |
| `quality` | Quality level (high/medium/low) |
| `source` | Origin type (manual/conversation/web/file) |
| `relevance_score` | Semantic relevance (0-1) |

---

### 3.3 Key Scripts

| Script | Purpose |
|--------|---------|
| `knowledge-server.py` | Socket server (per-project daemon) |
| `knowledge-query.sh` | Query via socket (auto-starts server) |
| `knowledge-capture.py` | Add entries with V2 schema |
| `knowledge-search.py` | CLI search with 4 output formats |
| `kb-doctor.sh` | Diagnose and repair KB |
| `kb-init.sh` | Initialize new project KB |
| `kb-root.sh` | Path detection utilities |

---

### 3.4 Query Formats

```bash
# Compact (default) - ~30ms via server
~/.claude/scripts/knowledge-query.sh "search term"

# Detailed
~/.claude/scripts/knowledge-search.py --format detailed "search"

# For LLM injection
~/.claude/scripts/knowledge-search.py --format inject "search"

# JSON output
~/.claude/scripts/knowledge-search.py --format json "search"

# Direct query (slower, ~17s cold start)
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-search.py "<query>"
```

---

### 3.5 Trigger Keywords

In Claude Code prompts:

| Keyword | Action |
|---------|--------|
| `SaveThis: <text>` | Capture insight to KB |
| `SaveInfo: <text>` | Smart save with LLM evaluation |
| `FindKnowledge: <query>` | Search KB |

**Note:** Use `kb-init.sh` or `k-lean install` to initialize KB for a project.

---

### 3.6 Unified Memory System

Knowledge DB integrates with multiple sources:

```
+---------------------------------------------------------------+
|                     KNOWLEDGE DB SOURCES                       |
+---------------------------------------------------------------+
|  source: "manual"        <-- SaveThis keyword                  |
|  source: "web"           <-- GoodJob auto-capture              |
|  source: "agent_*"       <-- SmolKLN session memory (auto)     |
|  source: "serena"        <-- Synced from Serena (/kln:remember)|
+---------------------------------------------------------------+
```

---

### 3.7 SmolKLN Agent Integration

Agents automatically persist learnings to KB after execution:

```python
# In executor.py - happens automatically
result = executor.execute("security-auditor", "audit auth")
# Session memory saved to KB with source="agent_security-auditor"
# result["memory_persisted"] shows count of entries saved
```

Future agents can search these learnings:
```python
# Agent's knowledge_search tool finds prior agent insights
results = knowledge_search("SQL injection auth")
# Returns: entries from security-auditor's prior runs
```

---

### 3.8 Serena Sync

Curated Serena lessons can be synced to KB for agent access:

```bash
# Manual sync
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/sync-serena-kb.py

# Dry run (see what would sync)
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/sync-serena-kb.py --dry-run
```

Or via `/kln:remember` command at session end.

**Result**: SmolKLN agents can search all your Serena lessons via `knowledge_search`.

---

### 3.9 Socket Architecture

Each project gets a unique socket:
```
/tmp/kb-{md5_hash}.sock
```

Benefits:
- Fast queries (no process startup)
- Project isolation
- Auto-cleanup after 1hr idle

---

### 3.10 Troubleshooting

**KB Not Starting:**
```bash
k-lean doctor --auto-fix    # Auto-repair
~/.claude/scripts/kb-doctor.sh --fix  # Manual repair
```

**Corrupted Entries:**
```bash
~/.claude/scripts/kb-doctor.sh  # Diagnose
# Shows: X corrupted entries, Y valid
~/.claude/scripts/kb-doctor.sh --fix  # Rebuild index
```

**Check Status:**
```bash
k-lean status  # Shows KB status per project
```

---

### 3.11 Implementation Files

- Server: `src/klean/data/scripts/knowledge-server.py`
- Capture: `src/klean/data/scripts/knowledge-capture.py`
- Query: `src/klean/data/scripts/knowledge-query.sh`
- Search: `src/klean/data/scripts/knowledge-search.py`
- Doctor: `src/klean/data/scripts/kb-doctor.sh`
- Utils: `src/klean/data/scripts/kb_utils.py`

---

## 4. LiteLLM Integration

K-LEAN uses **LiteLLM proxy** to route requests to multiple LLM providers.

### Architecture

```
+-------------+    +------------------+    +-----------------+
|   Claude    |    |     LiteLLM      |    |    NanoGPT      |
|   Code      |<-->|  localhost:4000  |<-->|   12 models     |
|  (scripts)  |    |                  |    +-----------------+
+-------------+    |  /chat/completions|    |   OpenRouter    |
                   |  /v1/models       |    |   6 models      |
                   +------------------+    +-----------------+
```

---

### 4.1 Providers

| Provider | Models | Config File |
|----------|--------|-------------|
| NanoGPT | 12 | `~/.config/litellm/config.yaml` |
| OpenRouter | 6 | `~/.config/litellm/openrouter.yaml` |

---

### 4.2 NanoGPT Models (Sample)

Models are dynamically discovered from LiteLLM:

```yaml
# Sample models (via subscription)
- qwen3-coder           # Qwen 2.5 Coder
- deepseek-r1           # DeepSeek R1 (thinking)
- deepseek-v3-thinking  # DeepSeek V3 (thinking)
- glm-4.6-thinking      # GLM-4.6 (thinking)
- kimi-k2               # Kimi K2
- kimi-k2-thinking      # Kimi K2 (thinking)
- minimax-m2            # MiniMax M2 (thinking)
- llama-4-scout         # Llama 4 Scout
- llama-4-maverick      # Llama 4 Maverick
- hermes-4-70b          # Hermes 4 70B
- devstral-2            # Devstral 2
- qwen3-235b            # Qwen 3 235B
```

---

### 4.3 Thinking Models

These models return `reasoning_content` instead of `content`:
- DeepSeek R1, DeepSeek V3
- GLM-4.6
- Kimi K2
- MiniMax M2

---

### 4.4 Configuration

**File Locations:**
```
~/.config/litellm/
|-- config.yaml      # NanoGPT models
|-- openrouter.yaml  # OpenRouter models
`-- .env             # API keys (chmod 600)
```

**Environment Variables:**
```bash
# Required
NANOGPT_API_KEY=your-api-key

# Auto-detected (subscription vs pay-per-use)
NANOGPT_API_BASE=https://nano-gpt.com/api/subscription/v1
# or
NANOGPT_API_BASE=https://nano-gpt.com/api/v1
```

---

### 4.5 Config Syntax

```yaml
model_list:
  - model_name: coding-qwen
    litellm_params:
      model: openai/Qwen/Qwen2.5-Coder-32B-Instruct
      api_key: os.environ/NANOGPT_API_KEY  # NO quotes!
      api_base: os.environ/NANOGPT_API_BASE
```

**Critical:** `os.environ/KEY` must NOT be quoted. Common mistake:
```yaml
# Wrong - breaks env var substitution
api_key: "os.environ/NANOGPT_API_KEY"

# Correct
api_key: os.environ/NANOGPT_API_KEY
```

---

### 4.6 Setup

**Initial Setup:**
```bash
k-lean setup
```

**Wizard steps:**
1. Choose provider (NanoGPT/OpenRouter)
2. Enter API key (secure hidden input)
3. Auto-detect subscription status
4. Generate config files

**Starting LiteLLM:**
```bash
k-lean start              # Start proxy (foreground)
k-lean start -s all       # Start proxy + KB server
```

**Checking Status:**
```bash
k-lean doctor       # Validate config + subscription
k-lean models       # List available models
k-lean models --health  # Check model health
```

---

### 4.7 Scripts Reference

| Script | Purpose |
|--------|---------|
| `k-lean setup` | Interactive setup wizard (CLI) |
| `setup-litellm.sh` | Shell script setup (alternative) |
| `start-litellm.sh` | Start proxy with validation |
| `health-check.sh` | Full health check |
| `health-check-model.sh` | Single model health |
| `get-models.sh` | List models from /v1/models |
| `get-healthy-models.sh` | Filter healthy models |
| `validate-model.sh` | Verify model exists |

---

### 4.8 Dynamic Model Discovery

Scripts use dynamic discovery, not hardcoded lists:

```bash
# Get available models
models=$(curl -s http://localhost:4000/v1/models | jq -r '.data[].id')

# Filter healthy
healthy=$(~/.claude/scripts/get-healthy-models.sh)
```

---

### 4.9 Troubleshooting

**"Invalid session" Error:**
```bash
k-lean doctor --auto-fix
# Auto-detects subscription vs pay-per-use endpoint
```

**Proxy Not Starting:**
```bash
# Check if already running
lsof -i :4000

# Check logs
cat ~/.klean/logs/litellm.log
```

**Models Unhealthy:**
```bash
k-lean models --health
# Shows which models are down

# Common causes:
# - NanoGPT subscription expired
# - Model temporarily unavailable
# - Rate limiting
```

**Config Validation:**
`k-lean doctor` checks for:
- Missing .env file
- Quoted `os.environ/` (breaks substitution)
- Missing NANOGPT_API_BASE
- Invalid subscription

---

## 5. Review System

K-LEAN provides **multi-model code reviews** with consensus building across 3-5 LLMs.

### Review Types

| Type | Command | Models | Speed |
|------|---------|--------|-------|
| Quick | `/kln:quick` | 1 model | ~10s |
| Multi/Consensus | `/kln:multi` | 5 parallel | ~30s |
| Deep | `/kln:deep` | Claude SDK agent | ~3min |
| SmolKLN Agent | `/kln:agent` | Specialist persona | ~30s |
| Rethink | `/kln:rethink` | Contrarian analysis | ~20s |

---

### 5.1 Quick Review

Single model review via LiteLLM.

```bash
# Script: src/klean/data/scripts/quick-review.sh
quick-review.sh "review this function for security"
```

**Features:**
- Dynamic model discovery from LiteLLM
- Health fallback (if model unhealthy, try next)
- Thinking model support

---

### 5.2 Consensus Review

Parallel review across 5 models with agreement scoring.

```bash
# Script: src/klean/data/scripts/consensus-review.sh
consensus-review.sh "review authentication logic"
```

**Consensus Algorithm:**
1. Query 5 models in parallel (curl)
2. Parse JSON responses (with fallback to text)
3. Group findings by location similarity (>50% word overlap)
4. Classify by agreement:
   - **HIGH**: All models agree
   - **MEDIUM**: 2+ models agree
   - **LOW**: Single model only

---

### 5.3 Deep Review

Uses Claude Agent SDK for comprehensive analysis.

```bash
# Script: src/klean/data/scripts/deep-review.sh
deep-review.sh "full security audit"
```

**Features:**
- Read-only mode (no modifications)
- Comprehensive allow/deny lists
- Full codebase access

---

### 5.4 Rethink (Contrarian Debugging)

**Unique K-LEAN feature**: Challenges assumptions.

```bash
# Via command
/kln:rethink
```

**4 Contrarian Techniques:**
1. **Inversion**: Look at NOT-X if others looked at X
2. **Assumption Challenge**: What if key assumption is wrong?
3. **Domain Shift**: What would different expert see?
4. **Root Cause Reframe**: What if symptom isn't real problem?

---

### 5.5 Thinking Model Support

Some models (DeepSeek, GLM, Kimi, Minimax) return responses in `reasoning_content` instead of `content`.

**All scripts check both:**
```bash
content=$(echo "$response" | jq -r '.choices[0].message.content // empty')
if [ -z "$content" ]; then
    content=$(echo "$response" | jq -r '.choices[0].message.reasoning_content // empty')
fi
```

---

### 5.6 Review Prompts

Located in `src/klean/data/core/prompts/`:

| Prompt | Lines | Purpose |
|--------|-------|---------|
| `review.md` | 86 | 7-area review checklist |
| `rethink.md` | 92 | Contrarian debugging |
| `format-json.md` | 28 | Structured JSON output |
| `format-text.md` | 27 | Human-readable output |
| `agent-base.md` | 54 | SmolKLN agent template |

---

### 5.7 Review Areas (review.md)

1. CORRECTNESS
2. MEMORY SAFETY
3. ERROR HANDLING
4. CONCURRENCY
5. ARCHITECTURE
6. SECURITY
7. STANDARDS

---

### 5.8 Output Format

```json
{
  "grade": "B+",
  "risk": "MEDIUM",
  "findings": [
    {
      "severity": "HIGH",
      "location": "auth.py:42",
      "issue": "SQL injection vulnerability",
      "suggestion": "Use parameterized queries",
      "evidence": "user_input directly in query string"
    }
  ]
}
```

---

### 5.9 Core Engine

Main implementation: `src/klean/data/core/klean_core.py` (1190 lines)

**Key Classes:**
- `ModelResolver`: Auto-discovery from LiteLLM, latency caching
- `ReviewEngine`: Quick + multi-model execution

**Features:**
- Async parallel execution via `asyncio.gather`
- 24h latency caching (disk-based)
- Model diversity (limits thinking models to 50%)
- Robust JSON parsing (direct -> markdown -> raw braces)

---

### 5.10 Persistent Output

Reviews are saved to the project's `.claude/kln/` directory.

**Implementation:** `src/klean/data/scripts/session-helper.sh`

```
<project_root>/.claude/kln/
|-- quickReview/
|   `-- 2024-12-09_14-30-25_qwen_security.md
|-- quickCompare/
|   `-- 2024-12-09_16-00-00_consensus.md
|-- deepInspect/
|   `-- 2024-12-09_17-00-00_qwen_audit.md
`-- asyncDeepAudit/
    `-- 2024-12-09_18-00-00_parallel.md
```

**Filename format:** `YYYY-MM-DD_HH-MM-SS_model_focus.md`

**Fallback:** `/tmp/claude-reviews/` if project directory not writable.

---

### 5.11 Audit Mode (Security)

Deep reviews run in **read-only audit mode** for safe automation.

**Implementation:** `src/klean/data/scripts/deep-review.sh` (lines 180-212)

```json
{
  "permissions": {
    "allow": [
      "Read", "Glob", "Grep", "LS", "Agent", "Task",
      "WebFetch", "WebSearch",
      "mcp__tavily__*", "mcp__context7__*", "mcp__serena__find_*",
      "mcp__serena__list_*", "mcp__serena__read_*", "mcp__serena__search_*",
      "Bash(git diff:*)", "Bash(git log:*)", "Bash(git status:*)",
      "Bash(cat:*)", "Bash(find:*)", "Bash(ls:*)", "Bash(grep:*)"
    ],
    "deny": [
      "Write", "Edit", "NotebookEdit",
      "Bash(rm:*)", "Bash(mv:*)", "Bash(cp:*)", "Bash(mkdir:*)",
      "Bash(git add:*)", "Bash(git commit:*)", "Bash(git push:*)",
      "Bash(pip install:*)", "Bash(npm install:*)", "Bash(sudo:*)",
      "mcp__serena__replace_*", "mcp__serena__insert_*",
      "mcp__serena__rename_*", "mcp__serena__write_*", "mcp__serena__delete_*"
    ]
  }
}
```

Uses `--dangerously-skip-permissions` with restricted `allowedTools` for fast, safe automation.

---

### 5.12 Knowledge Integration

Reviews automatically extract and store reusable knowledge.

**Implementation:** `src/klean/data/scripts/fact-extract.sh`

**Flow:**
1. Review completes -> `fact-extract.sh` called with output
2. Claude Haiku extracts lessons (types: gotcha, pattern, solution, insight)
3. Stores in `.knowledge-db/` if `relevance_score >= 0.6`
4. Logs to `.knowledge-db/timeline.txt`

**Called from deep-review.sh:**
```bash
"$KB_SCRIPTS_DIR/fact-extract.sh" "$REVIEW_OUTPUT" "review" "$PROMPT" "$WORK_DIR"
```

**Extraction Types:**
- `gotcha` - Pitfalls to avoid
- `pattern` - Reusable approaches
- `solution` - Fixes that worked
- `insight` - Architectural observations

---

### 5.13 Scripts Reference

| Script | Purpose |
|--------|---------|
| `quick-review.sh` | Single model review |
| `consensus-review.sh` | 5-model parallel review |
| `deep-review.sh` | Claude SDK agent review |
| `smolkln-agent.sh` | SmolKLN agent execution |
| `parallel-deep-review.sh` | Multiple deep reviews |
| `second-opinion.sh` | Alternative perspective |
| `fact-extract.sh` | Extract knowledge from reviews |
| `session-helper.sh` | Output directory management |

---

## 6. SmolKLN Agents

SmolKLN is a production-grade SWE agent system using Smolagents + LiteLLM with memory, reflection, multi-agent orchestration, MCP integration, and async execution.

### 6.1 System Architecture

```
+----------------------------------------------------------------------+
|                           SmolKLN System                              |
+----------------------------------------------------------------------+
|                                                                       |
|  +-----------------+     +-----------------+     +-----------------+  |
|  |  Orchestrator   |---->|     Planner     |---->|    Executor     |  |
|  |  (multi-agent)  |     |  (task decomp)  |     |   (enhanced)    |  |
|  +-----------------+     +-----------------+     +-----------------+  |
|          |                       |                       |            |
|          v                       v                       v            |
|  +-------------------------------------------------------------------+|
|  |                    Project Context Layer                          ||
|  |  +----------+  +----------+  +----------+  +----------+          ||
|  |  | Project  |  |CLAUDE.md |  | Knowledge|  |  Serena  |          ||
|  |  |   Root   |  |  Loader  |  |    DB    |  |   Ready  |          ||
|  |  +----------+  +----------+  +----------+  +----------+          ||
|  +-------------------------------------------------------------------+|
|          |                                                            |
|          v                                                            |
|  +-------------------------------------------------------------------+|
|  |                       Memory Layer                                ||
|  |  +----------+  +----------+  +----------+  +----------+          ||
|  |  | Working  |  | Session  |  |Long-term |  | Artifact |          ||
|  |  | Context  |  |  Memory  |  |(Know.DB) |  |  Store   |          ||
|  |  +----------+  +----------+  +----------+  +----------+          ||
|  +-------------------------------------------------------------------+|
|          |                                                            |
|          v                                                            |
|  +-------------------------------------------------------------------+|
|  |                    Reflection Engine                              ||
|  |  +----------+  +----------+  +----------+                        ||
|  |  |  Critic  |  |  Retry   |  |  Lesson  |                        ||
|  |  |  Agent   |  | Manager  |  | Capture  |                        ||
|  |  +----------+  +----------+  +----------+                        ||
|  +-------------------------------------------------------------------+|
|          |                                                            |
|          v                                                            |
|  +-------------------------------------------------------------------+|
|  |                    MCP Tools Layer                                ||
|  |  +----------+  +----------+  +----------+  +----------+          ||
|  |  |filesystem|  |  serena  |  |   git    |  | knowledge|          ||
|  |  |   MCP    |  |   MCP    |  |   MCP    |  |   tool   |          ||
|  |  +----------+  +----------+  +----------+  +----------+          ||
|  +-------------------------------------------------------------------+|
|          |                                                            |
|          v                                                            |
|  +-------------------------------------------------------------------+|
|  |                    Async Execution Layer                          ||
|  |  +----------+  +----------+  +----------+                        ||
|  |  |  Task    |  | Worker   |  |  Status  |                        ||
|  |  |  Queue   |  |  Thread  |  | Tracker  |                        ||
|  |  +----------+  +----------+  +----------+                        ||
|  +-------------------------------------------------------------------+|
|                                                                       |
+----------------------------------------------------------------------+
```

---

### 6.2 Implementation Summary

| Phase | Component | File(s) | Status |
|-------|-----------|---------|--------|
| 0 | Project Awareness | `context.py` | Complete |
| 1 | Memory Integration | `memory.py`, `executor.py` | Complete |
| 2 | Reflection Loop | `reflection.py` | Complete |
| 3 | MCP Tools | `mcp_tools.py`, `tools.py` | Complete |
| 4 | Multi-Agent Orchestrator | `orchestrator.py` | Complete |
| 5 | Async Execution | `task_queue.py`, `async_executor.py` | Complete |

---

### 6.3 File Structure

```
src/klean/smol/
|-- __init__.py          # All exports (33 symbols)
|-- executor.py          # Main entry point - SmolKLNExecutor
|-- loader.py            # Agent .md file parser
|-- models.py            # LiteLLM model factory
|-- context.py           # Project awareness (git, CLAUDE.md, KB)
|-- memory.py            # Session + Knowledge DB memory
|-- reflection.py        # Self-critique and retry engine
|-- tools.py             # Tool definitions + MCP integration
|-- mcp_tools.py         # MCP server loading utilities
|-- orchestrator.py      # Multi-agent coordination
|-- task_queue.py        # Persistent file-based queue
`-- async_executor.py    # Background worker thread
```

---

### 6.4 Available Agents (8)

| Agent | Purpose |
|-------|---------|
| `security-auditor` | Security vulnerability analysis |
| `code-reviewer` | General code quality review |
| `performance-reviewer` | Performance optimization |
| `architecture-reviewer` | System design analysis |
| `test-reviewer` | Test coverage and quality |
| `documentation-reviewer` | Documentation completeness |
| `refactoring-advisor` | Code improvement suggestions |
| `debugging-assistant` | Bug investigation support |

---

### 6.5 Phase 0: Project Awareness

**Purpose**: Agents automatically know about the current project context.

**What agents receive:**
```
## Project: claudeAgentic
Root: `/home/calin/claudeAgentic`
Branch: `main` (9 files changed)

## Project Instructions (CLAUDE.md)
[Full CLAUDE.md content injected]

## Knowledge DB: Available at `.knowledge-db/`
Use `knowledge_search` tool to query prior solutions and lessons.

## Serena Memory: Available
Project memories and lessons-learned are accessible.
```

**Key Functions:**
- `detect_project_root()` - Git-aware project detection
- `gather_project_context()` - Collects all context (git, CLAUDE.md, KB, Serena)
- `format_context_for_prompt()` - Formats context for agent prompts

---

### 6.6 Phase 1: Memory Integration

**Purpose**: Agents maintain session memory and can query/save to Knowledge DB.

**Components:**
- `MemoryEntry` - Single memory item with timestamp and type (serializable)
- `SessionMemory` - Working memory for current task (max 50 entries, serializable)
- `AgentMemory` - Full memory system with KB integration

**Features:**
- Auto-starts session on each `execute()` call
- Records actions, results, and errors
- Queries prior knowledge from Knowledge DB
- Saves lessons learned back to Knowledge DB
- Token-limited context retrieval
- **Auto-persistence**: Session memory saved to KB after execution
- **Serena sync**: Bridge function to import Serena lessons to KB

**New Functions:**
- `persist_session_to_kb()` - Auto-saves meaningful entries after agent completes
- `sync_serena_to_kb()` - Imports Serena lessons-learned for agent access
- `to_dict()`/`from_dict()` - Serialization for future persistence
- `get_history()` - Inspect session memory entries

**Usage:**
```python
executor = SmolKLNExecutor()
result = executor.execute("code-reviewer", "review main.py")

# Memory automatically persisted to KB
print(f"Persisted: {result['memory_persisted']} entries")
print(f"History: {result['memory_history']}")

# Future agents find these learnings via knowledge_search
```

---

### 6.7 Phase 2: Reflection Loop

**Purpose**: Agents critique their own output and retry with feedback.

**Components:**
- `CritiqueVerdict` - PASS, RETRY, or FAIL
- `Critique` - Structured feedback with issues and suggestions
- `ReflectionEngine` - Critique and retry orchestration

**Critique Criteria:**
1. Did agent examine actual files?
2. Are findings specific with file:line references?
3. Are recommendations actionable?
4. Is output complete and well-structured?

**Flow:**
```
Execute -> Critique -> PASS? Done
                    -> RETRY? Execute with feedback
                    -> FAIL? Return with note
```

**Usage:**
```python
from klean.smol import create_reflection_engine, SmolKLNExecutor

executor = SmolKLNExecutor()
engine = create_reflection_engine()

result = engine.execute_with_reflection(
    executor,
    "security-auditor",
    "audit authentication"
)
print(f"Attempts: {result['attempts']}, Reflected: {result['reflected']}")
```

---

### 6.8 Phase 3: MCP Tools Integration

**Purpose**: Use MCP servers (Serena, filesystem, git) instead of custom tools.

**Key Insight**: Smolagents has native MCP support via `ToolCollection.from_mcp()`.

**Supported Servers:**
- `serena` - Project memory and context (auto-detected from `~/.claude.json`)
- `filesystem` - File operations (builtin)
- `git` - Git operations (builtin)

**Features:**
- Auto-loads MCP config from Claude settings
- Falls back to basic tools if MCP unavailable
- Supports custom server configuration

**Usage:**
```python
from klean.smol import get_mcp_tools, list_available_mcp_servers

# List available
servers = list_available_mcp_servers()
# {'serena': 'configured', 'filesystem': 'builtin', 'git': 'builtin'}

# Load tools
tools = get_mcp_tools(["serena"])
```

---

### 6.9 Default Tool Set

SmolKLN provides a comprehensive default tool set for all agents:

| Tool | Type | Purpose |
|------|------|---------|
| `knowledge_search` | Custom | Query project Knowledge DB for prior solutions |
| `web_search` | DuckDuckGo | Search web for documentation and articles |
| `visit_webpage` | Smolagents | Fetch and parse webpage content |
| `read_file` | Custom | Read file contents from project |
| `search_files` | Custom | Find files by glob pattern |
| `grep` | Custom | Search text patterns in files |

**Tool Loading** (from `tools.py`):
```python
from klean.smol import get_default_tools

tools = get_default_tools(project_path)
# Returns: [KnowledgeRetrieverTool, DuckDuckGoSearchTool,
#           VisitWebpageTool, read_file, search_files, grep]
```

---

### 6.10 Phase 4: Multi-Agent Orchestrator

**Purpose**: Coordinate multiple agents for complex tasks.

**Components:**
- `SubTask` - Single subtask with agent assignment
- `TaskPlan` - Full plan with parallel groups
- `SmolKLNOrchestrator` - Planning and execution engine

**Flow:**
```
Task -> Planner -> [Subtasks] -> Parallel Execution -> Synthesis -> Result
```

**Features:**
- Automatic task decomposition
- Dependency-aware scheduling
- Parallel execution (configurable workers)
- Result synthesis into cohesive output

**Usage:**
```python
from klean.smol import SmolKLNExecutor, SmolKLNOrchestrator

executor = SmolKLNExecutor()
orchestrator = SmolKLNOrchestrator(executor, max_parallel=3)

result = orchestrator.execute(
    "Full security and code quality audit",
    agents=["security-auditor", "code-reviewer", "performance-reviewer"]
)

print(f"Plan: {result['plan']}")
print(f"Success: {result['success']}")
print(f"Output:\n{result['output']}")
```

---

### 6.11 Phase 5: Async Execution

**Purpose**: Background task queue for non-blocking agent execution.

**Components:**
- `TaskState` - QUEUED, RUNNING, COMPLETED, FAILED
- `QueuedTask` - Task with full lifecycle tracking
- `TaskQueue` - Persistent file-based queue (`~/.klean/task_queue.json`)
- `AsyncExecutor` - Background worker thread

**Features:**
- Persistent queue survives restarts
- Automatic worker thread management
- Status polling and blocking wait
- Task cancellation (for queued tasks)
- Cleanup of old completed tasks

**Usage:**
```python
from klean.smol import submit_async, get_task_status, get_async_executor

# Submit task
task_id = submit_async("code-reviewer", "review main.py")
print(f"Submitted: {task_id}")

# Check status
status = get_task_status(task_id)
print(f"State: {status['state']}")

# Wait for completion
executor = get_async_executor()
result = executor.wait_for(task_id, timeout=120)
print(f"Result: {result}")

# List recent tasks
tasks = executor.list_tasks(limit=5)
```

---

### 6.12 Complete API Reference

**Core:**
```python
from klean.smol import (
    # Executor
    SmolKLNExecutor,

    # Agent loading
    load_agent,
    list_available_agents,
    Agent,
    AgentConfig,

    # Models
    create_model,
    get_model_for_role,
)
```

**Context:**
```python
from klean.smol import (
    ProjectContext,
    gather_project_context,
    format_context_for_prompt,
    detect_project_root,
)
```

**Memory:**
```python
from klean.smol import (
    AgentMemory,
    SessionMemory,
    MemoryEntry,
)
```

**Reflection:**
```python
from klean.smol import (
    ReflectionEngine,
    Critique,
    CritiqueVerdict,
    create_reflection_engine,
)
```

**MCP Tools:**
```python
from klean.smol import (
    get_mcp_tools,
    get_mcp_server_config,
    list_available_mcp_servers,
    load_mcp_config,
    KnowledgeRetrieverTool,
    get_default_tools,
)
```

**Orchestration:**
```python
from klean.smol import (
    SmolKLNOrchestrator,
    quick_orchestrate,
)
```

**Async Execution:**
```python
from klean.smol import (
    TaskQueue,
    QueuedTask,
    TaskState,
    AsyncExecutor,
    get_async_executor,
    submit_async,
    get_task_status,
)
```

---

### 6.13 Quick Start Examples

**Basic Execution:**
```python
from klean.smol import SmolKLNExecutor

executor = SmolKLNExecutor()
print(f"Project: {executor.project_root}")

result = executor.execute("security-auditor", "audit auth module")
print(result["output"])
```

**With Reflection:**
```python
from klean.smol import SmolKLNExecutor, create_reflection_engine

executor = SmolKLNExecutor()
engine = create_reflection_engine()

result = engine.execute_with_reflection(
    executor,
    "code-reviewer",
    "review error handling in api/"
)
print(f"Attempts: {result['attempts']}")
```

**Multi-Agent:**
```python
from klean.smol import SmolKLNExecutor, SmolKLNOrchestrator

executor = SmolKLNExecutor()
orchestrator = SmolKLNOrchestrator(executor)

result = orchestrator.execute("Complete codebase audit")
```

**Async Background:**
```python
from klean.smol import submit_async, get_async_executor

# Fire and forget
task_id = submit_async("code-reviewer", "review main.py")

# Later...
executor = get_async_executor()
result = executor.wait_for(task_id)
```

---

### 6.14 CLI Usage

```bash
smol-kln <agent> <task> [--model MODEL] [--telemetry]
smol-kln security-auditor "audit auth module"
smol-kln --list   # List available agents
```

**Output:** `.claude/kln/agentExecute/<timestamp>_<agent>_<task>.md`

---

### 6.15 Dependencies

- `smolagents[litellm]>=1.17.0` - Core agent framework
- `txtai>=7.0.0` - Knowledge DB (semantic search)
- `ddgs>=6.0.0` - DuckDuckGo web search tool
- `markdownify>=0.11.0` - HTML to markdown for VisitWebpageTool
- LiteLLM proxy at `localhost:4000` (configurable)

---

## 7. Quick Reference

### 7.1 Commands Quick Reference

| Command | Description | Example |
|---------|-------------|---------|
| `/kln:quick` | Fast review - single model (~30s) | `/kln:quick security` |
| `/kln:multi` | Consensus review - 3-5 models (~60s) | `/kln:multi --models 5 arch` |
| `/kln:deep` | Deep analysis - full codebase (~3min) | `/kln:deep --async security` |
| `/kln:agent` | SmolKLN - specialist agents | `/kln:agent --role security` |
| `/kln:rethink` | Fresh perspectives - debugging help | `/kln:rethink bug` |
| `/kln:doc` | Documentation - session notes | `/kln:doc "Sprint Review"` |
| `/kln:remember` | Knowledge capture - end of session | `/kln:remember` |
| `/kln:status` | System status - models, health | `/kln:status` |
| `/kln:help` | Command reference | `/kln:help` |

**Flags:** `--async` (background), `--models N` (count), `--output json/text`

---

### 7.2 Quick Commands (Type directly)

| Shortcut | Action |
|----------|--------|
| `healthcheck` | Check all LiteLLM models |
| `SaveThis <lesson>` | Save a lesson learned |
| `FindKnowledge <query>` | Search knowledge DB |

---

### 7.3 Knowledge Database Quick Reference

```bash
# Query via server (~30ms)
~/.claude/scripts/knowledge-query.sh "<topic>"

# Direct query (~17s cold)
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-search.py "<query>"
```

**Storage:** `.knowledge-db/` per project
**Server:** Auto-starts on first use

---

### 7.4 K-LEAN CLI Quick Reference

```bash
k-lean install    # Install components
k-lean setup      # Configure API provider
k-lean status     # Component status
k-lean doctor -f  # Diagnose + auto-fix
k-lean start      # Start services
k-lean models     # List with health
k-lean test       # Run test suite
```

---

### 7.5 SmolKLN CLI Quick Reference

```bash
smol-kln <agent> <task> [--model MODEL] [--telemetry]
smol-kln security-auditor "audit auth module"
smol-kln --list   # List available agents
```

**Output:** `.claude/kln/agentExecute/<timestamp>_<agent>_<task>.md`

---

### 7.6 Available Models

Auto-discovered from LiteLLM. Use `k-lean models` to see current list.

**Common:** `qwen3-coder`, `deepseek-v3-thinking`, `glm-4.6-thinking`, `kimi-k2-thinking`, `minimax-m2`

---

### 7.7 File Locations

| Type | Location |
|------|----------|
| CLI | `src/klean/cli.py` |
| Rules | `~/.claude/rules/k-lean.md` |
| Hooks | `~/.claude/hooks/` |
| Scripts | `~/.claude/scripts/` |
| Knowledge DB | `.knowledge-db/` (per project) |
| LiteLLM Config | `~/.config/litellm/` |
| SmolKLN Agents | `src/klean/smol/` |
| Review Output | `.claude/kln/` (per project) |

---

### 7.8 Serena Memories

Curated insights via `mcp__serena__*_memory` tools:
- `lessons-learned` - Gotchas, patterns
- `architecture-review-system` - System docs

---

### 7.9 Hooks Summary

| Hook | Trigger | Purpose |
|------|---------|---------|
| `session-start.sh` | SessionStart | Auto-start services |
| `user-prompt-handler.sh` | UserPromptSubmit | 7 keyword handlers |
| `post-bash-handler.sh` | PostToolUse (Bash) | Git timeline + facts |
| `post-web-handler.sh` | PostToolUse (Web*) | Auto-capture to KB |
| `async-review.sh` | UserPromptSubmit | Background reviews |

---

### 7.10 Research Foundation

SmolKLN implementation based on analysis of top SWE agents:
- **SWE-agent** - ACI (Agent-Computer Interface) design principles
- **OpenHands** - Multi-agent orchestration patterns
- **Aider** - Git-aware context and memory
- **Reflexion** - Self-critique and retry loops
- **MemGPT** - Tiered memory architecture

Key papers:
- "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering"
- "Reflexion: Language Agents with Verbal Reinforcement Learning"

---

*Generated from: cli.md, hooks.md, knowledge-db.md, litellm.md, review-system.md, smolkln-implementation.md*
