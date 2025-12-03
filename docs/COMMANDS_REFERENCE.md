# Commands Quick Reference

## Command Namespaces

| Namespace | Purpose | Source |
|-----------|---------|--------|
| `/sc:` | SuperClaude general-purpose commands | [SuperClaude Framework](https://github.com/SuperClaude-Org/SuperClaude_Framework) |
| `/kln:` | Custom review & knowledge framework | This project |

---

## Health Check

| Command | What It Does |
|---------|--------------|
| `healthcheck` | Check all 6 models (type in Claude prompt) |
| `~/.claude/scripts/health-check.sh` | Same, from terminal |
| `~/.claude/scripts/health-check.sh --quick` | Quick proxy check only |

---

## /kln: Review Commands (Custom Framework)

| Command | Models | Tools | Time | Use Case |
|---------|--------|-------|------|----------|
| `/kln:review <model> <focus>` | 1 | No | 30s | Quick sanity check |
| `/kln:secondOpinion <model> <question>` | 1 | No | 1min | Get independent opinion |
| `/kln:deepReview <model> <focus>` | 1 | Yes | 3min | Thorough single-model audit |
| `/kln:consensus <focus>` | 3 | No | 1min | Quick 3-model comparison |
| `/kln:parallelDeepReview <focus>` | 3 | Yes | 5min | Comprehensive 3-model audit |

**Models:**
- ✅ Reliable for tools: `qwen` (code), `kimi` (architecture), `glm` (standards)
- ⚠️ Quick reviews only: `deepseek` (design), `minimax` (research), `hermes` (scripting)

### Async Review Commands (Background Execution)

| Command/Keyword | What Runs | Output |
|-----------------|-----------|--------|
| `/kln:asyncDeepReview <focus>` | 3 models + tools | `{session}/deep-*.txt` |
| `/kln:asyncConsensus <focus>` | 3 models curl | `{session}/consensus-*.json` |
| `/kln:asyncReview qwen <focus>` | Single qwen | `{session}/quick-*.json` |
| `/kln:asyncSecondOpinion deepseek <q>` | Single model opinion | `{session}/opinion-*.json` |

### Documentation Commands

| Command | What It Does |
|---------|--------------|
| `/kln:createReviewDoc <title>` | Create session review documentation |
| `/kln:asyncReviewDoc <title>` | Create doc in background |
| `/kln:backgroundReviewDoc <title>` | Spawn doc creation in subagent |
| `/kln:help` | List all /kln: commands with model info |

**Output location:** `/tmp/claude-reviews/{session-id}/`

---

## /sc: SuperClaude Commands (30 Original)

| Category | Commands |
|----------|----------|
| Planning & Design | `/sc:brainstorm`, `/sc:design`, `/sc:estimate`, `/sc:spec-panel` |
| Development | `/sc:implement`, `/sc:build`, `/sc:improve`, `/sc:cleanup`, `/sc:explain` |
| Testing & Quality | `/sc:test`, `/sc:analyze`, `/sc:troubleshoot`, `/sc:reflect` |
| Documentation | `/sc:document`, `/sc:help` |
| Version Control | `/sc:git` |
| Project Management | `/sc:pm`, `/sc:task`, `/sc:workflow` |
| Research | `/sc:research`, `/sc:business-panel` |
| Utilities | `/sc:agent`, `/sc:index-repo`, `/sc:index`, `/sc:recommend`, `/sc:select-tool`, `/sc:spawn`, `/sc:load`, `/sc:save`, `/sc:sc` |

---

## Knowledge System Commands (Keywords)

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
| `~/.claude/scripts/test-headless.sh <model> "<prompt>"` | Test any model via headless Claude |
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
healthcheck -> CODE -> /kln:asyncDeepReview security -> KEEP CODING -> check results
```

### Knowledge Capture Workflow
```
research topic -> GoodJob <url> -> keep researching -> FindKnowledge <topic> -> apply knowledge
```

### Full Development Cycle
```
healthcheck -> CODE -> SaveThis lesson learned -> /kln:asyncConsensus review -> check results -> commit
```
