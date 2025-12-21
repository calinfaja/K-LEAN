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
| `review.md` | 86 | 7-area review checklist |
| `rethink.md` | 92 | Contrarian debugging |
| `format-json.md` | 28 | Structured JSON output |
| `format-text.md` | 27 | Human-readable output |
| `droid-base.md` | 54 | Factory droid template |

### Review Areas (review.md)

1. CORRECTNESS
2. MEMORY SAFETY
3. ERROR HANDLING
4. CONCURRENCY
5. ARCHITECTURE
6. SECURITY
7. STANDARDS

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

## Persistent Output

Reviews are saved to the project's `.claude/kln/` directory.

**Implementation:** `src/klean/data/scripts/session-helper.sh`

```
<project_root>/.claude/kln/
├── quickReview/
│   └── 2024-12-09_14-30-25_qwen_security.md
├── quickCompare/
│   └── 2024-12-09_16-00-00_consensus.md
├── deepInspect/
│   └── 2024-12-09_17-00-00_qwen_audit.md
└── asyncDeepAudit/
    └── 2024-12-09_18-00-00_parallel.md
```

**Filename format:** `YYYY-MM-DD_HH-MM-SS_model_focus.md`

**Fallback:** `/tmp/claude-reviews/` if project directory not writable.

## Audit Mode (Security)

Deep reviews run in **read-only audit mode** for safe automation.

**Implementation:** `src/klean/data/scripts/deep-review.sh` (lines 180-212)

```json
{
  "permissions": {
    "allow": [
      "Read", "Glob", "Grep", "LS", "Agent", "Task",
      "WebFetch", "WebSearch",
      "mcp__tavily__*", "mcp__context7__*", "mcp__serena__find_*",
      "mcp__serena__list_*", "mcp__serena__read_*", "mcp__serena__search_*",
      "Bash(git diff:*)", "Bash(git log:*)", "Bash(git status:*)",
      "Bash(cat:*)", "Bash(find:*)", "Bash(ls:*)", "Bash(grep:*)"
    ],
    "deny": [
      "Write", "Edit", "NotebookEdit",
      "Bash(rm:*)", "Bash(mv:*)", "Bash(cp:*)", "Bash(mkdir:*)",
      "Bash(git add:*)", "Bash(git commit:*)", "Bash(git push:*)",
      "Bash(pip install:*)", "Bash(npm install:*)", "Bash(sudo:*)",
      "mcp__serena__replace_*", "mcp__serena__insert_*",
      "mcp__serena__rename_*", "mcp__serena__write_*", "mcp__serena__delete_*"
    ]
  }
}
```

Uses `--dangerously-skip-permissions` with restricted `allowedTools` for fast, safe automation.

## Knowledge Integration

Reviews automatically extract and store reusable knowledge.

**Implementation:** `src/klean/data/scripts/fact-extract.sh`

**Flow:**
1. Review completes → `fact-extract.sh` called with output
2. Claude Haiku extracts lessons (types: gotcha, pattern, solution, insight)
3. Stores in `.knowledge-db/` if `relevance_score >= 0.6`
4. Logs to `.knowledge-db/timeline.txt`

**Called from deep-review.sh:**
```bash
"$KB_SCRIPTS_DIR/fact-extract.sh" "$REVIEW_OUTPUT" "review" "$PROMPT" "$WORK_DIR"
```

**Extraction Types:**
- `gotcha` - Pitfalls to avoid
- `pattern` - Reusable approaches
- `solution` - Fixes that worked
- `insight` - Architectural observations

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `quick-review.sh` | Single model review |
| `consensus-review.sh` | 5-model parallel review |
| `deep-review.sh` | Claude SDK agent review |
| `droid-review.sh` | Specialist droid review |
| `parallel-deep-review.sh` | Multiple deep reviews |
| `second-opinion.sh` | Alternative perspective |
| `fact-extract.sh` | Extract knowledge from reviews |
| `session-helper.sh` | Output directory management |

---
*See [droids.md](droids.md) for specialist personas*
*See [troubleshooting.md](troubleshooting.md) for common issues*
