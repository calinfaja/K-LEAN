# Commands Quick Reference

## Health Check

| Command | What It Does |
|---------|--------------|
| `healthcheck` | Check all 6 models (type in Claude prompt) |
| `~/.claude/scripts/health-check.sh` | Same, from terminal |
| `~/.claude/scripts/health-check.sh --quick` | Quick proxy check only |

---

## Review Commands (Inside Claude)

| Command | Models | Tools | Time | Use Case |
|---------|--------|-------|------|----------|
| `/sc:review <model> <focus>` | 1 | ❌ | 30s | Quick sanity check |
| `/sc:secondOpinion <model> <question>` | 1 | ❌ | 1min | Get independent opinion |
| `/sc:deepReview <model> <focus>` | 1 | ✅ | 3min | Thorough single-model audit |
| `/sc:consensus <focus>` | 3 | ❌ | 1min | Quick 3-model comparison |
| `/sc:parallelDeepReview <focus>` | 3 | ✅ | 5min | Comprehensive 3-model audit |

**Models:** `qwen` (code), `deepseek` (architecture), `glm` (standards), `minimax` (research), `kimi` (agent), `hermes` (scripting)

---

## Async Commands via Hooks (Background Execution)

| Keyword in Prompt | What Runs | Output |
|-------------------|-----------|--------|
| `asyncDeepReview <focus>` | 3 models + tools | `{session}/deep-*.txt` |
| `asyncConsensus <focus>` | 3 models curl | `{session}/consensus-*.json` |
| `asyncReview qwen <focus>` | Single qwen | `{session}/quick-*.json` |
| `asyncSecondOpinion deepseek <q>` | Single model opinion | `{session}/opinion-*.json` |

**Output location:** `/tmp/claude-reviews/{session-id}/`

**How:** Type keyword → Hook intercepts → Script runs in background → You keep working

---

## Terminal Commands

| Command | What It Does |
|---------|--------------|
| `start-nano-proxy` | Start LiteLLM proxy (alias) |
| `~/.claude/scripts/health-check.sh` | Test all 6 models |
| `~/.claude/scripts/quick-review.sh <model> "<focus>"` | Single model quick |
| `~/.claude/scripts/second-opinion.sh <model> "<q>"` | Single model opinion |
| `~/.claude/scripts/consensus-review.sh "<focus>"` | 3 models via curl |
| `~/.claude/scripts/parallel-deep-review.sh "<focus>"` | 3 models with tools |
| `~/.claude/scripts/test-system.sh` | Verify system works |

---

## Check Results

```bash
# List sessions
ls -la /tmp/claude-reviews/

# List files in current session
ls -la /tmp/claude-reviews/2024-12-03-*/

# Read specific result
cat /tmp/claude-reviews/*/quick-qwen-*.json | jq '.choices[0].message.content'

# Or ask Claude
"show me the review results"
```

---

## Hooks

| Trigger | What Happens |
|---------|--------------|
| Prompt with `async*` | Runs review in background |
| Prompt `healthcheck` | Checks all 6 models |
| After `git commit` | Updates Serena memories |

---

## Workflow

```
healthcheck → CODE → asyncDeepReview security → KEEP CODING → check results
```
