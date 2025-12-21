# K-LEAN Architecture

Technical implementation details for developers and maintainers.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        K-LEAN ARCHITECTURE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  USER INPUT                                                                 │
│       │                                                                     │
│       ▼                                                                     │
│  ┌─────────────────┐                                                        │
│  │  Claude Code    │                                                        │
│  │  (Native)       │                                                        │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ├──────────────────────────────────────────────────────┐          │
│           │                                                      │          │
│           ▼                                                      ▼          │
│  ┌─────────────────┐                                   ┌─────────────────┐  │
│  │     HOOKS       │                                   │ SLASH COMMANDS  │  │
│  │ (settings.json) │                                   │ (~/.claude/     │  │
│  └────────┬────────┘                                   │  commands/kln/) │  │
│           │                                            └────────┬────────┘  │
│           ▼                                                     │          │
│  ┌─────────────────┐                                            │          │
│  │    SCRIPTS      │◄───────────────────────────────────────────┘          │
│  │ (~/.claude/     │                                                        │
│  │  scripts/)      │                                                        │
│  └────────┬────────┘                                                        │
│           │                                                                 │
│           ├────────────────┬────────────────┬───────────────┐               │
│           ▼                ▼                ▼               ▼               │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │  LiteLLM Proxy  │ │  Headless       │ │ Factory     │ │ Knowledge   │   │
│  │  localhost:4000 │ │  Claude (CLI)   │ │ Droid (CLI) │ │ DB Server   │   │
│  └────────┬────────┘ └────────┬────────┘ └──────┬──────┘ └─────────────┘   │
│           │                   │                 │                          │
│           ▼                   ▼                 ▼                          │
│  ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐               │
│  │  NanoGPT API    │ │  MCP Tools      │ │ 8 Specialist    │               │
│  │  (6 models)     │ │  Serena/Context7│ │ Droids          │               │
│  └─────────────────┘ └─────────────────┘ └─────────────────┘               │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Hooks System

Hooks are shell scripts Claude Code executes at specific events.

### Hook Types

| Type | When | Use Case |
|------|------|----------|
| `UserPromptSubmit` | Before processing prompt | Intercept keywords, background tasks |
| `PostToolUse` | After tool completes | React to git commits, web fetches |

### Configuration (`~/.claude/settings.json`)

