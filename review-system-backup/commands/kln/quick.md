---
name: quick
description: "Fast review - single model analysis (~30s)"
allowed-tools: Bash, Read
argument-hint: "[--model MODEL] [--async] <focus>"
---

# /kln:quick - Fast Code Review

Quick single-model review via LiteLLM API. Fast (~30s), no file access.

## Arguments

$ARGUMENTS

## Flags

- `--model, -m` - Specific model (from discovery) or "auto" for fastest
- `--async, -a` - Run in background
- `--output, -o` - Output format: text (default), json, markdown

## Execution

```bash
# Parse arguments
ARGS="$ARGUMENTS"
MODEL="auto"
ASYNC=false
OUTPUT="text"
FOCUS=""

# Extract flags
while [[ $# -gt 0 ]]; do
    case "$1" in
        -m|--model) MODEL="$2"; shift 2 ;;
        -a|--async) ASYNC=true; shift ;;
        -o|--output) OUTPUT="$2"; shift 2 ;;
        *) FOCUS="$FOCUS $1"; shift ;;
    esac
done

PYTHON=~/.local/share/pipx/venvs/k-lean/bin/python
CORE=~/.claude/k-lean/klean_core.py

if [ "$ASYNC" = true ]; then
    # Run in background
    LOG="/tmp/claude-reviews/quick-$(date +%Y%m%d-%H%M%S).log"
    mkdir -p /tmp/claude-reviews
    nohup $PYTHON $CORE quick -m "$MODEL" -o "$OUTPUT" $FOCUS > "$LOG" 2>&1 &
    echo "Running in background. Log: $LOG"
else
    $PYTHON $CORE quick -m "$MODEL" -o "$OUTPUT" $FOCUS
fi
```

Run the above bash script to execute the review. Display the output to the user.

If no focus is provided, use "general code review" as default.

## Examples

```
/kln:quick security audit
/kln:quick --model qwen3-coder check memory safety
/kln:quick -a architecture review   # async
```
