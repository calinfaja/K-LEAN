#!/bin/bash
#
# K-LEAN Knowledge DB Doctor
# Diagnose and repair common knowledge database issues
#
# Usage: kb-doctor.sh [--fix] [--project PATH]
#
# Options:
#   --fix       Automatically fix issues found
#   --project   Specify project path (default: current directory)
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

FIX_MODE=false
PROJECT_PATH=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --fix|-f)
            FIX_MODE=true
            shift
            ;;
        --project|-p)
            PROJECT_PATH="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: kb-doctor.sh [--fix] [--project PATH]"
            echo ""
            echo "Options:"
            echo "  --fix, -f       Automatically fix issues found"
            echo "  --project, -p   Specify project path (default: find from cwd)"
            echo ""
            echo "Checks:"
            echo "  1. .knowledge-db directory exists"
            echo "  2. entries.jsonl is valid JSONL format"
            echo "  3. Index directory exists and is valid"
            echo "  4. Knowledge server is running for this project"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Find project root
find_project_root() {
    local dir="${1:-$PWD}"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.knowledge-db" ]; then
            echo "$dir"
            return 0
        fi
        dir=$(dirname "$dir")
    done
    return 1
}

# Send command to Unix socket (try nc, then socat, then Python)
send_to_socket() {
    local msg="$1"
    local sock="$2"
    if command -v nc &> /dev/null; then
        echo "$msg" | timeout 2 nc -U "$sock" 2>/dev/null
    elif command -v socat &> /dev/null; then
        echo "$msg" | timeout 2 socat - UNIX-CONNECT:"$sock" 2>/dev/null
    else
        python3 -c "
import socket
s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.settimeout(2)
s.connect('$sock')
s.sendall(b'$msg')
print(s.recv(4096).decode())
s.close()
" 2>/dev/null
    fi
}

if [ -n "$PROJECT_PATH" ]; then
    PROJECT="$PROJECT_PATH"
else
    PROJECT=$(find_project_root) || PROJECT=""
fi

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║           K-LEAN Knowledge DB Doctor                       ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

ISSUES=0
FIXED=0

#------------------------------------------------------------------------------
# Check 1: .knowledge-db directory
#------------------------------------------------------------------------------
echo -e "${BLUE}[1/5] Checking .knowledge-db directory...${NC}"
if [ -z "$PROJECT" ]; then
    echo -e "  ${RED}✗ No .knowledge-db found in current directory tree${NC}"
    echo -e "    Create with: mkdir -p .knowledge-db"
    ISSUES=$((ISSUES + 1))

    if [ "$FIX_MODE" = true ]; then
        mkdir -p "$PWD/.knowledge-db"
        echo -e "  ${GREEN}✓ Created .knowledge-db in $PWD${NC}"
        PROJECT="$PWD"
        FIXED=$((FIXED + 1))
    fi
else
    echo -e "  ${GREEN}✓ Found: $PROJECT/.knowledge-db${NC}"
fi

if [ -z "$PROJECT" ]; then
    echo ""
    echo -e "${RED}Cannot continue without .knowledge-db directory${NC}"
    exit 1
fi

KB_DIR="$PROJECT/.knowledge-db"

#------------------------------------------------------------------------------
# Check 2: entries.jsonl exists and is valid
#------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[2/5] Checking entries.jsonl...${NC}"
ENTRIES_FILE="$KB_DIR/entries.jsonl"

if [ ! -f "$ENTRIES_FILE" ]; then
    echo -e "  ${YELLOW}○ entries.jsonl does not exist (will be created on first entry)${NC}"
else
    TOTAL_LINES=$(wc -l < "$ENTRIES_FILE")
    VALID_LINES=0
    INVALID_LINES=0
    LINE_NUM=0

    while IFS= read -r line || [ -n "$line" ]; do
        LINE_NUM=$((LINE_NUM + 1))
        if [ -z "$line" ]; then
            continue
        fi
        if echo "$line" | jq . > /dev/null 2>&1; then
            VALID_LINES=$((VALID_LINES + 1))
        else
            INVALID_LINES=$((INVALID_LINES + 1))
            if [ $INVALID_LINES -le 3 ]; then
                echo -e "  ${RED}✗ Invalid JSON at line $LINE_NUM${NC}"
            fi
        fi
    done < "$ENTRIES_FILE"

    if [ $INVALID_LINES -gt 0 ]; then
        echo -e "  ${RED}✗ Found $INVALID_LINES invalid lines out of $TOTAL_LINES${NC}"
        ISSUES=$((ISSUES + 1))

        if [ "$FIX_MODE" = true ]; then
            echo -e "  ${YELLOW}→ Attempting to repair...${NC}"

            # Backup original
            cp "$ENTRIES_FILE" "$ENTRIES_FILE.bak"

            # Try to parse as concatenated JSON objects
            PYTHON="${HOME}/.venvs/knowledge-db/bin/python"
            if [ -x "$PYTHON" ]; then
                $PYTHON -c "
