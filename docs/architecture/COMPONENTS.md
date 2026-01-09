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

The K-LEAN CLI provides commands for managing the system.

### Command Overview

| Command | Purpose | Speed |
|---------|---------|-------|
| `kln init` | Initialize with provider selection | ~10s |
| `kln install` | Install components | Varies |
| `kln uninstall` | Remove components | ~5s |
| `kln doctor` | Validate config (.env, subscription, services) | ~3s |
| `kln doctor -f` | Auto-fix issues | ~5s |
| `kln status` | Show installed components and services | ~2s |
| `kln model list` | List available models | ~1s |
| `kln model list --health` | Check model health | ~60s |
| `kln model add` | Add individual model | ~1s |
| `kln model remove` | Remove model | ~1s |
| `kln model test` | Test specific model | ~5s |
| `kln provider list` | List providers | ~1s |
| `kln provider add` | Add provider | ~5s |
| `kln provider set-key` | Update API key | ~1s |
| `kln start` | Start LiteLLM proxy | ~3s |
| `kln stop` | Stop services | ~1s |
| `kln admin sync` | Sync package data (dev) | ~2s |
| `kln admin debug` | Live monitoring dashboard | Continuous |

### User Mental Model

```
"Is my SYSTEM configured?" --> kln doctor
"What's RUNNING now?"      --> kln status
"Are my MODELS working?"   --> kln model list --health
```

---

### 1.1 init

Interactive setup combining provider configuration and installation.

```bash
kln init                        # Interactive wizard
kln init --provider nanogpt     # Direct setup
kln init --provider nanogpt --api-key $KEY  # Non-interactive
```

**Steps:**
1. Provider selection (NanoGPT/OpenRouter)
2. API key input (secure hidden)
3. Auto-detect subscription status
4. Install components
5. Start services

---

### 1.2 doctor

Validates configuration and services.

```bash
kln doctor             # Check everything
kln doctor --auto-fix  # Fix issues automatically
kln doctor -f          # Short form
```

**Checks performed:**
- `.env` file exists with `NANOGPT_API_KEY`
- `NANOGPT_API_BASE` configured (auto-detects subscription vs pay-per-use)
- NanoGPT subscription status + remaining quota
- LiteLLM proxy running
- Knowledge server running
- Hook entry points exist

---

### 1.3 status

Shows installed components and running services.

```bash
kln status
```

**Output includes:**
- Scripts count (symlinked status)
- KLN commands (9)
- SuperClaude availability (optional)
- Hook entry points (4)
- SmolKLN Agents (8)
- Knowledge DB (per-project status + entry count)
- LiteLLM Proxy (model count + provider)
- K-LEAN CLI version

---

### 1.4 model list

Lists and tests available LLM models.

```bash
kln model list           # List all models
kln model list --health  # Check health (calls each model)
```

**Dynamic Discovery:** Models are discovered from LiteLLM at runtime, not hardcoded.

---

### 1.5 start / stop

Controls K-LEAN services.

```bash
kln start                    # Start LiteLLM (default)
kln start -s knowledge       # Start Knowledge server
kln start -s all             # Start both services
kln start -p 4001            # Custom port
kln stop                     # Stop for current project
kln stop --all-projects      # Stop all KB servers
kln stop -s litellm          # Stop specific service
```

---

### 1.6 install / uninstall

Manages K-LEAN components.

```bash
kln install                      # Full installation
kln install --component scripts  # Specific component
kln install --dev                # Dev mode (symlinks)

kln uninstall                    # Remove all
kln uninstall --yes              # Skip confirmation
```

**Components:** all, scripts, commands, hooks, smolkln, config, knowledge

---

### 1.7 Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Error / test failures |
| 2 | Configuration error |

---

### 1.8 Environment Variables

| Variable | Purpose |
|----------|---------|
| `KLEAN_KB_PORT` | Override KB server port (default: 14000) |
| `KLEAN_KB_PYTHON` | Override Python path |
| `KLEAN_SCRIPTS_DIR` | Override scripts location |

---

### 1.9 Implementation

Main CLI: `src/klean/cli.py`

Uses:
- `click` for CLI framework
- `rich` for terminal output
- `httpx` for async HTTP
- `psutil` for process management
- `platformdirs` for cross-platform paths

---

## 2. Hooks System

K-LEAN integrates with Claude Code via **4 Python entry points** that trigger on specific events.

### Hook Overview

| Entry Point | Trigger | Purpose |
|-------------|---------|---------|
| `kln-hook-session` | SessionStart | Auto-start LiteLLM + per-project KB |
| `kln-hook-prompt` | UserPromptSubmit | Keyword detection (7 keywords) |
| `kln-hook-bash` | PostToolUse (Bash) | Git events -> timeline |
| `kln-hook-web` | PostToolUse (Web*) | Auto-capture web content to KB |

