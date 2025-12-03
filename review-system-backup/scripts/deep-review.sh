#!/bin/bash
#
# Deep Review Script - Runs Claude headless with LiteLLM models
# The reviewing model gets FULL tool access (Serena, Bash, Read, etc.)
#
# Usage: deep-review.sh <model> "<prompt>" [working_dir]
#
# Models:
#   qwen     -> coding-qwen (via sonnet)     - Code quality, bugs
#   deepseek -> architecture-deepseek (haiku) - Architecture review
#   glm      -> tools-glm (via opus)          - Standards/MISRA
#

set -e

# Arguments
MODEL="${1:-qwen}"
PROMPT="${2:-Review the codebase for issues}"
WORK_DIR="${3:-$(pwd)}"

# Map model alias to Claude model name
case "$MODEL" in
    qwen|code|bugs)
        CLAUDE_MODEL="sonnet"
        MODEL_DESC="coding-qwen (code quality)"
        ;;
    deepseek|arch|architecture)
        CLAUDE_MODEL="haiku"
        MODEL_DESC="architecture-deepseek (design)"
        ;;
    glm|standards|misra)
        CLAUDE_MODEL="opus"
        MODEL_DESC="tools-glm (standards)"
        ;;
    *)
        CLAUDE_MODEL="sonnet"
        MODEL_DESC="coding-qwen (default)"
        ;;
esac

# Check LiteLLM is running
if ! curl -s http://localhost:4000/health > /dev/null 2>&1; then
    echo "ERROR: LiteLLM proxy not running on localhost:4000"
    echo "Start it with: start-nano-proxy"
    exit 1
fi

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
REVIEW_SETTINGS="$HOME/.claude-review/settings.json"

# Backup current settings
cp "$ORIGINAL_SETTINGS" "$BACKUP_SETTINGS"

# Switch to LiteLLM settings
cp "$REVIEW_SETTINGS" "$ORIGINAL_SETTINGS"

# Run the headless review
cd "$WORK_DIR"

# Use --print for non-interactive output
claude --model "$CLAUDE_MODEL" --print "$FULL_PROMPT"

REVIEW_EXIT_CODE=$?

# Restore original settings
cp "$BACKUP_SETTINGS" "$ORIGINAL_SETTINGS"
rm -f "$BACKUP_SETTINGS"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "DEEP REVIEW COMPLETE"
echo "═══════════════════════════════════════════════════════════════"

exit $REVIEW_EXIT_CODE
