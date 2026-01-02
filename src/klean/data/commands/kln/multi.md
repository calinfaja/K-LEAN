---
name: multi
description: "Runs 3-5 LiteLLM models in parallel via asyncio, calculates grade/risk consensus, and groups findings by confidence level (high/medium/low). Use when multiple perspectives matter."
allowed-tools: Bash, Read
argument-hint: "[--models N|list] [--async] <focus>"
---

# /kln:multi - Multi-Model Consensus Review

Run multiple models in parallel for consensus review. Uses smart model selection
with latency-based ranking and task-aware routing.

## When to Use

- Important decisions needing multiple perspectives
- Validation through consensus (2+ models agree)
- Pre-release or PR reviews where confidence matters
- When you want high/medium/low confidence grouping

**NOT for:**
- Quick feedback when time is short → use `/kln:quick`
- Need to actually read files for evidence → use `/kln:agent`
- Domain-specific expertise needed → use `/kln:agent`

## Arguments

$ARGUMENTS

## Flags

- `--models, -n` - Number of models (default: 3) OR comma-separated model names
- `--telemetry` - Enable Phoenix telemetry tracing
- `--output, -o` - Output format: text (default), json, markdown

## Execution

```bash
PYTHON=~/.local/share/pipx/venvs/kln-ai/bin/python
CORE="-m klean.core"

# Run multi-model review
$PYTHON $CORE multi $ARGUMENTS
```

Execute the command above and display the aggregated results showing:
1. Models used and their latencies
2. Individual reviews from each model
3. Consensus analysis (common issues, grade agreement)

## Model Discovery

Models are **dynamically discovered** from LiteLLM proxy. If user gives partial name (e.g. "qwen"), run `curl -s localhost:4000/models | jq -r '.data[].id'` to find full match.

The system automatically:
1. Queries LiteLLM for available models at runtime
2. Applies latency-based ranking (fastest first)
3. Boosts models based on task keywords (security, architecture, performance)
4. Ensures diversity (mix of thinking + fast models)

## Examples

```
/kln:multi security audit                    # 3 models, auto-selected
/kln:multi --models 5 full review            # 5 models
/kln:multi --models qwen3-coder,kimi-k2,deepseek-r1 check error handling
/kln:multi --models gemini-2.5-flash,grok-4.1-fast --telemetry review auth
```

## Output Format

Results show:
- Individual reviews per model with latency
- Consensus section with:
  - Grade agreement (A/B/C/D/F)
  - Risk level consensus
  - Common issues (found by 2+ models)
  - Divergent opinions
