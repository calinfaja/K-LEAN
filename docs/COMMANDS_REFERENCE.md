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
| `/sc:review <model> <focus>` | 1 | No | 30s | Quick sanity check |
| `/sc:secondOpinion <model> <question>` | 1 | No | 1min | Get independent opinion |
| `/sc:deepReview <model> <focus>` | 1 | Yes | 3min | Thorough single-model audit |
| `/sc:consensus <focus>` | 3 | No | 1min | Quick 3-model comparison |
| `/sc:parallelDeepReview <focus>` | 3 | Yes | 5min | Comprehensive 3-model audit |

**Models:** `qwen` (code), `deepseek` (architecture), `glm` (standards), `minimax` (research), `kimi` (agent), `hermes` (scripting)

---

## Knowledge System Commands (Inside Claude)

| Keyword in Prompt | What It Does |
|-------------------|--------------|
| `GoodJob <url>` | Capture knowledge from URL |
| `GoodJob <url> <focus>` | Capture with specific focus |
| `SaveThis <description>` | Save a lesson learned |
| `FindKnowledge <query>` | Search knowledge database |

**Example:**
```
GoodJob https://docs.txtai.io/embeddings focus on SQLite backend
SaveThis connection pooling improves PostgreSQL performance 10x
FindKnowledge BLE power optimization
```

---

## Async Commands via Hooks (Background Execution)

| Keyword in Prompt | What Runs | Output |
|-------------------|-----------|--------|
| `asyncDeepReview <focus>` | 3 models + tools | `{session}/deep-*.txt` |
| `asyncConsensus <focus>` | 3 models curl | `{session}/consensus-*.json` |
| `asyncReview qwen <focus>` | Single qwen | `{session}/quick-*.json` |
| `asyncSecondOpinion deepseek <q>` | Single model opinion | `{session}/opinion-*.json` |

**Output location:** `/tmp/claude-reviews/{session-id}/`

**How:** Type keyword -> Hook intercepts -> Script runs in background -> You keep working

---

## Terminal Commands

### Review Scripts

| Command | What It Does |
|---------|--------------|
| `start-nano-proxy` | Start LiteLLM proxy (alias) |
| `~/.claude/scripts/health-check.sh` | Test all 6 models |
| `~/.claude/scripts/quick-review.sh <model> "<focus>"` | Single model quick |
| `~/.claude/scripts/second-opinion.sh <model> "<q>"` | Single model opinion |
| `~/.claude/scripts/consensus-review.sh "<focus>"` | 3 models via curl |
| `~/.claude/scripts/parallel-deep-review.sh "<focus>"` | 3 models with tools |
| `~/.claude/scripts/test-system.sh` | Verify system works |

### Knowledge System Scripts

| Command | What It Does |
|---------|--------------|
| `~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge_db.py stats` | Show DB statistics |
| `~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge_db.py search "query"` | Search entries |
| `~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge_db.py recent` | List recent entries |
| `~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge_db.py rebuild` | Rebuild index from JSONL |
| `~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-search.py "query" --format inject` | Search with LLM format |

### Maintenance Scripts

| Command | What It Does |
|---------|--------------|
| `~/.claude/scripts/sync-check.sh` | Check scripts/commands/config sync |
| `~/.claude/scripts/sync-check.sh --sync` | Sync differences to backup |
| `~/.claude/scripts/sync-check.sh --scripts` | Check scripts only |
| `~/.claude/scripts/sync-check.sh --commands` | Check slash commands only |
| `~/.claude/scripts/sync-check.sh --config` | Check settings.json only |

---

## Check Results

```bash
# List sessions
ls -la /tmp/claude-reviews/

# List files in current session
ls -la /tmp/claude-reviews/2025-12-03-*/

# Read specific result
cat /tmp/claude-reviews/*/quick-qwen-*.json | jq '.choices[0].message.content'

# Or ask Claude
"show me the review results"
```

---

## Hooks Summary

| Trigger | Hook | What Happens |
|---------|------|--------------|
| Prompt with `async*` | UserPromptSubmit | Runs review in background |
| Prompt `healthcheck` | UserPromptSubmit | Checks all 6 models |
| Prompt `GoodJob/SaveThis` | UserPromptSubmit | Captures knowledge |
| Prompt `FindKnowledge` | UserPromptSubmit | Searches knowledge DB |
| After `git commit` | PostToolUse (Bash) | Updates Serena memories |
| After `WebFetch` | PostToolUse | Auto-captures valuable findings |
| After `WebSearch` | PostToolUse | Auto-captures search results |

---

## Workflow Examples

### Code Review Workflow
```
healthcheck -> CODE -> asyncDeepReview security -> KEEP CODING -> check results
```

### Knowledge Capture Workflow
```
research topic -> GoodJob <url> -> keep researching -> FindKnowledge <topic> -> apply knowledge
```

### Full Development Cycle
```
healthcheck -> CODE -> SaveThis lesson learned -> asyncConsensus review -> check results -> commit
```