```json
{
  "alwaysThinkingEnabled": true,
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/scripts/async-dispatch.sh",
            "timeout": 5
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/scripts/post-commit-docs.sh",
            "timeout": 10
          }
        ]
      },
      {
        "matcher": "WebFetch",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/scripts/auto-capture-hook.sh",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### Hook Input/Output

**Input (JSON via stdin):**
```json
{
  "prompt": "user typed text",
  "tool": "Bash",
  "tool_input": {"command": "git commit -m 'msg'"},
  "result": "tool output"
}
```

**Output:**
```json
{"decision": "block", "reason": "Message to user"}
```
Or no output (exit 0) to pass through.

### async-dispatch.sh

Main UserPromptSubmit hook. Handles:

| Keyword | Action |
|---------|--------|
| `healthcheck` | Check all 6 models, block with results |
| `asyncDeepAudit` | Start parallel-deep-review.sh in background |
| `asyncQuickCompare` | Start consensus-review.sh in background |
| `asyncQuickReview` | Start quick-review.sh in background |
| `asyncQuickConsult` | Start second-opinion.sh in background |
| `GoodJob` | Start goodjob-dispatch.sh in background |
| `SaveThis` | Save lesson via goodjob-dispatch.sh |
| `FindKnowledge` | Search knowledge DB, block with results |

### post-commit-docs.sh

PostToolUse hook for Bash. Triggers after `git commit`:
1. Detects git commit in command
2. Spawns headless Claude
3. Updates Serena memories with commit info

### auto-capture-hook.sh

PostToolUse hook for WebFetch/WebSearch:
1. Checks content length (>200 chars)
2. Skips error pages
3. Calls Haiku for extraction
4. Stores if relevance > 0.5

---

## Slash Commands System

Commands in `~/.claude/commands/kln/*.md` expand into prompts.

### Command Structure

```markdown
---
name: quickReview
description: Fast single-model code review
allowed-tools: Bash, Read, Grep
argument-hint: "[model] [focus]"
---

# Quick Review

**Arguments:** $ARGUMENTS

## Step 1: Parse Arguments
...

## Step 2: Execute
\`\`\`bash
~/.claude/scripts/quick-review.sh "$MODEL" "$FOCUS" "$(pwd)"
\`\`\`
```

### Execution Methods

**API Method (Quick):**
```
Command → Script → curl → LiteLLM:4000 → NanoGPT → Response
```
- Used by: quickReview, quickCompare, quickConsult
- Fast (~30-60s), no tool access

**CLI Method (Deep):**
```
Command → Script → Headless Claude → LiteLLM Model
                         ↓
                   Full MCP Tools
```
- Used by: deepInspect, deepAudit
- Slower (~3-5min), full tool access, READ-ONLY

**Droid Method (Fast Agentic):**
```
Command → Script → Factory Droid CLI → LiteLLM Model
                         ↓
                   Built-in Tools (Read, Grep, Glob, Execute)
```
- Used by: droid, droidAudit, droidExecute
- Fast (~30s-1min), agentic file access, built-in ripgrep

---

## Knowledge System

Per-project semantic database using txtai.

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  KNOWLEDGE FLOW                                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  CAPTURE                                                        │
│  ├─ Manual: "GoodJob <url>" → goodjob-dispatch.sh              │
│  └─ Auto: WebFetch → auto-capture-hook.sh                      │
│                    ↓                                            │
│  EXTRACT: knowledge-extract.sh → Haiku → JSON                  │
│                    ↓                                            │
│  STORE: knowledge_db.py → .knowledge-db/                       │
│         ├─ index/        (txtai embeddings)                    │
│         └─ entries.jsonl (human-readable backup)               │
│                    ↓                                            │
│  SEARCH: "FindKnowledge <query>" → knowledge-search.py         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Data Schema

```json
{
  "id": "uuid",
  "title": "Short descriptive title",
  "summary": "What was found (2-3 sentences)",
  "type": "web|code|solution|lesson",
  "url": "https://source-url",
  "problem_solved": "What problem this solves",
  "key_concepts": ["keyword1", "keyword2"],
  "relevance_score": 0.0-1.0,
  "what_worked": "For solutions",
  "constraints": "Limitations",
  "found_date": "ISO timestamp"
}
```

### Scripts

| Script | Purpose |
|--------|---------|
| `knowledge_db.py` | Core class: add, search, stats, rebuild |
| `knowledge-search.py` | Search interface with output formats |
| `knowledge-extract.sh` | Haiku extraction wrapper |
| `goodjob-dispatch.sh` | Manual capture handler |
| `auto-capture-hook.sh` | Auto-capture PostToolUse hook |

### Integration with Reviews

Review scripts search knowledge DB before reviewing:
```bash
KNOWLEDGE=$("$PYTHON" "$SCRIPTS/knowledge-search.py" "$FOCUS" --format inject)
# Inject into system prompt
```

---

## Scripts Reference

### Review Scripts

| Script | Purpose | Called By |
|--------|---------|-----------|
| `quick-review.sh` | Single model API review | quickReview, asyncQuickReview |
| `second-opinion.sh` | Single model consultation | quickConsult, asyncQuickConsult |
| `consensus-review.sh` | 3 models API comparison | quickCompare, asyncQuickCompare |
| `deep-review.sh` | Single model CLI + tools | deepInspect |
| `parallel-deep-review.sh` | 3 models CLI + tools | deepAudit, asyncDeepAudit |
| `droid-review.sh` | Single model Factory Droid | droid, asyncDroid |
| `parallel-droid-review.sh` | 3 models Factory Droid | droidAudit, asyncDroidAudit |
| `droid-execute.sh` | Specialized droid execution | droidExecute |

### Hook Scripts

| Script | Hook Type | Trigger |
|--------|-----------|---------|
| `async-dispatch.sh` | UserPromptSubmit | All prompts |
| `post-commit-docs.sh` | PostToolUse (Bash) | git commit |
| `auto-capture-hook.sh` | PostToolUse (WebFetch) | Web fetches |

### Utility Scripts

| Script | Purpose |
|--------|---------|
| `health-check.sh` | Test all 6 models |
| `session-helper.sh` | Create session directory |
| `start-litellm.sh` | Start LiteLLM proxy |
| `sync-check.sh` | Verify scripts/commands synced |
| `test-system.sh` | Full system verification |
| `test-headless.sh` | Test model via headless Claude |

---

## LiteLLM Configuration

`~/.config/litellm/nanogpt.yaml`:

```yaml
model_list:
  - model_name: qwen3-coder
    litellm_params:
      model: openai/Qwen/Qwen3-Coder
      api_base: https://api.nano-gpt.com/v1
      api_key: os.environ/NANOGPT_API_KEY

  - model_name: deepseek-v3-thinking
    litellm_params:
      model: openai/deepseek-chat
      api_base: https://api.nano-gpt.com/v1

  - model_name: kimi-k2-thinking
    litellm_params:
      model: openai/kimi-k2-0711-preview
      api_base: https://api.nano-gpt.com/v1

  - model_name: glm-4.6-thinking
    litellm_params:
      model: openai/glm-z1-air
      api_base: https://api.nano-gpt.com/v1

  - model_name: minimax-m2
    litellm_params:
      model: openai/MiniMax-M2-Large
      api_base: https://api.nano-gpt.com/v1

  - model_name: hermes-4-70b
    litellm_params:
      model: openai/hermes-4-mini
      api_base: https://api.nano-gpt.com/v1
```

---

## Unified Prompts (v2.0)

All models use the same prompt structure:

### REVIEW Category

```
You are an expert embedded systems code reviewer.

REVIEW ALL of these areas, with extra attention to the user's focus:

## CORRECTNESS
- Logic errors, edge cases, off-by-one
- Algorithm correctness, state management

## MEMORY SAFETY
- Buffer overflows, null pointer dereferences
- Memory leaks (especially error paths)

## ERROR HANDLING
- Input validation at trust boundaries
- Error propagation and resource cleanup

## CONCURRENCY
- Race conditions, thread safety
- ISR constraints, shared data protection

## ARCHITECTURE
- Module coupling and cohesion
- Abstraction quality, API consistency

## HARDWARE (if applicable)
- I/O state correctness, timing
- Volatile usage for registers

## STANDARDS
- Coding style consistency
- MISRA-C guidelines (where applicable)
```

### CONSULT Category

```
You are an independent expert providing a SECOND OPINION.

YOUR ROLE:
- Evaluate the approach/decision objectively
- Challenge assumptions - what might be wrong?
- Consider alternatives that may have been missed
- Identify risks not yet considered
- Be honest, not just agreeable
```

### Deep Review Additions

For CLI method (deepInspect, deepAudit):

```
TOOLS AVAILABLE:
- Read, Grep, Glob, Bash - explore and read any file
- Sequential Thinking MCP - use for complex analysis
- Serena MCP - access project memories and symbols
- Context7 MCP - lookup library documentation

IMPORTANT CONSTRAINTS:
- READ-ONLY: Do NOT modify, edit, or implement any code
- Do NOT create files or make changes to the codebase
- Your ONLY output is the review report
```

---

## File Locations

```
~/.claude/
├── settings.json          # Hooks configuration
├── CLAUDE.md              # System instructions
├── mcp.json               # MCP servers
├── scripts/               # All scripts
│   ├── async-dispatch.sh
│   ├── quick-review.sh
│   ├── knowledge_db.py
│   └── ...
└── commands/
    └── kln/               # Slash commands
        ├── quickReview.md
        ├── deepAudit.md
        └── ...

~/.config/litellm/
└── nanogpt.yaml           # LiteLLM model config

~/.venvs/knowledge-db/     # txtai virtual environment

/tmp/claude-reviews/       # Output directory
└── {session-id}/
    ├── quick-*.log
    ├── deep-*.log
    └── ...

{project}/
├── .knowledge-db/         # Per-project knowledge
│   ├── index/
│   └── entries.jsonl
└── .serena/               # Serena memories
```

---

## Extending the System

### Add New Model

1. Add to `~/.config/litellm/nanogpt.yaml`
2. Update `async-dispatch.sh` model list
3. Update `/kln:help` documentation

### Add New Slash Command

1. Create `~/.claude/commands/kln/newcommand.md`
2. Add frontmatter (name, description, allowed-tools)
3. Use `$ARGUMENTS` for user input
4. Call scripts or inline bash

### Add New Hook

1. Create script in `~/.claude/scripts/`
2. Make executable: `chmod +x`
3. Add to `~/.claude/settings.json` hooks section
4. Test with manual JSON input

### Add New Keyword

1. Edit `~/.claude/scripts/async-dispatch.sh`
2. Add pattern match: `if echo "$PROMPT" | grep -qi "keyword"`
3. Add handler logic
4. Use `block_with_message` to respond

---

## Troubleshooting

### Hook not firing

```bash
# Check settings has hooks
cat ~/.claude/settings.json | jq '.hooks'

# Test script manually
echo '{"prompt":"healthcheck"}' | ~/.claude/scripts/async-dispatch.sh
```

### Script permission denied

```bash
chmod +x ~/.claude/scripts/*.sh
```

### LiteLLM not responding

```bash
curl http://localhost:4000/health
pkill -f litellm
start-nano-proxy
```

### Knowledge DB errors

```bash
# Check venv
~/.venvs/knowledge-db/bin/python -c "from txtai import Embeddings; print('OK')"

# Rebuild index
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge_db.py rebuild
```

---

---

## Factory Droid System

Factory Droid provides fast agentic code review with built-in tools.

### Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                  FACTORY DROID FLOW                            │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  /kln:droidExecute <model> <droid> <prompt>                   │
│           │                                                   │
│           ▼                                                   │
│  ┌─────────────────┐                                          │
│  │ droid-execute.sh│ ← Queries Knowledge DB for context       │
│  └────────┬────────┘                                          │
│           │                                                   │
│           ▼                                                   │
│  ┌─────────────────┐                                          │
│  │ Factory Droid   │ ← Uses specialist droid from             │
│  │ CLI             │   ~/.factory/droids/                     │
│  └────────┬────────┘                                          │
│           │                                                   │
│           ▼                                                   │
│  ┌─────────────────┐                                          │
│  │ LiteLLM Proxy   │ ← Routes to NanoGPT models               │
│  │ localhost:4000  │                                          │
│  └─────────────────┘                                          │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### 8 Specialist Droids

| Droid | Lines | Focus |
|-------|-------|-------|
| `orchestrator` | 766 | Master coordinator, task delegation, memory system |
| `code-reviewer` | 201 | OWASP Top 10, SOLID principles, structured output |
| `security-auditor` | 90 | Vulnerability detection, auth flows, encryption |
| `debugger` | 100 | Root cause analysis, hypothesis testing |
| `arm-cortex-expert` | 265 | ARM Cortex-M, DMA, ISRs, cache coherency, FreeRTOS |
| `c-pro` | 36 | C99/C11, POSIX, memory management, MISRA |
| `rust-expert` | 38 | Ownership, lifetimes, no_std embedded |
| `performance-engineer` | 37 | Profiling, optimization, benchmarks |

### Droid Configuration (`~/.factory/config.json`)

```json
{
  "custom_models": [
    {
      "model_display_name": "Qwen3 Coder [LiteLLM]",
      "model": "qwen3-coder",
      "base_url": "http://localhost:4000/v1/",
      "api_key": "sk-litellm",
      "provider": "generic-chat-completion-api"
    }
  ]
}
```

### Key Features

- **model: inherit** - All droids inherit model from runtime selection
- **Knowledge DB Integration** - Context injected before execution
- **Persistent Output** - Results saved to `.claude/kln/droidExecute/`
- **Built-in Tools** - Read, Grep, Glob, Execute, WebSearch

---

## Version History

- **v3.0 (2025-12-10)**: Factory Droid integration, 8 specialist droids, droidExecute command
- **v2.0 (2025-12-08)**: Unified prompts, 3 categories, MCP tools, custom model selection
- **v1.0 (2025-12-03)**: Initial release, model specializations, knowledge system
