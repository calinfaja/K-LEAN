---
name: deep
description: "Spawns headless Claude Agent with Read/Grep/Glob/Bash tools for evidence-based review (~3min). Actually reads files, searches patterns, and provides findings with code snippets."
allowed-tools: Bash, Read, Grep, Glob, Task
argument-hint: "[--models N] [--async] <focus>"
---

# /kln:deep - Deep Code Review with Tools

Thorough review using Claude Agent SDK with full tool access (Read, Grep, Glob, Bash).
Slower but can analyze actual codebase, follow references, and verify patterns.

## Arguments

$ARGUMENTS

## Flags

- `--models, -n` - Number of parallel reviews (default: 1, max: 3)
- `--async, -a` - Run in background
- `--save` - Save results to knowledge DB

## Execution Method

This command spawns a headless Claude instance via the SDK with:
- Full file system access (Read, Grep, Glob)
- Bash for running tests/linters
- Serena MCP for semantic code analysis

## How It Works

1. **Context Gathering**: Claude reads relevant source files
2. **Pattern Search**: Searches for common issues, anti-patterns
3. **Dependency Analysis**: Traces imports and references
4. **Verification**: Runs available linters/tests if present
5. **Report Generation**: Comprehensive review with evidence

## Execution

For a deep review, spawn a Task agent with the following prompt:

```
Perform a thorough code review with focus on: $ARGUMENTS

You have access to Read, Grep, Glob, and Bash tools.

Steps:
1. First, explore the codebase structure (use Glob to find relevant files)
2. Read the main source files related to the focus area
3. Search for potential issues using Grep
4. Check for related code and dependencies
5. If tests exist, note their coverage

Provide a comprehensive review with:
- GRADE: A/B/C/D/F
- RISK: LOW/MEDIUM/HIGH/CRITICAL
- CRITICAL ISSUES: List with file:line references
- WARNINGS: Medium-priority concerns
- SUGGESTIONS: Improvements
- EVIDENCE: Code snippets showing issues
```

Use the Task tool with subagent_type="general-purpose" to execute this review.

## Examples

```
/kln:deep security audit of authentication module
/kln:deep --models 3 comprehensive pre-release review
/kln:deep --async full codebase architecture analysis
```

## When to Use

- Thorough investigation requiring actual file access
- Evidence-based findings with file:line references
- Tracing dependencies and imports across codebase
- Pre-release security/architecture audits
- When you need code snippets proving issues

**NOT for:**
- Quick feedback when time is short → use `/kln:quick`
- Just want multiple opinions without file access → use `/kln:multi`
- Domain-specific role-based analysis → use `/kln:droid`
