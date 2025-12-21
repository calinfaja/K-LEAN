# K-LEAN Path Management Implementation Plan

## Executive Summary

This plan eliminates all 78 hardcoded paths across 28 files by centralizing path management in `kb-root.sh`. The approach maintains backward compatibility while enabling seamless installation on new systems.

---

## Current State: Hardcoded Paths Inventory

### Summary
| Category | Count | Pattern |
|----------|-------|---------|
| Python interpreter | 23 | `$HOME/.venvs/knowledge-db/bin/python` |
| Scripts directory | 45 | `~/.claude/scripts/` |
| Config paths | 5 | `~/.config/litellm/` |
| Other | 5 | Comments, symlinks |
| **Total** | **78** | |

### Complete File-by-Line Inventory

#### Hooks (5 files, 15 occurrences)

| File | Line | Current Code |
|------|------|--------------|
| `hooks/session-start.sh` | 10 | `SCRIPTS_DIR="$HOME/.claude/scripts"` |
| `hooks/session-start.sh` | 19 | `~/.claude/scripts/setup-litellm.sh` (in message) |
| `hooks/session-start.sh` | 80 | `PYTHON="$HOME/.venvs/knowledge-db/bin/python"` |
| `hooks/user-prompt-handler.sh` | 35 | `SCRIPTS_DIR="$HOME/.claude/scripts"` |
| `hooks/user-prompt-handler.sh` | 84 | `PYTHON_BIN="$HOME/.venvs/knowledge-db/bin/python"` |
| `hooks/user-prompt-handler.sh` | 140 | `PYTHON_BIN="$HOME/.venvs/knowledge-db/bin/python"` |
| `hooks/user-prompt-handler.sh` | 186 | `"$HOME/.venvs/knowledge-db/bin/python"` |
| `hooks/user-prompt-handler.sh` | 190 | `"$HOME/.venvs/knowledge-db/bin/python"` |
| `hooks/post-bash-handler.sh` | 25 | `SCRIPTS_DIR="$HOME/.claude/scripts"` |
| `hooks/post-bash-handler.sh` | 53 | `"$HOME/.venvs/knowledge-db/bin/python"` |
| `hooks/post-web-handler.sh` | 29 | `SCRIPTS_DIR="$HOME/.claude/scripts"` |
| `hooks/async-review.sh` | 25 | `~/.claude/scripts/parallel-deep-review.sh` |

#### Knowledge Scripts (8 files, 20 occurrences)

| File | Line | Current Code |
|------|------|--------------|
| `scripts/kb-root.sh` | 34-35 | Primary path definition (OK) |
| `scripts/kb-root.sh` | 45 | `KB_SCRIPTS_DIR` default (OK) |
| `scripts/kb-doctor.sh` | 236,280,308,346 | Uses `${KB_PYTHON:-fallback}` ✓ |
| `scripts/kb-doctor.sh` | 237,281,309,347 | Uses `${KB_SCRIPTS_DIR:-fallback}` ✓ |
| `scripts/kb-doctor.sh` | 251 | Hardcoded in echo message |
| `scripts/knowledge-query.sh` | 19 | Uses `${KB_PYTHON:-fallback}` ✓ |
| `scripts/kb-init.sh` | 54 | `PYTHON="${PYTHON:-$HOME/.venvs/...}"` |
| `scripts/fact-extract.sh` | 49 | `PYTHON="$HOME/.venvs/knowledge-db/bin/python"` |
| `scripts/fact-extract.sh` | 50 | `KNOWLEDGE_DB="$HOME/.claude/scripts/knowledge_db.py"` |
| `scripts/smart-capture.sh` | 46 | `PYTHON="$HOME/.venvs/..."` |
| `scripts/smart-capture.sh` | 47 | `KNOWLEDGE_DB="$HOME/.claude/scripts/..."` |
| `scripts/smart-web-capture.sh` | 53-54 | Hardcoded Python and KB path |
| `scripts/smart-web-capture.sh` | 93 | `KNOWLEDGE_QUERY="$HOME/.claude/scripts/..."` |
| `scripts/smart-web-capture.sh` | 275-276 | Hardcoded event script path |
| `scripts/auto-capture-hook.sh` | 20-21 | Hardcoded SCRIPTS_DIR and PYTHON |

#### Python Scripts (4 files, 5 occurrences)

