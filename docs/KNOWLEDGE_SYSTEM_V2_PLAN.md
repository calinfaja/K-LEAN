# Knowledge System V2 - Implementation Plan

## Executive Summary

This plan addresses all issues discussed regarding the Knowledge System, hooks, statusline, and SaveThis/SaveInfo improvements. The goal is to create a robust, consistent, and intelligent knowledge capture system.

---

## Issues Addressed

| Issue | Description | Solution |
|-------|-------------|----------|
| **Statusline confusion** | `kb:✗` shows for new projects (not initialized) | Rich status symbols: `✓ ○ — ✗` |
| **Project root inconsistency** | Different scripts use different detection strategies | Unified `kb-root.sh` sourced everywhere |
| **Server startup issues** | KB server doesn't start on new projects | `InitKB` command + improved session-start hook |
| **SaveThis is dumb** | Stores verbatim without analysis | Claude structures + enhanced schema |
| **SaveInfo not smart** | No evaluation of content quality | LiteLLM evaluation with relevance scoring |
| **Schema lacks fields** | Missing atomic_insight, key_concepts, etc. | Enhanced schema with new high-value fields |
| **No source tracking** | Can't tell where knowledge came from | Add source + source_path fields |

---

## Implementation Phases

### Phase 1: Foundation (Unified Detection + Enhanced Schema)

**Files to create/modify:**
- `~/.claude/scripts/kb-root.sh` (NEW)
- `~/.claude/scripts/knowledge_db.py` (MODIFY)
- `~/claudeAgentic/review-system-backup/scripts/` (sync)

#### 1.1 Create `kb-root.sh` - Unified Project Detection

```bash
#!/bin/bash
# kb-root.sh - Single source of truth for project root detection
# Source this in ALL knowledge-related scripts

find_project_root() {
    local start_dir="${1:-$(pwd)}"
    local dir="$start_dir"

    # Priority 1: Environment variable (Claude sets this)
    if [ -n "$CLAUDE_PROJECT_DIR" ] && [ -d "$CLAUDE_PROJECT_DIR" ]; then
        echo "$CLAUDE_PROJECT_DIR"
        return 0
    fi

    # Priority 2: Walk up looking for markers (in priority order)
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

get_project_hash() {
    local root="$1"
    echo -n "$root" | md5sum | cut -c1-8
}

get_socket_path() {
    local root="$1"
    local hash=$(get_project_hash "$root")
    echo "/tmp/kb-${hash}.sock"
}

get_pid_path() {
    local root="$1"
    local hash=$(get_project_hash "$root")
    echo "/tmp/kb-${hash}.pid"
}

# Export functions for subshells
export -f find_project_root get_project_hash get_socket_path get_pid_path
```

#### 1.2 Enhanced Schema for `knowledge_db.py`

**New fields to add:**

```python
ENHANCED_SCHEMA = {
    # Existing fields
    "id": str,                    # UUID
    "title": str,                 # Short descriptive title
    "summary": str,               # Full explanation
    "type": str,                  # lesson|finding|solution|pattern|warning|best-practice
    "tags": list,                 # 3-5 relevant tags
    "found_date": str,            # ISO timestamp
    "relevance_score": float,     # 0.0-1.0
    "confidence_score": float,    # 0.0-1.0
    "usage_count": int,           # Times retrieved
    "last_used": str,             # ISO timestamp or None

    # NEW high-value fields
    "atomic_insight": str,        # One-sentence takeaway (Zettelkasten atomic)
    "key_concepts": list,         # Terms for hybrid search boost
    "quality": str,               # high|medium|low
    "source": str,                # conversation|web|file|manual
    "source_path": str,           # URL or file path (optional)
}

# Default values for migration
SCHEMA_DEFAULTS = {
    "atomic_insight": "",
    "key_concepts": [],
    "quality": "medium",
    "source": "manual",
    "source_path": "",
}
```

**Migration logic:**
```python
def migrate_entry(entry: dict) -> dict:
    """Add missing fields with defaults for backward compatibility."""
    for field, default in SCHEMA_DEFAULTS.items():
        if field not in entry:
            entry[field] = default
    return entry
```

---

### Phase 2: Statusline Enhancement

**Files to modify:**
- `~/.claude/scripts/klean-statusline.py` (MODIFY)

#### 2.1 Rich Status Symbols