import json
import sys

with open('$ENTRIES_FILE', 'r') as f:
    content = f.read()

entries = []
decoder = json.JSONDecoder()
idx = 0
errors = 0

while idx < len(content):
    remaining = content[idx:].lstrip()
    if not remaining:
        break
    try:
        obj, end = decoder.raw_decode(remaining)
        entries.append(obj)
        idx += len(content[idx:]) - len(remaining) + end
    except json.JSONDecodeError as e:
        # Skip to next potential JSON start
        next_brace = remaining.find('{', 1)
        if next_brace == -1:
            break
        idx += len(content[idx:]) - len(remaining) + next_brace
        errors += 1

with open('$ENTRIES_FILE', 'w') as f:
    for entry in entries:
        f.write(json.dumps(entry) + '\n')

print(f'Recovered {len(entries)} entries, skipped {errors} corrupted sections')
"
                FIXED=$((FIXED + 1))
                echo -e "  ${GREEN}✓ Repaired entries.jsonl (backup: entries.jsonl.bak)${NC}"
            else
                echo -e "  ${RED}✗ Cannot repair: Python venv not found${NC}"
            fi
        fi
    else
        echo -e "  ${GREEN}✓ Valid JSONL format ($VALID_LINES entries)${NC}"
    fi
fi

#------------------------------------------------------------------------------
# Check 3: Index directory
#------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[3/5] Checking index...${NC}"
INDEX_DIR="$KB_DIR/index"

if [ ! -d "$INDEX_DIR" ]; then
    echo -e "  ${RED}✗ Index directory missing${NC}"
    ISSUES=$((ISSUES + 1))

    if [ "$FIX_MODE" = true ] && [ -f "$ENTRIES_FILE" ]; then
        echo -e "  ${YELLOW}→ Rebuilding index...${NC}"
        PYTHON="${HOME}/.venvs/knowledge-db/bin/python"
        KB_SCRIPT="${HOME}/.claude/scripts/knowledge_db.py"

        if [ -x "$PYTHON" ] && [ -f "$KB_SCRIPT" ]; then
            cd "$PROJECT"
            if $PYTHON "$KB_SCRIPT" rebuild 2>&1; then
                echo -e "  ${GREEN}✓ Index rebuilt${NC}"
                FIXED=$((FIXED + 1))
            else
                echo -e "  ${RED}✗ Index rebuild failed${NC}"
            fi
        else
            echo -e "  ${RED}✗ Cannot rebuild: missing Python or knowledge_db.py${NC}"
        fi
    else
        echo -e "    Run: cd $PROJECT && ~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge_db.py rebuild"
    fi
else
    # Check index has files
    INDEX_FILES=$(ls -1 "$INDEX_DIR" 2>/dev/null | wc -l)
    if [ "$INDEX_FILES" -eq 0 ]; then
        echo -e "  ${RED}✗ Index directory is empty${NC}"
        ISSUES=$((ISSUES + 1))
    else
        echo -e "  ${GREEN}✓ Index exists ($INDEX_FILES files)${NC}"
    fi
fi

#------------------------------------------------------------------------------
# Check 4: Knowledge server status
#------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[4/5] Checking knowledge server...${NC}"

# Calculate socket path
HASH=$(echo -n "$PROJECT" | md5sum | cut -c1-8)
SOCKET="/tmp/kb-${HASH}.sock"

