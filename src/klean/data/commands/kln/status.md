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
- Actual code review → use `/kln:quick`, `/kln:multi`, or `/kln:agent`
- CLI troubleshooting → use `kln doctor -f`

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
   ~/.local/share/pipx/venvs/kln-ai/bin/python ~/.claude/kln/klean_core.py status
   ```

3. **For "health" subcommand:**
   Check all critical services using `kln doctor`:

   ```bash
   kln doctor
   ```

   Or check individually:
   - **LiteLLM Proxy:** `kln model list` (lists models if healthy)
   - **Knowledge Database:** Use KB Python API or check server port file
   - **Serena MCP Server:** Verify Serena tools are available in session

4. **For "help" subcommand:**
   Display this quick reference:

   ```
   K-LEAN Commands
   ==================

   /kln:quick <focus>        Fast single-model review (~30s)
   /kln:multi <focus>        Multi-model consensus (~60s)
   /kln:rethink [context]    Contrarian debugging (~20s)
   /kln:agent <role> <task>  Specialist agent (~2min)
   /kln:doc <title>          Session documentation
   /kln:learn [topic]        Mid-session knowledge capture
   /kln:remember             End-of-session capture
   /kln:status [sub]         System health (this command)
   /kln:help                 Full command reference

   Need more info? Try: /kln:help or kln --help
   ```

## Example Output

### Models Status
```
K-LEAN Status Dashboard
=======================

Core Components:
  [[OK]] LiteLLM Proxy (N models)
  [[OK]] Knowledge DB (N entries)
  [[OK]] Serena MCP (connected)

Models Available:
  model-a                          [[OK]] 1.2s
  model-b                          [[OK]] 2.3s
  model-c                          [[OK]] 1.8s
  ...                              (varies by provider)
```

### Health Check
```
Service Health Check
====================

[[OK]] LiteLLM Proxy
    Status: OK
    Endpoint: localhost:4000

[[OK]] Knowledge Database
    Status: Active
    Server: Running
    Response: 23ms

[[OK]] Serena MCP
    Status: Connected
    Tools: 2 available
    - lessons-learned
    - architecture-review-system
```

## Error Handling

- If subcommand is invalid, show help message
- If services are down, report specific failures with troubleshooting hints
- Suggest `kln doctor -f` for auto-fix of common issues
