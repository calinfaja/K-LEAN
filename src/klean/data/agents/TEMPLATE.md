# Optimal Agent.md Structure Guide

## Research Summary

Based on comprehensive research of Factory.ai documentation, Anthropic's context engineering guide, and industry best practices for autonomous AI agents.

---

## Key Principles for Autonomous Agents

### 1. Planning-First Architecture (Factory.ai)
> "A agent is only as good as its plan."

- **Subtask decomposition**: Break complex tasks into manageable steps
- **Model predictive control**: Plan → Execute → Validate → Adjust
- **Environmental grounding**: Stay connected to actual codebase state

### 2. Goldilocks Zone (Anthropic)
> "The right altitude is between hardcoded brittle logic and vague high-level guidance."

- Not too specific (fragile, high maintenance)
- Not too vague (fails to guide behavior)
- Minimal set of information that fully outlines expected behavior

### 3. Consistency Across Components (Augment Code)
- System prompt, tool definitions, and behavior must align
- Working directory, capabilities, and constraints must be consistent

### 4. Structured Output (Factory)
- Organize prompts to emit clear sections like `Summary:` and `Findings:`
- Task tool UI can summarize results clearly

---

## Optimal Agent.md Template

```markdown
---
name: <agent-name>
description: >
  <Clear 1-2 sentence description of what this agent does, when to use it,
  and what makes it unique. Include "Use PROACTIVELY when..." trigger.>
model: inherit
tools: ["knowledge_search", "web_search", "visit_webpage", "read_file", "search_files", "grep"]
---

# Role & Identity

You are a [ROLE] specializing in [DOMAIN]. You have deep expertise in [SPECIFIC_AREAS].

## Core Competencies
- [Competency 1]
- [Competency 2]
- [Competency 3]

---

# Immediate Actions

When invoked, ALWAYS:
1. **Gather Context**: [Specific commands/tools to run]
2. **Analyze State**: [What to check first]
3. **Create Plan**: Use TodoWrite to create execution plan
4. **Execute**: Follow plan systematically
5. **Validate**: Verify results meet requirements

---

# Process & Methodology

## Step 1: [Phase Name]
[Detailed instructions for this phase]

## Step 2: [Phase Name]
[Detailed instructions for this phase]

## Step 3: [Phase Name]
[Detailed instructions for this phase]

---

# Tool Usage Patterns

## When to Use Each Tool
| Tool | Use For | Example |
|------|---------|---------|
| Read | [Purpose] | [Example] |
| Grep | [Purpose] | [Example] |
| Execute | [Purpose] | [Example] |

## Tool Chains
- **Pattern Discovery**: Glob → Read → Grep
- **Implementation**: Edit → Execute (test) → Validate
- **Documentation**: Read → Create → Edit

---

# Output Format

Structure ALL responses with:

## Summary
[1-3 bullet points of key findings/actions]

## Findings
### [Category] - [Severity: Critical/Warning/Info]
- **Location**: [file:line]
- **Issue**: [Description]
- **Impact**: [Why it matters]
- **Fix**: [Specific solution]

## Actions Taken
- [Action 1]
- [Action 2]

## Recommendations
1. [Priority recommendation]
2. [Secondary recommendation]

## Next Steps
- [What should happen next]
- [Dependencies or blockers]

---

# Quality Standards

## Always
- Provide specific file:line references
- Include concrete code examples
- Validate changes work before completing
- Use TodoWrite to track progress

## Never
- Make assumptions without verification
- Skip validation steps
- Provide generic feedback
- Leave tasks incomplete

---

# Orchestrator Integration

When working as part of an orchestrated task:

## Before Starting
- Review complete task context from orchestrator
- Identify dependencies on other agents' work
- Check for existing artifacts from previous phases

## During Execution
- Document decisions for orchestrator records
- Flag issues that may block subsequent phases
- Provide clear status updates

## After Completion
- Summarize what was accomplished
- List any remaining work or blockers
- Specify if other agents are needed

## Context Requirements
Always provide:
- Complete analysis with severity levels
- List of actions taken with explanations
- Specific code patterns or configurations used
- Next phase requirements

## Example Orchestrated Output
\`\`\`
✅ [Task Type] Complete:

Summary:
- [Key finding 1]
- [Key finding 2]

Actions Taken:
- [Action with file:line reference]
- [Action with file:line reference]

Quality Assessment:
- Critical: [count] issues
- Warning: [count] issues
- Info: [count] suggestions

Next Phase Suggestion:
- [agent-name] should [task]
- [agent-name] should [task]
\`\`\`

---

# Domain-Specific Knowledge

## [Topic 1]
[Detailed domain knowledge]

## [Topic 2]
[Detailed domain knowledge]

## Common Patterns
[Patterns specific to this domain]

## Anti-Patterns to Avoid
[What NOT to do]

---

# Examples

## Example 1: [Scenario]
**Input**: [User request]
**Process**: [How agent handles it]
**Output**: [What agent produces]

## Example 2: [Scenario]
**Input**: [User request]
**Process**: [How agent handles it]
**Output**: [What agent produces]
```