| Symbol | Meaning | Color | Condition |
|--------|---------|-------|-----------|
| `kb:✓` | Running, healthy | Green | Socket exists + responds to ping |
| `kb:○` | Initialized, not running | Yellow | `.knowledge-db/` exists, no socket |
| `kb:—` | Not initialized | Dim/Gray | No `.knowledge-db/` found |
| `kb:✗` | Error (stale socket) | Red | Socket exists but can't connect |

#### 2.2 Implementation in `klean-statusline.py`

```python
def check_knowledge_db() -> tuple[str, str]:
    """
    Returns: (symbol, color)
    """
    # Use unified detection
    project_root = find_project_root_py()

    if not project_root:
        return ("—", "dim")  # No project detected

    kb_dir = Path(project_root) / ".knowledge-db"
    if not kb_dir.exists():
        return ("—", "dim")  # Not initialized

    socket_path = get_socket_path_py(project_root)

    if not Path(socket_path).exists():
        return ("○", "yellow")  # Exists but server not running

    # Try to connect
    if try_socket_ping(socket_path):
        return ("✓", "green")  # Running and healthy
    else:
        # Stale socket - clean up
        try:
            os.unlink(socket_path)
        except:
            pass
        return ("✗", "red")  # Error state
```

---

### Phase 3: InitKB Command

**Files to create/modify:**
- `~/.claude/scripts/kb-init.sh` (NEW)
- `~/.claude/hooks/user-prompt-handler.sh` (MODIFY)

#### 3.1 Create `kb-init.sh`

```bash
#!/bin/bash
# kb-init.sh - Initialize Knowledge DB for current project

source ~/.claude/scripts/kb-root.sh

# Find or determine project root
PROJECT_ROOT=$(find_project_root)

if [ -z "$PROJECT_ROOT" ]; then
    # No markers found - use pwd but warn
    PROJECT_ROOT=$(pwd)
    echo "⚠️  No project markers found (.git, .serena, .claude)"
    echo "   Initializing in: $PROJECT_ROOT"
fi

KB_DIR="$PROJECT_ROOT/.knowledge-db"

if [ -d "$KB_DIR" ]; then
    echo "✓ Knowledge DB already exists: $KB_DIR"

    # Check if server running
    SOCKET=$(get_socket_path "$PROJECT_ROOT")
    if [ -S "$SOCKET" ]; then
        echo "✓ Server running: $SOCKET"
    else
        echo "○ Server not running"
        if [[ "$1" == "--start" ]]; then
            echo "🚀 Starting server..."
            ~/.claude/scripts/knowledge-server.py start "$PROJECT_ROOT" &
            sleep 2
            echo "✓ Server started"
        else
            echo "  Use 'InitKB --start' to start server"
        fi
    fi
else
    echo "📦 Initializing Knowledge DB..."
    mkdir -p "$KB_DIR"
    touch "$KB_DIR/entries.jsonl"
    echo "# Knowledge Timeline - $(date -I)" > "$KB_DIR/timeline.txt"
    echo "✓ Created: $KB_DIR"

    # Add to gitignore if git repo
    GITIGNORE="$PROJECT_ROOT/.gitignore"
    if [ -f "$GITIGNORE" ]; then
        if ! grep -q "^\.knowledge-db" "$GITIGNORE"; then
            echo ".knowledge-db/" >> "$GITIGNORE"
            echo "✓ Added to .gitignore"
        fi
    elif [ -d "$PROJECT_ROOT/.git" ]; then
        echo ".knowledge-db/" > "$GITIGNORE"
        echo "✓ Created .gitignore with .knowledge-db/"
    fi

    # Start server if requested
    if [[ "$1" == "--start" ]]; then
        echo "🚀 Starting server..."
        ~/.claude/scripts/knowledge-server.py start "$PROJECT_ROOT" &
        sleep 2
        echo "✓ Server started"
    fi
fi

echo ""
echo "📊 Status:"
echo "   Project: $PROJECT_ROOT"
echo "   KB Dir:  $KB_DIR"
```

#### 3.2 Add InitKB to `user-prompt-handler.sh`

```bash
# Add to the case statement in user-prompt-handler.sh

case "$input" in
    InitKB*)
        args="${input#InitKB}"
        args="${args# }"  # Trim leading space
        ~/.claude/scripts/kb-init.sh $args
        exit 0
        ;;
    # ... existing cases ...
esac
```

---

### Phase 4: SaveThis Enhancement

**Approach:** Claude (in session) structures the knowledge, no external LLM needed.

**Files to modify:**
- `~/.claude/scripts/knowledge-capture.py` (MODIFY)
- `~/.claude/hooks/user-prompt-handler.sh` (MODIFY)

