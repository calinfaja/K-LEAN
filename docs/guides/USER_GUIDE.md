# K-LEAN User Guide

Complete reference for using K-LEAN in your daily workflow.

---

## Quick Reference

| Command | Description | Example |
|---------|-------------|---------|
| `/kln:quick` | Fast single-model review | `/kln:quick security` |
| `/kln:multi` | Multi-model consensus | `/kln:multi --models 5 architecture` |
| `/kln:deep` | Deep analysis with tools | `/kln:deep --async security audit` |
| `/kln:droid` | Specialist agent | `/kln:droid --role security check auth` |
| `/kln:rethink` | Fresh debugging perspectives | `/kln:rethink this bug` |
| `/kln:doc` | Create session documentation | `/kln:doc "Sprint Review"` |
| `/kln:remember` | Capture session knowledge | `/kln:remember` |
| `/kln:status` | System health | `/kln:status` |
| `/kln:help` | Command reference | `/kln:help` |
| `healthcheck` | Test all models | `healthcheck` |
| `SaveThis` | Save lesson learned | `SaveThis always validate input` |
| `FindKnowledge` | Search knowledge DB | `FindKnowledge authentication` |

---

## Slash Commands

### `/kln:quick` - Fast Review

Single-model review via API. Fast and lightweight.

**Usage:**
```
/kln:quick <focus>
/kln:quick --model <model> <focus>
```

**Examples:**
```
/kln:quick security audit
/kln:quick check error handling
/kln:quick --model deepseek-v3-thinking architecture review
```

**Time:** ~30 seconds

---

### `/kln:multi` - Consensus Review

Multiple models review in parallel, findings synthesized.

**Usage:**
```
/kln:multi <focus>
/kln:multi --models <count> <focus>
```

**Examples:**
```
/kln:multi security audit
/kln:multi --models 5 comprehensive review
/kln:multi architecture and error handling
```

**Flags:**
- `--models N` - Number of models (3-5, default: 3)
- `--output json|text` - Output format

**Time:** ~60 seconds

---

### `/kln:deep` - Deep Analysis

Full codebase analysis with tool access (read files, grep, git).

**Usage:**
```
/kln:deep <focus>
/kln:deep --async <focus>
```

**Examples:**
```
/kln:deep security audit all authentication code
/kln:deep --async full pre-release review
/kln:deep analyze dependencies and coupling
```

**Flags:**
- `--async` - Run in background
- `--output json|text` - Output format

**Time:** ~3 minutes

---

### `/kln:droid` - Specialist Agent

Invoke domain expert droids for specialized analysis.

**Usage:**
```
/kln:droid <task>
/kln:droid --role <droid> <task>
```

**Examples:**
```
/kln:droid security audit
/kln:droid --role security-auditor check authentication flow
/kln:droid --role performance-engineer analyze memory usage
/kln:droid --role rust-expert review unsafe blocks
```

**Available Droids:**

| Droid | Expertise |
|-------|-----------|
| `code-reviewer` | Code quality, SOLID, OWASP top 10 |
| `security-auditor` | Vulnerabilities, auth, encryption |
| `performance-engineer` | Profiling, optimization, memory |
| `debugger` | Root cause analysis, error tracing |
| `rust-expert` | Ownership, lifetimes, embedded Rust |
| `c-pro` | C99/C11, POSIX, memory management |
| `arm-cortex-expert` | ARM Cortex-M, DMA, ISRs, FreeRTOS |
| `orchestrator` | Multi-droid coordination |

**Time:** ~2 minutes

---

### `/kln:rethink` - Fresh Perspectives

When stuck on a bug, get alternative debugging approaches.

**Usage:**
```
/kln:rethink <problem>
```

**Examples:**
```
/kln:rethink this null pointer exception
/kln:rethink memory leak in connection pool
/kln:rethink why tests fail intermittently
```

**Time:** ~30 seconds

---

### `/kln:doc` - Session Documentation

Create documentation from current session.

**Usage:**
```
/kln:doc "<title>"
```

**Examples:**
```
/kln:doc "BLE Implementation Complete"
/kln:doc "Fixed Crypto Memory Leak"
/kln:doc "Sprint 12 Review"
```

---

### `/kln:remember` - Knowledge Capture

End-of-session capture of important insights.

**Usage:**
```
/kln:remember
```

Automatically extracts and saves key learnings from the session.

---

### `/kln:status` - System Status

Check health of all K-LEAN components.

**Usage:**
```
/kln:status
```

Shows:
- LiteLLM proxy status
- Model availability
- Knowledge DB status
- Service health

---

### `/kln:help` - Command Help

Show all available commands.

**Usage:**
```
/kln:help
```

---

## Keywords

Type these directly in the prompt (no slash prefix).

### `healthcheck`

Test all configured models:

```
healthcheck
```

Output:
```
Model Health: ✅ qwen3-coder ✅ deepseek-v3-thinking ✅ glm-4.6-thinking ...
```

