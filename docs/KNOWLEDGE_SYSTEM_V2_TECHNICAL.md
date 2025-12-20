# Knowledge System V2 - Technical Implementation Plan

> **For Agent Execution** - Step-by-step instructions with exact file paths, code changes, and test commands.

---

## Overview

### Problems We Solve

| Problem | Root Cause | Solution |
|---------|-----------|----------|
| `kb:✗` confuses users on new projects | No distinction between "not init" and "error" | Show message: `kb:init needed` |
| Project root detection inconsistent | 4+ different strategies across scripts | Single `kb-root.sh` sourced everywhere |
| Server startup issues on new projects | No auto-init, no doctor checks | `InitKB` auto-starts + runs diagnostics |
| SaveThis stores raw text | No analysis or structure | Claude structures JSON with rich fields |
| SaveInfo has no smart evaluation | No LLM evaluation | LiteLLM evaluates with threshold |
| Socket/server problems persist | No automatic recovery | InitKB runs kb-doctor checks |

### Success Criteria

1. New project: Statusline shows `kb:init` (not `kb:✗`)
2. `InitKB` creates KB + starts server + verifies health (seamless)
3. All scripts use same project detection
4. SaveThis produces rich atomic notes
5. Zero manual debugging needed by user

---

## Execution Order

```
PHASE 1: kb-root.sh (foundation - all else depends on this)
    ↓
PHASE 2: knowledge_db.py schema enhancement
    ↓
PHASE 3: klean-statusline.py (user sees feedback immediately)
    ↓
PHASE 4: kb-init.sh + kb-doctor integration
    ↓
PHASE 5: knowledge-capture.py --json support
    ↓
PHASE 6: smart-capture.py for SaveInfo
    ↓
PHASE 7: user-prompt-handler.sh updates
    ↓
PHASE 8: session-start.sh updates
    ↓
PHASE 9: Update all other scripts to use kb-root.sh
    ↓
PHASE 10: Testing & sync to backup
```

---

## PHASE 1: Create kb-root.sh

### File: `~/.claude/scripts/kb-root.sh`

**Purpose:** Single source of truth for project detection. All scripts source this.

**Create new file:**

```bash
#!/bin/bash
# kb-root.sh - Unified project root detection for Knowledge System
# Source this file in ALL knowledge-related scripts
#
# Usage:
#   source ~/.claude/scripts/kb-root.sh
#   PROJECT_ROOT=$(find_project_root)
#   SOCKET=$(get_socket_path "$PROJECT_ROOT")

# Find project root by walking up directory tree
# Priority: CLAUDE_PROJECT_DIR env > .knowledge-db > .serena > .claude > .git
find_project_root() {
    local start_dir="${1:-$(pwd)}"
    local dir="$start_dir"

    # Priority 1: Environment variable (Claude sets this)
    if [ -n "$CLAUDE_PROJECT_DIR" ] && [ -d "$CLAUDE_PROJECT_DIR" ]; then
        echo "$CLAUDE_PROJECT_DIR"
        return 0
    fi

    # Priority 2: Walk up looking for markers
    while [ "$dir" != "/" ]; do
        for marker in ".knowledge-db" ".serena" ".claude" ".git"; do
            if [ -d "$dir/$marker" ]; then
                echo "$dir"
                return 0
            fi
        done
        dir=$(dirname "$dir")
    done

    # Not found
    return 1
}

# Calculate MD5 hash of project path (first 8 chars)
get_project_hash() {
    local root="$1"
    echo -n "$root" | md5sum | cut -c1-8
}

# Get socket path for project
get_socket_path() {
    local root="$1"
    local hash=$(get_project_hash "$root")
    echo "/tmp/kb-${hash}.sock"
}

# Get PID file path for project
get_pid_path() {
    local root="$1"
    local hash=$(get_project_hash "$root")
    echo "/tmp/kb-${hash}.pid"
}

# Check if KB is initialized for project
is_kb_initialized() {
    local root="$1"
    [ -d "$root/.knowledge-db" ]
}

# Check if KB server is running
is_kb_server_running() {
    local root="$1"
    local socket=$(get_socket_path "$root")

    if [ ! -S "$socket" ]; then
        return 1
    fi

    # Try to ping
    echo '{"cmd":"ping"}' | timeout 2 socat - UNIX-CONNECT:"$socket" 2>/dev/null | grep -q "pong"
}

# Clean stale socket if exists
clean_stale_socket() {
    local root="$1"
    local socket=$(get_socket_path "$root")
    local pid_file=$(get_pid_path "$root")

    if [ -S "$socket" ]; then
        if ! is_kb_server_running "$root"; then
            rm -f "$socket" "$pid_file" 2>/dev/null
            return 0  # Cleaned
        fi
    fi
    return 1  # Nothing to clean
}
```

