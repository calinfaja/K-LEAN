---
name: status
description: "Checks LiteLLM proxy health (localhost:4000), lists available models with cached latency, and verifies Knowledge DB and Serena MCP status. Use to diagnose K-LEAN issues."
allowed-tools: ["Bash", "Read", "Grep", "Glob"]
argument-hint: "[models|health|help]"
---

# /kln:status - K-LEAN System Status

Check the health and status of K-LEAN components and services.

## When to Use

- Check if K-LEAN is working properly
- See available models and their latency
- Diagnose why commands are failing
- Get quick command reference (help subcommand)

**NOT for:**
- Actual code review → use `/kln:quick`, `/kln:multi`, or `/kln:deep`
- CLI troubleshooting → use `k-lean doctor -f`

## Subcommands

- **models** (default) - Show K-LEAN component status
- **health** - Check all external services (LiteLLM, Knowledge DB, Serena)
- **help** - Display quick reference of all K-LEAN commands

## Usage

```
/kln:status          # Shows models/component status
/kln:status models   # Same as above
/kln:status health   # Check all services
/kln:status help     # Show command reference
```

## Implementation

When invoked:

1. **Parse argument** (default to "models" if none provided)

2. **For "models" subcommand:**
   ```bash
   ~/.local/share/pipx/venvs/k-lean/bin/python ~/.claude/k-lean/klean_core.py status
   ```

3. **For "health" subcommand:**
   Check all critical services:

   - **LiteLLM Proxy:**
     ```bash
     curl -s localhost:4000/health
     ```
     Expected: `{"status":"ok"}`

   - **Knowledge Database:**
     ```bash
     ~/.claude/scripts/knowledge-query.sh "test"
     ```
     Check if query returns results or server is accessible

   - **Serena MCP Server:**
     Verify Serena tools are available in the current session

4. **For "help" subcommand:**
   Display this quick reference:

   ```
   K-LEAN Commands
   ==================

   /kln:quick <model> <focus>
     Fast single-model review (~30s)
     Models: qwen, deepseek, glm, minimax, kimi, hermes

   /kln:multi <focus>
     Multi-model consensus review (~60s)
     Uses: qwen, deepseek, glm

   /kln:deep <model> <focus>
     Thorough review with tools (~3min)
     Full context + agentic exploration

   /kln:droid <model> <role> <task>
     Role-based worker execution
     Roles: architect, security, perf, test, doc, refactor

   /kln:doc [summary|detailed]
     Generate session documentation
     Default: summary format

   /kln:remember <lesson>
     End-of-session knowledge capture
     Saves to Serena lessons-learned

   /kln:status [models|health|help]
     System status and health checks
     This command

   Need more info? Try: k-lean --help
   ```

## Example Output

### Models Status
```
K-LEAN Status Dashboard
=======================

Core Components:
  [✓] LiteLLM Proxy (6 models)
  [✓] Knowledge DB (1,234 entries)
  [✓] Serena MCP (2 memory stores)

Models Available:
  qwen/qwen2.5-72b-instruct         [✓] 2.3s
  deepseek/deepseek-chat            [✓] 1.8s
  glm/glm-4-flash                   [✓] 1.2s
  minimax/Minimax-Text-01           [✓] 2.1s
  kimi/moonshot-v1-128k             [✓] 1.9s
  hermes/hermes-3-llama-3.1-405b    [✓] 3.4s
```

### Health Check
```
Service Health Check
====================

[✓] LiteLLM Proxy
    Status: OK
    Endpoint: localhost:4000

[✓] Knowledge Database
    Status: Active
    Server: Running
    Response: 23ms

[✓] Serena MCP
    Status: Connected
    Tools: 2 available
    - lessons-learned
    - architecture-review-system
```

## Error Handling

- If subcommand is invalid, show help message
- If services are down, report specific failures with troubleshooting hints
- Suggest `k-lean doctor -f` for auto-fix of common issues
