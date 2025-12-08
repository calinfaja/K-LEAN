#!/bin/bash
#
# Deep Review Script - Runs Claude headless with LiteLLM models
# The reviewing model gets FULL tool access (Serena, Bash, Read, etc.)
#
# Usage: deep-review.sh <model> "<prompt>" [working_dir]
#
# Models:
#   qwen     -> qwen3-coder      - Code quality, bugs (RELIABLE)
#   kimi     -> kimi-k2-thinking       - Architecture, planning (RELIABLE)
#   glm      -> glm-4.6-thinking        - Standards/compliance (RELIABLE)
#   deepseek -> NOT RECOMMENDED for tool use (empty output issue)
#

set -e

# Arguments
# Default to qwen (most reliable for tool use)
MODEL="${1:-qwen}"
PROMPT="${2:-Review the codebase for issues}"
WORK_DIR="${3:-$(pwd)}"

# Model priority for fallback (only reliable models for tool use)
MODELS_PRIORITY="qwen3-coder kimi-k2-thinking glm-4.6-thinking"

# Health check function (test actual model response)
check_model_health() {
    local model="$1"
    local resp=$(curl -s --max-time 10 http://localhost:4000/chat/completions \
        -H "Content-Type: application/json" \
        -d "{\"model\": \"$model\", \"messages\": [{\"role\": \"user\", \"content\": \"hi\"}], \"max_tokens\": 5}" 2>/dev/null)
    echo "$resp" | jq -e '.choices[0]' > /dev/null 2>&1
}

# Find healthy model with fallback
find_healthy_model() {
    local preferred="$1"
    if check_model_health "$preferred"; then
        echo "$preferred"
        return 0
    fi
    echo "⚠️  $preferred unhealthy, trying fallback..." >&2
    for m in $MODELS_PRIORITY; do
        if [ "$m" != "$preferred" ] && check_model_health "$m"; then
            echo "✓ Using $m" >&2
            echo "$m"
            return 0
        fi
    done
    return 1
}

# Map model alias to LiteLLM model name and Claude model name
get_model_info() {
    case "$1" in
        qwen|code|bugs)
            echo "qwen3-coder"
            ;;
        kimi|arch|architecture|planning)
            echo "kimi-k2-thinking"
            ;;
        glm|standards|misra|compliance)
            echo "glm-4.6-thinking"
            ;;
        deepseek)
            echo "WARNING: deepseek not recommended for tool use" >&2
            echo "deepseek-v3-thinking"
            ;;
        *)
            echo "qwen3-coder"
            ;;
    esac
}

# Get Claude model name from LiteLLM model name
litellm_to_claude() {
    case "$1" in
        qwen3-coder) echo "sonnet" ;;
        deepseek-v3-thinking) echo "haiku" ;;
        glm-4.6-thinking) echo "opus" ;;
        *) echo "sonnet" ;;
    esac
}

# Get model description
get_model_desc() {
    case "$1" in
        qwen3-coder) echo "qwen3-coder (code quality, bugs)" ;;
        kimi-k2-thinking) echo "kimi-k2-thinking (architecture, planning)" ;;
        glm-4.6-thinking) echo "glm-4.6-thinking (standards, compliance)" ;;
        deepseek-v3-thinking) echo "deepseek-v3-thinking (NOT RECOMMENDED)" ;;
        *) echo "$1" ;;
    esac
}

# Get preferred model info (now returns just LiteLLM name)
PREFERRED_LITELLM=$(get_model_info "$MODEL")

# Find healthy model
echo "Checking model health..."
LITELLM_MODEL=$(find_healthy_model "$PREFERRED_LITELLM")
if [ -z "$LITELLM_MODEL" ]; then
    echo "ERROR: No healthy models available"
    echo "Check if LiteLLM proxy is running: start-nano-proxy"
    exit 1
fi

# Use LiteLLM model name directly (don't convert to Claude aliases)
# The settings-nanogpt.json routes via LiteLLM, so use LiteLLM names
CLAUDE_MODEL="$LITELLM_MODEL"
MODEL_DESC=$(get_model_desc "$LITELLM_MODEL")

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

# Save current settings and switch to review config
ORIGINAL_SETTINGS="$HOME/.claude/settings.json"
BACKUP_SETTINGS="$HOME/.claude/settings-pre-review-backup.json"
REVIEW_SETTINGS="$HOME/.claude/settings-nanogpt.json"

# Backup current settings
cp "$ORIGINAL_SETTINGS" "$BACKUP_SETTINGS"

# Switch to LiteLLM settings
cp "$REVIEW_SETTINGS" "$ORIGINAL_SETTINGS"

# Run the headless review
cd "$WORK_DIR"

# Use --print for non-interactive output
# Capture output for fact extraction
REVIEW_OUTPUT=$(claude --model "$CLAUDE_MODEL" --print "$FULL_PROMPT")
REVIEW_EXIT_CODE=$?

# Display the output
echo "$REVIEW_OUTPUT"

# Auto-extract facts from review (Tier 1)
~/.claude/scripts/fact-extract.sh "$REVIEW_OUTPUT" "review" "$PROMPT" "$WORK_DIR"

# Restore original settings
cp "$BACKUP_SETTINGS" "$ORIGINAL_SETTINGS"
rm -f "$BACKUP_SETTINGS"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "DEEP REVIEW COMPLETE"
echo "═══════════════════════════════════════════════════════════════"

exit $REVIEW_EXIT_CODE
