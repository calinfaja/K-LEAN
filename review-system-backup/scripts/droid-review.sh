#!/bin/bash
# Factory Droid review script - fast agentic code review
# Usage: droid-review.sh "[model] [focus]" [working_dir]
#
# Uses custom droids (subagents) for thorough file-based analysis

set -e

ARGS="$1"
WORKDIR="${2:-$(pwd)}"

# Parse arguments: first word is model, rest is focus
MODEL=$(echo "$ARGS" | awk '{print $1}')
FOCUS=$(echo "$ARGS" | cut -d' ' -f2-)

# Default model if not specified
if [ -z "$MODEL" ] || [ "$MODEL" = "$FOCUS" ]; then
    MODEL="qwen3-coder"
    FOCUS="$ARGS"
fi

# Default focus if not specified
if [ -z "$FOCUS" ]; then
    FOCUS="Review this codebase for bugs, security issues, and code quality"
fi

# Validate model exists in config (use dynamic discovery)
VALID_MODELS=$(~/.claude/scripts/get-models.sh 2>/dev/null | tr '\n' ' ')
if [ -z "$VALID_MODELS" ]; then
    # Fallback to known models if LiteLLM not running
    VALID_MODELS="qwen3-coder deepseek-v3-thinking glm-4.6-thinking minimax-m2 kimi-k2-thinking hermes-4-70b"
fi

if ! echo "$VALID_MODELS" | grep -qw "$MODEL"; then
    echo "ERROR: Invalid model '$MODEL'"
    echo "Available models: $VALID_MODELS"
    exit 1
fi

# Check if FACTORY_API_KEY is set
if [ -z "$FACTORY_API_KEY" ]; then
    source ~/.bashrc 2>/dev/null || true
    source ~/.profile 2>/dev/null || true
fi

if [ -z "$FACTORY_API_KEY" ]; then
    echo "ERROR: FACTORY_API_KEY not set"
    echo "Run: export FACTORY_API_KEY=fk-YOUR_KEY"
    exit 1
fi

echo "=== Factory Droid Review ==="
echo "Model: $MODEL"
echo "Focus: $FOCUS"
echo "Working directory: $WORKDIR"
echo "============================"
echo ""

# Create review prompt that forces tool usage
REVIEW_PROMPT="You are reviewing code in: $WORKDIR

IMPORTANT: You MUST use your tools to examine the actual files before providing feedback.

## Required Steps:
1. Use Glob to find relevant files (e.g., '**/*.sh' for shell scripts)
2. Use Read to examine each file's actual content
3. Use Grep to search for specific patterns if needed

## Review Focus:
$FOCUS

## Output Requirements:
- Provide specific file:line references for ALL findings
- Grade the code A-F with detailed justification
- List concrete issues found with severity (CRITICAL/WARNING/SUGGESTION)

DO NOT provide generic feedback. Read the files first, then provide specific analysis."

# Determine reasoning effort based on model type
REASONING_EFFORT="low"
if echo "$MODEL" | grep -q "thinking"; then
    REASONING_EFFORT="medium"
fi

echo "Autonomy: medium | Reasoning: $REASONING_EFFORT"
echo ""

# Run droid in exec mode with the review prompt
# --auto medium: Required for tool usage (file reads, reversible commands)
# -r: Reasoning effort based on model type
cd "$WORKDIR"
droid exec --auto medium -r "$REASONING_EFFORT" --model "custom:$MODEL" "$REVIEW_PROMPT"
