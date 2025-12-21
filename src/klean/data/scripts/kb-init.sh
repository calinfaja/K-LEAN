#!/usr/bin/env bash
#
# K-LEAN kb-init.sh - Initialize Knowledge DB for Project
# ========================================================
# Creates .knowledge-db directory, starts server, runs health checks.
# Use this when statusline shows kb:init
#
# Usage:
#   kb-init.sh              # Initialize current project
#   kb-init.sh /path/to/project  # Initialize specific project
#
# This is the "InitKB" command referenced in docs.
#

set -e

# Source unified project detection
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/kb-root.sh"

# Colors
GREEN='\033[32m'
YELLOW='\033[33m'
RED='\033[31m'
CYAN='\033[36m'
DIM='\033[2m'
RESET='\033[0m'

log_info() { echo -e "${CYAN}ℹ${RESET} $1"; }
log_success() { echo -e "${GREEN}✓${RESET} $1"; }
log_warn() { echo -e "${YELLOW}⚠${RESET} $1"; }
log_error() { echo -e "${RED}✗${RESET} $1"; }

# Get project root (from argument or auto-detect)
if [ -n "$1" ]; then
    PROJECT_ROOT="$1"
    if [ ! -d "$PROJECT_ROOT" ]; then
        log_error "Directory not found: $PROJECT_ROOT"
        exit 1
    fi
else
    PROJECT_ROOT=$(find_kb_project_root)
    if [ -z "$PROJECT_ROOT" ]; then
        log_error "No project root found. Create .git, .claude, or .serena directory first."
        exit 1
    fi
fi

KB_DIR="$PROJECT_ROOT/.knowledge-db"
SOCKET=$(get_kb_socket_path "$PROJECT_ROOT")
PID_FILE=$(get_kb_pid_path "$PROJECT_ROOT")

# Use Python from kb-root.sh (already sourced above)
PYTHON="$KB_PYTHON"
if [ -z "$PYTHON" ] || [ ! -x "$PYTHON" ]; then
    require_kb_python || exit 1
fi

echo -e "${CYAN}K-LEAN Knowledge DB Initialization${RESET}"
echo -e "${DIM}Project: $PROJECT_ROOT${RESET}"
echo ""

# Step 1: Create .knowledge-db directory
if [ -d "$KB_DIR" ]; then
    log_success "Knowledge DB directory exists: $KB_DIR"
else
    log_info "Creating knowledge DB directory..."
    mkdir -p "$KB_DIR"
    log_success "Created: $KB_DIR"
fi

# Step 2: Create timeline.txt if not exists
if [ ! -f "$KB_DIR/timeline.txt" ]; then
    log_info "Creating timeline.txt..."
    echo "# K-LEAN Timeline Log" > "$KB_DIR/timeline.txt"
    echo "# Format: [YYYY-MM-DD HH:MM] [TYPE] message" >> "$KB_DIR/timeline.txt"
    echo "" >> "$KB_DIR/timeline.txt"
    date '+[%Y-%m-%d %H:%M] [INIT] Knowledge DB initialized' >> "$KB_DIR/timeline.txt"
    log_success "Created timeline.txt"
fi

# Step 2b: Initialize txtai index if not exists
if [ ! -d "$KB_DIR/index" ]; then
    log_info "Initializing knowledge index..."

    # Create initial entry to bootstrap the index
    "$PYTHON" "$SCRIPT_DIR/knowledge_db.py" add \
        --project "$PROJECT_ROOT" \
        --json-input '{"title":"Knowledge DB Initialized","summary":"This project knowledge database was initialized.","type":"system","source":"kb-init","quality":"low","tags":["system","initialization"]}' \
        --json 2>/dev/null

    if [ -d "$KB_DIR/index" ]; then
        log_success "Created initial knowledge index"
    else
        log_error "Failed to create knowledge index"
        exit 1
    fi
fi

# Step 3: Clean stale socket if exists
if [ -S "$SOCKET" ]; then
    if ! is_kb_server_running "$PROJECT_ROOT"; then
        log_warn "Found stale socket, cleaning up..."
        rm -f "$SOCKET" "$PID_FILE" 2>/dev/null
        log_success "Cleaned stale socket"
    fi
fi

# Step 4: Start knowledge server if not running
if is_kb_server_running "$PROJECT_ROOT"; then
    log_success "Knowledge server already running"
else
    log_info "Starting knowledge server..."

    # Find knowledge-server.py
    KB_SERVER="$SCRIPT_DIR/knowledge-server.py"
    if [ ! -f "$KB_SERVER" ]; then
        log_error "knowledge-server.py not found at $KB_SERVER"
        exit 1
    fi

    # Start server in background
    cd "$PROJECT_ROOT"
    "$PYTHON" "$KB_SERVER" start "$PROJECT_ROOT" > /dev/null 2>&1 &
    SERVER_PID=$!

    # Wait for server to start (txtai index loading takes ~12-15s on cold start)
    log_info "Waiting for server to initialize (this may take 15-20 seconds on first run)..."

    MAX_WAIT=25
    WAITED=0
    while [ $WAITED -lt $MAX_WAIT ]; do
        sleep 2
        WAITED=$((WAITED + 2))
        if is_kb_server_running "$PROJECT_ROOT"; then
            log_success "Knowledge server started (waited ${WAITED}s)"
            break
        fi
        # Show progress dots
        echo -n "."
    done
    echo ""

    if ! is_kb_server_running "$PROJECT_ROOT"; then
        log_error "Failed to start knowledge server after ${MAX_WAIT}s"
        log_warn "Check manually with: $PYTHON $KB_SERVER start $PROJECT_ROOT"
        exit 1
    fi
fi

# Step 5: Run health check (doctor)
echo ""
log_info "Running health checks..."

# Check 1: Socket exists and responds
if is_kb_server_running "$PROJECT_ROOT"; then
    log_success "Server responds to ping"
else
    log_error "Server not responding"
    exit 1
fi

# Check 2: Test search command
SEARCH_TEST=$(echo '{"cmd":"search","query":"test","limit":1}' | timeout 2 socat - UNIX-CONNECT:"$SOCKET" 2>/dev/null || echo '{"error":"timeout"}')
if echo "$SEARCH_TEST" | grep -q '"results"'; then
    log_success "Search command works"
elif echo "$SEARCH_TEST" | grep -q '"error"'; then
    log_warn "Search returned error (may be empty DB)"
else
    log_error "Search command failed"
fi

# Check 3: Verify txtai can be imported
if "$PYTHON" -c "from txtai import Embeddings" 2>/dev/null; then
    log_success "txtai library available"
else
    log_error "txtai not installed. Run: pip install txtai[database,ann]"
fi

# Step 6: Summary
echo ""
echo -e "${GREEN}═══════════════════════════════════════${RESET}"
echo -e "${GREEN}Knowledge DB Ready!${RESET}"
echo -e "${DIM}Directory: $KB_DIR${RESET}"
echo -e "${DIM}Socket: $SOCKET${RESET}"
echo ""
echo -e "Commands:"
echo -e "  ${CYAN}SaveThis${RESET} <lesson>     - Save knowledge"
echo -e "  ${CYAN}FindKnowledge${RESET} <query> - Search knowledge"
echo -e "${GREEN}═══════════════════════════════════════${RESET}"
