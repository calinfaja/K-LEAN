#!/bin/bash
#
# Hook: Intercept async review requests and run them directly
#
# This hook runs on user prompt submission and checks if the user
# is requesting an async review. If so, it runs the script in background.
#
# To enable: Add to ~/.claude/settings.json under "hooks"
#

# Get the user's prompt from stdin or environment
USER_PROMPT="$CLAUDE_USER_PROMPT"

# Check if this is an async review request
if echo "$USER_PROMPT" | grep -qi "asyncDeepReview\|async.*deep.*review\|background.*review"; then
    # Extract the focus (everything after the command)
    FOCUS=$(echo "$USER_PROMPT" | sed 's/.*asyncDeepReview[[:space:]]*//' | sed 's/.*async.*review[[:space:]]*//')

    if [ -z "$FOCUS" ]; then
        FOCUS="General code review"
    fi

    # Run the review in background
    echo "🚀 Starting background review: $FOCUS"
    nohup ~/.claude/scripts/parallel-deep-review.sh "$FOCUS" "$(pwd)" > /tmp/claude-reviews/latest-review.log 2>&1 &

    echo "📁 Review running in background. Check /tmp/claude-reviews/ for results."
    echo "📋 Log: /tmp/claude-reviews/latest-review.log"

    # Exit with special code to indicate we handled it
    exit 0
fi

# Not an async review request, continue normally
exit 0