---

## Required Sections (Minimum Viable Agent)

| Section | Purpose | Required |
|---------|---------|----------|
| YAML Frontmatter | Metadata, tools | ✅ Yes |
| Role & Identity | Who the agent is | ✅ Yes |
| Immediate Actions | First steps when invoked | ✅ Yes |
| Process & Methodology | How to execute tasks | ✅ Yes |
| Output Format | Consistent structured output | ✅ Yes |
| Quality Standards | What to always/never do | ✅ Yes |
| Orchestrator Integration | Multi-agent coordination | ✅ Yes |

## Optional Sections (Enhanced Agents)

| Section | Purpose | When to Include |
|---------|---------|-----------------|
| Tool Usage Patterns | Explicit tool chains | Complex workflows |
| Domain-Specific Knowledge | Deep expertise | Specialized domains |
| Examples | Concrete demonstrations | New or complex agents |
| Memory System | Learning from past | Orchestrator-level agents |

---

## Tools Recommendations

### Standard Toolset (All SmolKLN Agents)
```yaml
tools: ["knowledge_search", "web_search", "visit_webpage", "read_file", "search_files", "grep"]
```

**Read-only by design** - agents analyze and report, they don't modify code directly.

| Tool | Purpose | Example |
|------|---------|---------|
| `knowledge_search` | Query project Knowledge DB for prior solutions | `knowledge_search("JWT authentication patterns")` |
| `web_search` | DuckDuckGo search for docs/articles | `web_search("OWASP JWT best practices 2024")` |
| `visit_webpage` | Fetch and parse webpage content | `visit_webpage("https://owasp.org/...")` |
| `read_file` | Read file contents | `read_file("src/auth/login.py")` |
| `search_files` | Find files by glob pattern | `search_files("*.py", recursive=True)` |
| `grep` | Search text patterns in files | `grep("password", file_pattern="*.py")` |

### Tool Chains
- **Research**: `knowledge_search` → `web_search` → `visit_webpage`
- **Code Analysis**: `search_files` → `read_file` → `grep`
- **Full Review**: Knowledge DB + Web research + Local analysis

---

## Size Guidelines

Based on analysis of effective agents:

| Agent Type | Optimal Lines | Optimal KB |
|------------|---------------|------------|
| Orchestrator | 400-800 | 15-30 KB |
| Specialist (Complex) | 150-300 | 6-12 KB |
| Specialist (Standard) | 80-150 | 3-6 KB |
| Minimal (Focused) | 40-80 | 1.5-3 KB |

**Key insight**: c-pro at 35 lines is too minimal. arm-cortex-expert at 265 lines is well-sized for its complexity.

---

## Common Issues to Avoid

### 1. Hardcoded Paths
❌ `/Users/besi/.factory/orchestrator/memory/`
✅ `~/.factory/orchestrator/memory/`

### 2. Missing Tools
❌ `tools: []` (agent can't do anything)
✅ `tools: ["Read", "Grep", "Glob", ...]`

### 3. No Orchestrator Integration
❌ Just task instructions
✅ Before/During/After sections for multi-agent coordination

### 4. Vague Instructions
❌ "Review the code"
✅ "Run `git diff` to see changes, use Grep to find patterns, provide file:line references"

### 5. No Output Structure
❌ Free-form responses
✅ `## Summary`, `## Findings`, `## Recommendations` sections

---

## Sources

- [Factory Agent Documentation](https://docs.factory.ai/cli/configuration/custom-agents)
- [Anthropic Context Engineering Guide](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Anthropic Building Effective Agents](https://www.anthropic.com/research/building-effective-agents)
- [Augment Code: 11 Prompting Techniques](https://www.augmentcode.com/blog/how-to-build-your-agent-11-prompting-techniques-for-better-ai-agents)
- [AGENTS.md Standard](https://agents.md/)
- [Factory Power User Guide](https://docs.factory.ai/guides/power-user/setup-checklist)
