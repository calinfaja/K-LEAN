---
name: agent
description: "Execute SmolKLN agents for specialized analysis. Use /kln:agent <role> \"<task>\" [--model MODEL]"
allowed-tools: [Bash, Read, Glob, Grep]
argument-hint: "<role> \"<task>\""
---

# SmolKLN Agent Executor

Execute specialized agents using Smolagents + LiteLLM.

## Available Agents

| Agent | Focus | Default Model |
|-------|-------|---------------|
| `security-auditor` | Security vulnerabilities | glm-4.6-thinking |
| `code-reviewer` | Code quality & best practices | qwen3-coder |
| `debugger` | Bug hunting & root cause analysis | qwen3-coder |
| `performance-engineer` | Performance optimization | deepseek-v3-thinking |
| `orchestrator` | High-level coordination | deepseek-v3-thinking |
| `arm-cortex-expert` | ARM Cortex-M firmware | qwen3-coder |
| `c-pro` | C/C++ systems programming | qwen3-coder |
| `rust-expert` | Rust systems programming | qwen3-coder |

## Execution

Parse the user's input to extract:
- `ROLE`: The agent role (e.g., "security-auditor")
- `TASK`: The task description (e.g., "audit the authentication module")
- `MODEL` (optional): Override model with --model flag

Then execute:

```bash
~/.claude/scripts/smol-kln.py "$ROLE" "$TASK" --model "$MODEL"
```

## Usage Examples

```
/kln:agent security-auditor "audit the authentication module"
/kln:agent code-reviewer "review error handling in src/"
/kln:agent debugger "investigate memory leak in worker.py" --model deepseek
/kln:agent --list  # List available agents
```

## Model Selection

Models are automatically selected based on agent role. Override with `--model`:
- `qwen` - Fast coding tasks
- `deepseek` - Deep reasoning
- `glm` - Security analysis
- `kimi` - Agentic tasks
- `hermes` - Scripting

## Output Format

The agent will:
1. Search the knowledge database for relevant prior solutions
2. Examine actual code files
3. Provide findings with:
   - 🔴 Critical issues
   - 🟡 Warnings
   - 🟢 Suggestions
   - Specific file:line references
   - Actionable recommendations
