---
name: consensus
description: "Run ALL 3 models (qwen, deepseek, glm) in PARALLEL and compare their reviews"
allowed-tools: Bash, Read, Grep
argument-hint: "[focus-prompt] — Runs qwen, deepseek, AND glm simultaneously"
---

# Consensus Review - All 3 Models in Parallel

Runs **qwen**, **deepseek**, and **glm** reviews **simultaneously** via parallel curl calls.
Compares their findings to identify consensus and disagreements.

**Arguments:** $ARGUMENTS

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────────┐
│  /sc:consensus "security audit"                                     │
│       │                                                             │
│       ├──► coding-qwen ────────┐                                   │
│       │    (bugs, memory)      │                                   │
│       │                        │                                   │
│       ├──► architecture-deepseek ──► PARALLEL                      │
│       │    (design, coupling)  │     EXECUTION                     │
│       │                        │                                   │
│       └──► tools-glm ──────────┘                                   │
│            (MISRA, standards)                                       │
│                                                                     │
│       All 3 return simultaneously                                   │
│                    │                                                │
│                    ▼                                                │
│       COMPARE & SYNTHESIZE                                          │
│       • Issues found by ALL 3 = HIGH CONFIDENCE                    │
│       • Issues found by 2/3 = MEDIUM CONFIDENCE                    │
│       • Issues found by 1/3 = LOW CONFIDENCE (review manually)     │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Gather Context

```bash
# Get diff and file list
DIFF=$(git diff HEAD~1..HEAD 2>/dev/null | head -300)
FILES=$(git diff --name-only HEAD~1..HEAD 2>/dev/null)
echo "Context gathered: $(echo "$DIFF" | wc -l) lines of diff"
```

---

## Step 2: Run Parallel Reviews

Execute this bash script to run all 3 models in parallel:

```bash
#!/bin/bash
FOCUS="$ARGUMENTS"
DIFF=$(git diff HEAD~1..HEAD 2>/dev/null | head -300)

# Common review prompt
REVIEW_PROMPT="Review this code for: $FOCUS

CODE CHANGES:
$DIFF

Provide:
1. Grade (A-F)
2. Risk Level (CRITICAL/HIGH/MEDIUM/LOW)
3. Top 3 Critical Issues (if any)
4. Top 3 Warnings
5. Verdict (APPROVE/REQUEST_CHANGES)"

# Run all 3 in parallel using background processes
echo "Starting parallel reviews..."
mkdir -p /tmp/claude-reviews

# QWEN (code quality)
curl -s http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"coding-qwen\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"You are a code reviewer focused on bugs and memory safety.\"},
      {\"role\": \"user\", \"content\": $(echo "$REVIEW_PROMPT" | jq -Rs .)}
    ],
    \"temperature\": 0.3,
    \"max_tokens\": 1500
  }" > /tmp/claude-reviews/review_qwen.json &
PID_QWEN=$!

# DEEPSEEK (architecture)
curl -s http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"architecture-deepseek\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"You are an architect focused on design and coupling.\"},
      {\"role\": \"user\", \"content\": $(echo "$REVIEW_PROMPT" | jq -Rs .)}
    ],
    \"temperature\": 0.3,
    \"max_tokens\": 1500
  }" > /tmp/claude-reviews/review_deepseek.json &
PID_DEEPSEEK=$!

# GLM (standards)
curl -s http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"tools-glm\",
    \"messages\": [
      {\"role\": \"system\", \"content\": \"You are a compliance reviewer focused on MISRA and standards.\"},
      {\"role\": \"user\", \"content\": $(echo "$REVIEW_PROMPT" | jq -Rs .)}
    ],
    \"temperature\": 0.3,
    \"max_tokens\": 1500
  }" > /tmp/claude-reviews/review_glm.json &
PID_GLM=$!

# Wait for all to complete
echo "Waiting for all reviews to complete..."
wait $PID_QWEN $PID_DEEPSEEK $PID_GLM

echo "All reviews complete!"
```

---

## Step 3: Display Individual Results

After the parallel execution, read and display each result:

```bash
echo "═══════════════════════════════════════════════════════════════"
echo "QWEN (Code Quality)"
echo "═══════════════════════════════════════════════════════════════"
cat /tmp/claude-reviews/review_qwen.json | jq -r '.choices[0].message.content // .choices[0].message.reasoning_content // "Error"'

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "DEEPSEEK (Architecture)"
echo "═══════════════════════════════════════════════════════════════"
cat /tmp/claude-reviews/review_deepseek.json | jq -r '.choices[0].message.content // .choices[0].message.reasoning_content // "Error"'

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "GLM (Standards)"
echo "═══════════════════════════════════════════════════════════════"
cat /tmp/claude-reviews/review_glm.json | jq -r '.choices[0].message.content // .choices[0].message.reasoning_content // "Error"'
```

---

## Step 4: Synthesize Consensus

After showing individual results, analyze and synthesize:

**Look for:**
- Issues mentioned by ALL 3 models → **HIGH CONFIDENCE** (definitely fix)
- Issues mentioned by 2 models → **MEDIUM CONFIDENCE** (likely fix)
- Issues mentioned by only 1 model → **LOW CONFIDENCE** (investigate)

**Create a consensus summary:**

```markdown
## Consensus Summary

### HIGH CONFIDENCE (All 3 agree)
| Issue | Qwen | DeepSeek | GLM |
|-------|------|----------|-----|
| [issue] | ✅ | ✅ | ✅ |

### MEDIUM CONFIDENCE (2/3 agree)
| Issue | Qwen | DeepSeek | GLM |
|-------|------|----------|-----|
| [issue] | ✅ | ✅ | ❌ |

### LOW CONFIDENCE (Only 1 found)
| Issue | Found By | Action |
|-------|----------|--------|
| [issue] | [model] | Investigate |

### Grade Consensus
| Model | Grade | Risk |
|-------|-------|------|
| Qwen | [A-F] | [level] |
| DeepSeek | [A-F] | [level] |
| GLM | [A-F] | [level] |
| **AVERAGE** | **[X]** | **[level]** |

### Final Verdict
[APPROVE / REQUEST_CHANGES based on consensus]
```

---

## Usage

```bash
# Run consensus review
/sc:consensus security audit focusing on memory safety

# Specific focus areas
/sc:consensus check buffer handling and error paths
/sc:consensus architecture review before refactor
/sc:consensus pre-release compliance check
```

---

## Benefits

1. **Speed**: All 3 run in parallel (same total time as 1 review)
2. **Coverage**: Different models catch different issues
3. **Confidence**: Consensus = higher confidence in findings
4. **No blind spots**: What one model misses, another catches