#### 4.1 Enhanced `knowledge-capture.py`

Add support for structured JSON input:

```python
def add_structured(self, data: dict) -> str:
    """
    Add a pre-structured entry (from Claude session).
    Expected fields: title, summary, atomic_insight, type, tags, key_concepts, quality, source, source_path
    """
    entry = {
        "id": str(uuid.uuid4()),
        "found_date": datetime.now().isoformat(),
        "usage_count": 0,
        "last_used": None,
        "relevance_score": data.get("relevance_score", 0.8),
        "confidence_score": data.get("confidence_score", 0.8),
        # Required fields
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

    # Build searchable text including new fields
    searchable = f"{entry['title']} {entry['summary']} {entry['atomic_insight']} {' '.join(entry['tags'])} {' '.join(entry['key_concepts'])}"

    # Add to index and save
    self._add_to_index(entry, searchable)
    self._append_jsonl(entry)
    self._log_timeline(f"save | {entry['title']} [{entry['type']}]")

    return entry["id"]
```

CLI enhancement:
```bash
# New CLI usage
python knowledge-capture.py --json '{"title":"...", "summary":"...", ...}'
```

#### 4.2 SaveThis Behavior (Claude-Driven)

When user types `SaveThis`, Claude should:

1. **Summarize** the key insight from recent conversation
2. **Structure** as JSON with all fields
3. **Call** `knowledge-capture.py --json '{...}'`
4. **Report** verbose confirmation

**Expected JSON from Claude:**
```json
{
  "title": "Connection Pooling Performance Gain",
  "summary": "Database connection pooling improves performance by 10x by reusing existing connections instead of creating new ones for each query. This eliminates the overhead of TCP handshake, authentication, and connection setup.",
  "atomic_insight": "Reuse DB connections via pooling to avoid connection overhead",
  "type": "finding",
  "tags": ["performance", "database", "optimization"],
  "key_concepts": ["connection pooling", "database performance", "connection reuse"],
  "quality": "high",
  "source": "conversation",
  "source_path": ""
}
```

**Verbose confirmation format:**
```
✓ Saved to Knowledge DB:
  Title: "Connection Pooling Performance Gain"
  Type: finding | Quality: high
  Tags: performance, database, optimization
  Insight: Reuse DB connections via pooling to avoid connection overhead
```

---

### Phase 5: SaveInfo Enhancement

**Approach:** Uses LiteLLM (qwen3-coder) for evaluation since content is external.

**Files to create/modify:**
- `~/.claude/scripts/smart-capture.py` (NEW or MODIFY existing)
- `~/.claude/hooks/user-prompt-handler.sh` (MODIFY)

#### 5.1 Create/Update `smart-capture.py`

