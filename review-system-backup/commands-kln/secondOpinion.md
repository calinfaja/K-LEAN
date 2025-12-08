---
name: secondOpinion
description: Get a second opinion from local LLM (qwen/deepseek/glm) with FULL context from current session
allowed-tools: Read, Bash, Grep, Glob, mcp__serena__list_memories, mcp__serena__read_memory
argument-hint: "[model] [question] — models: qwen (code), deepseek (architecture), glm (standards)"
---

# Second Opinion from Local LLM

Get a **comprehensive second opinion** from a local LLM model with full session context.
Uses LiteLLM directly (not through Claude Code) so your primary session stays on native Claude.

**Arguments:** $ARGUMENTS

---

## Why This Exists

- **Primary work:** Native Claude (Opus/Sonnet) - full power, MCP access
- **Second opinion:** Local LLM via LiteLLM - independent review with full context

---

## Model Selection

| Alias | Model | Best For |
|-------|-------|----------|
| `qwen` | qwen3-coder | Code quality, bugs, memory safety |
| `deepseek` | deepseek-v3-thinking | Architecture, design decisions |
| `glm` | glm-4.6-thinking | Standards, MISRA, compliance |

**Default:** `qwen`

---

## Step 1: Parse Arguments

From $ARGUMENTS:
- **Model**: First word if `qwen`/`deepseek`/`glm`, else default to `qwen`
- **Question**: The rest (what you want reviewed/answered)

---

## Step 2: Gather COMPREHENSIVE Context

**This is the key difference from /kln:review - we gather EVERYTHING relevant.**

### 2.1 Git Context
```bash
echo "=== GIT DIFF (last 3 commits) ==="
git diff HEAD~3..HEAD 2>/dev/null | head -300

echo "=== FILES CHANGED ==="
git diff --name-only HEAD~3..HEAD 2>/dev/null

echo "=== RECENT COMMITS ==="
git log --oneline -5 2>/dev/null

echo "=== UNCOMMITTED CHANGES ==="
git diff --stat 2>/dev/null | head -20
```

### 2.2 Current Working Files
Identify files the user is likely working on:
```bash
echo "=== RECENTLY MODIFIED FILES ==="
find . -name "*.c" -o -name "*.h" -mmin -60 2>/dev/null | head -10
```

Read the **most recently changed files** (limit to avoid token overflow):
- Read each file (max 3 files, max 200 lines each)
- Focus on .c, .h files in embedded projects

### 2.3 Project Configuration
```bash
echo "=== PROJECT CONFIG ==="
cat prj.conf 2>/dev/null | head -50
echo "=== BOARD CONFIG ==="
grep "BOARD" prj.conf CMakeLists.txt 2>/dev/null | head -5
```

### 2.4 Serena Memories (Lessons Learned)
Check for relevant memories:
```
mcp__serena__list_memories
```

If there are `review-*.md` files, read the most recent one for context.

### 2.5 Session Context
The user's **question** in $ARGUMENTS tells you what they're trying to achieve.
Include this prominently in the context.

---

## Step 3: Build the Second Opinion Request

### System Prompt (Model-Specific)

**QWEN (qwen3-coder):**
```
You are an independent code reviewer providing a SECOND OPINION on embedded systems code.
You are reviewing work done by another AI (Claude). Be constructive but thorough.

CONTEXT: Zephyr RTOS / nRF5340 embedded development

YOUR ROLE:
- Catch issues the primary AI might have missed
- Challenge assumptions
- Verify memory safety, error handling, edge cases
- Provide specific, actionable feedback

OUTPUT FORMAT:
## Second Opinion Summary
[2-3 sentences: Do you agree with the approach? Major concerns?]

## Agreement Points
- [What looks good/correct]

## Concerns & Challenges
| Severity | Concern | Why It Matters | Suggestion |
|----------|---------|----------------|------------|
| HIGH/MED/LOW | [issue] | [impact] | [fix] |

## Risk Assessment
- Overall Risk: [CRITICAL/HIGH/MEDIUM/LOW]
- Confidence in Current Approach: [HIGH/MEDIUM/LOW]

## Alternative Approaches
[If you would do something differently, explain why]

## Final Verdict
[APPROVE / APPROVE_WITH_CHANGES / REQUEST_CHANGES / NEEDS_DISCUSSION]
```