| File | Line | Current Code |
|------|------|--------------|
| `scripts/kb_utils.py` | 19 | `PYTHON_BIN = Path.home() / ".venvs/knowledge-db/bin/python"` |
| `scripts/knowledge-capture.py` | 64 | `Path.home() / ".claude/scripts/knowledge-server.py"` |
| `scripts/smart-capture.py` | 183 | `Path.home() / ".claude/scripts/knowledge-capture.py"` |
| `scripts/knowledge_db.py` | 42 | Error message (low priority) |

#### Review Scripts (7 files, 25 occurrences)

| File | Line | Current Code |
|------|------|--------------|
| `scripts/quick-review.sh` | 16 | `source ~/.claude/scripts/session-helper.sh` |
| `scripts/quick-review.sh` | 18 | `source ~/.claude/scripts/review-logger.sh` |
| `scripts/quick-review.sh` | 71-75 | Hardcoded Python and knowledge-search.py |
| `scripts/quick-review.sh` | 149 | `~/.claude/scripts/fact-extract.sh` |
| `scripts/consensus-review.sh` | 14 | `source ~/.claude/scripts/session-helper.sh` |
| `scripts/consensus-review.sh` | 45-48 | Hardcoded Python and knowledge-search.py |
| `scripts/consensus-review.sh` | 164 | `~/.claude/scripts/fact-extract.sh` |
| `scripts/deep-review.sh` | 25 | `source ~/.claude/scripts/session-helper.sh` |
| `scripts/deep-review.sh` | 209 | Symlink to ~/.claude/scripts |
| `scripts/deep-review.sh` | 242 | `~/.claude/scripts/fact-extract.sh` |
| `scripts/second-opinion.sh` | 14 | `source ~/.claude/scripts/session-helper.sh` |
| `scripts/second-opinion.sh` | 104-107 | Hardcoded Python and knowledge-search.py |
| `scripts/parallel-deep-review.sh` | 22 | `source ~/.claude/scripts/session-helper.sh` |
| `scripts/parallel-deep-review.sh` | 158 | Symlink to ~/.claude/scripts |
| `scripts/parallel-deep-review.sh` | 259 | `~/.claude/scripts/fact-extract.sh` |
| `scripts/droid-review.sh` | 28 | `~/.claude/scripts/get-models.sh` |
| `scripts/droid-review.sh` | 158-159 | `~/.claude/scripts/knowledge-events.py` |
| `scripts/parallel-droid-review.sh` | 31 | `~/.claude/scripts/get-healthy-models.sh` |
| `scripts/parallel-droid-review.sh` | 206-207 | `~/.claude/scripts/knowledge-events.py` |

#### Dispatcher (1 file, 12 occurrences)

| File | Line | Current Code |
|------|------|--------------|
| `scripts/async-dispatch.sh` | 9 | `source ~/.claude/scripts/session-helper.sh` |
| `scripts/async-dispatch.sh` | 27 | `~/.claude/scripts/knowledge-init.sh` |
| `scripts/async-dispatch.sh` | 78 | `~/.claude/scripts/parallel-deep-review.sh` |
| `scripts/async-dispatch.sh` | 86 | `~/.claude/scripts/consensus-review.sh` |
| `scripts/async-dispatch.sh` | 95 | `~/.claude/scripts/quick-review.sh` |
| `scripts/async-dispatch.sh` | 100 | `~/.claude/scripts/quick-review.sh` |
| `scripts/async-dispatch.sh` | 105 | `~/.claude/scripts/quick-review.sh` |
| `scripts/async-dispatch.sh` | 115 | `~/.claude/scripts/second-opinion.sh` |
| `scripts/async-dispatch.sh` | 120 | `~/.claude/scripts/second-opinion.sh` |
| `scripts/async-dispatch.sh` | 125 | `~/.claude/scripts/second-opinion.sh` |
| `scripts/async-dispatch.sh` | 133 | `~/.claude/scripts/goodjob-dispatch.sh` |
| `scripts/async-dispatch.sh` | 146 | Both Python and scripts path |

#### Utility/Test Scripts (Low Priority)

| File | Lines | Notes |
|------|-------|-------|
| `scripts/post-commit-docs.sh` | 85 | fact-extract.sh call |
| `scripts/test-*.sh` | Various | Test scripts |
| `scripts/bashrc-additions.sh` | 12,36 | User shell functions |
| `scripts/setup-litellm.sh` | 170 | Echo message only |