---

### 2.1 kln-hook-session

**Trigger:** Claude Code session starts

**Actions:**
1. Start LiteLLM proxy (if not running)
2. Start per-project KB server
3. Show configuration warnings

**Implementation:** `src/klean/hooks.py:session_start()`

---

### 2.2 kln-hook-prompt

**Trigger:** User submits a prompt

**Keywords detected:**

| Keyword | Action |
|---------|--------|
| `FindKnowledge <query>` | Search KB |
| `SaveInfo <url>` | Smart save URL with LLM evaluation |
| `InitKB` | Initialize project KB |
| `asyncReview` | Background quick review |
| `asyncConsensus` | Background consensus review |

**Note:** `SaveThis` was replaced by `/kln:learn` for context-aware capture.

**Implementation:** `src/klean/hooks.py:prompt_handler()`

---

### 2.3 kln-hook-bash

**Trigger:** After any Bash command

**Detects:**
- `git commit` -> Log to timeline
- `git push` -> Log to timeline
- Other git operations

**Implementation:** `src/klean/hooks.py:post_bash()`

---

### 2.4 kln-hook-web

**Trigger:** After WebFetch/WebSearch/Tavily tools

**Action:** Smart capture of web content to KB

**Implementation:** `src/klean/hooks.py:post_web()`

---

### 2.5 Hook Registration

Hooks are registered in `~/.claude/settings.json` as Python entry points:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [{"type": "command", "command": "kln-hook-session", "timeout": 10}]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [{"type": "command", "command": "kln-hook-prompt", "timeout": 30}]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [{"type": "command", "command": "kln-hook-bash", "timeout": 15}]
      },
      {
        "matcher": "WebFetch|WebSearch",
        "hooks": [{"type": "command", "command": "kln-hook-web", "timeout": 10}]
      }
    ]
  }
}
```

**Note:** Entry points work cross-platform - pip creates appropriate wrappers on Windows.

---

### 2.6 Hook I/O Protocol

Hooks read JSON from stdin and output JSON to stdout:

**Input:**
```json
{"source": "startup", "prompt": "user text", "tool_name": "Bash", ...}
```

**Output:**
```json
{"decision": "allow", "additionalContext": "..."}
```
or
```json
{"decision": "block", "reason": "..."}
```

---

### 2.7 Exit Code Behavior

| Code | Behavior |
|------|----------|
| 0 | Success, continue |
| 1 | Error (logged, operation continues) |
| 2 | **Block operation** (reason shown to Claude) |

---

### 2.8 Debugging Hooks

```bash
# Test hooks manually
echo '{"source":"startup"}' | kln-hook-session
echo '{"prompt":"FindKnowledge test"}' | kln-hook-prompt
```

---

## 3. Knowledge Database

The Knowledge DB provides **persistent semantic memory** across Claude Code sessions using fastembed (ONNX-based, ~200MB).

### Key Features

- **Per-project isolation**: Each git repo gets its own KB
- **Semantic search**: Find related knowledge by meaning, not just keywords
- **Fast queries**: TCP server with 1hr idle timeout (~30ms latency)
- **V2 schema**: Rich metadata for quality and provenance
- **Immediate indexing**: Server-owned writes for instant searchability

---

### 3.1 Architecture

```
+-----------------------------------------------------+
|                   Claude Code                        |
|  /kln:learn "topic" (context-aware extraction)       |
+---------------------+-------------------------------+
                      | Claude extracts insights
                      v
+-----------------------------------------------------+
|               knowledge-capture.py                   |
|  Parse -> V2 Schema -> TCP to server OR direct file |
+---------------------+-------------------------------+
                      |
                      v
+-----------------------------------------------------+
|                 .knowledge-db/                       |
|  |-- entries.jsonl     # All captured knowledge     |
|  |-- embeddings.npy    # Dense vectors              |
|  `-- entries.pkl       # Entry metadata             |
+-----------------------------------------------------+
                      ^
                      | TCP query (localhost)
+---------------------+-------------------------------+
|              knowledge-server.py                     |
|  Port: 14000 + hash offset                          |
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
| `knowledge-server.py` | TCP server (per-project daemon) |
| `knowledge-capture.py` | Add entries via server or direct |
| `knowledge_db.py` | Core fastembed-based DB |
| `kb_utils.py` | Cross-platform utilities |

---

### 3.4 Server-Owned Writes

Entries added via the server are immediately searchable:

```python
# Via TCP (preferred - immediate index update)
sock.sendall(json.dumps({
    "cmd": "add",
    "entry": {"title": "...", "summary": "...", ...}
}).encode())

# Via capture script (uses TCP internally)
knowledge-capture.py "lesson text" --type lesson --tags tag1,tag2
```

---

### 3.5 Query Methods

```bash
# Via server (~30ms)
echo '{"cmd":"search","query":"auth bug","limit":5}' | nc localhost 14XXX