**DEEPSEEK (deepseek-v3-thinking):**
```
You are an independent software architect providing a SECOND OPINION on system design.
You are reviewing architectural decisions made by another AI (Claude).

YOUR ROLE:
- Evaluate architectural soundness
- Challenge design decisions
- Consider scalability, maintainability, testability
- Identify potential technical debt

OUTPUT FORMAT:
## Architecture Assessment
[Is the design sound? Major structural concerns?]

## Design Decisions Review
| Decision | Assessment | Alternative |
|----------|------------|-------------|
| [decision made] | [GOOD/QUESTIONABLE/RISKY] | [alternative approach] |

## Coupling & Cohesion
- Module coupling: [LOOSE/MODERATE/TIGHT]
- Concerns: [specific issues]

## Future-Proofing
- Extensibility: [GOOD/FAIR/POOR]
- Testability: [GOOD/FAIR/POOR]

## Recommendation
[APPROVE / REFACTOR_SUGGESTED / MAJOR_REDESIGN_NEEDED]
```

**GLM (glm-4.6-thinking):**
```
You are an independent compliance reviewer providing a SECOND OPINION on code standards.
You are reviewing code for MISRA-C and embedded best practices.

YOUR ROLE:
- Check MISRA-C:2012 compliance
- Verify coding standards
- Identify safety concerns
- Assess production readiness

OUTPUT FORMAT:
## Compliance Summary
- MISRA Violations: [count by severity]
- Standards Adherence: [GOOD/FAIR/POOR]

## Violations Found
| Rule | Severity | Location | Issue |
|------|----------|----------|-------|
| MISRA X.Y | MANDATORY/REQUIRED/ADVISORY | file:line | [description] |

## Safety Concerns
[Any safety-critical issues for embedded systems]

## Production Readiness
[READY / NEEDS_FIXES / NOT_READY]
```

### User Prompt Template

```
SECOND OPINION REQUEST
======================

QUESTION/FOCUS:
$USER_QUESTION

CONTEXT: I'm working on a Zephyr RTOS project for nRF5340. Another AI (Claude) has been helping me implement features. I want your independent assessment.

---

PROJECT CONFIGURATION:
$PROJECT_CONFIG

---

RECENT CODE CHANGES:
$GIT_DIFF

---

FILES BEING WORKED ON:
$FILE_CONTENTS

---

PREVIOUS LESSONS LEARNED:
$SERENA_MEMORIES

---

Please provide your SECOND OPINION following the output format specified.
Be thorough but constructive. If you disagree with the approach, explain why and suggest alternatives.
```

---

## Step 4: Call LiteLLM

```bash
MODEL="qwen3-coder"  # or deepseek-v3-thinking / glm-4.6-thinking

# Build the full context (Claude should construct this from gathered data)
CONTEXT="[CONSTRUCTED FROM STEPS ABOVE]"

curl -s http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'$MODEL'",
    "messages": [
      {"role": "system", "content": "[SYSTEM_PROMPT]"},
      {"role": "user", "content": "'"$CONTEXT"'"}
    ],
    "temperature": 0.4,
    "max_tokens": 4000
  }' | jq -r '.choices[0].message.content // .choices[0].message.reasoning_content'
```

---

## Step 5: Present Results

Show the full second opinion to the user.

Summarize at the end:
```
═══════════════════════════════════════════════════════════════
SECOND OPINION COMPLETE
═══════════════════════════════════════════════════════════════
🤖 Model: [qwen/deepseek/glm]
📊 Verdict: [APPROVE/APPROVE_WITH_CHANGES/REQUEST_CHANGES]
⚠️  Concerns Raised: [count]
✅ Agreement Points: [count]
═══════════════════════════════════════════════════════════════
```

---

## Usage Examples

```bash
# Quick code review second opinion
/kln:secondOpinion qwen Is this implementation memory-safe?

# Architecture decision review
/kln:secondOpinion deepseek Is this module structure correct for BLE + Crypto?

# Compliance check
/kln:secondOpinion glm Check MISRA compliance before merge

# Default (qwen) with open question
/kln:secondOpinion Should I use static allocation here or k_malloc?
```

---

## Key Benefits

1. **Full Context**: Not just git diff, but files, config, memories
2. **Independent Review**: Different model = different perspective
3. **Native Claude Primary**: Your main session stays on powerful Claude
4. **Structured Output**: Clear verdict, not just text dump