---

## Target Architecture

### kb-root.sh: Enhanced Version

```bash
#!/usr/bin/env bash
#
# K-LEAN kb-root.sh - Single Source of Truth for All Paths
# =========================================================
# Source this file in ANY script that needs paths.
#
# Usage:
#   source "$SCRIPT_DIR/kb-root.sh"
#   $KB_PYTHON script.py
#   $(get_kb_script "fact-extract.sh") "$CONTENT"
#

# =============================================================================
# PATH CONFIGURATION (with environment variable overrides)
# =============================================================================

# Python interpreter - check multiple locations
if [ -n "$KLEAN_KB_PYTHON" ] && [ -x "$KLEAN_KB_PYTHON" ]; then
    KB_PYTHON="$KLEAN_KB_PYTHON"
elif [ -x "$HOME/.venvs/knowledge-db/bin/python" ]; then
    KB_PYTHON="$HOME/.venvs/knowledge-db/bin/python"
elif [ -x "$HOME/.local/share/klean/venv/bin/python" ]; then
    KB_PYTHON="$HOME/.local/share/klean/venv/bin/python"
elif command -v python3 &>/dev/null; then
    KB_PYTHON="python3"
else
    KB_PYTHON=""
fi

# Scripts directory - prefer same directory as this file
_KB_ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd)"
if [ -n "$KLEAN_SCRIPTS_DIR" ] && [ -d "$KLEAN_SCRIPTS_DIR" ]; then
    KB_SCRIPTS_DIR="$KLEAN_SCRIPTS_DIR"
elif [ -n "$_KB_ROOT_DIR" ] && [ -f "$_KB_ROOT_DIR/kb-root.sh" ]; then
    KB_SCRIPTS_DIR="$_KB_ROOT_DIR"
else
    KB_SCRIPTS_DIR="$HOME/.claude/scripts"
fi

# Socket directory
KB_SOCKET_DIR="${KLEAN_SOCKET_DIR:-/tmp}"

# Config directory (LiteLLM, etc.)
KB_CONFIG_DIR="${KLEAN_CONFIG_DIR:-$HOME/.config/litellm}"

# Export all
export KB_PYTHON KB_SCRIPTS_DIR KB_SOCKET_DIR KB_CONFIG_DIR

# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

# Validate Python is available and executable
require_kb_python() {
    if [ -z "$KB_PYTHON" ]; then
        echo "ERROR: K-LEAN Python not configured." >&2
        echo "" >&2
        echo "Solutions:" >&2
        echo "  1. Install: ./install.sh --knowledge" >&2
        echo "  2. Set manually: export KLEAN_KB_PYTHON=/path/to/python" >&2
        return 1
    fi
    if [ ! -x "$KB_PYTHON" ]; then
        echo "ERROR: K-LEAN Python not executable: $KB_PYTHON" >&2
        echo "" >&2
        echo "Solutions:" >&2
        echo "  1. Reinstall: ./install.sh --knowledge" >&2
        echo "  2. Check path: ls -la $KB_PYTHON" >&2
        return 1
    fi
    return 0
}

# Validate scripts directory exists
require_kb_scripts() {
    if [ -z "$KB_SCRIPTS_DIR" ] || [ ! -d "$KB_SCRIPTS_DIR" ]; then
        echo "ERROR: K-LEAN scripts not found: ${KB_SCRIPTS_DIR:-'(not set)'}" >&2
        echo "" >&2
        echo "Solutions:" >&2
        echo "  1. Install: ./install.sh --scripts" >&2
        echo "  2. Set manually: export KLEAN_SCRIPTS_DIR=/path/to/scripts" >&2
        return 1
    fi
    return 0
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# Get full path to a K-LEAN script
get_kb_script() {
    local script="$1"
    echo "${KB_SCRIPTS_DIR}/${script}"
}

# Get full path to a K-LEAN Python script
get_kb_py_script() {
    local script="$1"
    echo "${KB_SCRIPTS_DIR}/${script}"
}

# =============================================================================
# PROJECT DETECTION (existing functions)
# =============================================================================

find_kb_project_root() {
    local start_dir="${1:-$(pwd)}"
    local dir="$start_dir"

    if [ -n "$CLAUDE_PROJECT_DIR" ] && [ -d "$CLAUDE_PROJECT_DIR" ]; then
        echo "$CLAUDE_PROJECT_DIR"
        return 0
    fi

    while [ "$dir" != "/" ]; do
        for marker in ".knowledge-db" ".serena" ".claude" ".git"; do
            if [ -d "$dir/$marker" ]; then
                echo "$dir"
                return 0
            fi
        done
        dir=$(dirname "$dir")
    done

    return 1
}

get_kb_project_hash() {
    local root="$1"
    if [ -z "$root" ]; then return 1; fi
    local abs_path=$(cd "$root" 2>/dev/null && pwd)
    if command -v md5sum &>/dev/null; then
        echo -n "$abs_path" | md5sum | cut -c1-8
    elif command -v md5 &>/dev/null; then
        echo -n "$abs_path" | md5 | cut -c1-8
    else
        echo -n "$abs_path" | python3 -c "import sys,hashlib; print(hashlib.md5(sys.stdin.read().encode()).hexdigest()[:8])"
    fi
}

get_kb_socket_path() {
    local root="$1"
    local hash=$(get_kb_project_hash "$root")
    if [ -z "$hash" ]; then return 1; fi
    echo "${KB_SOCKET_DIR}/kb-${hash}.sock"
}

get_kb_pid_path() {
    local root="$1"
    local hash=$(get_kb_project_hash "$root")
    if [ -z "$hash" ]; then return 1; fi
    echo "${KB_SOCKET_DIR}/kb-${hash}.pid"
}

is_kb_initialized() {
    local root="$1"
    [ -d "$root/.knowledge-db" ]
}

is_kb_server_running() {
    local root="$1"
    local socket=$(get_kb_socket_path "$root")
    [ -S "$socket" ] || return 1

    local response
    if command -v socat &> /dev/null; then
        response=$(echo '{"cmd":"ping"}' | timeout 2 socat - UNIX-CONNECT:"$socket" 2>/dev/null)
    elif command -v nc &> /dev/null; then
        response=$(echo '{"cmd":"ping"}' | timeout 2 nc -U "$socket" 2>/dev/null)
    fi
    echo "$response" | grep -q '"pong"' 2>/dev/null
}

clean_kb_stale_socket() {
    local root="$1"
    local socket=$(get_kb_socket_path "$root")
    local pid_file=$(get_kb_pid_path "$root")
    if [ -S "$socket" ]; then
        if ! is_kb_server_running "$root"; then
            rm -f "$socket" "$pid_file" 2>/dev/null
            return 0
        fi
    fi
    return 1
}

get_kb_dir() {
    local root="$1"
    [ -n "$root" ] && echo "$root/.knowledge-db"
}

# Export functions for subshells
export -f find_kb_project_root get_kb_project_hash get_kb_socket_path
export -f get_kb_pid_path is_kb_initialized is_kb_server_running
export -f clean_kb_stale_socket get_kb_dir
export -f require_kb_python require_kb_scripts get_kb_script get_kb_py_script
```