```python
#!/usr/bin/env python3
"""
smart-capture.py - Evaluate and capture external content using LLM.
Uses LiteLLM for content Claude hasn't seen.
"""

import json
import sys
import requests
from pathlib import Path

LITELLM_URL = "http://localhost:4000"
EVAL_MODEL = "qwen3-coder"

EVALUATION_PROMPT = """You are evaluating content for inclusion in a knowledge base.

CONTENT TO EVALUATE:
{content}

PROJECT CONTEXT: {project}

EVALUATE this content and respond in JSON:
{{
  "should_save": boolean,     // Is this worth preserving?
  "relevance_score": 0.0-1.0, // How universally applicable?
  "title": "Short title (5-10 words)",
  "summary": "One paragraph explanation",
  "atomic_insight": "One sentence core takeaway",
  "type": "lesson|finding|solution|pattern|warning|best-practice",
  "tags": ["tag1", "tag2", "tag3"],
  "key_concepts": ["concept1", "concept2"],
  "quality": "high|medium|low",
  "reasoning": "Why this is/isn't worth saving"
}}

If not worth saving: {{"should_save": false, "reasoning": "..."}}
"""

def evaluate_content(content: str, project: str = "") -> dict:
    """Evaluate content using LiteLLM."""
    prompt = EVALUATION_PROMPT.format(content=content, project=project)

    try:
        response = requests.post(
            f"{LITELLM_URL}/chat/completions",
            json={
                "model": EVAL_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.3,
            },
            timeout=30
        )
        response.raise_for_status()

        result = response.json()
        content = result["choices"][0]["message"].get("content") or \
                  result["choices"][0]["message"].get("reasoning_content", "")

        # Parse JSON from response
        # Handle markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]

        return json.loads(content.strip())

    except Exception as e:
        return {"should_save": False, "reasoning": f"Evaluation error: {e}"}


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("content", nargs="?", help="Content to evaluate")
    parser.add_argument("--file", help="Read content from file")
    parser.add_argument("--url", help="Source URL")
    parser.add_argument("--path", help="Source file path")
    parser.add_argument("--project", default="", help="Project name")
    parser.add_argument("--threshold", type=float, default=0.7, help="Min relevance")
    args = parser.parse_args()

    # Get content
    if args.file:
        content = Path(args.file).read_text()
    elif args.content:
        content = args.content
    else:
        content = sys.stdin.read()

    if not content.strip():
        print("❌ No content provided")
        sys.exit(1)

    # Evaluate
    result = evaluate_content(content, args.project)

    if not result.get("should_save"):
        print(f"⊘ Skipped: {result.get('reasoning', 'Low relevance')}")
        sys.exit(0)

    if result.get("relevance_score", 0) < args.threshold:
        print(f"⊘ Skipped: Relevance {result['relevance_score']:.2f} < {args.threshold}")
        sys.exit(0)

    # Add source info
    result["source"] = "web" if args.url else ("file" if args.path else "manual")
    result["source_path"] = args.url or args.path or ""

    # Save using knowledge-capture.py
    import subprocess
    save_result = subprocess.run(
        [sys.executable, str(Path(__file__).parent / "knowledge-capture.py"),
         "--json", json.dumps(result)],
        capture_output=True, text=True
    )

    if save_result.returncode == 0:
        print(f"✓ Saved: \"{result['title']}\"")
        print(f"  Type: {result['type']} | Quality: {result['quality']}")
        print(f"  Tags: {', '.join(result['tags'])}")
        print(f"  Insight: {result['atomic_insight']}")
    else:
        print(f"❌ Save failed: {save_result.stderr}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

#### 5.2 Update `user-prompt-handler.sh` for SaveInfo

```bash
case "$input" in
    SaveInfo\ *)
        content="${input#SaveInfo }"
        ~/.venvs/knowledge-db/bin/python ~/.claude/scripts/smart-capture.py "$content"
        exit 0
        ;;
    # ... other cases ...
esac
```

---

### Phase 6: Session Start Hook Update

**Files to modify:**
- `~/.claude/hooks/session-start.sh` (MODIFY)

#### 6.1 Updated `session-start.sh`

```bash
#!/bin/bash
# session-start.sh - Initialize services on Claude Code startup

source ~/.claude/scripts/kb-root.sh

# --- LiteLLM Proxy (global, shared) ---
LITELLM_PORT=4000
if ! curl -s --max-time 2 "http://localhost:$LITELLM_PORT/models" > /dev/null 2>&1; then
    if [ -f ~/.config/litellm/config.yaml ]; then
        nohup ~/.claude/scripts/start-litellm.sh > /tmp/litellm-startup.log 2>&1 &
    fi
fi

# --- Knowledge Server (per-project) ---
PROJECT_ROOT=$(find_project_root)

if [ -n "$PROJECT_ROOT" ]; then
    KB_DIR="$PROJECT_ROOT/.knowledge-db"

    if [ -d "$KB_DIR" ]; then
        # KB exists - ensure server is running
        SOCKET=$(get_socket_path "$PROJECT_ROOT")

        if [ ! -S "$SOCKET" ]; then
            # Start server
            nohup ~/.venvs/knowledge-db/bin/python \
                ~/.claude/scripts/knowledge-server.py start "$PROJECT_ROOT" \
                > /tmp/kb-startup.log 2>&1 &
        fi
    fi
    # If no KB_DIR, don't auto-create - let user run InitKB
fi

exit 0
```

---

### Phase 7: Update Scripts to Use kb-root.sh

**Files to modify:**
- `~/.claude/scripts/knowledge-server.py`
- `~/.claude/scripts/knowledge-query.sh`
- `~/.claude/scripts/knowledge-capture.py`
- `~/.claude/hooks/post-bash-handler.sh`
- `~/.claude/hooks/post-web-handler.sh`

#### 7.1 Pattern for Bash Scripts

```bash
#!/bin/bash
# At the top of each script:

# Source unified detection
source ~/.claude/scripts/kb-root.sh

# Use it
PROJECT_ROOT=$(find_project_root)
if [ -z "$PROJECT_ROOT" ]; then
    echo "Error: No project root found"
    exit 1
fi

SOCKET=$(get_socket_path "$PROJECT_ROOT")
KB_DIR="$PROJECT_ROOT/.knowledge-db"
# ... rest of script ...
```

#### 7.2 Python Helper Function

```python
# Add to knowledge_db.py or create kb_utils.py

