---
name: rethink
description: "Extracts debugging context from conversation, then queries LiteLLM with contrarian techniques (inversion, assumption challenge, domain shift). Returns ranked novel ideas. Use when stuck 10+ minutes."
allowed-tools: Bash, Read, Grep, Glob
argument-hint: "[--models N|MODEL] [--async] [focus]"
---

# /kln:rethink - Break Out of Debugging Ruts

When you're stuck debugging and have tried multiple approaches without success, this command
gets fresh perspectives from external models using contrarian thinking techniques.

## When to Use

- Stuck on same issue for 10+ minutes
- Already tried obvious approaches without success
- Need "fresh eyes" from different thinking models
- Want ideas you probably dismissed or didn't consider

**NOT for:**
- Initial debugging (try standard approaches first)
- Code review → use `/kln:quick` or `/kln:agent`
- When you haven't tried anything yet

## How It Works

1. **Claude auto-summarizes** the current conversation to extract:
   - What problem you're debugging
   - What approaches were tried
   - Why each approach failed
   - What assumptions you're making

2. **External model(s)** apply contrarian techniques:
   - **Inversion**: Look where you DIDN'T look
   - **Assumption Challenge**: What if X is wrong?
   - **Domain Shift**: Different expertise perspective
   - **Root Cause Reframe**: Is the symptom the real problem?

3. **Results ranked** by novelty and actionability (multi-model mode)

## Arguments

$ARGUMENTS

## Flags

- `--models, -n` - Number of models (default: 5) OR specific model name
- `--async, -a` - Run in background
- `--output, -o` - Output format: text (default), json

## Step 1: Extract Context (Claude does this)

Analyze this conversation and extract:

### PROBLEM
What specific issue is being debugged? Be precise about symptoms and error messages.

### TRIED
List ALL approaches/solutions attempted so far, including:
- Code changes made
- Debug commands run
- Theories explored

### FAILED
For each approach, WHY it didn't work or what it revealed.

### ASSUMPTIONS
What assumptions has the user made? These are prime targets for challenge.

---

## Step 2: Build Summary

Create a structured summary in this format:

```
DEBUGGING CONTEXT
=================
Problem: [1-2 sentence description of the issue]

What Was Tried:
1. [approach 1] → [result/why it failed]
2. [approach 2] → [result/why it failed]
3. [approach 3] → [result/why it failed]

Current Assumptions:
- [assumption 1]
- [assumption 2]
- [assumption 3]

User's Focus (if specified): [focus from arguments]
```

---

## Step 3: Call LiteLLM Models

```bash
# Parse arguments
ARGS="$ARGUMENTS"
MODEL_COUNT=5
MODEL=""
ASYNC=false
OUTPUT="text"
FOCUS=""

# Default model for single-model mode
DEFAULT_MODEL="deepseek-v3-thinking"

# If first arg is a number, use it as model count
# If first arg matches a model name, use single model
# Otherwise treat as focus

PYTHON=~/.local/share/pipx/venvs/kln-ai/bin/python
CORE=~/.claude/kln/klean_core.py

# Execute rethink
if [ "$ASYNC" = true ]; then
    LOG="/tmp/claude-reviews/rethink-$(date +%Y%m%d-%H%M%S).log"
    mkdir -p /tmp/claude-reviews
    nohup $PYTHON $CORE rethink $ARGS > "$LOG" 2>&1 &
    echo "Running in background. Log: $LOG"
else
    $PYTHON $CORE rethink $ARGS
fi
```

**IMPORTANT**: Before executing the bash command, you MUST:
1. Replace the context placeholder in the Python call with the actual extracted summary
2. Pass the summary via stdin or temp file

Actually, use this approach - write the context to a temp file:

```bash
# Write context summary to temp file
CONTEXT_FILE="/tmp/rethink-context-$$.txt"
cat > "$CONTEXT_FILE" << 'CONTEXT_EOF'
[INSERT EXTRACTED CONTEXT HERE]
CONTEXT_EOF

PYTHON=~/.local/share/pipx/venvs/kln-ai/bin/python
CORE=~/.claude/kln/klean_core.py

$PYTHON $CORE rethink --context-file "$CONTEXT_FILE" $ARGUMENTS

rm -f "$CONTEXT_FILE"
```

---

## Step 4: Display Results

For each idea returned, display:

```
═══════════════════════════════════════════════════════════════
FRESH PERSPECTIVE #N [Model: model-name]
═══════════════════════════════════════════════════════════════

**Approach**: [one-line description]

**Why You Probably Didn't Try This**:
[explanation of why this angle was likely overlooked]

**Why It Might Work**:
[contrarian reasoning - why this could succeed when others failed]

**First Step**:
[concrete, actionable command or action to test this approach]

───────────────────────────────────────────────────────────────
```

For multi-model mode, also show:

```
═══════════════════════════════════════════════════════════════
RANKING SUMMARY
═══════════════════════════════════════════════════════════════
Ideas ranked by: Novelty (different from tried) + Actionability

Top 3 Recommendations:
1. [approach] - from [model] - [why highly ranked]
2. [approach] - from [model] - [why ranked]
3. [approach] - from [model] - [why ranked]
═══════════════════════════════════════════════════════════════
```

---

## Examples

```bash
# Default: 5 models, auto-extract context
/kln:rethink

# Single model (deepseek by default for reasoning)
/kln:rethink --models deepseek

# Specific model
/kln:rethink --models qwen

# Different count
/kln:rethink --models 3

# With focus hint
/kln:rethink memory leak that persists after fix

# Async mode
/kln:rethink --async
```

---

## Model Discovery

Models are auto-discovered from LiteLLM. Use `kln model list` to see available models.

**Substring matching**: Type part of a model name and it will match:
- `deepseek` → matches `deepseek-v3-thinking` (prefers thinking models)
- `qwen` → matches `qwen3-coder`
- `glm` → matches `glm-4.6-thinking`

**Default**: `deepseek-v3-thinking` (best for reasoning tasks)

**Multi-model mode**: When using a number (e.g., `--models 5`), system auto-selects diverse models from all available.