if [ ! -S "$SOCKET" ]; then
    echo -e "  ${YELLOW}○ Server not running for this project${NC}"
    echo -e "    Socket: $SOCKET"

    if [ "$FIX_MODE" = true ] && [ -d "$INDEX_DIR" ]; then
        echo -e "  ${YELLOW}→ Starting server...${NC}"
        PYTHON="${HOME}/.venvs/knowledge-db/bin/python"
        SERVER="${HOME}/.claude/scripts/knowledge-server.py"

        if [ -x "$PYTHON" ] && [ -f "$SERVER" ]; then
            cd "$PROJECT"
            nohup "$PYTHON" "$SERVER" start "$PROJECT" > /tmp/kb-startup-${HASH}.log 2>&1 &
            sleep 3

            if [ -S "$SOCKET" ]; then
                echo -e "  ${GREEN}✓ Server started${NC}"
                FIXED=$((FIXED + 1))
            else
                echo -e "  ${RED}✗ Server failed to start (check /tmp/kb-startup-${HASH}.log)${NC}"
            fi
        fi
    fi
else
    # Test server connectivity
    PING_RESPONSE=$(send_to_socket '{"cmd":"ping"}' "$SOCKET" || echo "")
    if [ -n "$PING_RESPONSE" ] && echo "$PING_RESPONSE" | jq -e '.pong == true' > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓ Server running and responsive${NC}"
    else
        echo -e "  ${YELLOW}○ Server socket exists but not responding${NC}"
        ISSUES=$((ISSUES + 1))

        if [ "$FIX_MODE" = true ]; then
            echo -e "  ${YELLOW}→ Removing stale socket and restarting...${NC}"
            rm -f "$SOCKET"
            PYTHON="${HOME}/.venvs/knowledge-db/bin/python"
            SERVER="${HOME}/.claude/scripts/knowledge-server.py"

            cd "$PROJECT"
            nohup "$PYTHON" "$SERVER" start "$PROJECT" > /tmp/kb-startup-${HASH}.log 2>&1 &
            sleep 3

            if [ -S "$SOCKET" ]; then
                echo -e "  ${GREEN}✓ Server restarted${NC}"
                FIXED=$((FIXED + 1))
            fi
        fi
    fi
fi

#------------------------------------------------------------------------------
# Check 5: Entry count consistency
#------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}[5/5] Checking consistency...${NC}"

if [ -f "$ENTRIES_FILE" ] && [ -d "$INDEX_DIR" ]; then
    JSONL_COUNT=$(grep -c '^{' "$ENTRIES_FILE" 2>/dev/null || echo "0")

    # Get index count via server status command
    if [ -S "$SOCKET" ]; then
        STATUS_RESPONSE=$(send_to_socket '{"cmd":"status"}' "$SOCKET" || echo "{}")
        INDEX_COUNT=$(echo "$STATUS_RESPONSE" | jq -r '.entries // 0' 2>/dev/null || echo "?")
    else
        INDEX_COUNT="?"
    fi

    if [ "$INDEX_COUNT" != "?" ] && [ "$JSONL_COUNT" != "$INDEX_COUNT" ]; then
        echo -e "  ${YELLOW}○ Entry count mismatch: JSONL=$JSONL_COUNT, Index=$INDEX_COUNT${NC}"
        echo -e "    Consider rebuilding index if significantly different"

        if [ "$FIX_MODE" = true ]; then
            echo -e "  ${YELLOW}→ Rebuilding index to sync...${NC}"
            PYTHON="${HOME}/.venvs/knowledge-db/bin/python"
            KB_SCRIPT="${HOME}/.claude/scripts/knowledge_db.py"
            cd "$PROJECT"
            if $PYTHON "$KB_SCRIPT" rebuild 2>&1; then
                echo -e "  ${GREEN}✓ Index rebuilt${NC}"
                FIXED=$((FIXED + 1))
            fi
        fi
    else
        echo -e "  ${GREEN}✓ Entries: $JSONL_COUNT in JSONL${NC}"
    fi
else
    echo -e "  ${YELLOW}○ Cannot check consistency (missing entries or index)${NC}"
fi

#------------------------------------------------------------------------------
# Summary
#------------------------------------------------------------------------------
echo ""
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ All checks passed! Knowledge DB is healthy.${NC}"
else
    if [ "$FIX_MODE" = true ]; then
        echo -e "Found ${YELLOW}$ISSUES${NC} issues, fixed ${GREEN}$FIXED${NC}"
    else
        echo -e "Found ${RED}$ISSUES${NC} issues. Run with ${YELLOW}--fix${NC} to repair."
    fi
fi
echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"

exit $ISSUES
