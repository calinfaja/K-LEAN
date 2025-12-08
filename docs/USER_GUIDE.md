# K-LEAN User Guide

How to use the K-LEAN review and knowledge system in your daily workflow.

---

## Quick Reference

| What You Type | What Happens |
|---------------|--------------|
| `healthcheck` | Check all 6 models are working |
| `/kln:quickReview qwen security` | Fast code review (30s) |
| `/kln:quickCompare check errors` | 3-model comparison (60s) |
| `/kln:deepAudit pre-release` | Full audit with tools (5min) |
| `/kln:quickConsult kimi Is this correct?` | Get second opinion |
| `GoodJob https://url` | Capture knowledge from URL |
| `SaveThis lesson learned` | Save a lesson |
| `FindKnowledge BLE optimization` | Search knowledge DB |
| `/kln:help` | Show all commands |

---

## Slash Commands

Slash commands start with `/kln:` and expand into full prompts.

### Review Commands (Find Issues)

**`/kln:quickReview <model> <focus>`**
- Fast single-model review via API
- Time: ~30 seconds
- No file access (just analyzes recent changes)

```
/kln:quickReview qwen check buffer handling
/kln:quickReview deepseek review architecture
/kln:quickReview glm MISRA compliance
```

**`/kln:quickCompare [models] <focus>`**
- 3 models review in parallel, compare findings
- Time: ~60 seconds
- Default models: qwen, kimi, glm

```
/kln:quickCompare security audit
/kln:quickCompare qwen,deepseek,glm check error handling
```

**`/kln:deepInspect <model> <focus>`**
- Thorough review with full tool access
- Time: ~3 minutes
- Can read files, grep code, check git (READ-ONLY)

```
/kln:deepInspect qwen full security audit of crypto module
/kln:deepInspect kimi analyze module dependencies
```

**`/kln:deepAudit [models] <focus>`**
- 3 models with full tool access, maximum coverage
- Time: ~5 minutes
- Best for pre-release reviews

```
/kln:deepAudit pre-release quality check
/kln:deepAudit kimi,hermes,minimax architecture review
```

### Consult Commands (Challenge Decisions)

**`/kln:quickConsult <model> <question>`**
- Get independent second opinion
- Challenges assumptions, suggests alternatives

```
/kln:quickConsult deepseek Is this state machine approach scalable?
/kln:quickConsult kimi Should I use static or dynamic allocation?
```

### Document Commands

**`/kln:createReport <title>`**
- Create session documentation
- Saves to Serena memories

```
/kln:createReport BLE Implementation Complete
/kln:createReport Fixed Crypto Memory Leak
```

---

## Keywords (Type in Prompt)

These keywords are intercepted by hooks and handled automatically.

### `healthcheck`

Check if all 6 models are working:

```
healthcheck
```

Output:
```
Model Health: ✅ qwen3-coder ✅ deepseek-v3-thinking ✅ glm-4.6-thinking ...
```

### `GoodJob <url> [instructions]`

Capture knowledge from a URL:

```
GoodJob https://docs.nordicsemi.com/ble
GoodJob https://example.com/api focus on authentication patterns
```

What happens:
1. Fetches the URL
2. Haiku extracts key knowledge
3. Stores in project's `.knowledge-db/`
4. You see: "📚 Capturing knowledge..."

### `SaveThis <lesson>`

Save a lesson learned:

```
SaveThis connection pooling improves PostgreSQL performance 10x
SaveThis always check return values from k_malloc
```

### `FindKnowledge <query>`

Search your knowledge database:

```
FindKnowledge BLE power optimization
FindKnowledge error handling patterns
```

Returns matching entries with relevance scores.

---

## Async Commands (Background)

Run reviews in background while you keep coding:

| Async Command | What It Runs |
|---------------|--------------|
| `/kln:asyncQuickReview qwen <focus>` | Single model API review |
| `/kln:asyncQuickCompare <focus>` | 3-model API comparison |
| `/kln:asyncQuickConsult kimi <question>` | Single model consultation |
| `/kln:asyncDeepAudit <focus>` | 3-model deep review with tools |

### Example Workflow

```
# Start a review in background
/kln:asyncDeepAudit security review

# Claude says: "🚀 Deep audit started. Results: /tmp/claude-reviews/..."

# Keep coding - the review runs in background

# Later, check results
cat /tmp/claude-reviews/*/deep-audit-latest.log
```

---

## Model Selection

### Available Models