# Via capture script
~/.claude/scripts/knowledge-query.sh "search term"

# Direct Python (slower, ~17s cold start)
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge_db.py search "query"
```

---

### 3.6 Knowledge Capture Methods

| Method | Type | Context-Aware | Description |
|--------|------|---------------|-------------|
| `/kln:learn` | Slash | Yes | Extract learnings from conversation context |
| `/kln:learn "topic"` | Slash | Yes | Focused extraction on specific topic |
| `/kln:remember` | Slash | Yes | End-of-session comprehensive capture |
| `FindKnowledge <query>` | Hook | N/A | Search KB |
| `SaveInfo <url>` | Hook | Partial | LLM evaluates URL content |

---

### 3.7 TCP Protocol

| Command | Request | Response |
|---------|---------|----------|
| search | `{"cmd":"search","query":"...","limit":5}` | `{"results":[...],"search_time_ms":...}` |
| add | `{"cmd":"add","entry":{...}}` | `{"status":"ok","id":"..."}` |
| status | `{"cmd":"status"}` | `{"status":"running","entries":...}` |
| ping | `{"cmd":"ping"}` | `{"pong":true}` |

---

### 3.8 Port Management

Each project gets a unique port based on path hash:

```
Base port: 14000 (or KLEAN_KB_PORT env var)
Project offset: MD5(project_path)[:2] % 256
Final port: base + offset
```

Port and PID files stored in runtime directory:
- Linux/macOS: `/tmp/klean-{username}/kb-{hash}.port`
- Windows: `%TEMP%\klean-{username}\kb-{hash}.port`

---

### 3.9 Troubleshooting

**KB Not Starting:**
```bash
kln doctor --auto-fix    # Auto-repair
kln start -s knowledge   # Manual start
```

**Check Status:**
```bash
kln status  # Shows KB status per project
```

---

## 4. LiteLLM Integration

K-LEAN uses **LiteLLM proxy** to route requests to multiple LLM providers.

### Architecture

```
+-------------+    +------------------+    +-----------------+
|   Claude    |    |     LiteLLM      |    |    NanoGPT      |
|   Code      |<-->|  localhost:4000  |<-->|   (dynamic)     |
|  (reviews)  |    |                  |    +-----------------+
+-------------+    |  /chat/completions|    |   OpenRouter    |
                   |  /v1/models       |    |   (dynamic)     |
                   +------------------+    +-----------------+
```

---

### 4.1 Providers

| Provider | Models | Config File |
|----------|--------|-------------|
| NanoGPT | Dynamic | `~/.config/litellm/config.yaml` |
| OpenRouter | Dynamic | `~/.config/litellm/openrouter.yaml` |

---

### 4.2 Thinking Models

These models return `reasoning_content` instead of `content`:
- DeepSeek R1, DeepSeek V3
- GLM-4.6
- Kimi K2
- MiniMax M2

The `reviews.py` module handles this automatically.

---

### 4.3 Configuration

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
```

---

### 4.4 Config Syntax

```yaml
model_list:
  - model_name: coding-qwen
    litellm_params:
      model: openai/Qwen/Qwen2.5-Coder-32B-Instruct
      api_key: os.environ/NANOGPT_API_KEY  # NO quotes!
      api_base: os.environ/NANOGPT_API_BASE
```

**Critical:** `os.environ/KEY` must NOT be quoted.

---

### 4.5 Setup

```bash
kln init                # Interactive setup
kln start               # Start proxy
kln model list --health # Check models
```

---

## 5. Review System

K-LEAN provides **multi-model code reviews** with consensus building.

### Review Types

| Type | Command | Models | Speed |
|------|---------|--------|-------|
| Quick | `/kln:quick` | 1 model | ~10s |
| Multi/Consensus | `/kln:multi` | 5 parallel | ~30s |
| SmolKLN Agent | `/kln:agent` | Specialist persona | ~2min |
| Rethink | `/kln:rethink` | Contrarian analysis | ~20s |

---

### 5.1 Implementation

Main module: `src/klean/reviews.py`

**Key Functions:**
- `quick_review()` - Single model async review
- `consensus_review()` - Parallel multi-model review
- `second_opinion()` - Alternative perspective

**Features:**
- Async httpx for parallel execution
- Automatic thinking model handling
- JSON parsing with fallbacks

---

### 5.2 Thinking Model Support

Models may return content in different fields:

```python
# reviews.py handles this automatically
content = response.get("content") or response.get("reasoning_content")
# Also strips <think> tags from thinking models
```

---

### 5.3 Consensus Algorithm

