#!/usr/bin/env bash
#
# Deep Review Script - Runs Claude headless with LiteLLM models
# READ-ONLY AUDIT MODE: Full read/search/research access, NO write/edit/delete
# Uses --dangerously-skip-permissions with restricted allowedTools for safe automation
# Uses dynamic model discovery from LiteLLM API
#
# Usage: deep-review.sh <model> "<prompt>" [working_dir]
# Run get-models.sh to see available models
#
# Security: Runs in audit mode with:
#   - ALLOWED: Read, Grep, Glob, WebSearch, WebFetch, git read ops, MCP search tools
#   - DENIED: Write, Edit, rm, mv, git commit/push, any destructive operations
#

set -e

# Arguments
MODEL="${1:-}"
PROMPT="${2:-Review the codebase for issues}"
WORK_DIR="${3:-$(pwd)}"
SCRIPTS_DIR="$(dirname "$0")"

# Source kb-root.sh for unified paths
if [ -f "$SCRIPTS_DIR/kb-root.sh" ]; then
    source "$SCRIPTS_DIR/kb-root.sh"
else
    KB_PYTHON="${KLEAN_KB_PYTHON:-$HOME/.venvs/knowledge-db/bin/python}"
    KB_SCRIPTS_DIR="${KLEAN_SCRIPTS_DIR:-$HOME/.claude/scripts}"
fi

# Persistent output directory in project's .claude/kln/deepInspect/
source "$KB_SCRIPTS_DIR/session-helper.sh"
source "$SCRIPTS_DIR/../lib/common.sh" 2>/dev/null || true

# Validate model is specified
if [ -z "$MODEL" ]; then
    echo "ERROR: No model specified" >&2
    echo "Usage: deep-review.sh <model> \"<prompt>\" [working_dir]" >&2
    echo "" >&2
    echo "Available models:" >&2
    "$SCRIPTS_DIR/get-models.sh" >&2
    exit 1
fi

# Validate model exists in LiteLLM
if ! "$SCRIPTS_DIR/validate-model.sh" "$MODEL" 2>/dev/null; then
    echo "ERROR: Invalid model '$MODEL'" >&2
    echo "Available models:" >&2
    "$SCRIPTS_DIR/get-models.sh" >&2
    exit 1
fi

# Check model health with fallback
echo "Checking model health..."
if ! "$SCRIPTS_DIR/health-check-model.sh" "$MODEL" 2>/dev/null; then
    echo "⚠️  Model $MODEL unhealthy, trying fallback..." >&2
    LITELLM_MODEL=$("$SCRIPTS_DIR/get-healthy-models.sh" 1 2>/dev/null | head -1)
    if [ -z "$LITELLM_MODEL" ]; then
        echo "ERROR: No healthy models available" >&2
        echo "Check if LiteLLM proxy is running: start-nano-proxy" >&2
        exit 1
    fi
    echo "✓ Using $LITELLM_MODEL" >&2
else
    LITELLM_MODEL="$MODEL"
fi

OUTPUT_DIR=$(get_output_dir "deepInspect" "$WORK_DIR")
OUTPUT_FILENAME=$(generate_filename "$LITELLM_MODEL" "$PROMPT" ".md")

# Use LiteLLM model name directly
CLAUDE_MODEL="$LITELLM_MODEL"
MODEL_DESC="$LITELLM_MODEL"

# Build the system context for the review
SYSTEM_CONTEXT="You are an independent code reviewer with FULL TOOL ACCESS.

YOUR CAPABILITIES:
- You can READ any file in the codebase
- You can use GREP to search for patterns
- You can use BASH to run commands (git, find, etc.)
- You can access SERENA memories for project context
- You can VERIFY your assumptions by checking the actual code

YOUR MISSION:
Conduct a thorough, independent review. Do NOT just give opinions - INVESTIGATE.
When you suspect an issue, USE YOUR TOOLS to verify it exists.

REVIEW METHODOLOGY:
1. First, understand the project structure (list_dir, find_file)
2. Check recent changes (git diff, git log)
3. Read relevant files to understand context
4. Search for specific patterns (grep for buffer ops, malloc, etc.)
5. Check Serena memories for lessons learned
6. Verify each finding before reporting

OUTPUT FORMAT:
After your investigation, provide:

## Investigation Summary
[What you checked and how]

## Verified Findings

### Critical Issues (VERIFIED - blocks merge)
| # | File:Line | Issue | Evidence | Fix |
|---|-----------|-------|----------|-----|

### Warnings (VERIFIED - should fix)
| # | File:Line | Issue | Evidence | Fix |
|---|-----------|-------|----------|-----|

### Suggestions
[Improvements you noticed]

## Code Practices Assessment
| Practice | Status | Evidence |
|----------|--------|----------|
| Memory Safety | ✅/⚠️/❌ | [what you found] |
| Error Handling | ✅/⚠️/❌ | [what you found] |
| Thread Safety | ✅/⚠️/❌ | [what you found] |

