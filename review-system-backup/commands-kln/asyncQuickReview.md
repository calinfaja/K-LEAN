---
name: asyncReview
description: "Run /kln:quickReview in a SEPARATE subagent - you can keep working!"
allowed-tools: Task
argument-hint: "[model] [focus] — Runs in background subagent"
---

# Async Review (Tier 1 in Subagent)

Runs `/kln:quickReview` in a **separate subagent context**.
You can **continue working** while the review runs.

**Arguments:** $ARGUMENTS

---

## Execute Now

Use the **Task tool** with:

**subagent_type:** `general-purpose`

**model:** `haiku`

**description:** `Async code review`

**prompt:**
```
You are running a quick code review in the background.

## Your Task

1. Parse arguments: "$ARGUMENTS"
   - First word if qwen/deepseek/glm = model (default: qwen)
   - Rest = focus prompt

2. Gather context:
```bash
echo "=== GIT DIFF ===" && git diff HEAD~1..HEAD 2>/dev/null | head -200
echo "=== FILES CHANGED ===" && git diff --name-only HEAD~1..HEAD 2>/dev/null
```

3. Call LiteLLM API:
```bash
MODEL="qwen3-coder"  # or deepseek-v3-thinking or glm-4.6-thinking based on selection
curl -s http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'$MODEL'",
    "messages": [
      {"role": "system", "content": "You are an expert embedded systems code reviewer."},
      {"role": "user", "content": "Review this code for: [FOCUS]\n\n[DIFF]"}
    ],
    "temperature": 0.3,
    "max_tokens": 2000
  }' | jq -r '.choices[0].message.content // .choices[0].message.reasoning_content'
```

4. Return CONCISE summary:
```
═══════════════════════════════════════
ASYNC REVIEW COMPLETE (Tier 1)
═══════════════════════════════════════
🤖 Model: [qwen/deepseek/glm]
📊 Grade: [A-F]
⚠️  Risk: [CRITICAL/HIGH/MEDIUM/LOW]
🔴 Critical: [count or "None"]
🟡 Warnings: [count]
✅ Verdict: [APPROVE/REQUEST_CHANGES]

Top Issues:
1. [Most important issue]
2. [Second issue]
3. [Third issue]
═══════════════════════════════════════
```

ARGUMENTS: $ARGUMENTS
```