---

## Implementation Phases

### Phase 0: Enhance kb-root.sh

**Changes**:
1. Add `KB_CONFIG_DIR` export
2. Add `require_kb_python()` function
3. Add `require_kb_scripts()` function
4. Add `get_kb_script()` helper
5. Improve `KB_SCRIPTS_DIR` detection (prefer same directory)

**Test**:
```bash
source scripts/kb-root.sh
echo "Python: $KB_PYTHON"
echo "Scripts: $KB_SCRIPTS_DIR"
require_kb_python && echo "✓ Python OK"
get_kb_script "fact-extract.sh"  # Should return full path
```

### Phase 1: Knowledge Scripts (6 files)

**Pattern**:
```bash
# Add at top of script (after shebang)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/kb-root.sh" || exit 1

# Replace:
#   $HOME/.venvs/knowledge-db/bin/python → $KB_PYTHON
#   $HOME/.claude/scripts/xxx.sh → $(get_kb_script "xxx.sh")
#   $HOME/.claude/scripts/xxx.py → $KB_SCRIPTS_DIR/xxx.py
```

**Files**:
1. `kb-init.sh` - Line 54
2. `fact-extract.sh` - Lines 49-50
3. `smart-capture.sh` - Lines 46-47
4. `smart-web-capture.sh` - Lines 53-54, 93, 275-276
5. `auto-capture-hook.sh` - Lines 20-21
6. Python files: `kb_utils.py`, `knowledge-capture.py`, `smart-capture.py`