import subprocess
import os

def find_project_root() -> str | None:
    """Find project root using kb-root.sh logic."""
    # Check env var first
    if env_root := os.environ.get("CLAUDE_PROJECT_DIR"):
        if os.path.isdir(env_root):
            return env_root

    # Walk up looking for markers
    current = os.getcwd()
    markers = [".knowledge-db", ".serena", ".claude", ".git"]

    while current != "/":
        for marker in markers:
            if os.path.isdir(os.path.join(current, marker)):
                return current
        current = os.path.dirname(current)

    return None
```

---

## File Summary

### New Files
| File | Purpose |
|------|---------|
| `~/.claude/scripts/kb-root.sh` | Unified project detection |
| `~/.claude/scripts/kb-init.sh` | Initialize Knowledge DB |
| `~/.claude/scripts/smart-capture.py` | LLM-powered content evaluation |

### Modified Files
| File | Changes |
|------|---------|
| `~/.claude/scripts/knowledge_db.py` | Enhanced schema, migration, structured input |
| `~/.claude/scripts/klean-statusline.py` | Rich status symbols (✓ ○ — ✗) |
| `~/.claude/scripts/knowledge-capture.py` | Accept --json input |
| `~/.claude/scripts/knowledge-server.py` | Use kb-root.sh |
| `~/.claude/scripts/knowledge-query.sh` | Use kb-root.sh |
| `~/.claude/hooks/session-start.sh` | Use kb-root.sh, better startup logic |
| `~/.claude/hooks/user-prompt-handler.sh` | Add InitKB, update SaveThis/SaveInfo |
| `~/.claude/hooks/post-bash-handler.sh` | Use kb-root.sh |
| `~/.claude/hooks/post-web-handler.sh` | Use kb-root.sh |

---

## Testing Checklist

### Phase 1 Tests
- [ ] `source kb-root.sh && find_project_root` returns correct path
- [ ] `get_socket_path` returns consistent hash-based path
- [ ] Schema migration adds new fields to old entries

### Phase 2 Tests
- [ ] New project (no .knowledge-db): statusline shows `kb:—`
- [ ] KB exists, server not running: shows `kb:○`
- [ ] KB exists, server running: shows `kb:✓`
- [ ] Stale socket gets cleaned up, shows `kb:✗` briefly then `kb:○`

### Phase 3 Tests
- [ ] `InitKB` creates .knowledge-db/ structure
- [ ] `InitKB --start` also starts server
- [ ] Adds to .gitignore if in git repo

### Phase 4 Tests
- [ ] `knowledge-capture.py --json '{...}'` accepts structured input
- [ ] All new fields are stored correctly
- [ ] Search finds entries by key_concepts

### Phase 5 Tests
- [ ] `SaveInfo "some content"` evaluates via LiteLLM
- [ ] Low relevance content is skipped
- [ ] High relevance content is saved with verbose output

### Phase 6 Tests
- [ ] Session start finds project root correctly
- [ ] Starts KB server if .knowledge-db exists
- [ ] Doesn't create .knowledge-db automatically

### Phase 7 Tests
- [ ] All scripts use consistent project detection
- [ ] Works from subdirectories
- [ ] Respects CLAUDE_PROJECT_DIR env var

---

## Implementation Order

```
Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5 ──► Phase 6 ──► Phase 7
   │           │           │           │           │           │           │
   ▼           ▼           ▼           ▼           ▼           ▼           ▼
kb-root.sh  statusline   InitKB    SaveThis   SaveInfo   session    update
+ schema    enhancement  command   enhance    enhance    hook       all scripts
```

**Estimated Effort:**
- Phase 1: 1-2 hours
- Phase 2: 1 hour
- Phase 3: 30 min
- Phase 4: 1-2 hours
- Phase 5: 1 hour
- Phase 6: 30 min
- Phase 7: 1 hour

**Total: ~7-9 hours**

---

## Rollback Plan

Each phase can be rolled back independently:
1. Keep original files in `~/claudeAgentic/review-system-backup/`
2. Test each phase before proceeding
3. If issues: `cp backup/file ~/.claude/scripts/file`

---

## Success Criteria

1. **Statusline** clearly shows KB state (not just ✓/✗)
2. **Project detection** works consistently from any subdirectory
3. **InitKB** provides clean initialization path
4. **SaveThis** stores rich, searchable atomic notes
5. **SaveInfo** intelligently evaluates external content
6. **All scripts** use unified detection logic
