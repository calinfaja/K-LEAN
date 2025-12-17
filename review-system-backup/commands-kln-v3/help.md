---
name: help
description: "Command reference - all commands with examples"
version: 3.0.0
category: help
tags: [commands, reference, guide]
created: 2025-12-16
---

# K-LEAN v3.0 Command Reference

Knowledge-driven Lightweight Execution & Analysis Network

## Core Commands

| Command | Type | Duration | Description |
|---------|------|----------|-------------|
| `/kln:quick <focus>` | API | ~30s | Fast single-model review for quick insights |
| `/kln:multi <focus>` | API | ~60s | Multi-model consensus (parallel execution) |
| `/kln:deep <focus>` | SDK | ~3min | Thorough review with tool access and deep analysis |
| `/kln:droid <task>` | SDK | ~2min | Role-based specialized worker for specific tasks |
| `/kln:doc <title>` | Local | ~30s | Create documentation from current session |
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

Use `/kln:status` or `healthcheck` to see current model availability and latency.

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

### Deep Review
```bash
# Full analysis with tool access
/kln:deep "Refactor authentication system"

# Fastest available model
/kln:deep "Debug memory leak" --fastest

# Background deep dive
/kln:deep "Optimize database queries" -a
```

### Specialized Droids
```bash
# Role-based task execution
/kln:droid "Audit security practices"

# Specific model for droid
/kln:droid "Generate test suite" -m hermes

# Complex multi-step task
/kln:droid "Migrate to new API version"
```

### Documentation
```bash
# Create session docs
/kln:doc "Authentication Refactor Sprint"

# Markdown output
/kln:doc "API Design Review" -o markdown
```

### Session Capture
```bash
# End-of-session summary and knowledge capture
/kln:remember

# Include specific learnings
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

Quick-access commands for knowledge management:

| Command | Description | Example |
|---------|-------------|---------|
| `healthcheck` | Test all 6 LiteLLM models | `healthcheck` |
| `GoodJob <url>` | Capture web content to knowledge DB | `GoodJob https://example.com/article` |
| `SaveThis <lesson>` | Save a lesson learned | `SaveThis "Always validate inputs before DB queries"` |
| `FindKnowledge <query>` | Search knowledge database | `FindKnowledge "postgres optimization"` |

## K-LEAN CLI

System management commands:

```bash
k-lean status      # Component status and health
k-lean doctor -f   # Diagnose issues with auto-fix
k-lean start       # Start all services
k-lean debug       # Live monitoring dashboard
k-lean models      # List models with health checks
k-lean models --test  # Test all models with latency
```

## Getting Started

1. **Check system health**: `/kln:status` or `healthcheck`
2. **Start simple**: Try `/kln:quick "Review my latest changes"`
3. **Use consensus**: For important decisions, use `/kln:multi`
4. **Go deep**: When you need thorough analysis, use `/kln:deep`
5. **Capture knowledge**: End sessions with `/kln:remember`

## Architecture

- **API Mode**: Direct LiteLLM calls, fast responses, no tool access
- **SDK Mode**: Full Claude SDK agent with tool use capabilities
- **Local Mode**: Direct execution on system, no external calls

## Need Help?

- Quick reference: `/kln:status`
- Model health: `healthcheck` or `k-lean models --test`
- System diagnostics: `k-lean doctor -f`
- Timeline: `~/.claude/scripts/timeline-query.sh today`

## Version

K-LEAN v3.0.0 - 2025-12-16
