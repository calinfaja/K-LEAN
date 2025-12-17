#!/bin/bash
#
# K-LEAN Session Start Hook
# Auto-starts LiteLLM proxy and per-project Knowledge Server
#
# Triggered by Claude Code's SessionStart event (matcher: startup)
# Both services start in background - non-blocking (~0.1s)
#

# === LiteLLM Proxy (Global - Port 4000) ===
# Only start if not already running
if ! curl -s --max-time 1 http://localhost:4000/health >/dev/null 2>&1; then
    # Check if config exists
    if [ -f ~/.config/litellm/config.yaml ] && [ -f ~/.config/litellm/.env ]; then
        (
            source ~/.config/litellm/.env
            nohup litellm --config ~/.config/litellm/config.yaml \
                --port 4000 \
                > /tmp/litellm.log 2>&1 &
        )
    fi
fi

# === Knowledge Server (Per-Project) ===
# Find project root by walking up looking for .knowledge-db
find_project_root() {
    local dir="$PWD"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.knowledge-db" ]; then
            echo "$dir"
            return 0
        fi
        dir=$(dirname "$dir")
    done
    return 1
}

PROJECT=$(find_project_root)

# Only start if we're in a project with knowledge-db
if [ -n "$PROJECT" ]; then
    # Calculate socket path (must match knowledge-server.py's hash)
    HASH=$(echo -n "$PROJECT" | md5sum | cut -c1-8)
    SOCKET="/tmp/kb-${HASH}.sock"

    # Start if not already running
    if [ ! -S "$SOCKET" ]; then
        PYTHON="$HOME/.venvs/knowledge-db/bin/python"
        SERVER="$HOME/.claude/scripts/knowledge-server.py"

        if [ -x "$PYTHON" ] && [ -f "$SERVER" ]; then
            (
                cd "$PROJECT"
                nohup "$PYTHON" "$SERVER" start "$PROJECT" \
                    > /tmp/kb-startup-${HASH}.log 2>&1 &
            )
        fi
    fi
fi

# Hook must exit 0 for session to continue
exit 0
