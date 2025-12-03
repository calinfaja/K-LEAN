# Commands Quick Reference

## Review Commands (Inside Claude)

| Command | Models | Tools | Async | Time | Use Case |
|---------|--------|-------|-------|------|----------|
| `/sc:review <model> <focus>` | 1 | ❌ | ❌ | 30s | Quick sanity check |
| `/sc:secondOpinion <model> <question>` | 1 | ❌ | ❌ | 1min | Get independent opinion with context |
| `/sc:deepReview <model> <focus>` | 1 | ✅ | ❌ | 3min | Thorough single-model audit |
| `/sc:consensus <focus>` | 3 | ❌ | ❌ | 1min | Quick 3-model comparison |
| `/sc:parallelDeepReview <focus>` | 3 | ✅ | ❌ | 5min | Comprehensive 3-model audit |
| `/sc:createReviewDoc <title>` | - | Serena | ❌ | 1min | Document session to Serena memory |

**Models:** `qwen` (bugs), `deepseek` (architecture), `glm` (standards)

---

## Async Commands via Hooks (Background Execution)

| Keyword in Prompt | What Runs | Output Location |
|-------------------|-----------|-----------------|
| `asyncDeepReview <focus>` | 3 models + tools | `/tmp/claude-reviews/deep-review-*.txt` |
| `asyncConsensus <focus>` | 3 models curl | `/tmp/claude-reviews/consensus-*.txt` |
| `asyncReview qwen <focus>` | Single qwen | `/tmp/claude-reviews/review-qwen-*.txt` |
| `asyncReview deepseek <focus>` | Single deepseek | `/tmp/claude-reviews/review-deepseek-*.txt` |
| `asyncReview glm <focus>` | Single glm | `/tmp/claude-reviews/review-glm-*.txt` |
| `asyncSecondOpinion <model> <q>` | Single model opinion | `/tmp/claude-reviews/opinion-*-*.txt` |

**How:** Type keyword anywhere in your prompt → Hook intercepts → Script runs in background → You keep working

---

## Automatic Hooks

| Trigger | Hook | What Happens |
|---------|------|--------------|
| Any prompt with `async*` | `UserPromptSubmit` | Runs review script in background |
| After `git commit` | `PostToolUse` (Bash) | Updates Serena memories + creates commit docs |

---

## Terminal Commands (Outside Claude)

| Command | What It Does |
|---------|--------------|
| `~/.claude/scripts/parallel-deep-review.sh "<focus>" <dir>` | 3 models with tools |
| `~/.claude/scripts/consensus-review.sh "<focus>" <dir>` | 3 models via curl |
| `~/.claude/scripts/quick-review.sh <model> "<focus>" <dir>` | Single model quick |
| `~/.claude/scripts/second-opinion.sh <model> "<question>" <dir>` | Single model opinion |

---

## Check Results

```bash
# List all results
ls -la /tmp/claude-reviews/

# Read specific result
cat /tmp/claude-reviews/deep-review-latest.txt
cat /tmp/claude-reviews/consensus-latest.txt
cat /tmp/claude-reviews/post-commit-docs-*.txt

# Or ask Claude
"show me the review results"
"read /tmp/claude-reviews/deep-review-latest.txt"
```

---

## Workflow Summary

```
CODE → asyncDeepReview security → KEEP CODING → check results → COMMIT → auto-docs
```
