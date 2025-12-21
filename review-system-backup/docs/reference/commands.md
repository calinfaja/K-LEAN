# Commands Reference

Complete reference for K-LEAN v1.0.0-beta slash commands.

## Commands (9 total)

### Review Commands

| Command | Method | Time | Description |
|---------|--------|------|-------------|
| `/kln:quick` | API | ~30s | Single LiteLLM model, returns GRADE/RISK/findings without file access |
| `/kln:multi` | API | ~60s | 3-5 models via asyncio, consensus grades, findings by confidence |
| `/kln:deep` | SDK | ~3min | Claude Agent with Read/Grep/Glob/Bash tools, evidence-based |
| `/kln:droid` | SDK | ~2min | Claude Agent with role-specific prompts (coder/architect/auditor) |
| `/kln:rethink` | API | ~60s | Contrarian techniques (inversion, assumption challenge) |

### Utility Commands

| Command | Description |
|---------|-------------|
| `/kln:doc` | Session docs to Serena memory via mcp__serena__write_memory |
| `/kln:remember` | Git review + KB capture + Serena lessons-learned index |
| `/kln:status` | LiteLLM health, model latency, KB/Serena status |
| `/kln:help` | Command reference with flags, examples, architecture |

## Command Details

### /kln:quick

Calls single LiteLLM model for fast code review. Returns GRADE, RISK, and findings without file access.

```bash
/kln:quick [--model MODEL] [--async] [--output text|json] <focus>
```

**Examples:**
```bash
/kln:quick security                    # Auto-select model
/kln:quick --model qwen3-coder memory  # Specific model
/kln:quick --async architecture        # Background
```

### /kln:multi

Runs 3-5 LiteLLM models in parallel via asyncio, calculates grade/risk consensus, and groups findings by confidence level.

```bash
/kln:multi [--models N|list] [--async] <focus>
```

**Examples:**
```bash
/kln:multi security                              # 3 models (default)
/kln:multi --models 5 architecture              # 5 models
/kln:multi --models qwen3-coder,glm-4.6-thinking security
```

**Output includes:**
- Individual reviews per model
- Consensus grade and risk level
- HIGH/MEDIUM/LOW confidence findings
- Ranked issues by agreement

### /kln:deep

Spawns headless Claude Agent with Read/Grep/Glob/Bash tools for evidence-based review. Actually reads files and provides findings with code snippets.

```bash
/kln:deep [--model MODEL] [--async] <focus>
```

**Examples:**
```bash
/kln:deep security audit              # Deep investigation
/kln:deep --async full review         # Background deep review
```

### /kln:droid

Spawns Claude Agent with role-specific prompts from prompts/roles/ directory. Uses expert system prompts for domain-specific analysis.

```bash
/kln:droid [--model MODEL] [--role ROLE] [--parallel] <task>
```

**Roles:**
- `reviewer` - Code quality, bugs
- `architect` - System design, patterns
- `auditor` - Security, compliance
- `coder` - Performance, optimization
- `researcher` - Documentation, exploration

**Examples:**
```bash
/kln:droid --role security audit auth flow
/kln:droid --parallel review all modules
```

### /kln:rethink

Extracts debugging context from conversation, then queries LiteLLM with contrarian techniques (inversion, assumption challenge, domain shift). Returns ranked novel ideas.

```bash
/kln:rethink [--models N|MODEL] [--async] [focus]
```

**Features:**
- Auto-summarizes current debugging context
- Applies inversion, assumption challenge, domain shift
- Multi-model mode ranks ideas by novelty + actionability

**Examples:**
```bash
/kln:rethink                           # 5 models, auto-context
/kln:rethink --models deepseek-v3-thinking memory leak
/kln:rethink --models 3 "bug persists after fix"
```

### /kln:doc

Generates session documentation (report/session/lessons types) and persists to Serena memory via mcp__serena__write_memory.

```bash
/kln:doc [--async] "Session Title"
```

### /kln:remember

Reviews git status/diff/log, extracts learnings by category, saves to Knowledge DB via knowledge-capture.py, and appends index to Serena lessons-learned.

```bash
/kln:remember
```

### /kln:status

Checks LiteLLM proxy health (localhost:4000), lists available models with cached latency, and verifies Knowledge DB and Serena MCP status.

```bash
/kln:status
```

Shows:
- 9 active commands
- 12 LiteLLM models
- Service health (LiteLLM proxy, Knowledge DB)

### /kln:help

Displays K-LEAN command reference with flags, examples, model routing, and architecture overview.

```bash
/kln:help
```

## Common Flags

| Flag | Description | Commands |
|------|-------------|----------|
| `--async, -a` | Run in background | All review commands |
| `--model, -m` | Specific model | quick, deep, droid |
| `--models, -n` | Model count or list | multi, rethink |
| `--output, -o` | Output format (text/json) | quick, multi |
| `--role` | Worker role | droid |
| `--parallel` | Parallel execution | droid |

## Model Discovery

Models are auto-discovered from LiteLLM. Use substring matching:

```bash
/kln:quick --model deepseek security   # Matches deepseek-v3-thinking
/kln:quick --model qwen security       # Matches qwen3-coder
```

Current models (12):
- qwen3-coder
- deepseek-v3-thinking, deepseek-r1
- glm-4.6-thinking
- kimi-k2, kimi-k2-thinking
- minimax-m2
- hermes-4-70b
- llama-4-scout, llama-4-maverick
- devstral-2
- qwen3-235b

## Hook-Triggered Keywords

These keywords are detected by hooks:

| Keyword | Action |
|---------|--------|
| `healthcheck` | Check all LiteLLM models |
| `GoodJob <url>` | Capture URL to knowledge DB |
| `SaveThis <lesson>` | Direct save to knowledge DB |
| `FindKnowledge <query>` | Search knowledge DB |

## Migration from Old Commands

| Old Command (removed) | New Command |
|----------------------|----------------|
| `/kln:quickReview` | `/kln:quick` |
| `/kln:asyncQuickReview` | `/kln:quick --async` |
| `/kln:quickCompare` | `/kln:multi` |
| `/kln:asyncQuickCompare` | `/kln:multi --async` |
| `/kln:deepInspect` | `/kln:deep` |
| `/kln:deepAudit` | `/kln:deep --models 3` |
| `/kln:asyncDeepAudit` | `/kln:deep --models 3 --async` |
| `/kln:droidAudit` | `/kln:droid --parallel` |
| `/kln:droidExecute` | `/kln:droid --role <role>` |
| `/kln:createReport` | `/kln:doc` |
| `/kln:models` | `/kln:status` |

## Troubleshooting

### Command not found

```bash
# Check symlinks
ls -la ~/.claude/commands/kln/

# Should show 9 command files
```

### Model error

```bash
# Check LiteLLM health
curl http://localhost:4000/health

# Check specific model
k-lean models --test
```

### Async not working

- Verify hooks in `~/.claude/settings.json`
- Check hook scripts are executable
- Check `/tmp/claude-reviews/` for logs
