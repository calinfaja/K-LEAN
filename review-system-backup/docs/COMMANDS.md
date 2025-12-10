# Commands Reference

Complete reference for all K-LEAN slash commands and keywords.

## Slash Commands (/kln:)

### Review Commands

| Command | Description | Usage |
|---------|-------------|-------|
| `/kln:quickReview` | Single model API review (exact name) | `/kln:quickReview qwen3-coder security` |
| `/kln:quickCompare` | First 5 healthy models in parallel | `/kln:quickCompare architecture` |
| `/kln:quickConsult` | Get second opinion on question | `/kln:quickConsult kimi-k2-thinking "is this safe?"` |
| `/kln:deepInspect` | Single model with full tool access | `/kln:deepInspect qwen3-coder full audit` |
| `/kln:models` | List available LiteLLM models | `/kln:models` |

### Async Commands (Background)

| Command | Description | Usage |
|---------|-------------|-------|
| `/kln:asyncQuickReview` | Quick review in background | `/kln:asyncQuickReview qwen3-coder security` |
| `/kln:asyncQuickCompare` | Multi-model compare in background | `/kln:asyncQuickCompare security` |
| `/kln:asyncDeepAudit` | 3 healthy models with tools in background | `/kln:asyncDeepAudit architecture` |
| `/kln:asyncQuickConsult` | Consult in background | `/kln:asyncQuickConsult kimi-k2-thinking "question"` |

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
| `/kln:deepInspect` | `.claude/kln/deepInspect/` |
| `/kln:asyncDeepAudit` | `.claude/kln/asyncDeepAudit/` |

**Filename format:** `YYYY-MM-DD_HH-MM-SS_model_focus.md`

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

## Command Files

Located at `~/.claude/commands/kln/`:

```
~/.claude/commands/kln/
├── quickReview.md
├── quickCompare.md
├── quickConsult.md
├── deepInspect.md
├── asyncQuickReview.md
├── asyncQuickCompare.md
├── asyncDeepAudit.md
├── asyncQuickConsult.md
├── createReport.md
├── backgroundReport.md
└── help.md
```

## Scripts Behind Commands

| Command | Script |
|---------|--------|
| quickReview | `~/.claude/scripts/quick-review.sh` |
| quickCompare | `~/.claude/scripts/consensus-review.sh` |
| deepInspect | `~/.claude/scripts/deep-review.sh` |
| asyncDeepAudit | `~/.claude/scripts/parallel-deep-review.sh` |

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
