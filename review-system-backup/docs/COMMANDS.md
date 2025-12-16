# Commands Reference

Complete reference for K-LEAN v1.0.0-beta slash commands.

## V3 Commands (9 total)

### Review Commands

| Command | Method | Time | Description |
|---------|--------|------|-------------|
| `/kln:quick` | API | ~30s | Fast single-model review |
| `/kln:multi` | API | ~60s | Multi-model consensus (parallel) |
| `/kln:deep` | SDK | ~3min | Thorough review with Claude SDK tools |
| `/kln:droid` | Droid | ~30s | Role-based AI workers |
| `/kln:rethink` | API | ~60s | Fresh debugging perspectives |

### Utility Commands

| Command | Description |
|---------|-------------|
| `/kln:doc` | Create session documentation |
| `/kln:remember` | End-of-session knowledge capture |
| `/kln:status` | Models, health, system status |
| `/kln:help` | Complete command reference |

## Command Details

### /kln:quick

Fast single-model review via LiteLLM API.

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

Multi-model consensus review with parallel execution.

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

Thorough review using Claude SDK with full tool access.

```bash
/kln:deep [--model MODEL] [--async] <focus>
```

**Examples:**
```bash
/kln:deep security audit              # Deep investigation
/kln:deep --async full review         # Background deep review
```

### /kln:droid

Role-based AI workers with specialized expertise.

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

Fresh perspectives when stuck debugging. Uses contrarian techniques.

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

Create session documentation.

```bash
/kln:doc [--async] "Session Title"
```

### /kln:remember

End-of-session knowledge capture to Serena memory.

```bash
/kln:remember
```

### /kln:status

System status and model health.

```bash
/kln:status
```

Shows:
- 9 active commands
- 12 LiteLLM models
- Service health (LiteLLM proxy, Knowledge DB)

### /kln:help

Complete command reference.

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

| Old Command (removed) | New V3 Command |
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

# Should show 9 files pointing to commands-kln-v3/
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
