# Implementation Plan: Auto-Detection of LiteLLM Models

## Overview

Replace hardcoded model names with dynamic discovery from LiteLLM API endpoint. Models configured in LiteLLM become automatically available - no script changes needed.

## Current State (Problems)

```
┌─────────────────────────────────────────────────────────────────┐
│  HARDCODED MODEL NAMES                                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  quick-review.sh:                                                │
│  ├── get_litellm_model() with case statement                    │
│  ├── qwen → qwen3-coder                                         │
│  ├── deepseek → deepseek-v3-thinking                            │
│  └── MODELS_PRIORITY="qwen3-coder deepseek-v3-thinking..."      │
│                                                                  │
│  consensus-review.sh:                                            │
│  └── for model in qwen3-coder deepseek-v3-thinking glm-4.6...   │
│                                                                  │
│  deep-review.sh:                                                 │
│  ├── get_model_info() case statement                            │
│  └── MODELS_PRIORITY="qwen3-coder kimi-k2-thinking..."          │
│                                                                  │
│  parallel-deep-review.sh:                                        │
│  └── for model in qwen3-coder kimi-k2-thinking glm-4.6...       │
│                                                                  │
│  PROBLEM: Add/remove model in LiteLLM → Edit 4+ scripts         │
└─────────────────────────────────────────────────────────────────┘
```

## Target State (Solution)

```
┌─────────────────────────────────────────────────────────────────┐
│  DYNAMIC MODEL DISCOVERY                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Single Source of Truth:                                         │
│  └── curl http://localhost:4000/v1/models | jq '.data[].id'     │
│                                                                  │
│  Scripts Use:                                                    │
│  ├── get-models.sh         → List all from API                  │
│  ├── get-healthy-models.sh → First N healthy                    │
│  └── validate-model.sh     → Check if name valid                │
│                                                                  │
│  User Experience:                                                │
│  ├── /kln:quickReview qwen3-coder security    (exact name)      │
│  ├── /kln:quickCompare security               (auto 5 models)   │
│  └── /kln:models                              (list available)  │
│                                                                  │
│  BENEFIT: Add/remove model in LiteLLM → Automatically works     │
└─────────────────────────────────────────────────────────────────┘
```

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Model source | API endpoint only | Always accurate to running instance |
| Aliases | Removed | Use exact LiteLLM model names |
| quickCompare models | First 5 healthy | More perspectives, API calls are cheap |
| asyncDeepAudit models | First 3 healthy | Headless instances are resource-heavy |
| Invalid model | Fail with list | Show available models, let user retry |
| Unavailable model | Fail with list | Same behavior, prompt happens in conversation |

## Implementation Phases

### Phase 1: Helper Scripts

#### 1.1 `get-models.sh`
```bash
#!/bin/bash
# Returns all models from LiteLLM API (sorted)
# Usage: get-models.sh
# Exit 1 if LiteLLM not running

LITELLM_URL="${LITELLM_URL:-http://localhost:4000}"

RESPONSE=$(curl -s --max-time 5 "$LITELLM_URL/v1/models" 2>/dev/null)

if [ $? -ne 0 ] || [ -z "$RESPONSE" ]; then
    echo "ERROR: LiteLLM not running at $LITELLM_URL" >&2
    exit 1
fi

echo "$RESPONSE" | jq -r '.data[].id' | sort
```

#### 1.2 `get-healthy-models.sh`
```bash
#!/bin/bash
# Returns first N healthy models
# Usage: get-healthy-models.sh [count]
# Default count: 5

COUNT="${1:-5}"
SCRIPTS_DIR="$(dirname "$0")"

HEALTHY=()
while IFS= read -r model; do
    if "$SCRIPTS_DIR/health-check-model.sh" "$model" 2>/dev/null; then
        HEALTHY+=("$model")
        [ ${#HEALTHY[@]} -ge "$COUNT" ] && break
    fi
done < <("$SCRIPTS_DIR/get-models.sh")

if [ ${#HEALTHY[@]} -eq 0 ]; then
    echo "ERROR: No healthy models found" >&2
    exit 1
fi

printf '%s\n' "${HEALTHY[@]}"
```