**Test:**
```bash
chmod +x ~/.claude/scripts/kb-root.sh
source ~/.claude/scripts/kb-root.sh
find_project_root  # Should return project path
get_socket_path "$(find_project_root)"  # Should return /tmp/kb-XXXXXXXX.sock
```

---

## PHASE 2: Enhance knowledge_db.py Schema

### File: `~/.claude/scripts/knowledge_db.py`

**Changes needed:**

1. Add new schema fields
2. Add migration for existing entries
3. Add `add_structured()` method for JSON input
4. Update search to include new fields

**Locate and modify:**

### 2.1 Add schema defaults (find SCHEMA or similar, add after):

```python
# Enhanced schema fields with defaults for migration
SCHEMA_DEFAULTS = {
    "atomic_insight": "",
    "key_concepts": [],
    "quality": "medium",
    "source": "manual",
    "source_path": "",
}
```

### 2.2 Add migration function:

```python
def migrate_entry(entry: dict) -> dict:
    """Add missing fields with defaults for backward compatibility."""
    for field, default in SCHEMA_DEFAULTS.items():
        if field not in entry:
            entry[field] = default
    return entry
```

### 2.3 Update the `add` method to include new fields in searchable text:

Find the line that builds searchable text (likely looks like):
```python
# OLD:
searchable = f"{entry['title']} {entry['summary']} {' '.join(entry.get('tags', []))}"
```

Change to:
```python
# NEW:
searchable = " ".join([
    entry.get('title', ''),
    entry.get('summary', ''),
    entry.get('atomic_insight', ''),
    ' '.join(entry.get('tags', [])),
    ' '.join(entry.get('key_concepts', [])),
])
```

### 2.4 Add CLI support for --json input:

Find the `if __name__ == "__main__"` section or argparse setup, add:

```python
# Add to argument parser
parser.add_argument('--json', help='Add entry from JSON string')

# Add to main logic
if args.json:
    data = json.loads(args.json)
    entry_id = db.add_structured(data)
    print(f"Added: {entry_id}")
    sys.exit(0)
```

### 2.5 Add `add_structured` method to KnowledgeDB class:

```python
def add_structured(self, data: dict) -> str:
    """
    Add a pre-structured entry (from Claude session or smart-capture).
    Accepts: title, summary, atomic_insight, type, tags, key_concepts, quality, source, source_path
    """
    entry = {
        "id": data.get("id", str(uuid.uuid4())),
        "found_date": data.get("found_date", datetime.now().isoformat()),
        "usage_count": data.get("usage_count", 0),
        "last_used": data.get("last_used"),
        "relevance_score": data.get("relevance_score", 0.8),
        "confidence_score": data.get("confidence_score", 0.8),
        # Core fields
        "title": data["title"],
        "summary": data["summary"],
        "type": data.get("type", "lesson"),
        "tags": data.get("tags", []),
        # Enhanced fields
        "atomic_insight": data.get("atomic_insight", ""),
        "key_concepts": data.get("key_concepts", []),
        "quality": data.get("quality", "medium"),
        "source": data.get("source", "conversation"),
        "source_path": data.get("source_path", ""),
    }

    # Build searchable text
    searchable = " ".join([
        entry['title'],
        entry['summary'],
        entry.get('atomic_insight', ''),
        ' '.join(entry.get('tags', [])),
        ' '.join(entry.get('key_concepts', [])),
    ])

    # Use existing add logic
    return self.add(entry, searchable_override=searchable)
```

**Test:**
```bash
cd /some/project/with/.knowledge-db
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge_db.py --json '{
  "title": "Test Entry",
  "summary": "This is a test",
  "atomic_insight": "Testing works",
  "type": "lesson",
  "tags": ["test"],
  "key_concepts": ["testing"],
  "quality": "high",
  "source": "manual",
  "source_path": ""
}'
# Should output: Added: <uuid>
```