| Alias | Full Name | Notes |
|-------|-----------|-------|
| `qwen` | qwen3-coder | Default for single-model |
| `deepseek` | deepseek-v3-thinking | Good for architecture |
| `kimi` | kimi-k2-thinking | Good for planning |
| `glm` | glm-4.6-thinking | Good for standards |
| `minimax` | minimax-m2 | Research focus |
| `hermes` | hermes-4-70b | Scripting focus |

### Defaults

- **Single-model commands**: `qwen` if not specified
- **Multi-model commands**: `qwen`, `kimi`, `glm` if not specified

### Custom Selection (Multi-Model)

Specify 3 models comma-separated:

```
/kln:quickCompare qwen,deepseek,glm security audit
/kln:deepAudit kimi,hermes,minimax architecture review
```

---

## What Gets Reviewed

All models review ALL of these areas (unified prompts):

| Area | What's Checked |
|------|----------------|
| **CORRECTNESS** | Logic errors, edge cases, algorithm correctness |
| **MEMORY SAFETY** | Buffer overflows, null pointers, leaks |
| **ERROR HANDLING** | Validation, propagation, resource cleanup |
| **CONCURRENCY** | Race conditions, ISR safety, shared data |
| **ARCHITECTURE** | Coupling, cohesion, API consistency |
| **HARDWARE** | I/O correctness, volatile usage, timing |
| **STANDARDS** | Coding style, MISRA guidelines |

Your focus = extra attention, not restriction.

---

## Output Formats

### Review Output

```
## Grade: B+
## Risk: MEDIUM

## Critical Issues
| # | File:Line | Issue | Fix |
|---|-----------|-------|-----|
| 1 | crypto.c:142 | Buffer overflow possible | Add bounds check |

## Warnings
...

## Verdict: REQUEST_CHANGES
```

### Consult Output

```
## Assessment
The approach is sound but has scalability concerns...

## Concerns
| Severity | Concern | Suggestion |
|----------|---------|------------|
| HIGH | Memory growth | Consider pooling |

## Alternatives
| Alternative | Pros | Cons |
|-------------|------|------|
| Static allocation | Predictable | Less flexible |

## Verdict: AGREE_WITH_RESERVATIONS
```

### Multi-Model Comparison

```
## Consensus Summary

### HIGH CONFIDENCE (All 3 found)
- Buffer overflow in crypto.c:142

### MEDIUM CONFIDENCE (2/3 found)
- Missing error check in ble.c:89

### LOW CONFIDENCE (1/3 found)
- Style inconsistency (investigate)

## Final Verdict: REQUEST_CHANGES
```

---

## Checking Results

### Session Output Directory

All results go to `/tmp/claude-reviews/{session-id}/`:

```bash
# List all sessions
ls /tmp/claude-reviews/

# List files in current session
ls /tmp/claude-reviews/2025-12-08-*/

# Read specific result
cat /tmp/claude-reviews/*/quick-review-qwen-latest.log
cat /tmp/claude-reviews/*/deep-audit-latest.log
```

### Or Ask Claude

```
show me the review results
what did the audit find?
```

---

## Workflows

### Quick Sanity Check

```
/kln:quickReview check for obvious issues
```

### Pre-Commit Review

```
/kln:quickCompare review changes before commit
```

### Pre-Release Audit

```
/kln:deepAudit comprehensive pre-release security and quality audit
```

### Background Review While Coding

```
/kln:asyncDeepAudit full review
# keep coding...
# check results when done
```

### Challenge a Decision

```
/kln:quickConsult deepseek Is this the right architecture for BLE + Crypto?
```

### Capture Research

```
# After finding useful documentation
GoodJob https://docs.zephyrproject.org/ble focus on power management

# Save a lesson
SaveThis BLE scanning drains battery - use passive scanning when possible

# Later, recall it
FindKnowledge BLE power
```

### Document Session

```
/kln:createReport BLE Power Optimization Complete
```

---

## Troubleshooting

### "LiteLLM proxy not running"

```bash
start-nano-proxy
# wait a few seconds
healthcheck
```

### Command not recognized

Make sure you're using the correct prefix:
- Slash commands: `/kln:quickReview` (with slash)
- Keywords: `healthcheck` (no slash, just type it)

### Review takes too long

- Use `quickReview` instead of `deepInspect` for faster results
- Use `asyncDeepAudit` to run in background

### No results found

```bash
# Check if results exist
ls /tmp/claude-reviews/

# Check log files for errors
cat /tmp/claude-reviews/*/*.log | tail -50
```
