# K-LEAN System Summary

**K-LEAN** = Knowledge-Leveraged Engineering Analysis Network

Last Updated: 2025-12-10

---

## System Overview

K-LEAN is a multi-model code review and knowledge capture system for Claude Code, designed for embedded systems development with a focus on ARM Cortex-M, C, Rust, and Linux.

### Three Execution Methods

| Method | Tools | Time | Use Case |
|--------|-------|------|----------|
| **API** | None | ~30s | Quick checks, fast feedback |
| **CLI** | Full MCP | ~3-5min | Deep analysis, comprehensive audits |
| **DROID** | Built-in | ~30s-1min | Fast agentic reviews with file access |

---

## Components

### 1. LiteLLM Proxy (localhost:4000)

6 models available via NanoGPT:

| Model | Full Name | Notes |
|-------|-----------|-------|
| qwen | qwen3-coder | Default, best for code |
| deepseek | deepseek-v3-thinking | Architecture focus |
| kimi | kimi-k2-thinking | Planning focus |
| glm | glm-4.6-thinking | Standards compliance |
| minimax | minimax-m2 | Research focus |
| hermes | hermes-4-70b | Scripting focus |

### 2. Slash Commands (21 total)

**Review Commands:**
- `/kln:quickReview` - Fast single-model API review
- `/kln:quickCompare` - 3-model API comparison
- `/kln:deepInspect` - Thorough CLI review with tools
- `/kln:deepAudit` - 3-model CLI audit

**Droid Commands:**
- `/kln:droid` - Fast agentic review
- `/kln:droidAudit` - 3-droid parallel review
- `/kln:droidExecute` - Specialized droid execution

**Consult Commands:**
- `/kln:quickConsult` - Second opinion

**Document Commands:**
- `/kln:createReport` - Session documentation

**Async Commands:**
- `/kln:asyncQuickReview` - Background API review
- `/kln:asyncQuickCompare` - Background 3-model comparison
- `/kln:asyncDeepAudit` - Background 3-model audit
- `/kln:asyncDroid` - Background droid review
- `/kln:asyncQuickConsult` - Background consultation

### 3. Factory Droid System

8 specialist droids for domain-specific reviews:

| Droid | Lines | Expertise |
|-------|-------|-----------|
| **orchestrator** | 766 | Master coordinator, memory system, task delegation |
| **code-reviewer** | 201 | OWASP Top 10, SOLID principles, structured output |
| **security-auditor** | 90 | Vulnerability detection, auth flows, encryption |
| **debugger** | 100 | Root cause analysis, hypothesis testing |
| **arm-cortex-expert** | 265 | ARM Cortex-M, DMA, ISRs, cache coherency, FreeRTOS |
| **c-pro** | 36 | C99/C11, POSIX, memory management, MISRA |
| **rust-expert** | 38 | Ownership, lifetimes, no_std embedded |
| **performance-engineer** | 37 | Profiling, optimization, benchmarks |

### 4. Knowledge Database

Per-project semantic search using txtai embeddings:

- **Capture**: `GoodJob <url>` or auto-capture from WebFetch
- **Store**: `.knowledge-db/` with JSONL backup
- **Search**: `FindKnowledge <query>` (~30ms via server)
- **Integration**: Reviews query KB for relevant context

### 5. Hooks System

Automatic triggers in `~/.claude/settings.json`:

| Hook | Trigger | Action |
|------|---------|--------|
| UserPromptSubmit | All prompts | Keyword dispatch (healthcheck, GoodJob, etc.) |
| PostToolUse (Bash) | git commit | Update Serena memories, timeline |
| PostToolUse (WebFetch) | Web fetches | Auto-capture to knowledge DB |

---

## File Structure

```
~/.claude/
├── settings.json         # Hooks configuration
├── CLAUDE.md             # System instructions
├── mcp.json              # MCP servers
├── scripts/              # 30+ scripts
│   ├── quick-review.sh
│   ├── deep-review.sh
│   ├── droid-review.sh
│   ├── droid-execute.sh
│   ├── knowledge_db.py
│   └── ...
└── commands/
    └── kln/              # 21 slash commands
        ├── quickReview.md
        ├── droidExecute.md
        └── ...

~/.factory/
├── config.json           # Custom LiteLLM models
└── droids/               # 8 specialist droids
    ├── orchestrator.md
    ├── code-reviewer.md
    └── ...

~/.config/litellm/
├── config.yaml           # NanoGPT config
└── .env                  # API keys

{project}/
├── .knowledge-db/        # Per-project knowledge
├── .claude/kln/          # Review outputs
└── .serena/              # Serena memories
```

---

## Usage Patterns

### Quick Sanity Check
```
/kln:quickReview qwen check for obvious issues
```

### Pre-Commit Review
```
/kln:quickCompare review changes before commit
```

### Pre-Release Audit
```
/kln:deepAudit comprehensive security and quality audit
```

### Fast Agentic Review
```
/kln:droid qwen security check
```

### Specialized Domain Review
```
/kln:droidExecute glm arm-cortex-expert Review ISR priorities
/kln:droidExecute deepseek security-auditor Check authentication
/kln:droidExecute kimi rust-expert Audit unsafe blocks
```

### Background Review
```
/kln:asyncDeepAudit full review
# Keep coding while review runs
```

### Knowledge Capture
```
GoodJob https://docs.nordicsemi.com/ble focus on power management
SaveThis BLE scanning drains battery - use passive scanning
FindKnowledge BLE power
```

---

## Performance Benchmarks

| Command | Method | Time | Grade Quality |
|---------|--------|------|---------------|
| quickReview | API | ~30s | Good, no file access |
| quickCompare | API | ~60s | 3 perspectives, consensus |
| deepInspect | CLI | ~3min | Excellent, full tools |
| deepAudit | CLI | ~5min | Comprehensive, multi-model |
| droid | Droid | ~30s | Good, file access |
| droidAudit | Droid | ~1min | Good, parallel |
| droidExecute | Droid | ~30s-3min | Specialized expertise |

---

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/claudeAgentic.git
cd claudeAgentic/review-system-backup

# Full install (scripts, commands, hooks, knowledge-db, droids)
./install.sh --full

# Start LiteLLM proxy
~/.claude/scripts/litellm-start.sh

# Install Factory Droid CLI
curl -fsSL https://app.factory.ai/cli | sh
export FACTORY_API_KEY="fk-your-key"

# Verify
healthcheck
```

---

## Version History

- **v3.0 (2025-12-10)**: Factory Droid integration, 8 specialist droids, droidExecute command
- **v2.0 (2025-12-08)**: Unified prompts, 3 categories, MCP tools, custom model selection
- **v1.0 (2025-12-03)**: Initial release, model specializations, knowledge system