### Phase 2: Hooks (5 files)

**Pattern for hooks** (need inline fallback):
```bash
# Hooks are entry points - need fallback if kb-root.sh missing
SCRIPTS_DIR="${KLEAN_SCRIPTS_DIR:-$HOME/.claude/scripts}"
if [ -f "$SCRIPTS_DIR/kb-root.sh" ]; then
    source "$SCRIPTS_DIR/kb-root.sh"
else
    KB_PYTHON="${KLEAN_KB_PYTHON:-$HOME/.venvs/knowledge-db/bin/python}"
    KB_SCRIPTS_DIR="$SCRIPTS_DIR"
fi
```

**Files**:
1. `session-start.sh` - Lines 10, 19, 80
2. `user-prompt-handler.sh` - Lines 35, 84, 140, 186, 190
3. `post-bash-handler.sh` - Lines 25, 53
4. `post-web-handler.sh` - Line 29
5. `async-review.sh` - Line 25

### Phase 3: Review Scripts (7 files)

**Approach**: Update `session-helper.sh` to source `kb-root.sh`, then all review scripts get variables automatically.

**Files**:
1. `session-helper.sh` - Add: `source "$SCRIPT_DIR/kb-root.sh" 2>/dev/null || true`
2. `quick-review.sh` - Lines 16, 18, 71-75, 149
3. `consensus-review.sh` - Lines 14, 45-48, 164
4. `deep-review.sh` - Lines 25, 209, 242
5. `second-opinion.sh` - Lines 14, 104-107
6. `parallel-deep-review.sh` - Lines 22, 158, 259
7. `droid-review.sh` - Lines 28, 158-159
8. `parallel-droid-review.sh` - Lines 31, 206-207

### Phase 4: Dispatcher (1 file)

**File**: `async-dispatch.sh` (12 occurrences)

**All script calls become**:
```bash
$(get_kb_script "parallel-deep-review.sh") ...
$(get_kb_script "consensus-review.sh") ...
$(get_kb_script "quick-review.sh") ...
```

### Phase 5: Utilities (6 files - optional)

- `post-commit-docs.sh`
- `bashrc-additions.sh`
- `test-*.sh`
- `setup-litellm.sh`

---

## Verification Tests

### Test 1: Fresh Install
```bash
rm -rf ~/.claude/scripts ~/.venvs/knowledge-db
./install.sh --full
source ~/.claude/scripts/kb-root.sh
require_kb_python && echo "✓ Fresh install works"
```

### Test 2: Environment Override
```bash
export KLEAN_KB_PYTHON=/usr/bin/python3
source scripts/kb-root.sh
[ "$KB_PYTHON" = "/usr/bin/python3" ] && echo "✓ Override works"
```

### Test 3: Missing Dependencies
```bash
mv ~/.venvs/knowledge-db ~/.venvs/knowledge-db.bak
source scripts/kb-root.sh
require_kb_python  # Should show clear error
mv ~/.venvs/knowledge-db.bak ~/.venvs/knowledge-db
```

### Test 4: Grep Verification
```bash
# Should return only fallback patterns
grep -r "\.venvs/knowledge-db" scripts/*.sh hooks/*.sh | grep -v "KB_PYTHON:-" | grep -v "^#"
# Expected: 0 results

grep -r '~/.claude/scripts/' scripts/*.sh hooks/*.sh | grep -v "KB_SCRIPTS_DIR" | grep -v "^#"
# Expected: 0 results
```

---

## Files Changed Summary

| Phase | Files | Estimated Changes |
|-------|-------|-------------------|
| 0 | kb-root.sh | +50 lines (new functions) |
| 1 | 6 shell + 3 Python | ~60 line changes |
| 2 | 5 hooks | ~30 line changes |
| 3 | 8 review scripts | ~70 line changes |
| 4 | 1 dispatcher | ~25 line changes |
| 5 | 6 utilities | ~20 line changes |
| **Total** | **29 files** | **~255 line changes** |

---

## Success Criteria

| Criterion | Metric |
|-----------|--------|
| Hardcoded paths | 0 (excluding fallbacks in kb-root.sh) |
| Fresh install | Works without manual path config |
| Env override | `KLEAN_*` vars respected |
| Error messages | Clear, with solution |
| Backward compatible | Existing installs unchanged |
