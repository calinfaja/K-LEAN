# Factory Droid Integration System

## Overview

Factory Droid is an AI coding agent that integrates with K-LEAN to provide fast, agentic code reviews and analysis. Unlike headless Claude which requires spawning full browser sessions, Factory Droid runs as a lightweight CLI tool with built-in file reading, code search, and analysis capabilities.

**Key Benefits:**
- **Speed**: 30s-2min vs 3-15min for headless Claude reviews
- **Agentic Tools**: Built-in Read, Grep, Glob, LS for file navigation
- **Parallel Execution**: Run multiple models simultaneously
- **LiteLLM Integration**: Uses your existing localhost:4000 proxy
- **Specialist Personas**: Pre-configured expert droids for different tasks

**Architecture Flow:**
```
User → Claude → /kln:droid command → droid-review.sh
     → Factory Droid CLI → LiteLLM Proxy (localhost:4000)
     → Model Provider (NanoGPT/OpenRouter/etc)
     → Results saved to /tmp/droid-audit-*
```

## Available Specialists

Factory Droid supports specialist personas that can be customized via markdown configuration files:

| Specialist | Focus Area | Tools Available | Use Case |
|-----------|------------|----------------|----------|
| **code-reviewer** | Code quality, bugs, best practices | Read, LS, Grep, Glob | General code review with file:line references |
| **security-auditor** | OWASP compliance, vulnerabilities | Read, LS, Grep, Glob, WebSearch | Security audit with CWE references |
| **orchestrator** | Master coordinator, task delegation | All tools | Complex multi-step analysis |
| **debugger** | Root cause analysis, error tracing | Read, Grep, Glob, Bash | Bug investigation and stack trace analysis |
| **arm-cortex-expert** | Embedded systems, microcontrollers | Read, Grep, Glob, WebSearch | ARM Cortex-M firmware review |
| **c-pro** | C systems programming | Read, Grep, Glob | C code review, memory safety |
| **rust-expert** | Safe systems programming | Read, Grep, Glob | Rust code review, ownership analysis |
| **performance-engineer** | Optimization, profiling | Read, Grep, Glob, Bash | Performance bottleneck identification |

### Specialist Configurations

Specialists are defined in markdown files at `/home/calin/claudeAgentic/review-system-backup/config/factory-droids/`:

**Example: code-reviewer.md**
```yaml
---
name: code-reviewer
description: Reviews code for quality, security, and best practices
model: inherit
tools: ["Read", "LS", "Grep", "Glob"]
---
You are a senior code reviewer performing thorough code analysis.

CRITICAL: You MUST use your tools to read the actual source code before making any assessments.

## Required Workflow
1. Discover Files: Use Glob or LS to find relevant files
2. Read Content: Use Read to examine each file's actual content
3. Search Patterns: Use Grep to find specific patterns
4. Analyze: Based on ACTUAL file contents, provide detailed feedback
```

**Example: security-auditor.md**
```yaml
---
name: security-auditor
description: Security-focused code audit with OWASP awareness
model: inherit
tools: ["Read", "LS", "Grep", "Glob", "WebSearch"]
---
You are a security auditor specializing in code vulnerability analysis.

## Security Checklist
- Command injection vectors
- SQL/NoSQL injection
- XSS vulnerabilities
- Path traversal
- Hardcoded secrets/credentials
- Insecure cryptography
```

## Usage

### K-LEAN Commands

| Command | Description | Execution Time |
|---------|-------------|----------------|
| `/kln:droid [model] [focus]` | Single model review (interactive) | 30s-1min |
| `/kln:asyncDroid [model] [focus]` | Single model (background) | 30s-1min |
| `/kln:droidAudit [focus]` | 3 models in parallel | 1-2min |
| `/kln:asyncDroidAudit [focus]` | 3 models parallel (background) | 1-2min |

### Examples

**Single Model Review:**
```bash
/kln:droid qwen3-coder Review authentication logic for security issues
```

**Parallel Multi-Model Audit:**
```bash
/kln:droidAudit Comprehensive security and quality review
```

**Background Async Review:**
```bash
/kln:asyncDroid deepseek-v3-thinking Analyze architecture and design patterns
```

### Direct CLI Usage

You can also use Factory Droid directly from the command line:

```bash
# Single review with specific model
~/.claude/scripts/droid-review.sh "qwen3-coder Review for bugs" /path/to/project

# Parallel review with 3 models
~/.claude/scripts/parallel-droid-review.sh "Security audit" /path/to/project

# Direct droid exec (requires FACTORY_API_KEY)
droid exec --model "custom:qwen3-coder" "Review this codebase for bugs"
```

