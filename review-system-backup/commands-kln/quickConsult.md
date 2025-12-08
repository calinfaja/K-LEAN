---
name: quickConsult
description: Get a second opinion from local LLM with full session context
allowed-tools: Read, Bash, Grep, Glob, mcp__serena__list_memories, mcp__serena__read_memory
argument-hint: "[model] [question] — models: qwen, deepseek, kimi, glm, minimax, hermes"
---

# Quick Consult - Second Opinion (API)

Get an **independent second opinion** from a local LLM model.
Different from review - this is for **challenging decisions and approaches**.

**Arguments:** $ARGUMENTS

---

## Review vs Consult

| Command | Purpose | Output |
|---------|---------|--------|
| `/kln:quickReview` | Find issues in code | Grade, Issues, Risk |
| **`/kln:quickConsult`** | **Challenge decisions** | **Verdict, Alternatives** |

---

## Model Selection

| Alias | Model |
|-------|-------|
| `qwen` | qwen3-coder |
| `deepseek` | deepseek-v3-thinking |
| `kimi` | kimi-k2-thinking |
| `glm` | glm-4.6-thinking |
| `minimax` | minimax-m2 |
| `hermes` | hermes-4-70b |

**Default:** `qwen` if no model specified

---

## Step 1: Parse Arguments

From $ARGUMENTS:
- **Model**: First word if it matches a model alias, else default to `qwen`
- **Question**: Everything after the model

Examples:
- `qwen Is this the right approach for BLE pairing?`
- `deepseek Should I use static allocation here?`
- `Is this architecture scalable?` → model=qwen (default)

---

## Step 2: Gather COMPREHENSIVE Context

This command gathers MORE context than quickReview:

```bash
echo "=== GIT DIFF (last 3 commits) ==="
git diff HEAD~3..HEAD 2>/dev/null | head -300

echo "=== FILES CHANGED ==="
git diff --name-only HEAD~3..HEAD 2>/dev/null

echo "=== RECENT COMMITS ==="
git log --oneline -5 2>/dev/null

echo "=== UNCOMMITTED CHANGES ==="
git diff --stat 2>/dev/null | head -20

echo "=== PROJECT CONFIG ==="
cat prj.conf 2>/dev/null | head -50
```

Also read recently modified files (max 3 files, max 200 lines each).

Check Serena memories for relevant past decisions:
```
mcp__serena__list_memories
```

---

## Step 3: Build Consult Request

### System Prompt (UNIFIED - Same for ALL models)

```
You are an independent embedded systems expert providing a SECOND OPINION.
You are reviewing work and decisions made by another engineer.

YOUR ROLE:
- Evaluate the approach/decision objectively
- Challenge assumptions - what might be wrong?
- Consider alternatives that may have been missed
- Identify risks not yet considered
- Be honest, not just agreeable

ANALYSIS AREAS:
## CORRECTNESS
- Is the logic sound? Edge cases covered?
- Will this work under all conditions?

## TRADE-OFFS
- What are the pros/cons of this approach?
- What alternatives exist?

## RISKS
- What could go wrong?
- What assumptions might be invalid?

## EMBEDDED CONSTRAINTS
- Memory/resource implications?
- Timing/performance concerns?
- Hardware interaction issues?

## MAINTAINABILITY
- Will this be easy to understand/modify later?
- Is it testable?
```

### User Prompt Template

```
SECOND OPINION REQUEST
======================

QUESTION:
[USER_QUESTION]

CONTEXT:
I'm working on an embedded systems project. Another AI (Claude) has been helping me. I want your independent assessment.

PROJECT CONFIG:
[PROJECT_CONFIG]

RECENT CHANGES:
[GIT_DIFF]

FILES BEING WORKED ON:
[FILE_CONTENTS]

PREVIOUS DECISIONS:
[SERENA_MEMORIES_IF_RELEVANT]

---

Provide your SECOND OPINION:

## Assessment
[2-3 sentences: Do you agree? Major concerns?]

## Agreement Points
- [What looks correct/good]

## Concerns
| Severity | Concern | Why It Matters | Suggestion |
|----------|---------|----------------|------------|

## Alternatives
| Alternative | Pros | Cons |
|-------------|------|------|

## Risk Assessment
- Overall Risk: [CRITICAL/HIGH/MEDIUM/LOW]
- Confidence in Current Approach: [HIGH/MEDIUM/LOW]

## Verdict
[AGREE / AGREE_WITH_RESERVATIONS / DISAGREE / NEEDS_MORE_INFO]

## Recommendation
[Concrete next steps]
```

---

## Step 4: Call LiteLLM API

```bash
MODEL="[mapped-model-name]"

curl -s http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "'$MODEL'",
    "messages": [
      {"role": "system", "content": "[SYSTEM_PROMPT]"},
      {"role": "user", "content": "[USER_PROMPT_WITH_CONTEXT]"}
    ],
    "temperature": 0.4,
    "max_tokens": 4000
  }' | jq -r '.choices[0].message.content // .choices[0].message.reasoning_content'
```

---

## Step 5: Display Results

Show the full opinion, then summarize:

```
═══════════════════════════════════════════════════════════════
SECOND OPINION COMPLETE
═══════════════════════════════════════════════════════════════
Model: [model]
Verdict: [AGREE/AGREE_WITH_RESERVATIONS/DISAGREE]
Risk: [level]
Concerns: [count]
═══════════════════════════════════════════════════════════════
```

---

## Usage

```bash
# Architecture question
/kln:quickConsult deepseek Is this module structure correct for BLE + Crypto?

# Implementation decision
/kln:quickConsult qwen Should I use static allocation or k_malloc here?

# Design review
/kln:quickConsult kimi Is this state machine approach scalable?

# Default model
/kln:quickConsult Is this error handling pattern correct?
```

---

## Key Differences from quickReview

| Aspect | quickReview | quickConsult |
|--------|-------------|--------------|
| Purpose | Find bugs/issues | Challenge decisions |
| Context | Recent diff only | Full session context |
| Output | Grade + Issues | Verdict + Alternatives |
| Tone | Auditor | Peer reviewer |
