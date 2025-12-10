# Commands Reference

Complete reference for all K-LEAN slash commands and keywords.

## Slash Commands (/kln:)

### Review Commands

| Command | Method | Time | Description | Usage |
|---------|--------|------|-------------|-------|
| `/kln:quickReview` | API | ~30s | Single model API review | `/kln:quickReview qwen security` |
| `/kln:quickCompare` | API | ~60s | 3 models in parallel | `/kln:quickCompare architecture` |
| `/kln:deepInspect` | CLI | ~3min | Single model with full tools | `/kln:deepInspect qwen full audit` |
| `/kln:deepAudit` | CLI | ~5min | 3 models with full tools | `/kln:deepAudit security` |
| `/kln:droid` | DROID | ~30s | Fast agentic review | `/kln:droid qwen security` |
| `/kln:droidAudit` | DROID | ~1min | 3 droids in parallel | `/kln:droidAudit architecture` |
| `/kln:droidExecute` | DROID | ~30s | Specialized droid | `/kln:droidExecute qwen arm-cortex-expert Review ISRs` |
| `/kln:quickConsult` | API | ~60s | Get second opinion | `/kln:quickConsult kimi "is this safe?"` |
| `/kln:models` | - | - | List available models | `/kln:models` |

### Async Commands (Background)

| Sync Command | Async Variant | Description |
|--------------|---------------|-------------|
| `/kln:quickReview` | `/kln:asyncQuickReview` | Review while you keep coding |
| `/kln:quickCompare` | `/kln:asyncQuickCompare` | Multi-model compare in background |
| `/kln:quickConsult` | `/kln:asyncQuickConsult` | Get opinion in background |
| `/kln:deepAudit` | `/kln:asyncDeepAudit` | Full audit in background |
| `/kln:droid` | `/kln:asyncDroid` | Fast droid in background |
| `/kln:droidAudit` | `/kln:asyncDroidAudit` | Parallel droids in background |
| `/kln:createReport` | `/kln:asyncCreateReport` | Document session in background |

### Utility Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `/kln:help` | List all /kln: commands | `/kln:help` |
| `/kln:createReport` | Create session documentation | `/kln:createReport "Session Title"` |
| `/kln:backgroundReport` | Create report in background | `/kln:backgroundReport "Title"` |

## Keywords (Hook-Triggered)

These keywords are detected by the UserPromptSubmit hook and trigger automated actions.

### Health Check

```bash
healthcheck
```

Checks health of all 6 models via LiteLLM proxy.

### Knowledge Capture

```bash
GoodJob <url>
GoodJob <url> <instructions>
```

Captures a URL to the knowledge database.

**Examples:**
```bash
GoodJob https://docs.example.com/api
GoodJob https://blog.example.com/auth focus on OAuth section
```

```bash
SaveThis <lesson>
```

Direct save to knowledge DB (no AI evaluation, always saves).

**Examples:**
```bash
SaveThis connection pooling improves database performance 10x
SaveThis always sanitize user input before SQL queries
```

```bash
SaveInfo <content>
```

Smart save with AI relevance evaluation using Claude Haiku. Only saves if relevance score ≥ 0.7.

**Examples:**
```bash
SaveInfo Thinking models return reasoning_content instead of content field
SaveInfo K-LEAN review outputs are saved to .claude/kln/ with timestamps
```

| Keyword | AI Evaluation | Threshold | Use Case |
|---------|---------------|-----------|----------|
| `SaveThis` | ❌ No | Always saves | You're certain it's valuable |
| `SaveInfo` | ✅ Haiku | score ≥ 0.7 | Let AI decide if worth saving |

### Knowledge Search

```bash
FindKnowledge <query>
```

Searches the knowledge database semantically.

**Examples:**
```bash
FindKnowledge authentication patterns
FindKnowledge database optimization techniques
```

### Async Reviews

```bash
asyncDeepReview <focus>
asyncConsensus <focus>
asyncReview <model> <focus>
```

Triggers background review via hooks.

**Examples:**
```bash
asyncDeepReview security vulnerabilities
asyncConsensus code quality
asyncReview qwen error handling
```

## Model Aliases

Available for all review commands:

| Alias | LiteLLM Model | Specialization |
|-------|---------------|----------------|
| `qwen` | qwen3-coder | Code quality, bugs |
| `deepseek` | deepseek-v3-thinking | Architecture, design |
| `glm` | glm-4.6-thinking | Standards, MISRA |
| `kimi` | kimi-k2-thinking | Agent tasks |
| `minimax` | minimax-m2 | Research |
| `hermes` | hermes-4-70b | Scripting |

## Output Locations

