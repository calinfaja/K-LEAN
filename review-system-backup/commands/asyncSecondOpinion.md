---
name: asyncSecondOpinion
description: "Run /sc:secondOpinion in a SEPARATE subagent - you can keep working!"
allowed-tools: Task
argument-hint: "[model] [question] — Runs in background subagent with full context"
---

# Async Second Opinion (Tier 2 in Subagent)

Runs `/sc:secondOpinion` in a **separate subagent context**.
Gathers FULL context and gets independent review while you keep working.

**Arguments:** $ARGUMENTS

---

## Execute Now

Use the **Task tool** with:

**subagent_type:** `general-purpose`

**description:** `Async second opinion review`

**prompt:**
```
You are getting a second opinion from a local LLM in the background.

## Your Task

1. Parse arguments: "$ARGUMENTS"
   - First word if qwen/deepseek/glm = model (default: qwen)
   - Rest = question/focus

2. Gather COMPREHENSIVE context:
```bash
echo "=== GIT DIFF (3 commits) ===" && git diff HEAD~3..HEAD 2>/dev/null | head -300
echo "=== FILES CHANGED ===" && git diff --name-only HEAD~3..HEAD 2>/dev/null
echo "=== RECENT COMMITS ===" && git log --oneline -5 2>/dev/null
echo "=== PROJECT CONFIG ===" && cat prj.conf 2>/dev/null | head -30
```

3. Read recently modified files (max 3 files, 100 lines each)

4. Check Serena memories if available:
   - Call mcp__serena__list_memories
   - Read relevant review-*.md files

5. Build full context and call LiteLLM:
```bash
MODEL="coding-qwen"  # based on selection
curl -s http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'$MODEL'",
    "messages": [
      {"role": "system", "content": "You are providing an independent SECOND OPINION on code. Be thorough but constructive."},
      {"role": "user", "content": "[FULL CONTEXT + QUESTION]"}
    ],
    "temperature": 0.4,
    "max_tokens": 3000
  }' | jq -r '.choices[0].message.content // .choices[0].message.reasoning_content'
```

6. Return summary:
```
═══════════════════════════════════════════════════
ASYNC SECOND OPINION COMPLETE (Tier 2)
═══════════════════════════════════════════════════
🤖 Model: [qwen/deepseek/glm]
❓ Question: [user's question]

📊 Verdict: [APPROVE/APPROVE_WITH_CHANGES/REQUEST_CHANGES]
⚠️  Risk: [CRITICAL/HIGH/MEDIUM/LOW]
🎯 Confidence: [HIGH/MEDIUM/LOW]

## Agreement Points
- [What looks good]

## Concerns Raised
| Severity | Concern |
|----------|---------|
| [HIGH/MED/LOW] | [concern] |

## Recommendation
[1-2 sentence recommendation]
═══════════════════════════════════════════════════
```

ARGUMENTS: $ARGUMENTS
```
