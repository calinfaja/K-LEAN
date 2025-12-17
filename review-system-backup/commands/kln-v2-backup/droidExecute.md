---
name: droidExecute
description: "Execute specialized Factory Droid with role-specific expertise and knowledge DB context"
allowed-tools: Bash
argument-hint: "[model] [droid] [prompt] — Execute a Factory Droid with specialized role and KB context"
---

# Factory Droid Execute - Specialized Role Execution

Execute a Factory Droid with specialized expertise and knowledge database context integration.

**Arguments:** $ARGUMENTS

## Argument Format

Parse $ARGUMENTS into three parts:
1. **model** - First word (required)
2. **droid** - Second word (required)
3. **prompt** - Remaining text (required)

## Available Models

Short names (automatically mapped to full LiteLLM names):
- **qwen** - Qwen3 Coder (qwen3-coder)
- **deepseek** - DeepSeek V3 Thinking (deepseek-v3-thinking)
- **glm** - GLM 4.6 Thinking (glm-4.6-thinking)
- **kimi** - Kimi K2 Thinking (kimi-k2-thinking)
- **minimax** - Minimax M2 (minimax-m2)
- **hermes** - Hermes 4 70B (hermes-4-70b)

Or use full model names: qwen3-coder, deepseek-v3-thinking, etc.

## Available Droid Types

Each droid has specialized expertise and system prompts:

- **orchestrator** - System architect & high-level design
  - Focus: Architecture, component interactions, scalability, system coherence

- **code-reviewer** - Code quality & best practices expert
  - Focus: Code quality, readability, design patterns, error handling, testing

- **security-auditor** - Security vulnerability specialist
  - Focus: OWASP Top 10, CWE/SANS Top 25, input validation, crypto, memory safety

- **debugger** - Root cause analysis & bug hunting
  - Focus: Root causes, error patterns, execution flow, memory issues, race conditions

- **arm-cortex-expert** - ARM Cortex-M embedded systems specialist
  - Focus: ARM Cortex-M (M0-M85), CMSIS, RTOS, peripherals, NVIC, power management

- **c-pro** - C language expert for embedded systems
  - Focus: C99/C11/C17, memory management, volatile, bit manipulation, MISRA C

- **rust-expert** - Rust language & safety expert
  - Focus: Ownership, borrowing, memory safety, embedded Rust, unsafe auditing

- **performance-engineer** - Performance optimization & profiling
  - Focus: Algorithm complexity, cache optimization, profiling, embedded constraints

## How It Works

The command will:

1. **Query Knowledge DB** for relevant context based on the prompt
2. **Inject specialized role** system prompt for the selected droid type
3. **Execute** Factory Droid with enriched prompt containing:
   - Droid role and expertise description
   - User's task/prompt
   - Relevant knowledge from database
   - Detailed instructions for tool usage
4. **Save output** to `.claude/kln/droidExecute/` with metadata

## Execution

Use the Bash tool to execute:

```bash
~/.claude/scripts/droid-execute.sh "$ARGUMENTS"
```

The script will:
- Parse and validate all arguments
- Query knowledge DB for context
- Create enriched prompt with droid role
- Execute Factory Droid with custom model
- Display results and save to output directory

## Examples

**Example 1: Security audit with DeepSeek**
```
/kln:droidExecute deepseek security-auditor Review authentication system for vulnerabilities
```

**Example 2: Code review with Qwen**
```
/kln:droidExecute qwen code-reviewer Analyze error handling in main.c
```

**Example 3: ARM Cortex expert with GLM**
```
/kln:droidExecute glm arm-cortex-expert Review interrupt priorities in interrupt_handlers.c
```

**Example 4: Performance analysis with Hermes**
```
/kln:droidExecute hermes performance-engineer Optimize memory usage in data processing pipeline
```

**Example 5: Rust safety audit with Kimi**
```
/kln:droidExecute kimi rust-expert Review unsafe code blocks for soundness
```

## Output

Results are:
- Displayed in the terminal
- Saved to `.claude/kln/droidExecute/[timestamp]_[model]_[snippet].txt`
- Include execution metadata (duration, timestamp, working directory)

## Notes

- Requires `FACTORY_API_KEY` environment variable
- Uses LiteLLM proxy at `http://localhost:4000` by default
- Knowledge DB context automatically included if relevant entries found
- All droids have file reading/searching tools enabled
- Output includes specific file:line references and severity ratings
