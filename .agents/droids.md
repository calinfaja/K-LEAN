# K-LEAN Factory Droids

## Overview

Factory Droids are **specialist AI personas** for domain-specific code reviews.

## Available Droids

| Droid | Specialization | Lines |
|-------|---------------|-------|
| `orchestrator` | Master coordinator | 765 |
| `code-reviewer` | OWASP, SOLID, quality | 258 |
| `security-auditor` | Vulnerabilities, auth, crypto | 89 |
| `debugger` | Root cause analysis | 99 |
| `arm-cortex-expert` | Embedded ARM systems | 320 |
| `c-pro` | C99/C11/POSIX | 275 |
| `rust-expert` | Ownership, lifetimes, safety | 170 |
| `performance-engineer` | Profiling, optimization | 175 |

## Usage

```bash
# Via slash command
/kln:droid security-auditor

# Via script
~/.claude/scripts/droid-execute.sh security-auditor "audit auth module"
```

## Droid Structure

Each droid file (`src/klean/data/droids/*.md`) contains:

```markdown
---
name: droid-name
description: What this droid does
model: coding-qwen  # Preferred model
tools:
  - Read
  - Grep
  - Glob
  - TodoWrite
---

# Droid Name

## Identity
Expert persona description...

## Immediate Actions
```bash
# First commands to run
```

## Review Framework
| Area | Check |
|------|-------|

## Output Format
🔴 Critical | 🟡 Warning | 🟢 Suggestion | 📊 Summary

## Orchestrator Integration
- Before/During/After coordination
```

## Standardized Toolset

All review droids use read-only tools:

```yaml
tools:
  - Read        # Read files
  - LS          # List directories
  - Grep        # Search content
  - Glob        # Find files
  - Execute     # Run commands
  - WebSearch   # Research
  - FetchUrl    # Fetch documentation
  - TodoWrite   # Track findings
  - Task        # Spawn sub-agents
  - GenerateDroid  # Create new droids
```

## Orchestrator

The `orchestrator` droid coordinates other droids:

1. **Analyze task** - Determine which specialists needed
2. **Spawn droids** - Run relevant specialists
3. **Aggregate results** - Combine findings
4. **Prioritize** - Rank by severity and agreement

## Creating New Droids

1. Copy template:
   ```bash
   cp src/klean/data/droids/TEMPLATE.md src/klean/data/droids/new-droid.md
   ```

2. Customize:
   - Identity and expertise
   - Immediate actions (first bash commands)
   - Review framework (checklist table)
   - Output format

3. Sync:
   ```bash
   k-lean sync
   ```

## Template Guidelines

Based on Factory.ai docs and Anthropic research:

- **Optimal length**: 300-1000 tokens
- **Structure**: "Goldilocks zone" - not too rigid, not too vague
- **Subtask decomposition**: "A droid is only as good as its plan"
- **Output format**: Consistent severity indicators

## Integration with Factory CLI

If Factory CLI is installed, droids can run in agentic mode:

```bash
# Check Factory CLI
k-lean status  # Shows Factory CLI version

# Agentic execution
droid security-auditor "full security audit"
```

## File Locations

- Source: `src/klean/data/droids/*.md`
- Installed: `~/.factory/droids/*.md` (symlinked)
- Template: `src/klean/data/droids/TEMPLATE.md`

## Implementation

Script: `src/klean/data/scripts/droid-execute.sh`

**Key function:**
```bash
get_droid_system_prompt() {
    local droid_file="$HOME/.factory/droids/${droid}.md"
    # Extract content after YAML frontmatter
    local end_line=$(grep -n "^---$" "$droid_file" | sed -n '2p' | cut -d: -f1)
    tail -n +"$((end_line + 1))" "$droid_file"
}
```

---
*See [hooks.md](hooks.md) for Claude Code integration*
