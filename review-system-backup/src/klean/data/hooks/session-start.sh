#!/bin/bash
#
# K-LEAN Session Start Hook v2
# Auto-starts LiteLLM proxy and per-project Knowledge Server
#
# Triggered by Claude Code's SessionStart event (matcher: startup)
# Both services start in background - non-blocking (~0.1s)
#

SCRIPTS_DIR="$HOME/.claude/scripts"

# === LiteLLM Proxy (Global - Port 4000) ===
# Only start if not already running
if ! curl -s --max-time 1 http://localhost:4000/health >/dev/null 2>&1; then
    # Check if config exists and surface issues
    if [ ! -f ~/.config/litellm/config.yaml ]; then
        # One-time warning per session
        if [ ! -f /tmp/klean-litellm-warned ]; then
            echo "{\"systemMessage\": \"⚠️ LiteLLM config not found. Run: ~/.claude/scripts/setup-litellm.sh\"}" >&2
            touch /tmp/klean-litellm-warned
        fi
    elif [ ! -f ~/.config/litellm/.env ]; then
        if [ ! -f /tmp/klean-litellm-warned ]; then
            echo "{\"systemMessage\": \"⚠️ LiteLLM .env not found. Add API keys to ~/.config/litellm/.env\"}" >&2
            touch /tmp/klean-litellm-warned
        fi
    else
        # Config exists, start LiteLLM
        (
            source ~/.config/litellm/.env
            nohup litellm --config ~/.config/litellm/config.yaml \
                --port 4000 \
                > /tmp/litellm.log 2>&1 &
        )
    fi
fi

# === Knowledge Server (Per-Project) ===
# Source unified project detection (kb-root.sh)
if [ -f "$SCRIPTS_DIR/kb-root.sh" ]; then
    source "$SCRIPTS_DIR/kb-root.sh"
    PROJECT=$(find_kb_project_root)
else
    # Fallback: inline detection
    PROJECT=""
    dir="$PWD"
    while [ "$dir" != "/" ]; do
        for marker in ".knowledge-db" ".serena" ".claude" ".git"; do
            if [ -d "$dir/$marker" ]; then
                PROJECT="$dir"
                break 2
            fi
        done
        dir=$(dirname "$dir")
    done
fi

# Only start if we're in a project with knowledge-db initialized
if [ -n "$PROJECT" ] && [ -d "$PROJECT/.knowledge-db" ]; then
    # Get socket path (use kb-root.sh function or calculate inline)
    if type get_kb_socket_path &>/dev/null; then
        SOCKET=$(get_kb_socket_path "$PROJECT")
        HASH=$(get_kb_project_hash "$PROJECT")
    else
        HASH=$(echo -n "$(cd "$PROJECT" && pwd)" | md5sum | cut -c1-8)
        SOCKET="/tmp/kb-${HASH}.sock"
    fi

    # Clean stale socket if server not responding
    if [ -S "$SOCKET" ]; then
        if type is_kb_server_running &>/dev/null; then
            if ! is_kb_server_running "$PROJECT"; then
                rm -f "$SOCKET" "/tmp/kb-${HASH}.pid" 2>/dev/null
            fi
        fi
    fi

    # Start if not already running
    if [ ! -S "$SOCKET" ]; then
        PYTHON="$HOME/.venvs/knowledge-db/bin/python"
        SERVER="$SCRIPTS_DIR/knowledge-server.py"

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