## Architecture

### System Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         User Request                         │
│            "/kln:droidAudit security review"                 │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Claude (Main Agent)                       │
│   • Parses command arguments (model, focus)                 │
│   • Invokes droid-review.sh or parallel-droid-review.sh     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│             Shell Scripts (Bash Orchestration)               │
│                                                              │
│  ┌──────────────────┐        ┌──────────────────┐          │
│  │ droid-review.sh  │        │parallel-droid.sh │          │
│  │ • Validates model│        │ • Spawns 3 droids│          │
│  │ • Sets context   │        │ • Runs in parallel│         │
│  │ • Single droid   │        │ • Aggregates      │         │
│  └────────┬─────────┘        └────────┬─────────┘          │
│           │                           │                     │
│           └───────────┬───────────────┘                     │
└───────────────────────┼─────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────┐
│                  Factory Droid CLI                          │
│   • Command: droid exec --model "custom:MODEL" "PROMPT"    │
│   • Tools: Read, Grep, Glob, LS, WebSearch                 │
│   • Agentic file navigation                                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              LiteLLM Proxy (localhost:4000)                 │
│   • Model routing and load balancing                       │
│   • API key management                                     │
│   • Rate limiting and retries                              │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  NanoGPT    │  │ OpenRouter  │  │   Ollama    │
│  Provider   │  │  Provider   │  │  (Local)    │
└─────────────┘  └─────────────┘  └─────────────┘

         Results flow back up the stack
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│               Output Storage & Display                       │
│   • Saved to: /tmp/droid-audit-TIMESTAMP/                  │
│   • Format: MODEL_NAME.md                                   │
│   • Displayed to user in Claude chat                        │
└─────────────────────────────────────────────────────────────┘
```

### Component Details

**1. K-LEAN Command Layer**
- Command definitions in `/home/calin/claudeAgentic/review-system-backup/commands/kln/`
- Parse user arguments (model, focus)
- Validate model availability
- Invoke appropriate shell script

**2. Shell Script Orchestration**
- `droid-review.sh`: Single model execution
- `parallel-droid-review.sh`: Multi-model parallel execution
- Dynamic model discovery via `get-models.sh`
- Prompt engineering for tool usage enforcement

**3. Factory Droid CLI**
- Binary at `/home/calin/.local/bin/droid`
- Exec mode: Non-interactive, automation-friendly
- Built-in tools for file operations
- Session management and resume capability

**4. LiteLLM Integration**
- Proxy running at `localhost:4000`
- Configuration at `~/.config/litellm/`
- Environment: `FACTORY_API_KEY` required
- Model routing to various providers

## Model Mapping

Factory Droid uses LiteLLM's `custom:` prefix to route to models configured in your LiteLLM proxy:

| Short Name | Full LiteLLM Model | Provider | Specialization |
|-----------|-------------------|----------|----------------|
| `qwen3-coder` | `nanogpt/Qwen/Qwen3-Coder` | NanoGPT | Code quality, bug detection |
| `deepseek-v3-thinking` | `nanogpt/deepseek-ai/DeepSeek-V3` | NanoGPT | Architecture, design patterns |
| `glm-4.6-thinking` | `nanogpt/THUDM/glm-4.6-thinking` | NanoGPT | Standards, compliance, security |
| `kimi-k2-thinking` | `nanogpt/moonshot-ai/Kimi-K2` | NanoGPT | Agent tasks, complex reasoning |
| `minimax-m2` | `nanogpt/MiniMax/MiniMax-M2` | NanoGPT | Research, exploration |
| `hermes-4-70b` | `nanogpt/NousResearch/Hermes-4-70b` | NanoGPT | Scripting, automation |

### Dynamic Model Discovery

Models are discovered dynamically at runtime:

```bash
# List available models from LiteLLM
~/.claude/scripts/get-models.sh

# Get first N healthy models
~/.claude/scripts/get-healthy-models.sh 3
```

This allows the system to adapt to your LiteLLM configuration without hardcoding model lists.

## Output Storage

### Location Structure

```
/tmp/droid-audit-YYYYMMDD_HHMMSS/
├── qwen3-coder.md
├── deepseek-v3-thinking.md
└── glm-4.6-thinking.md
```

### Output Format

Each model's output is saved as markdown with metadata:

```markdown
# qwen3-coder Review

**Focus:** Comprehensive security and quality review
**Time:** Wed Dec 10 22:30:15 PST 2025

---

[Review content with file:line references...]

