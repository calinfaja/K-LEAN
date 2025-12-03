---
name: asyncConsensus
description: "Run /sc:consensus (3 models) in a SEPARATE subagent - you can keep working!"
allowed-tools: Task
argument-hint: "[focus-prompt] — Runs 3 models in parallel in background subagent"
---

# Async Consensus Review (Tier 2P in Subagent)

Runs `/sc:consensus` (all 3 models) in a **separate subagent context**.
You can **continue working** while 3 models review in parallel.

**Arguments:** $ARGUMENTS

---

## Execute Now

Use the **Task tool** with:

**subagent_type:** `general-purpose`

**description:** `Async consensus review (3 models)`

**prompt:**
```
You are running a consensus review with 3 models in the background.

## Your Task

1. Gather context:
```bash
DIFF=$(git diff HEAD~1..HEAD 2>/dev/null | head -300)
FILES=$(git diff --name-only HEAD~1..HEAD 2>/dev/null)
echo "Context: $(echo "$DIFF" | wc -l) lines of diff"
```

2. Run 3 parallel curl requests:
```bash
FOCUS="$ARGUMENTS"

# QWEN
mkdir -p /tmp/claude-reviews

curl -s http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"coding-qwen","messages":[{"role":"system","content":"Code reviewer for bugs."},{"role":"user","content":"Review for: '$FOCUS'\n\n'$DIFF'"}],"max_tokens":1500}' \
  > /tmp/claude-reviews/consensus_qwen.json &

# DEEPSEEK
curl -s http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"architecture-deepseek","messages":[{"role":"system","content":"Architecture reviewer."},{"role":"user","content":"Review for: '$FOCUS'\n\n'$DIFF'"}],"max_tokens":1500}' \
  > /tmp/claude-reviews/consensus_deepseek.json &

# GLM
curl -s http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"tools-glm","messages":[{"role":"system","content":"Standards reviewer."},{"role":"user","content":"Review for: '$FOCUS'\n\n'$DIFF'"}],"max_tokens":1500}' \
  > /tmp/claude-reviews/consensus_glm.json &

wait
```

3. Parse all 3 responses and analyze consensus:
   - Issues found by ALL 3 = HIGH CONFIDENCE
   - Issues found by 2/3 = MEDIUM CONFIDENCE
   - Issues found by 1/3 = LOW CONFIDENCE

4. Return consensus summary:
```
═══════════════════════════════════════════════════════════════
ASYNC CONSENSUS COMPLETE (Tier 2P - 3 Models)
═══════════════════════════════════════════════════════════════
📊 Focus: $ARGUMENTS

## Individual Verdicts
| Model | Grade | Risk | Verdict |
|-------|-------|------|---------|
| QWEN | [A-F] | [level] | [verdict] |
| DEEPSEEK | [A-F] | [level] | [verdict] |
| GLM | [A-F] | [level] | [verdict] |

## Consensus Analysis

### HIGH CONFIDENCE (All 3 agree)
- [Issue that all 3 found]

### MEDIUM CONFIDENCE (2/3 agree)
- [Issue that 2 found]

### LOW CONFIDENCE (1/3 found - investigate)
- [Issue only 1 found]

## Final Consensus
📊 Average Grade: [X]
⚠️  Risk Level: [level]
✅ Verdict: [APPROVE/REQUEST_CHANGES]
═══════════════════════════════════════════════════════════════
```

FOCUS: $ARGUMENTS
```
