---
name: asyncDeepReview
description: "Run parallelDeepReview in a SEPARATE subagent - you can keep working!"
allowed-tools: Task
argument-hint: "[focus-prompt] — Runs in background subagent, returns summary when done"
---

# Async Deep Review (Background Subagent)

Spawns `/kln:deepAudit` in a **separate subagent context**.
You can **continue working** while the review runs. Results come back when done.

**Arguments:** $ARGUMENTS

---

## How It Works

```
YOUR SESSION                         SUBAGENT (separate context)
     │                                     │
     │ ──► Task tool ────────────────────► │ Runs parallelDeepReview
     │                                     │ • 3 models in parallel
     │     YOU KEEP WORKING               │ • Full tool access
     │     (no waiting!)                   │ • Takes 5-10 minutes
     │                                     │
     │ ◄── Returns summary ◄────────────── │
     │                                     │
```

---

## Execute Now

Use the **Task tool** with:

**subagent_type:** `general-purpose`

**description:** `Async parallel deep review`

**prompt:**
```
You are running a parallel deep review in the background.

WORKING DIRECTORY: Determine from environment or use current directory.

## Your Task

Run the parallel deep review script:

```bash
~/.claude/scripts/parallel-deep-review.sh "$ARGUMENTS" "$(pwd)"
```

Wait for it to complete (may take 5-10 minutes).

## When Complete

Read the output files:
- /tmp/claude-reviews/review-qwen-*.txt
- /tmp/claude-reviews/review-deepseek-*.txt
- /tmp/claude-reviews/review-glm-*.txt

## Return Summary

Provide a CONCISE summary (not full output):

```
═══════════════════════════════════════════════════════════════
ASYNC DEEP REVIEW COMPLETE
═══════════════════════════════════════════════════════════════
⏱️  Duration: [X minutes]
📁  Review Focus: $ARGUMENTS

## Reviewer Verdicts
| Model | Grade | Risk | Verdict |
|-------|-------|------|---------|
| QWEN | [A-F] | [level] | [APPROVE/REQUEST_CHANGES] |
| DEEPSEEK | [A-F] | [level] | [verdict] |
| GLM | [A-F] | [level] | [verdict] |

## Critical Issues Found
[List any CRITICAL issues - or "None"]

## High Priority Warnings
[List HIGH priority items - or "None"]

## Consensus
[APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION]

## Output Files
- /tmp/claude-reviews/review-qwen-[timestamp].txt
- /tmp/claude-reviews/review-deepseek-[timestamp].txt
- /tmp/claude-reviews/review-glm-[timestamp].txt

Read these files for full details.
═══════════════════════════════════════════════════════════════
```

FOCUS: $ARGUMENTS
```

---

## Usage

```bash
# Start review and keep working
/kln:asyncDeepAudit Review the HKDF-SHA256 implementation

# You can now do other things...
# The subagent will return results when done
```

---

## Key Difference from /kln:deepAudit

| Command | Behavior |
|---------|----------|
| `/kln:deepAudit` | Blocks your session, polls output repeatedly |
| `/kln:asyncDeepAudit` | **Runs in subagent**, you keep working |

---

## Retrieving Full Results

The subagent returns a summary. For full details:

```bash
cat /tmp/claude-reviews/review-qwen-*.txt
cat /tmp/claude-reviews/review-deepseek-*.txt
cat /tmp/claude-reviews/review-glm-*.txt
```

Or use:
```bash
ls -la /tmp/claude-reviews/
```