---
*Completed at Wed Dec 10 22:31:42 PST 2025*
```

### Output Contents

Factory Droid reviews include:

1. **File Discovery**: List of files examined
2. **Specific Findings**:
   - File path and line number
   - Severity level (CRITICAL/WARNING/SUGGESTION)
   - Description and impact
   - Remediation steps
3. **Code Grade**: A-F with justification
4. **Summary**: Key issues and recommendations

**Example Finding:**
```
[CRITICAL] scripts/deploy.sh:42
Description: Command injection via unquoted variable expansion
Impact: Attacker could execute arbitrary commands
Fix: Quote variable: "$USER_INPUT" instead of $USER_INPUT
```

## Knowledge DB Integration

Factory Droid reviews can leverage K-LEAN's knowledge database for context:

### Automatic Context Injection

When you run a droid review, relevant knowledge can be injected into the prompt:

```bash
# Search knowledge DB for relevant context
CONTEXT=$(~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-search.py "security patterns" --format inject)

# Include in droid prompt
droid exec --model "custom:security-auditor" "Review with context: $CONTEXT"
```

### Manual Knowledge Search

Before running reviews, check for prior findings:

```bash
# Check if we've reviewed similar code before
~/.claude/scripts/knowledge-query.sh "authentication security"

# Then run focused review
/kln:droid security-auditor Review authentication based on previous findings
```

### Post-Review Knowledge Capture

Save valuable findings to knowledge DB:

```bash
# User command after reviewing droid output
SaveThis Security issue found: SQL injection in user_query.py line 42
```

## Customization

### Adding New Specialists

1. **Create Specialist Definition**

Create `/home/calin/claudeAgentic/review-system-backup/config/factory-droids/NEW_SPECIALIST.md`:

```yaml
---
name: database-expert
description: Database schema and query optimization specialist
model: inherit
tools: ["Read", "Grep", "Glob", "WebSearch"]
---
You are a database expert specializing in schema design and query optimization.

