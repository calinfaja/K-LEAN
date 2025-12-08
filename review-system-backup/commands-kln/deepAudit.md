---
name: parallelDeepReview
description: "Run ALL 3 deep reviews (qwen, deepseek, glm) in PARALLEL with FULL TOOL ACCESS"
allowed-tools: Bash
argument-hint: "[focus-prompt] — Spawns 3 headless instances simultaneously"
---

# Parallel Deep Review - 3 Models, Full Tool Access, Simultaneous

Spawns **3 headless Claude instances** running different LiteLLM models **in parallel**.
Each instance has **FULL TOOL ACCESS** and can investigate independently.

**Arguments:** $ARGUMENTS

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│  /kln:deepAudit "security audit"                            │
│       │                                                             │
│       ├──► Headless #1: qwen3-coder ───────────┐                   │
│       │    • Full tool access                   │                   │
│       │    • Investigates bugs, memory          │   PARALLEL       │
│       │                                         │   EXECUTION      │
│       ├──► Headless #2: deepseek-v3-thinking ──┤   (2-5 min)      │
│       │    • Full tool access                   │                   │
│       │    • Investigates architecture          │                   │
│       │                                         │                   │
│       └──► Headless #3: glm-4.6-thinking ─────────────┘                   │
│            • Full tool access                                       │
│            • Investigates MISRA/standards                           │
│                                                                     │
│       All 3 complete → Compare findings                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Comparison with Other Commands

| Command | Models | Parallel | Tool Access | Time |
|---------|--------|----------|-------------|------|
| `/kln:quickReview` | 1 | N/A | ❌ None | 30s |
| `/kln:quickConsult` | 1 | N/A | ❌ None | 1min |
| `/kln:deepInspect` | 1 | N/A | ✅ Full | 3min |
| `/kln:quickCompare` | 3 | ✅ Yes | ❌ None | 1min |
| **`/kln:deepAudit`** | **3** | **✅ Yes** | **✅ Full** | **5min** |

---

## Warning

This command:
- Spawns 3 headless Claude processes
- Each runs for 2-5 minutes
- Uses significant system resources
- Temporarily modifies settings (restored automatically)

**Use for:** Pre-release audits, major merges, security reviews

---

## Instructions

### Step 1: Inform User

```
⚠️  PARALLEL DEEP REVIEW - Maximum Coverage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
This will spawn 3 headless Claude instances in parallel:
  • QWEN: Code quality, bugs, memory safety
  • DEEPSEEK: Architecture, design, coupling
  • GLM: Standards, MISRA compliance

Each has FULL TOOL ACCESS to investigate the codebase.
Expected time: 3-5 minutes (all run simultaneously)

Focus: $ARGUMENTS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Step 2: Execute Parallel Review

Run the parallel review script:

```bash
/home/calin/.claude/scripts/parallel-deep-review.sh "$ARGUMENTS" "$(pwd)"
```

### Step 3: Display Results

The script outputs all 3 reviews. After displaying, synthesize:

```markdown
## Parallel Deep Review Summary

### Reviewer Verdicts
| Reviewer | Grade | Risk | Verdict |
|----------|-------|------|---------|
| QWEN | [A-F] | [level] | [APPROVE/REQUEST_CHANGES] |
| DEEPSEEK | [A-F] | [level] | [APPROVE/REQUEST_CHANGES] |
| GLM | [A-F] | [level] | [APPROVE/REQUEST_CHANGES] |

### Consensus Analysis
- **Unanimous Issues** (all 3 found): [list]
- **Majority Issues** (2/3 found): [list]
- **Single Reviewer Issues** (investigate): [list]

### Final Recommendation
Based on consensus: [APPROVE / REQUEST_CHANGES / NEEDS_DISCUSSION]
```

---

## Usage Examples

```bash
# Comprehensive pre-release audit
/kln:deepAudit Complete security and quality audit before v1.0 release

# Major refactor review
/kln:deepAudit Review the BLE stack refactor for issues

# Architecture validation
/kln:deepAudit Validate the new module structure
```

---

## From Terminal

```bash
# Run directly from bash
~/.claude/scripts/parallel-deep-review.sh "security audit" /path/to/project

# Or use the alias (after sourcing bashrc)
parallel-review "security audit"
```

---

## Output Files

Results are saved to:
- `/tmp/claude-reviews/review-qwen-[timestamp].txt`
- `/tmp/claude-reviews/review-deepseek-[timestamp].txt`
- `/tmp/claude-reviews/review-glm-[timestamp].txt`

Compare these files for detailed analysis:
```bash
ls -la /tmp/claude-reviews/
```