#### 1.3 `health-check-model.sh`
```bash
#!/bin/bash
# Check if a specific model is healthy
# Usage: health-check-model.sh <model-name>
# Exit 0 if healthy, 1 if not

MODEL="$1"

if [ -z "$MODEL" ]; then
    echo "Usage: health-check-model.sh <model-name>" >&2
    exit 1
fi

curl -s --max-time 5 http://localhost:4000/chat/completions \
    -H "Content-Type: application/json" \
    -d "{\"model\": \"$MODEL\", \"messages\": [{\"role\": \"user\", \"content\": \"hi\"}], \"max_tokens\": 5}" \
    | jq -e '.choices[0]' > /dev/null 2>&1
```

#### 1.4 `validate-model.sh`
```bash
#!/bin/bash
# Validate model name against available models
# Usage: validate-model.sh <model-name>
# Exit 0 if valid, 1 if invalid (prints available models)

MODEL="$1"
SCRIPTS_DIR="$(dirname "$0")"

if [ -z "$MODEL" ]; then
    echo "ERROR: No model specified" >&2
    echo "Available models:" >&2
    "$SCRIPTS_DIR/get-models.sh" >&2
    exit 1
fi

AVAILABLE=$("$SCRIPTS_DIR/get-models.sh")

if echo "$AVAILABLE" | grep -qx "$MODEL"; then
    exit 0
else
    echo "ERROR: Invalid model '$MODEL'" >&2
    echo "Available models:" >&2
    echo "$AVAILABLE" >&2
    exit 1
fi
```

---

### Phase 2: Update Review Scripts

#### 2.1 `quick-review.sh` Changes

**Remove:**
```bash
# DELETE: Alias mapping function
get_litellm_model() {
    case "$1" in
        qwen) echo "qwen3-coder" ;;
        ...
    esac
}

# DELETE: Hardcoded priority
MODELS_PRIORITY="qwen3-coder deepseek-v3-thinking glm-4.6-thinking"
```

**Add:**
```bash
# Validate model against LiteLLM API
if ! ~/.claude/scripts/validate-model.sh "$MODEL"; then
    exit 1
fi

# Health check with fallback to first healthy
if ! ~/.claude/scripts/health-check-model.sh "$MODEL"; then
    echo "⚠️ Model $MODEL unhealthy, available healthy models:" >&2
    ~/.claude/scripts/get-healthy-models.sh 3 >&2
    exit 1
fi

# Use MODEL directly (no alias conversion)
LITELLM_MODEL="$MODEL"
```

#### 2.2 `consensus-review.sh` Changes

**Remove:**
```bash
# DELETE: Hardcoded model list
for model in qwen3-coder deepseek-v3-thinking glm-4.6-thinking; do
```

**Add:**
```bash
# Get first 5 healthy models dynamically
HEALTHY_MODELS=$(~/.claude/scripts/get-healthy-models.sh 5)
MODEL_COUNT=$(echo "$HEALTHY_MODELS" | wc -l)

echo "Running consensus with $MODEL_COUNT models..."

# Launch each healthy model in parallel
while IFS= read -r model; do
    # ... curl for each model
done <<< "$HEALTHY_MODELS"
```

#### 2.3 `deep-review.sh` Changes

**Remove:**
```bash
# DELETE: Alias mapping
get_model_info() {
    case "$1" in
        qwen|code|bugs) echo "qwen3-coder" ;;
        ...
    esac
}

# DELETE: Hardcoded priority
MODELS_PRIORITY="qwen3-coder kimi-k2-thinking glm-4.6-thinking"
```

**Add:**
```bash
# Validate model
if ! ~/.claude/scripts/validate-model.sh "$MODEL"; then
    exit 1
fi

# Health check
if ! ~/.claude/scripts/health-check-model.sh "$MODEL"; then
    echo "⚠️ Model $MODEL unhealthy" >&2
    echo "Available healthy models:" >&2
    ~/.claude/scripts/get-healthy-models.sh 3 >&2
    exit 1
fi

# Use directly
LITELLM_MODEL="$MODEL"
```

#### 2.4 `parallel-deep-review.sh` Changes

**Remove:**
```bash
# DELETE: Hardcoded models
for model in qwen3-coder kimi-k2-thinking glm-4.6-thinking; do
```

**Add:**
```bash
# Get first 3 healthy models (headless is resource-heavy)
HEALTHY_MODELS=$(~/.claude/scripts/get-healthy-models.sh 3)

# Create config and run for each
while IFS= read -r model; do
    # ... headless claude for each model
done <<< "$HEALTHY_MODELS"
```

---

### Phase 3: User Experience

#### 3.1 `/kln:models` Command

Create `~/.claude/commands/kln/models.md`:
```markdown
---
name: models
description: "List available LiteLLM models"
allowed-tools: Bash
---

# List Available Models

```bash
~/.claude/scripts/get-models.sh
```

Display the output to show the user which models are available.
```