---

## PHASE 3: Enhance Statusline

### File: `~/.claude/scripts/klean-statusline.py`

**Changes needed:**

1. Import/use kb-root.sh logic (reimplement in Python)
2. Return different messages based on state
3. Show `kb:init` for uninitialized, not `kb:✗`

**Find the `check_knowledge_db()` function and replace:**

```python
def find_project_root_py() -> str | None:
    """Python implementation of kb-root.sh logic."""
    import os

    # Priority 1: Environment variable
    if env_root := os.environ.get("CLAUDE_PROJECT_DIR"):
        if os.path.isdir(env_root):
            return env_root

    # Priority 2: Walk up from cwd
    current = os.getcwd()
    markers = [".knowledge-db", ".serena", ".claude", ".git"]

    while current != "/":
        for marker in markers:
            if os.path.isdir(os.path.join(current, marker)):
                return current
        current = os.path.dirname(current)

    return None


def get_project_hash_py(root: str) -> str:
    """Calculate MD5 hash of project path."""
    import hashlib
    return hashlib.md5(root.encode()).hexdigest()[:8]


def check_knowledge_db() -> tuple[str, str]:
    """
    Check KB status and return (display_text, color).

    States:
    - "kb:✓" green   = Server running, healthy
    - "kb:○" yellow  = Initialized but server not running
    - "kb:init" dim  = Not initialized (shows helpful message)
    - "kb:✗" red     = Error (stale socket, corruption)
    """
    import socket
    import os
    from pathlib import Path

    project_root = find_project_root_py()

    if not project_root:
        return ("kb:init", "dim")  # No project detected

    kb_dir = Path(project_root) / ".knowledge-db"

    if not kb_dir.exists():
        return ("kb:init", "dim")  # Not initialized - clear message

    # KB exists, check server
    project_hash = get_project_hash_py(project_root)
    socket_path = f"/tmp/kb-{project_hash}.sock"

    if not Path(socket_path).exists():
        return ("kb:○", "yellow")  # Init'd but server not running

    # Try to connect and ping
    try:
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(0.5)
        client.connect(socket_path)
        client.sendall(b'{"cmd":"ping"}')
        response = client.recv(1024)
        client.close()

        if b"pong" in response:
            return ("kb:✓", "green")  # Running and healthy
        else:
            return ("kb:✗", "red")  # Unexpected response
    except (socket.error, OSError):
        # Stale socket - clean it up
        try:
            os.unlink(socket_path)
            pid_file = f"/tmp/kb-{project_hash}.pid"
            if os.path.exists(pid_file):
                os.unlink(pid_file)
        except:
            pass
        return ("kb:✗", "red")  # Error state (just cleaned)
```

**Also update the statusline format** to show the new states clearly:

Find where the statusline is assembled and ensure `kb:init` shows in dim/gray color.

**Test:**
```bash
# In a new project without .knowledge-db
cd /tmp && mkdir test-project && cd test-project
~/.claude/scripts/klean-statusline.py  # Should show kb:init

# In a project with .knowledge-db but no server
cd ~/some-project-with-kb
pkill -f knowledge-server  # Stop server
~/.claude/scripts/klean-statusline.py  # Should show kb:○

# With server running
~/.claude/scripts/knowledge-server.py start
~/.claude/scripts/klean-statusline.py  # Should show kb:✓
```

---

## PHASE 4: Create kb-init.sh (with auto-start + doctor)

### File: `~/.claude/scripts/kb-init.sh`

**Purpose:** Initialize KB with seamless experience - creates dir, starts server, runs health checks.