## Risk Assessment
- Overall Risk: [CRITICAL/HIGH/MEDIUM/LOW]
- Confidence: [HIGH - I verified everything / MEDIUM - some assumptions / LOW - limited access]

## Verdict
[APPROVE / APPROVE_WITH_CHANGES / REQUEST_CHANGES / NEEDS_DISCUSSION]

## Recommendations
[Prioritized list of actions]
"

# Create the full prompt
FULL_PROMPT="$SYSTEM_CONTEXT

---

USER REQUEST:
$PROMPT

---

WORKING DIRECTORY: $WORK_DIR

Begin your investigation. Use your tools to verify findings.
"

# Log review start
type log_debug &>/dev/null && log_debug "review" "deep_start" "model=$LITELLM_MODEL" "prompt=$PROMPT" "dir=$WORK_DIR"

echo "═══════════════════════════════════════════════════════════════"
echo "DEEP REVIEW - Tier 3 (Full Tool Access)"
echo "═══════════════════════════════════════════════════════════════"
echo "Model: $MODEL_DESC"
echo "Directory: $WORK_DIR"
echo "Prompt: $PROMPT"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "Starting headless Claude with LiteLLM..."
echo "(The reviewing model has full tool access and will investigate)"
echo ""

# Use ~/.claude-nano as base config (it has proper LiteLLM setup)
# Create a temporary copy with model override if needed
NANO_CONFIG_DIR="$HOME/.claude-nano"

if [ ! -d "$NANO_CONFIG_DIR" ]; then
    echo "ERROR: ~/.claude-nano not configured. Run: k-lean install" >&2
    exit 1
fi

# Create temporary config based on nano profile with model override
AUDIT_CONFIG_DIR="${TMPDIR:-/tmp}/claude-audit-$$"
mkdir -p "$AUDIT_CONFIG_DIR"

# Copy nano settings and override the model
if [ -f "$NANO_CONFIG_DIR/settings.json" ]; then
    # Use jq if available, otherwise sed
    if command -v jq &>/dev/null; then
        jq --arg model "$CLAUDE_MODEL" '
            .defaultModel = $model |
            .env.ANTHROPIC_DEFAULT_SONNET_MODEL = $model |
            .env.ANTHROPIC_DEFAULT_HAIKU_MODEL = $model |
            .env.ANTHROPIC_DEFAULT_OPUS_MODEL = $model
        ' "$NANO_CONFIG_DIR/settings.json" > "$AUDIT_CONFIG_DIR/settings.json"
    else
        # Fallback: just copy and hope defaultModel works
        cp "$NANO_CONFIG_DIR/settings.json" "$AUDIT_CONFIG_DIR/settings.json"
    fi
fi

# Symlink everything else from nano profile
for item in commands scripts CLAUDE.md .credentials.json hooks; do
    if [ -e "$NANO_CONFIG_DIR/$item" ]; then
        ln -sf "$NANO_CONFIG_DIR/$item" "$AUDIT_CONFIG_DIR/$item" 2>/dev/null || true
    elif [ -e "$HOME/.claude/$item" ]; then
        ln -sf "$HOME/.claude/$item" "$AUDIT_CONFIG_DIR/$item" 2>/dev/null || true
    fi
done

# Run the headless review in AUDIT MODE (read-only)
cd "$WORK_DIR"

# Use --print for non-interactive output
# --dangerously-skip-permissions for automation
# Model is set via defaultModel in config (--model flag expects Anthropic names)
REVIEW_OUTPUT=$(CLAUDE_CONFIG_DIR="$AUDIT_CONFIG_DIR" claude --dangerously-skip-permissions --print "$FULL_PROMPT")
REVIEW_EXIT_CODE=$?

# Cleanup audit config
rm -rf "$AUDIT_CONFIG_DIR"

# Save to persistent markdown file
OUTPUT_FILE="$OUTPUT_DIR/$OUTPUT_FILENAME"
{
    echo "# Deep Inspect: $PROMPT"
    echo ""
    echo "**Model:** $MODEL_DESC"
    echo "**Date:** $(date '+%Y-%m-%d %H:%M:%S')"
    echo "**Directory:** $WORK_DIR"
    echo ""
    echo "---"
    echo ""
    echo "$REVIEW_OUTPUT"
} > "$OUTPUT_FILE"

# Display the output
echo "$REVIEW_OUTPUT"

# Auto-extract facts from review (Tier 1)
"$KB_SCRIPTS_DIR/fact-extract.sh" "$REVIEW_OUTPUT" "review" "$PROMPT" "$WORK_DIR"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "DEEP REVIEW COMPLETE"
echo "Saved: $OUTPUT_FILE"
echo "═══════════════════════════════════════════════════════════════"

# Log review complete
type log_debug &>/dev/null && log_debug "review" "deep_complete" "model=$LITELLM_MODEL" "output=$OUTPUT_FILE" "exit_code=$REVIEW_EXIT_CODE"

exit $REVIEW_EXIT_CODE