#### 3.2 Update `/kln:help`

Add to help output:
```
/kln:models              - List available LiteLLM models
```

#### 3.3 Error Message Format

When model is invalid:
```
ERROR: Invalid model 'qwen'
Available models:
  qwen3-coder
  deepseek-v3-thinking
  glm-4.6-thinking
  minimax-m2
  kimi-k2-thinking
  hermes-4-70b
```

---

### Phase 4: Documentation Updates

#### 4.1 Files to Update

| File | Changes |
|------|---------|
| `README.md` | Remove alias references, add /kln:models |
| `docs/COMMANDS.md` | Update model argument to exact names |
| `docs/REVIEW-SYSTEM.md` | Remove alias table, document auto-detection |
| `docs/INSTALLATION.md` | Add note about exact model names |
| `CLAUDE.md` | Update model references |

#### 4.2 Key Documentation Changes

**Before:**
```bash
/kln:quickReview qwen security
# Models: qwen, deepseek, glm, minimax, kimi, hermes
```

**After:**
```bash
/kln:quickReview qwen3-coder security
# Run /kln:models to see available models
```

---

## Testing Plan

### Test 1: Helper Scripts
```bash
# Test get-models.sh
~/.claude/scripts/get-models.sh
# Expected: List of model names from LiteLLM

# Test health-check-model.sh
~/.claude/scripts/health-check-model.sh qwen3-coder && echo "healthy" || echo "unhealthy"
# Expected: "healthy"

# Test get-healthy-models.sh
~/.claude/scripts/get-healthy-models.sh 3
# Expected: First 3 healthy model names

# Test validate-model.sh
~/.claude/scripts/validate-model.sh qwen3-coder && echo "valid"
~/.claude/scripts/validate-model.sh invalid-model || echo "invalid"
# Expected: "valid" then "invalid" with model list
```

### Test 2: Review Scripts
```bash
# Valid model
/kln:quickReview qwen3-coder security
# Expected: Review runs

# Invalid model
/kln:quickReview qwen security
# Expected: Error with available models list

# Consensus (auto models)
/kln:quickCompare security
# Expected: Uses first 5 healthy models
```

### Test 3: Add New Model
```bash
# 1. Add model to LiteLLM config
# 2. Restart LiteLLM
# 3. Run /kln:models
# Expected: New model appears automatically

# 4. Run /kln:quickReview new-model-name test
# Expected: Works without any script changes
```

---

## Migration Notes

### Breaking Changes

1. **Aliases removed**: `qwen` no longer works, use `qwen3-coder`
2. **Exact names required**: Must match LiteLLM config exactly
3. **quickCompare**: Now uses 5 models instead of 3

### User Action Required

Users must update any personal scripts/aliases that use short model names:
```bash
# Old (broken)
/kln:quickReview qwen security

# New (works)
/kln:quickReview qwen3-coder security
```

### Rollback Plan

If issues arise, revert to previous script versions from backup:
```bash
cd ~/claudeAgentic/review-system-backup
git checkout HEAD~1 -- scripts/quick-review.sh
cp scripts/quick-review.sh ~/.claude/scripts/
```

---

## Files Changed Summary

| File | Action |
|------|--------|
| `scripts/get-models.sh` | **NEW** |
| `scripts/get-healthy-models.sh` | **NEW** |
| `scripts/health-check-model.sh` | **NEW** |
| `scripts/validate-model.sh` | **NEW** |
| `scripts/quick-review.sh` | MODIFY - remove aliases |
| `scripts/consensus-review.sh` | MODIFY - dynamic models |
| `scripts/deep-review.sh` | MODIFY - remove aliases |
| `scripts/parallel-deep-review.sh` | MODIFY - dynamic models |
| `commands/kln/models.md` | **NEW** |
| `commands/kln/help.md` | MODIFY - add models |
| `docs/COMMANDS.md` | MODIFY |
| `docs/REVIEW-SYSTEM.md` | MODIFY |
| `README.md` | MODIFY |

---

## Timeline

| Phase | Effort | Dependencies |
|-------|--------|--------------|
| Phase 1: Helper Scripts | ~30 min | None |
| Phase 2: Update Scripts | ~1 hour | Phase 1 |
| Phase 3: User Experience | ~20 min | Phase 1 |
| Phase 4: Documentation | ~30 min | Phase 2, 3 |
| Testing | ~30 min | All phases |

**Total: ~3 hours**