| Command | Output Directory |
|---------|------------------|
| `/kln:quickReview` | `.claude/kln/quickReview/` |
| `/kln:quickCompare` | `.claude/kln/quickCompare/` |
| `/kln:quickConsult` | `.claude/kln/quickConsult/` |
| `/kln:deepInspect` | `.claude/kln/deepInspect/` |
| `/kln:deepAudit` | `.claude/kln/deepAudit/` |
| `/kln:droid` | `.claude/kln/droid/` |
| `/kln:droidAudit` | `.claude/kln/droidAudit/` |
| `/kln:droidExecute` | `.claude/kln/droidExecute/` |

**Filename format:** `YYYY-MM-DD_HH-MM-SS_model_focus.txt`

## Command Examples

### Security Review

```bash
# Quick single-model review
/kln:quickReview qwen security vulnerabilities in authentication

# Consensus from 3 models
/kln:quickCompare security audit for user input handling

# Deep investigation with tools
/kln:deepInspect glm comprehensive security audit with OWASP checks
```

### Architecture Review

```bash
# Quick architecture check
/kln:quickReview deepseek coupling and cohesion analysis

# Deep architecture investigation
/kln:deepInspect qwen architectural patterns and dependencies
```

### Compliance Review

```bash
# Standards compliance
/kln:quickReview glm MISRA C compliance check

# Full compliance audit
/kln:deepInspect glm comprehensive MISRA and coding standards audit
```

### Background Reviews

```bash
# Run in background while you continue working
/kln:asyncDeepAudit security patterns

# Check results later via AgentOutputTool
```

### Knowledge Operations

```bash
# Capture valuable finding
GoodJob https://owasp.org/Top10/ focus on injection prevention

# Save lesson learned
SaveThis never trust user input - always validate and sanitize

# Search for relevant knowledge
FindKnowledge injection prevention patterns
```

## Specialist Droids (for /kln:droidExecute)

| Droid | Expertise |
|-------|-----------|
| `orchestrator` | System architecture, task coordination, memory system |
| `code-reviewer` | Code quality, OWASP Top 10, SOLID principles |
| `security-auditor` | Vulnerabilities, auth flows, encryption |
| `debugger` | Root cause analysis, error tracing |
| `arm-cortex-expert` | ARM Cortex-M, DMA, ISRs, cache coherency, FreeRTOS |
| `c-pro` | C99/C11, POSIX, memory management, MISRA |
| `rust-expert` | Ownership, lifetimes, no_std embedded Rust |
| `performance-engineer` | Profiling, optimization, benchmarks |

**Example usage:**
```bash
/kln:droidExecute qwen code-reviewer Check error handling in main.c
/kln:droidExecute glm arm-cortex-expert Review ISR priorities
/kln:droidExecute deepseek security-auditor Audit authentication flow
/kln:droidExecute kimi rust-expert Check unsafe blocks
```

## Command Files

Located at `~/.claude/commands/kln/`:

```
~/.claude/commands/kln/
├── quickReview.md
├── quickCompare.md
├── quickConsult.md
├── deepInspect.md
├── deepAudit.md
├── droid.md
├── droidAudit.md
├── droidExecute.md
├── asyncQuickReview.md
├── asyncQuickCompare.md
├── asyncQuickConsult.md
├── asyncDeepAudit.md
├── asyncDroid.md
├── asyncDroidAudit.md
├── createReport.md
├── asyncCreateReport.md
├── models.md
└── help.md
```

## Scripts Behind Commands

| Command | Script |
|---------|--------|
| quickReview | `~/.claude/scripts/quick-review.sh` |
| quickCompare | `~/.claude/scripts/consensus-review.sh` |
| quickConsult | `~/.claude/scripts/second-opinion.sh` |
| deepInspect | `~/.claude/scripts/deep-review.sh` |
| deepAudit | `~/.claude/scripts/parallel-deep-review.sh` |
| droid | `~/.claude/scripts/droid-review.sh` |
| droidAudit | `~/.claude/scripts/parallel-droid-review.sh` |
| droidExecute | `~/.claude/scripts/droid-execute.sh` |

## Troubleshooting

### Command not found

```bash
# Check command files exist
ls ~/.claude/commands/kln/

# Verify symlinks if using nano profile
ls -la ~/.claude-nano/commands
```

### Review returns error

```bash
# Check LiteLLM proxy
curl http://localhost:4000/v1/models

# Check specific model health
curl -s http://localhost:4000/chat/completions \
  -d '{"model": "qwen3-coder", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}'
```

### Async command not working

- Hooks must be configured in `~/.claude/settings.json`
- Check hook files are executable
- Verify hook scripts exist at expected paths