```bash
#!/bin/bash
# kb-init.sh - Initialize Knowledge DB with full health checks
# Provides seamless user experience - no manual debugging needed

set -e

source ~/.claude/scripts/kb-root.sh

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
DIM='\033[2m'
NC='\033[0m' # No Color

log_success() { echo -e "${GREEN}✓${NC} $1"; }
log_warning() { echo -e "${YELLOW}⚠${NC} $1"; }
log_error() { echo -e "${RED}✗${NC} $1"; }
log_info() { echo -e "${DIM}ℹ${NC} $1"; }

# --- Find or set project root ---
PROJECT_ROOT=$(find_project_root)

if [ -z "$PROJECT_ROOT" ]; then
    PROJECT_ROOT=$(pwd)
    log_warning "No project markers found (.git, .serena, .claude)"
    log_info "Using current directory: $PROJECT_ROOT"
fi

KB_DIR="$PROJECT_ROOT/.knowledge-db"
SOCKET=$(get_socket_path "$PROJECT_ROOT")
PID_FILE=$(get_pid_path "$PROJECT_ROOT")
HASH=$(get_project_hash "$PROJECT_ROOT")

echo ""
echo "Knowledge DB Initialization"
echo "─────────────────────────────"
echo "Project: $PROJECT_ROOT"
echo ""

# --- Step 1: Clean stale sockets ---
if [ -S "$SOCKET" ]; then
    if ! is_kb_server_running "$PROJECT_ROOT"; then
        log_info "Cleaning stale socket..."
        rm -f "$SOCKET" "$PID_FILE" 2>/dev/null
        log_success "Stale socket cleaned"
    fi
fi

# --- Step 2: Initialize directory structure ---
if [ ! -d "$KB_DIR" ]; then
    log_info "Creating Knowledge DB structure..."
    mkdir -p "$KB_DIR"
    touch "$KB_DIR/entries.jsonl"
    echo "# Knowledge Timeline - Initialized $(date -I)" > "$KB_DIR/timeline.txt"
    log_success "Created $KB_DIR"

    # Add to gitignore
    GITIGNORE="$PROJECT_ROOT/.gitignore"
    if [ -d "$PROJECT_ROOT/.git" ]; then
        if [ -f "$GITIGNORE" ]; then
            if ! grep -q "^\.knowledge-db" "$GITIGNORE" 2>/dev/null; then
                echo ".knowledge-db/" >> "$GITIGNORE"
                log_success "Added to .gitignore"
            fi
        else
            echo ".knowledge-db/" > "$GITIGNORE"
            log_success "Created .gitignore"
        fi
    fi
else
    log_success "Knowledge DB exists"
fi

# --- Step 3: Validate JSONL ---
JSONL_FILE="$KB_DIR/entries.jsonl"
if [ -f "$JSONL_FILE" ] && [ -s "$JSONL_FILE" ]; then
    # Check each line is valid JSON
    INVALID_LINES=$(~/.venvs/knowledge-db/bin/python -c "
import json
import sys
invalid = 0
with open('$JSONL_FILE', 'r') as f:
    for i, line in enumerate(f, 1):
        line = line.strip()
        if line:
            try:
                json.loads(line)
            except:
                invalid += 1
print(invalid)
" 2>/dev/null || echo "0")

    if [ "$INVALID_LINES" -gt 0 ]; then
        log_warning "Found $INVALID_LINES invalid JSONL lines"
        log_info "Run kb-doctor.sh --fix to repair"
    else
        log_success "JSONL format valid"
    fi
else
    log_success "JSONL file ready (empty)"
fi

# --- Step 4: Check/create index ---
INDEX_DIR="$KB_DIR/index"
if [ ! -d "$INDEX_DIR" ] || [ -z "$(ls -A "$INDEX_DIR" 2>/dev/null)" ]; then
    if [ -s "$JSONL_FILE" ]; then
        log_info "Building search index..."
        ~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge_db.py rebuild 2>/dev/null && \
            log_success "Index built" || log_warning "Index build failed (will retry on server start)"
    else
        log_success "Index ready (no entries yet)"
    fi
else
    log_success "Search index exists"
fi

# --- Step 5: Start server ---
if is_kb_server_running "$PROJECT_ROOT"; then
    log_success "Server already running"
else
    log_info "Starting Knowledge Server..."

    # Start in background
    nohup ~/.venvs/knowledge-db/bin/python \
        ~/.claude/scripts/knowledge-server.py start "$PROJECT_ROOT" \
        > /tmp/kb-startup-$HASH.log 2>&1 &

    # Wait for socket (max 30 seconds)
    for i in {1..30}; do
        if is_kb_server_running "$PROJECT_ROOT"; then
            log_success "Server started (${i}s)"
            break
        fi
        sleep 1
    done

    if ! is_kb_server_running "$PROJECT_ROOT"; then
        log_error "Server failed to start"
        log_info "Check log: /tmp/kb-startup-$HASH.log"
        echo ""
        tail -5 /tmp/kb-startup-$HASH.log 2>/dev/null || true
        exit 1
    fi
fi

# --- Step 6: Verify server health ---
log_info "Verifying server health..."
PING_RESULT=$(echo '{"cmd":"ping"}' | timeout 2 socat - UNIX-CONNECT:"$SOCKET" 2>/dev/null)
if echo "$PING_RESULT" | grep -q "pong"; then
    log_success "Server responding to ping"
else
    log_error "Server not responding correctly"
    exit 1
fi

# --- Step 7: Get stats ---
STATS=$(echo '{"cmd":"status"}' | timeout 2 socat - UNIX-CONNECT:"$SOCKET" 2>/dev/null)
ENTRY_COUNT=$(echo "$STATS" | grep -o '"count":[0-9]*' | grep -o '[0-9]*' || echo "0")

echo ""
echo "─────────────────────────────"
log_success "Knowledge DB Ready"
echo ""
echo "  Entries: $ENTRY_COUNT"
echo "  Socket:  $SOCKET"
echo ""
echo "Commands:"
echo "  SaveThis         - Save insight from conversation"
echo "  SaveInfo <text>  - Evaluate and save content"
echo "  FindKnowledge    - Search your knowledge"
echo ""
```