## Analysis Workflow
1. Use Glob to find database files (*.sql, migrations/*, models/*)
2. Use Read to examine schema definitions
3. Use Grep to find query patterns
4. Analyze for:
   - Missing indexes
   - N+1 query problems
   - Inefficient joins
   - Missing constraints

## Output Format
[SEVERITY] file:line - Issue description
Recommendation: Specific optimization suggestion
```

2. **Update Model Mapping** (if needed)

Add to `droid-review.sh` validation if you want a specific model default:

```bash
case "$SPECIALIST" in
    database-expert)
        MODEL="deepseek-v3-thinking"  # Good at data structures
        ;;
esac
```

3. **Create K-LEAN Command** (optional)

Create `/home/calin/claudeAgentic/review-system-backup/commands/kln/databaseReview.md`:

```yaml
---
name: databaseReview
description: "Database schema and query optimization review"
allowed-tools: Bash
argument-hint: "[focus] — Uses database-expert specialist"
---

# Database Review

Run specialized database review with Factory Droid.

**Arguments:** $ARGUMENTS

```bash
~/.claude/scripts/droid-review.sh "database-expert $ARGUMENTS" "$(pwd)"
```
```

### Customizing Prompts

Edit specialist markdown files to change behavior:

**Example: Make security-auditor more strict**

```yaml
## Security Checklist
- [ ] Command injection vectors
- [ ] SQL/NoSQL injection
- [ ] XSS vulnerabilities
- [ ] Path traversal
- [ ] Hardcoded secrets/credentials
- [ ] Insecure cryptography
- [ ] Race conditions
- [ ] Resource exhaustion
- [ ] Missing input validation
- [ ] Improper error handling
+ [ ] CSRF protection
+ [ ] Rate limiting
+ [ ] Authentication bypass paths
+ [ ] Insufficient logging
```

### Configuring Tool Access

Control which tools specialists can use:

```yaml
# Read-only specialist (safe for untrusted code)
tools: ["Read", "Glob"]

# Full analysis with web research
tools: ["Read", "LS", "Grep", "Glob", "WebSearch"]

# Dangerous: can execute code
tools: ["Read", "Grep", "Glob", "Bash"]
```

## Configuration Requirements

### Environment Variables

```bash
# Required: Factory Droid API key
export FACTORY_API_KEY=fk-YOUR_KEY_HERE

# Optional: Override LiteLLM URL
export LITELLM_BASE_URL=http://localhost:4000
```

Add to `~/.bashrc` or `~/.profile` for persistence.

### LiteLLM Proxy Setup

Ensure LiteLLM is running with your desired models:

```bash
# Check LiteLLM status
curl http://localhost:4000/health

# View available models
curl http://localhost:4000/models

# Or use helper script
~/.claude/scripts/get-models.sh
```

Configuration at `~/.config/litellm/config.yaml`:

```yaml
model_list:
  - model_name: qwen3-coder
    litellm_params:
      model: nanogpt/Qwen/Qwen3-Coder
      api_key: os.environ/NANOGPT_API_KEY

  - model_name: deepseek-v3-thinking
    litellm_params:
      model: nanogpt/deepseek-ai/DeepSeek-V3
      api_key: os.environ/NANOGPT_API_KEY
```

### Factory Droid Installation

```bash
# Install via npm
npm install -g @factory-ai/factory-cli

# Verify installation
droid --version

# Configure API key
export FACTORY_API_KEY=fk-YOUR_KEY
```

## Performance Comparison

| Review Type | Tool | Models | Time | Cost | File Coverage |
|------------|------|--------|------|------|---------------|
| Quick | Headless Claude | 1 | 3-5min | $0.05 | Limited |
| Deep | Headless Claude | 1 | 5-10min | $0.10 | Good |
| Parallel | Headless Claude | 3 | 10-15min | $0.30 | Good |
| Quick | Factory Droid | 1 | 30s-1min | $0.01 | Excellent |
| Deep | Factory Droid | 1 | 1-2min | $0.02 | Excellent |
| Parallel | Factory Droid | 3 | 1-2min | $0.06 | Excellent |

**Key Advantages:**
- 5-10x faster execution
- Better file coverage (agentic tools)
- Lower cost per review
- Can run in parallel without browser overhead
- Better for CI/CD integration

## Troubleshooting

### Common Issues

**1. "FACTORY_API_KEY not set"**
```bash
# Solution: Export API key
export FACTORY_API_KEY=fk-YOUR_KEY
# Add to ~/.bashrc for persistence
echo 'export FACTORY_API_KEY=fk-YOUR_KEY' >> ~/.bashrc
```

**2. "Invalid model 'xyz'"**
```bash
# Solution: Check available models
~/.claude/scripts/get-models.sh

# Use exact model name from list
/kln:droid qwen3-coder Review this code
```

**3. "Connection refused to localhost:4000"**
```bash
# Solution: Start LiteLLM proxy
litellm --config ~/.config/litellm/config.yaml

# Or use systemd service if configured
systemctl --user start litellm
```

**4. "Droid command not found"**
```bash
# Solution: Install Factory Droid CLI
npm install -g @factory-ai/factory-cli

# Verify installation
which droid
droid --version
```

**5. Generic responses without file references**
```bash
# Issue: Droid didn't use tools to read files
# Solution: Prompt engineering enforces tool usage
# The scripts already include "MUST use your tools" prompts
# If still getting generic responses, check model capability
```

## Best Practices

### When to Use Factory Droid

**Use Factory Droid for:**
- Quick code reviews (< 5min turnaround)
- Security audits requiring file scanning
- Parallel multi-model analysis
- CI/CD pipeline integration
- Frequent incremental reviews

**Use Headless Claude for:**
- Browser-based testing
- Complex multi-step workflows requiring user interaction
- Deep architectural analysis requiring many iterations

### Review Workflow

1. **Start Broad**: Use `/kln:droidAudit` for comprehensive parallel review
2. **Focus Deep**: Based on findings, run specialist reviews
3. **Capture Knowledge**: Save important findings to knowledge DB
4. **Iterate**: Run focused reviews on modified code

**Example Session:**
```bash
# 1. Initial broad review
/kln:droidAudit Comprehensive security and quality review

# 2. Review output, identify security concerns in auth module
/kln:droid security-auditor Deep dive on authentication security

# 3. Save critical finding
SaveThis SQL injection vulnerability in auth/login.py:line 42

# 4. After fix, verify
/kln:droid qwen3-coder Verify SQL injection fix in auth module
```

### Specialist Selection

| Need | Recommended Specialist | Model Preference |
|------|----------------------|------------------|
| General code quality | code-reviewer | qwen3-coder |
| Security audit | security-auditor | glm-4.6-thinking |
| Architecture review | orchestrator | deepseek-v3-thinking |
| Bug investigation | debugger | qwen3-coder |
| Performance issues | performance-engineer | deepseek-v3-thinking |
| Embedded systems | arm-cortex-expert | qwen3-coder |
| C code review | c-pro | qwen3-coder |
| Rust code review | rust-expert | deepseek-v3-thinking |

## See Also

- [LiteLLM Configuration](~/.config/litellm/README.md)
- [Knowledge Database System](~/.claude/CLAUDE.md#knowledge-database-system)
- [Review System](~/.claude/CLAUDE.md#review-system)
- [Factory Droid Documentation](https://docs.factory.ai/)
