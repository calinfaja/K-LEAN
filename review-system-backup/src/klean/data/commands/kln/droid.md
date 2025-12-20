---
name: droid
description: "Spawns Claude Agent with role-specific prompts (coder/architect/auditor/researcher/reviewer). Uses expert system prompts from prompts/roles/. Use for domain-specific analysis."
allowed-tools: Bash, Read, Grep, Glob, Task
argument-hint: "[--role ROLE] [--model MODEL] [--parallel] <task>"
---

# /kln:droid - Factory Droid Execution

Specialized AI workers with role-based expertise. Each droid has a specific
focus area and optimized prompts for that domain.

## When to Use

- Task requires domain expertise (security audit, architecture review)
- Role-based analysis is more effective than general review
- Need 3 specialists in parallel (--parallel mode)
- Want model auto-selection optimized for the role

**NOT for:**
- General code review → use `/kln:quick` or `/kln:multi`
- Quick feedback without role specialization → use `/kln:quick`
- Fresh debugging perspectives → use `/kln:rethink`

## Arguments

$ARGUMENTS

## Flags

- `--role, -r` - Droid role: coder, architect, auditor, researcher, reviewer
- `--model, -m` - Specific model (auto-selects best for role if omitted)
- `--parallel, -p` - Run 3 droids in parallel (like old droidAudit)
- `--async, -a` - Run in background

## Available Roles

| Role | Focus | Best Model |
|------|-------|------------|
| `coder` | Implementation, refactoring, optimization | qwen3-coder |
| `architect` | Design patterns, structure, scalability | deepseek-v3-thinking |
| `auditor` | Security, compliance, standards | glm-4.6-thinking |
| `researcher` | Documentation, analysis, exploration | kimi-k2-thinking |
| `reviewer` | Code quality, bugs, best practices | qwen3-coder |

## Execution

Based on the role, spawn a Task agent with role-specific system prompt:

### For `--role coder`:
```
You are a senior software engineer focused on implementation excellence.
Task: $ARGUMENTS

Analyze the code and provide:
1. Implementation improvements
2. Performance optimizations
3. Refactoring suggestions
4. Clean code recommendations
```

### For `--role architect`:
```
You are a software architect focused on system design.
Task: $ARGUMENTS

Analyze and provide:
1. Architectural patterns assessment
2. Scalability considerations
3. Coupling/cohesion analysis
4. Design improvement recommendations
```

### For `--role auditor`:
```
You are a security and compliance auditor.
Task: $ARGUMENTS

Audit for:
1. Security vulnerabilities (OWASP top 10)
2. Compliance with standards
3. Authentication/authorization issues
4. Data handling concerns
```

### For `--role researcher`:
```
You are a technical researcher and documentation specialist.
Task: $ARGUMENTS

Research and document:
1. Codebase exploration findings
2. Architecture documentation
3. API analysis
4. Technical debt inventory
```

Use Task tool with subagent_type="general-purpose" for execution.

## Parallel Mode (--parallel)

When `--parallel` is set, spawn 3 droids simultaneously:
- coder (implementation focus)
- architect (design focus)
- auditor (security focus)

Aggregate their findings into a unified report.

## Examples

```
/kln:droid optimize the data processing pipeline
/kln:droid --role architect design review of API layer
/kln:droid --role auditor security check authentication
/kln:droid --parallel comprehensive analysis
/kln:droid -r researcher document the plugin system
```