**Test:**
```bash
chmod +x ~/.claude/scripts/kb-init.sh

# Test on new project
cd /tmp && rm -rf test-kb && mkdir test-kb && cd test-kb && git init
~/.claude/scripts/kb-init.sh
# Should: create .knowledge-db, add to .gitignore, start server, verify health

# Test on existing project
cd ~/claudeAgentic
~/.claude/scripts/kb-init.sh
# Should: verify existing, start server if needed, show stats
```

---

## PHASE 5: Update knowledge-capture.py for --json

### File: `~/.claude/scripts/knowledge-capture.py`

**Find the argparse section and add:**

```python
parser.add_argument('--json', '-j', help='Add entry from JSON string (structured input)')
```

**Find the main logic and add before other subcommands:**

```python
if args.json:
    import json
    try:
        data = json.loads(args.json)

        # Validate required fields
        if 'title' not in data or 'summary' not in data:
            print("Error: JSON must contain 'title' and 'summary'", file=sys.stderr)
            sys.exit(1)

        entry_id = db.add_structured(data)

        # Verbose output
        print(f"✓ Saved to Knowledge DB:")
        print(f"  Title: \"{data['title']}\"")
        print(f"  Type: {data.get('type', 'lesson')} | Quality: {data.get('quality', 'medium')}")
        if data.get('tags'):
            print(f"  Tags: {', '.join(data['tags'])}")
        if data.get('atomic_insight'):
            print(f"  Insight: {data['atomic_insight']}")

        sys.exit(0)

    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
```

**Test:**
```bash
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-capture.py --json '{
  "title": "Test Structured Entry",
  "summary": "Testing the new --json input mode",
  "atomic_insight": "Structured input works great",
  "type": "lesson",
  "tags": ["test", "json"],
  "key_concepts": ["structured input", "knowledge capture"],
  "quality": "high",
  "source": "conversation",
  "source_path": ""
}'
# Should show verbose confirmation
```

---

## PHASE 6: Create smart-capture.py for SaveInfo

### File: `~/.claude/scripts/smart-capture.py`

**Create new file:**

