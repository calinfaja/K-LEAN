#!/usr/bin/env bash
#
# Knowledge Fast Search - Per-project search with auto-start
#
# Usage:
#   knowledge-fast.sh "<query>" [limit]
#
# This is now an alias for knowledge-query.sh which handles:
# - Per-project server detection
# - Auto-start if not running
# - Fast socket-based queries
#

SCRIPT_DIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")"
exec "$SCRIPT_DIR/knowledge-query.sh" "$@"