### `SaveThis`

Save a lesson learned:

```
SaveThis always validate user input before database queries
SaveThis connection pooling requires explicit close() in Python
SaveThis BLE scanning drains battery - use passive mode
```

### `FindKnowledge`

Search your knowledge database:

```
FindKnowledge authentication patterns
FindKnowledge BLE power optimization
FindKnowledge error handling
```

Returns matching entries with relevance scores.

---

## Models

### Available Models

| Model | Alias | Strength |
|-------|-------|----------|
| `qwen3-coder` | qwen | Code quality, bugs |
| `deepseek-v3-thinking` | deepseek | Architecture, design |
| `glm-4.6-thinking` | glm | Standards, compliance |
| `minimax-m2` | minimax | Large context, research |
| `kimi-k2-thinking` | kimi | Planning, agents |
| `hermes-4-70b` | hermes | Scripting, automation |

### Check Model Status

```bash
k-lean models        # List all models
k-lean models --test # Test each model
healthcheck          # Quick health check
```

---

## Knowledge Database

Per-project semantic search for captured knowledge.

### Storage

Knowledge is stored in `.knowledge-db/` within each project:
- Semantic embeddings for fast search
- Timeline of all entries
- Automatic categorization

### Commands

```bash
# Save knowledge
SaveThis "lesson learned here"

# Search knowledge
FindKnowledge query terms

# Direct query (via server, ~30ms)
~/.claude/scripts/knowledge-query.sh "query"

# Timeline of entries
~/.claude/scripts/timeline-query.sh today
~/.claude/scripts/timeline-query.sh week
```

### Auto-Capture

Knowledge is automatically captured from:
- Web research (URLs you fetch)
- Lessons you save with `SaveThis`
- Post-commit analysis

---

## Background Execution

Run reviews in background while you continue coding.

### Async Flag

Add `--async` to any deep command:

```
/kln:deep --async comprehensive security audit
```

Claude responds:
```
🚀 Deep analysis started in background...
```

### Check Results

Results are saved to `/tmp/claude-reviews/`:

```bash
ls /tmp/claude-reviews/
cat /tmp/claude-reviews/*/latest.log
```

---

## Workflows

### Quick Sanity Check

Before committing small changes:

```
/kln:quick check for obvious issues
```

### Pre-Commit Review

Before committing significant changes:

```
/kln:multi security and quality review
```

### Pre-Release Audit

Before major releases:

```
/kln:deep --async comprehensive security and quality audit
```

### Debug Assistance

When stuck on a bug:

```
/kln:rethink this intermittent crash
/kln:droid --role debugger analyze this error
```

### Research Capture

When finding useful information:

```
# After reading documentation
SaveThis "PostgreSQL connection pooling requires min_connections >= 2"

# Later, recall it
FindKnowledge connection pooling
```

### End of Session

Before closing:

```
/kln:remember
```

---

## Output Formats

### Review Output

```markdown
## Grade: B+
## Risk: MEDIUM

## Critical Issues
| # | File:Line | Issue | Fix |
|---|-----------|-------|-----|
| 1 | crypto.c:142 | Buffer overflow | Add bounds check |

## Warnings
...

## Verdict: REQUEST_CHANGES
```

### Multi-Model Consensus

```markdown
## Consensus Summary

### HIGH CONFIDENCE (All models found)
- Buffer overflow in crypto.c:142

### MEDIUM CONFIDENCE (Majority found)
- Missing error check in ble.c:89

### LOW CONFIDENCE (One model found)
- Style inconsistency

## Final Verdict: REQUEST_CHANGES
```

---

## K-LEAN CLI

```bash
k-lean status     # Component status
k-lean doctor     # Diagnose issues
k-lean doctor -f  # Diagnose + auto-fix
k-lean start      # Start all services
k-lean stop       # Stop all services
k-lean models     # List models
k-lean test       # Run test suite
```

---

## Troubleshooting

### LiteLLM not running

```bash
k-lean doctor -f  # Auto-diagnose and fix
k-lean start      # Start services
```

### Model not responding

```bash
healthcheck       # Check all models
k-lean models     # See detailed status
```

### Slow responses

- Use `/kln:quick` instead of `/kln:deep`
- Use `--async` flag for background execution
- Check `k-lean status` for bottlenecks

### Knowledge not found

```bash
# Check if KB is running
k-lean status

# Initialize if needed (usually auto-initializes)
InitKB

# Search
FindKnowledge your query
```

### Command not recognized

```bash
/kln:help         # List all commands
```

---

## File Locations

| Type | Path |
|------|------|
| Scripts | `~/.claude/scripts/` |
| Commands | `~/.claude/commands/kln/` |
| Settings | `~/.claude/settings.json` |
| LiteLLM Config | `~/.config/litellm/config.yaml` |
| Droids | `~/.factory/droids/` |
| Review Output | `/tmp/claude-reviews/` |
| Knowledge | `.knowledge-db/` (per project) |