```python
#!/usr/bin/env python3
"""
smart-capture.py - Evaluate and capture external content using LLM.
Used by SaveInfo hook when evaluating content Claude hasn't seen.
"""

import json
import sys
import subprocess
from pathlib import Path

LITELLM_URL = "http://localhost:4000"
EVAL_MODEL = "qwen3-coder"
RELEVANCE_THRESHOLD = 0.7

EVALUATION_PROMPT = '''You are evaluating content for inclusion in a developer's knowledge base.

CONTENT TO EVALUATE:
{content}

PROJECT CONTEXT: {project}

TASK: Evaluate if this content contains reusable knowledge worth preserving.

CRITERIA:
- Is this a lesson learned, solution, pattern, or useful finding?
- Would it help solve future problems?
- Is it general enough to be reusable (not just project-specific trivia)?

RESPOND IN VALID JSON ONLY (no markdown, no explanation):
{{
  "should_save": true/false,
  "relevance_score": 0.0-1.0,
  "title": "Short descriptive title (5-10 words)",
  "summary": "One paragraph explanation of the insight",
  "atomic_insight": "One sentence core takeaway",
  "type": "lesson|finding|solution|pattern|warning|best-practice",
  "tags": ["tag1", "tag2", "tag3"],
  "key_concepts": ["concept1", "concept2"],
  "quality": "high|medium|low",
  "reasoning": "Brief explanation of your evaluation"
}}

If not worth saving: {{"should_save": false, "reasoning": "explanation"}}'''


def evaluate_content(content: str, project: str = "") -> dict:
    """Evaluate content using LiteLLM."""
    import requests

    prompt = EVALUATION_PROMPT.format(content=content[:3000], project=project)

    try:
        response = requests.post(
            f"{LITELLM_URL}/chat/completions",
            json={
                "model": EVAL_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.2,
            },
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        text = result["choices"][0]["message"].get("content") or \
               result["choices"][0]["message"].get("reasoning_content", "")

        # Clean response - remove markdown code blocks if present
        text = text.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        if text.endswith("```"):
            text = text[:-3]

        return json.loads(text.strip())

    except requests.RequestException as e:
        return {"should_save": False, "reasoning": f"LiteLLM unavailable: {e}"}
    except json.JSONDecodeError as e:
        return {"should_save": False, "reasoning": f"Invalid LLM response: {e}"}
    except Exception as e:
        return {"should_save": False, "reasoning": f"Evaluation error: {e}"}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Smart content evaluation and capture")
    parser.add_argument("content", nargs="?", help="Content to evaluate")
    parser.add_argument("--url", help="Source URL (for web content)")
    parser.add_argument("--file", help="Source file path")
    parser.add_argument("--project", default="", help="Project name for context")
    parser.add_argument("--threshold", type=float, default=RELEVANCE_THRESHOLD)
    parser.add_argument("--dry-run", action="store_true", help="Evaluate only, don't save")
    args = parser.parse_args()

    # Get content
    if args.content:
        content = args.content
    else:
        content = sys.stdin.read()

    content = content.strip()
    if not content:
        print("❌ No content provided")
        sys.exit(1)

    if len(content) < 20:
        print("⊘ Content too short to evaluate")
        sys.exit(0)

    # Check LiteLLM availability
    import requests
    try:
        requests.get(f"{LITELLM_URL}/models", timeout=2)
    except:
        print("❌ LiteLLM not available at localhost:4000")
        print("   Run: start-litellm.sh")
        sys.exit(1)

    # Evaluate
    print("Evaluating content...")
    result = evaluate_content(content, args.project)

    if not result.get("should_save"):
        print(f"⊘ Skipped: {result.get('reasoning', 'Low relevance')}")
        sys.exit(0)

    relevance = result.get("relevance_score", 0)
    if relevance < args.threshold:
        print(f"⊘ Skipped: Relevance {relevance:.2f} below threshold {args.threshold}")
        sys.exit(0)

    if args.dry_run:
        print(f"Would save: \"{result.get('title')}\"")
        print(f"  Relevance: {relevance:.2f}")
        print(json.dumps(result, indent=2))
        sys.exit(0)

    # Add source info
    if args.url:
        result["source"] = "web"
        result["source_path"] = args.url
    elif args.file:
        result["source"] = "file"
        result["source_path"] = args.file
    else:
        result["source"] = "manual"
        result["source_path"] = ""

    # Remove evaluation-only fields
    result.pop("should_save", None)
    result.pop("reasoning", None)

    # Save using knowledge-capture.py
    scripts_dir = Path(__file__).parent
    python = Path.home() / ".venvs/knowledge-db/bin/python"
    capture_script = scripts_dir / "knowledge-capture.py"

    save_result = subprocess.run(
        [str(python), str(capture_script), "--json", json.dumps(result)],
        capture_output=True, text=True
    )

    if save_result.returncode == 0:
        print(save_result.stdout)
    else:
        print(f"❌ Save failed: {save_result.stderr}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Test:**
```bash
chmod +x ~/.claude/scripts/smart-capture.py

# Test with direct content
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/smart-capture.py \
    "Connection pooling in databases improves performance by 10x because it reuses existing connections instead of creating new ones for each query" \
    --dry-run

# Test with URL source
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/smart-capture.py \
    "Always use parameterized queries to prevent SQL injection attacks" \
    --url "https://example.com/security-tips"
```

---

## PHASE 7: Update user-prompt-handler.sh

### File: `~/.claude/hooks/user-prompt-handler.sh`

**Add/update case statements:**

```bash
#!/bin/bash
# user-prompt-handler.sh - Handle user prompt keywords

# Source unified detection
source ~/.claude/scripts/kb-root.sh

# Get input from Claude
input="$1"
if [ -z "$input" ]; then
    input=$(cat)
fi

case "$input" in
    # --- Knowledge DB Initialization ---
    InitKB|initKB|initkb)
        ~/.claude/scripts/kb-init.sh
        exit 0
        ;;

    # --- SaveThis: Claude structures, we store ---
    # Note: SaveThis without args is handled by Claude directly
    # SaveThis with hint triggers evaluation
    SaveThis\ *)
        hint="${input#SaveThis }"
        echo "Hint received: $hint"
        echo "Claude should structure this as JSON and call knowledge-capture.py --json"
        exit 0
        ;;

    # --- SaveInfo: External content evaluation via LLM ---
    SaveInfo\ *)
        content="${input#SaveInfo }"
        ~/.venvs/knowledge-db/bin/python ~/.claude/scripts/smart-capture.py "$content"
        exit 0
        ;;

    # --- FindKnowledge: Hybrid search ---
    FindKnowledge\ *)
        query="${input#FindKnowledge }"
        ~/.claude/scripts/knowledge-query.sh "$query"
        exit 0
        ;;

    # --- Health check ---
    healthcheck|HealthCheck)
        ~/.claude/scripts/health-check.sh
        exit 0
        ;;

    # --- Other existing cases... ---

esac

# No match - continue normal processing
exit 0
```

**Test:**
```bash
echo "InitKB" | ~/.claude/hooks/user-prompt-handler.sh
echo "SaveInfo This is a test lesson about error handling" | ~/.claude/hooks/user-prompt-handler.sh
echo "FindKnowledge error handling" | ~/.claude/hooks/user-prompt-handler.sh
```

---

## PHASE 8: Update session-start.sh

### File: `~/.claude/hooks/session-start.sh`

**Replace with:**

```bash
#!/bin/bash
# session-start.sh - Initialize services on Claude Code startup
# Triggered on: startup, resume

# Source unified detection
source ~/.claude/scripts/kb-root.sh

# --- LiteLLM Proxy (global, shared across projects) ---
LITELLM_PORT=4000
if ! curl -s --max-time 2 "http://localhost:$LITELLM_PORT/models" > /dev/null 2>&1; then
    if [ -f ~/.config/litellm/config.yaml ]; then
        nohup ~/.claude/scripts/start-litellm.sh > /tmp/litellm-startup.log 2>&1 &
        sleep 1
    fi
fi

# --- Knowledge Server (per-project) ---
PROJECT_ROOT=$(find_project_root)

if [ -n "$PROJECT_ROOT" ]; then
    KB_DIR="$PROJECT_ROOT/.knowledge-db"

    if [ -d "$KB_DIR" ]; then
        # KB exists - ensure server is running
        # Clean any stale sockets first
        clean_stale_socket "$PROJECT_ROOT"

        if ! is_kb_server_running "$PROJECT_ROOT"; then
            HASH=$(get_project_hash "$PROJECT_ROOT")
            nohup ~/.venvs/knowledge-db/bin/python \
                ~/.claude/scripts/knowledge-server.py start "$PROJECT_ROOT" \
                > /tmp/kb-startup-$HASH.log 2>&1 &
        fi
    fi
    # If KB doesn't exist, user will see "kb:init" in statusline
fi

exit 0
```

**Test:**
```bash
# Manually trigger
~/.claude/hooks/session-start.sh

# Check LiteLLM started
curl -s http://localhost:4000/models | head -1

# Check KB server (if in project with .knowledge-db)
source ~/.claude/scripts/kb-root.sh
is_kb_server_running "$(find_project_root)" && echo "KB Running" || echo "KB Not Running"
```

---

## PHASE 9: Update Other Scripts to Use kb-root.sh

### Scripts to update:

1. `~/.claude/scripts/knowledge-server.py`
2. `~/.claude/scripts/knowledge-query.sh`
3. `~/.claude/hooks/post-bash-handler.sh`
4. `~/.claude/hooks/post-web-handler.sh`

**Pattern for bash scripts - add at top:**

```bash
#!/bin/bash
# Source unified detection
source ~/.claude/scripts/kb-root.sh

PROJECT_ROOT=$(find_project_root)
if [ -z "$PROJECT_ROOT" ]; then
    exit 0  # No project, silently exit
fi

KB_DIR="$PROJECT_ROOT/.knowledge-db"
SOCKET=$(get_socket_path "$PROJECT_ROOT")
# ... rest of script uses these variables ...
```

**For Python scripts - add helper or import logic from kb-root.sh equivalent.**

---

## PHASE 10: Testing & Sync

### Full Test Checklist

```bash
# 1. Test kb-root.sh
source ~/.claude/scripts/kb-root.sh
echo "Project: $(find_project_root)"
echo "Hash: $(get_project_hash "$(find_project_root)")"
echo "Socket: $(get_socket_path "$(find_project_root)")"

# 2. Test new project flow
cd /tmp && rm -rf kb-test && mkdir kb-test && cd kb-test && git init
# Check statusline shows "kb:init"
echo "InitKB" | ~/.claude/hooks/user-prompt-handler.sh
# Should create .knowledge-db, start server, verify health

# 3. Test SaveInfo
echo 'SaveInfo Always validate user input to prevent injection attacks' | ~/.claude/hooks/user-prompt-handler.sh

# 4. Test FindKnowledge
echo "FindKnowledge injection" | ~/.claude/hooks/user-prompt-handler.sh

# 5. Test session-start hook
~/.claude/hooks/session-start.sh

# 6. Verify statusline states
# kb:init (no KB) → kb:○ (KB exists, no server) → kb:✓ (running)
```

### Sync to Backup

```bash
# Copy modified files to backup repo
for file in kb-root.sh kb-init.sh smart-capture.py knowledge_db.py knowledge-capture.py klean-statusline.py; do
    cp ~/.claude/scripts/$file ~/claudeAgentic/review-system-backup/scripts/ 2>/dev/null || true
done

for file in user-prompt-handler.sh session-start.sh post-bash-handler.sh post-web-handler.sh; do
    cp ~/.claude/hooks/$file ~/claudeAgentic/review-system-backup/hooks/ 2>/dev/null || true
done

# Commit
cd ~/claudeAgentic
git add -A
git status
```

---

## SaveThis Behavior (For Claude Reference)

When user types `SaveThis`, Claude should:

1. **Summarize** the key insight from recent conversation
2. **Structure** as JSON:

```json
{
  "title": "Short descriptive title",
  "summary": "Full explanation paragraph",
  "atomic_insight": "One sentence takeaway",
  "type": "lesson|finding|solution|pattern|warning|best-practice",
  "tags": ["tag1", "tag2", "tag3"],
  "key_concepts": ["concept1", "concept2"],
  "quality": "high|medium|low",
  "source": "conversation",
  "source_path": ""
}
```

3. **Execute**:
```bash
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-capture.py --json '<JSON>'
```

4. **Report** verbose confirmation to user.

---

## Rollback Plan

If issues occur:

```bash
# Restore from backup
cp ~/claudeAgentic/review-system-backup/scripts/* ~/.claude/scripts/
cp ~/claudeAgentic/review-system-backup/hooks/* ~/.claude/hooks/
chmod +x ~/.claude/scripts/*.sh ~/.claude/hooks/*.sh
```

---

## Summary

| Phase | Files | Purpose |
|-------|-------|---------|
| 1 | kb-root.sh | Foundation - unified detection |
| 2 | knowledge_db.py | Enhanced schema |
| 3 | klean-statusline.py | Better user feedback |
| 4 | kb-init.sh | Seamless initialization |
| 5 | knowledge-capture.py | --json input support |
| 6 | smart-capture.py | LLM evaluation for SaveInfo |
| 7 | user-prompt-handler.sh | Hook updates |
| 8 | session-start.sh | Auto-start improvements |
| 9 | Various | Consistent detection everywhere |
| 10 | - | Testing and sync |