1. Query 5 models in parallel (httpx async)
2. Parse JSON responses (with fallback to text)
3. Group findings by location similarity (>50% word overlap)
4. Classify by agreement:
   - **HIGH**: All models agree
   - **MEDIUM**: 2+ models agree
   - **LOW**: Single model only

---

### 5.4 Rethink (Contrarian Debugging)

**4 Contrarian Techniques:**
1. **Inversion**: Look at NOT-X if others looked at X
2. **Assumption Challenge**: What if key assumption is wrong?
3. **Domain Shift**: What would different expert see?
4. **Root Cause Reframe**: What if symptom isn't real problem?

---

### 5.5 Output Format

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

### 5.6 Persistent Output

Reviews are saved to `.claude/kln/`:

```
<project_root>/.claude/kln/
|-- quickReview/
|   `-- 2024-12-09_14-30-25_qwen_security.md
|-- quickCompare/
|   `-- 2024-12-09_16-00-00_consensus.md
`-- agentExecute/
    `-- 2024-12-09_18-00-00_security-auditor.md
```

---

## 6. SmolKLN Agents

SmolKLN is a production-grade SWE agent system using Smolagents + LiteLLM.

### 6.1 Available Agents (8)

| Agent | Purpose |
|-------|---------|
| `code-reviewer` | OWASP, SOLID, code quality |
| `security-auditor` | Vulnerabilities, auth, crypto |
| `debugger` | Root cause analysis |
| `performance-engineer` | Profiling, optimization |
| `rust-expert` | Ownership, lifetimes, unsafe |
| `c-pro` | C99/C11, POSIX, embedded |
| `arm-cortex-expert` | ARM MCU, real-time |
| `orchestrator` | Multi-agent coordination |

---

### 6.2 File Structure

```
src/klean/smol/
|-- __init__.py          # All exports
|-- executor.py          # Main entry point - SmolKLNExecutor
|-- loader.py            # Agent .md file parser
|-- models.py            # LiteLLM model factory
|-- context.py           # Project awareness
|-- memory.py            # Session + KB memory
|-- reflection.py        # Self-critique and retry
|-- tools.py             # Tool definitions
|-- mcp_tools.py         # MCP server loading
|-- orchestrator.py      # Multi-agent coordination
|-- task_queue.py        # Persistent queue
`-- async_executor.py    # Background worker
```

---

### 6.3 Default Tool Set

| Tool | Purpose |
|------|---------|
| `knowledge_search` | Query project Knowledge DB |
| `web_search` | Search web (DuckDuckGo) |
| `visit_webpage` | Fetch webpage content |
| `read_file` | Read file from project |
| `search_files` | Find files by glob |
| `grep` | Search text patterns |

---

### 6.4 Usage

**CLI:**
```bash
kln-smol <agent> <task> [--model MODEL] [--telemetry]
kln-smol security-auditor "audit auth module"
kln-smol --list   # List available agents
```

**Python:**
```python
from klean.smol import SmolKLNExecutor

executor = SmolKLNExecutor()
result = executor.execute("security-auditor", "audit auth module")
print(result["output"])
```

---

## 7. Quick Reference

### 7.1 Commands Quick Reference

| Command | Description | Example |
|---------|-------------|---------|
| `/kln:quick` | Fast review - single model | `/kln:quick security` |
| `/kln:multi` | Consensus review - 3-5 models | `/kln:multi --models 5 arch` |
| `/kln:agent` | SmolKLN - specialist agents | `/kln:agent --role security` |
| `/kln:rethink` | Fresh perspectives | `/kln:rethink bug` |
| `/kln:learn` | Extract learnings | `/kln:learn "auth bug"` |
| `/kln:remember` | End of session capture | `/kln:remember` |
| `/kln:status` | System status | `/kln:status` |
| `/kln:help` | Command reference | `/kln:help` |

---

### 7.2 Hook Keywords (Type directly)

| Keyword | Action |
|---------|--------|
| `FindKnowledge <query>` | Search knowledge DB |
| `SaveInfo <url>` | Smart save URL |

---

### 7.3 CLI Quick Reference

```bash
kln init       # Interactive setup
kln install    # Install components
kln status     # Component status
kln doctor -f  # Diagnose + auto-fix
kln start      # Start services
kln model list # List models
```

---

### 7.4 File Locations

| Type | Location |
|------|----------|
| CLI | `src/klean/cli.py` |
| Hooks | `src/klean/hooks.py` |
| Reviews | `src/klean/reviews.py` |
| Platform | `src/klean/platform.py` |
| Rules | `~/.claude/rules/kln.md` |
| Scripts | `~/.claude/scripts/` |
| Knowledge DB | `.knowledge-db/` (per project) |
| LiteLLM Config | `~/.config/litellm/` |
| SmolKLN | `src/klean/smol/` |
| Review Output | `.claude/kln/` (per project) |

---

*Last updated: 2026-01*
