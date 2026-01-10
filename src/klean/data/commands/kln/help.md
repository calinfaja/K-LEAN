---
name: help
description: "Displays K-LEAN command reference with flags, examples, model routing, and architecture overview. Use to learn available commands and their usage patterns."
allowed-tools: []
argument-hint: "[command-name]"
---

# K-LEAN Command Reference

Knowledge-driven Lightweight Execution & Analysis Network

## Core Commands

| Command | Type | Duration | Description |
|---------|------|----------|-------------|
| `/kln:quick <focus>` | API | ~60s | Fast single-model review for quick insights |
| `/kln:multi <focus>` | API | ~2min | Multi-model consensus (parallel execution) |
| `/kln:agent <task>` | SDK | ~2min | SmolKLN specialist agent for domain-specific tasks |
| `/kln:doc <title>` | Local | ~30s | Create documentation from current session |
| `/kln:learn [topic]` | Local | ~30s | Extract learnings from context (mid-session) |
| `/kln:remember` | Local | ~60s | End-of-session knowledge capture and summary |
| `/kln:status` | Local | ~5s | System health, available models, and quick help |

## Universal Flags

All commands support these optional flags:

| Flag | Short | Description | Example |
|------|-------|-------------|---------|
| `--model` | `-m` | Use specific model | `-m qwen` |
| `--models` | `-n` | Number or list of models | `-n 3` or `-n qwen,deepseek` |
| `--async` | `-a` | Run in background | `-a` |
| `--output` | `-o` | Output format | `-o json` or `-o markdown` |
| `--fastest` | | Prefer models with lowest latency | `--fastest` |

**Output formats**: `text` (default), `json`, `markdown`

## Model Selection

K-LEAN dynamically queries available models from LiteLLM proxy (localhost:4000).

### Smart Routing

When no model is specified, K-LEAN selects based on task type:

- **Quality/Architecture**: `qwen` - Best overall reasoning
- **Code/Performance**: `deepseek` - Excellent for technical depth
- **Standards/Best Practices**: `glm` - Follows conventions strictly
- **Research/Documentation**: `minimax` - Great for context synthesis
- **Agent Workflows**: `kimi` - Strong at multi-step tasks
- **Scripts/Tools**: `hermes` - Fast and practical

### Model Health

Use `/kln:status` or `kln model list` to see current model availability.

## Command Examples

### Quick Review
```bash
# Single model, fast feedback
/kln:quick "Check error handling in auth module"

# Specific model
/kln:quick "Review API design" -m deepseek

# Background execution
/kln:quick "Performance bottlenecks" -a
```

### Multi-Model Consensus
```bash
# Default: 3 models in parallel
/kln:multi "Security vulnerabilities"

# Specify number of models
/kln:multi "Code quality issues" -n 5

# Specific models
/kln:multi "Architecture patterns" -n qwen,deepseek,glm

# JSON output for parsing
/kln:multi "Test coverage gaps" -o json
```

### SmolKLN Agents
```bash
# Role-based specialist analysis
/kln:agent --role security-auditor "Audit security practices"

# Specific model for agent
/kln:agent --role code-reviewer "Review auth module" -m qwen

# Domain expert analysis
/kln:agent --role performance-engineer "Optimize database queries"
```

### Documentation
```bash
# Create session docs
/kln:doc "Authentication Refactor Sprint"

# Markdown output
/kln:doc "API Design Review" -o markdown
```

### Knowledge Capture
```bash
# Mid-session: extract learnings from context
/kln:learn

# Focused extraction on specific topic
/kln:learn "auth bug fix"

# End-of-session: comprehensive capture
/kln:remember

# With markdown output
/kln:remember -o markdown
```

### System Status
```bash
# Check health and available models
/kln:status

# With latency details
/kln:status --fastest
```

## Knowledge Commands

| Command | Type | Description |
|---------|------|-------------|
| `/kln:learn` | Slash | Extract learnings from context (mid-session, context-aware) |
| `/kln:learn "topic"` | Slash | Focused extraction on specific topic |
| `/kln:remember` | Slash | Comprehensive end-of-session capture |
| `FindKnowledge <query>` | Hook | Semantic search knowledge database |
| `SaveInfo <url>` | Hook | Evaluate URL with LLM and save if relevant |

## K-LEAN CLI

System management commands:

```bash
kln status           # Component status and health
kln doctor -f        # Diagnose issues with auto-fix
kln start            # Start all services
kln admin debug      # Live monitoring dashboard
kln model list       # List available models
kln model list --test   # Test all models with latency
```

## Getting Started

1. **Check system health**: `/kln:status`
2. **Start simple**: Try `/kln:quick "Review my latest changes"`
3. **Use consensus**: For important decisions, use `/kln:multi`
4. **Use agents**: For specialist analysis, use `/kln:agent`
5. **Capture knowledge**: End sessions with `/kln:remember`

## Architecture

- **API Mode**: Direct LiteLLM calls, fast responses (`/kln:quick`, `/kln:multi`)
- **SDK Mode**: SmolKLN agents with tool use capabilities (`/kln:agent`)
- **Local Mode**: Direct execution on system, no external calls (`/kln:doc`, `/kln:remember`)

## Need Help?

- Quick reference: `/kln:status`
- Model health: `kln model list --health`
- System diagnostics: `kln doctor -f`
- Knowledge search: `FindKnowledge <query>`

