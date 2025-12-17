---
name: multi
description: "Consensus review - 3-5 models in parallel (~60s)"
allowed-tools: Bash, Read
argument-hint: "[--models N|list] [--async] <focus>"
---

# /kln:multi - Multi-Model Consensus Review

Run multiple models in parallel for consensus review. Uses smart model selection
with latency-based ranking and task-aware routing.

## Arguments

$ARGUMENTS

## Flags

- `--models, -n` - Number of models (default: 3) OR comma-separated list
- `--fastest` - Prefer fastest models by latency
- `--async, -a` - Run in background
- `--output, -o` - Output format: text (default), json, markdown

## Execution

```bash
PYTHON=~/.local/share/pipx/venvs/k-lean/bin/python
CORE=~/.claude/k-lean/klean_core.py

# Run multi-model review
$PYTHON $CORE multi $ARGUMENTS
```

Execute the command above and display the aggregated results showing:
1. Models used and their latencies
2. Individual reviews from each model
3. Consensus analysis (common issues, grade agreement)

## Smart Model Selection

The system automatically:
1. Discovers available models from LiteLLM
2. Applies latency-based ranking (fastest first)
3. Boosts models based on task keywords:
   - "security" → prefers glm-4.6-thinking
   - "architecture" → prefers deepseek-v3-thinking
   - "performance" → prefers qwen3-coder
4. Ensures diversity (mix of thinking + fast models)

## Examples

```
/kln:multi security audit                    # 3 models, auto-selected
/kln:multi --models 5 full review            # 5 models
/kln:multi --models qwen3-coder,kimi-k2,glm-4.6-thinking check error handling
/kln:multi --fastest architecture patterns   # Prefer lowest latency
```

## Output Format

Results show:
- Individual reviews per model with latency
- Consensus section with:
  - Grade agreement (A/B/C/D/F)
  - Risk level consensus
  - Common issues (found by 2+ models)
  - Divergent opinions
