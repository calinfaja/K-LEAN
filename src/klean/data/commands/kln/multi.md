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

- `-n, --models` - Number of models (default: 3) OR comma-separated model names
- `-c, --context-file` - File containing code to review (alternative to stdin)
- `-o, --output` - Output format: text (default), json, markdown
- `--telemetry` - Enable Phoenix telemetry tracing
- `--async, -a` - Run in background (continue working, check results later)

## Background Execution

To run multi-model reviews in background:
- Add `--async` flag: `/kln:multi --async "security audit"`
- Or say: "run this in background"
- Press `Ctrl+B` while command is running to background it

Background tasks return immediately with a task ID. Check status with `/tasks` or ask "what's the review status?"

## Your Job

Understand what user wants reviewed and gather the relevant code:

| User wants | You gather |
|------------|------------|
| "current changes" / "my changes" | `git diff` (unstaged) + `git diff --cached` (staged) |
| "last commit" | `git diff HEAD~1..HEAD` |
| "feature X" / "the auth module" | Read relevant files, get recent changes |
| "this file" / "file.py" | Read the file content |
| "PR" / "branch changes" | `git diff main..HEAD` |

## Execution

```bash
PYTHON=~/.local/share/pipx/venvs/kln-ai/bin/python
CORE=~/.claude/kln/klean_core.py

# 1. Gather code into temp file
git diff HEAD~1..HEAD | head -500 > /tmp/kln-review.txt

# 2. Run multi-model review (Option A: stdin)
cat /tmp/kln-review.txt | $PYTHON $CORE multi -n 3 "FOCUS"

# 2. Or use --context-file (Option B)
$PYTHON $CORE multi -n 3 -c /tmp/kln-review.txt "FOCUS"
```

Execute the command above and display the aggregated results showing:
1. Models used and their latencies
2. Individual reviews from each model
3. Consensus analysis (common issues, grade agreement)

## Model Discovery

Models are **dynamically discovered** from LiteLLM proxy. If user gives partial name (e.g. "qwen"), run `$PYTHON $CORE status` to list available models. The core module handles partial name resolution automatically.

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
