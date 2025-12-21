# K-LEAN Review System

## Overview

K-LEAN provides **multi-model code reviews** with consensus building across 3-5 LLMs.

## Review Types

| Type | Command | Models | Speed |
|------|---------|--------|-------|
| Quick | `/kln:quick` | 1 model | ~10s |
| Multi/Consensus | `/kln:multi` | 5 parallel | ~30s |
| Deep | `/kln:deep` | Claude SDK agent | ~3min |
| Droid | `/kln:droid` | Specialist persona | ~30s |
| Rethink | `/kln:rethink` | Contrarian analysis | ~20s |

## Quick Review

Single model review via LiteLLM.

```bash
# Script: src/klean/data/scripts/quick-review.sh
quick-review.sh "review this function for security"
```

**Features:**
- Dynamic model discovery from LiteLLM
- Health fallback (if model unhealthy, try next)
- Thinking model support

## Consensus Review

Parallel review across 5 models with agreement scoring.

```bash
# Script: src/klean/data/scripts/consensus-review.sh
consensus-review.sh "review authentication logic"
```

**Consensus Algorithm:**
1. Query 5 models in parallel (curl)
2. Parse JSON responses (with fallback to text)
3. Group findings by location similarity (>50% word overlap)
4. Classify by agreement:
   - **HIGH**: All models agree
   - **MEDIUM**: 2+ models agree
   - **LOW**: Single model only

## Deep Review

Uses Claude Agent SDK for comprehensive analysis.

```bash
# Script: src/klean/data/scripts/deep-review.sh
deep-review.sh "full security audit"
```

**Features:**
- Read-only mode (no modifications)
- Comprehensive allow/deny lists
- Full codebase access

## Rethink (Contrarian Debugging)

**Unique K-LEAN feature**: Challenges assumptions.

```bash
# Via command
/kln:rethink
```

**4 Contrarian Techniques:**
1. **Inversion**: Look at NOT-X if others looked at X
2. **Assumption Challenge**: What if key assumption is wrong?
3. **Domain Shift**: What would different expert see?
4. **Root Cause Reframe**: What if symptom isn't real problem?

## Thinking Model Support

Some models (DeepSeek, GLM, Kimi, Minimax) return responses in `reasoning_content` instead of `content`.

**All scripts check both:**
```bash
content=$(echo "$response" | jq -r '.choices[0].message.content // empty')
if [ -z "$content" ]; then
    content=$(echo "$response" | jq -r '.choices[0].message.reasoning_content // empty')
fi
```

## Review Prompts

Located in `src/klean/data/core/prompts/`:

| Prompt | Lines | Purpose |
|--------|-------|---------|
| `review.md` | 87 | 7-area review checklist |
| `rethink.md` | 93 | Contrarian debugging |
| `format-json.md` | 29 | Structured JSON output |
| `format-text.md` | 28 | Human-readable output |
| `droid-base.md` | 55 | Factory droid template |

### Review Areas (review.md)

1. Code Quality
2. Security
3. Performance
4. Error Handling
5. Testing
6. Documentation
7. Architecture

### Output Format

```json
{
  "grade": "B+",
  "risk": "MEDIUM",
  "findings": [
    {
      "severity": "HIGH",
      "location": "auth.py:42",
      "issue": "SQL injection vulnerability",
      "suggestion": "Use parameterized queries",
      "evidence": "user_input directly in query string"
    }
  ]
}
```

## Core Engine

Main implementation: `src/klean/data/core/klean_core.py` (1190 lines)

**Key Classes:**
- `ModelResolver`: Auto-discovery from LiteLLM, latency caching
- `ReviewEngine`: Quick + multi-model execution

**Features:**
- Async parallel execution via `asyncio.gather`
- 24h latency caching (disk-based)
- Model diversity (limits thinking models to 50%)
- Robust JSON parsing (direct → markdown → raw braces)

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `quick-review.sh` | Single model review |
| `consensus-review.sh` | 5-model parallel review |
| `deep-review.sh` | Claude SDK agent review |
| `droid-review.sh` | Specialist droid review |
| `parallel-deep-review.sh` | Multiple deep reviews |
| `second-opinion.sh` | Alternative perspective |

---
*See [droids.md](droids.md) for specialist personas*
