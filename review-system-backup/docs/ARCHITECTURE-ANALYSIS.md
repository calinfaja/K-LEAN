# K-LEAN System Architecture Analysis

## System Overview

K-LEAN is a multi-model code review and knowledge capture system for Claude Code with 3 main subsystems:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              K-LEAN SYSTEM                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐          │
│  │  REVIEW SYSTEM   │  │  KNOWLEDGE DB    │  │  DROIDS SYSTEM   │          │
│  │                  │  │                  │  │                  │          │
│  │  quick-review    │  │  knowledge-db.py │  │  droid-execute   │          │
│  │  consensus       │  │  knowledge-query │  │  droid-review    │          │
│  │  deep-review     │  │  knowledge-server│  │  8 specialists   │          │
│  │  parallel-*      │  │  fact-extract    │  │                  │          │
│  └────────┬─────────┘  └────────┬─────────┘  └────────┬─────────┘          │
│           │                     │                     │                     │
│           └──────────┬──────────┴──────────┬──────────┘                     │
│                      │                     │                                │
│           ┌──────────▼──────────┐ ┌────────▼────────┐                      │
│           │   SHARED INFRA      │ │   ENTRY POINTS  │                      │
│           │                     │ │                 │                      │
│           │  session-helper.sh  │ │  hooks/         │                      │
│           │  kb-root.sh         │ │  install.sh     │                      │
│           │  lib/common.sh      │ │  k-lean CLI     │                      │
│           └─────────────────────┘ └─────────────────┘                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Component Analysis

### 1. Entry Points

| Entry Point | Trigger | What it Does |
|-------------|---------|--------------|
| `hooks/session-start.sh` | SessionStart | Auto-starts LiteLLM + KB server |
| `hooks/user-prompt-handler.sh` | UserPromptSubmit | 7 keywords → script dispatch |
| `hooks/post-bash-handler.sh` | PostToolUse(Bash) | Post-commit docs, timeline |
| `hooks/post-web-handler.sh` | PostToolUse(Web*) | Auto-capture URLs |
| `install.sh` | User runs | Full system installation |

### 2. Shared Infrastructure (Critical Path)

```
kb-root.sh
    └── Exports: KB_PYTHON, KB_SCRIPTS_DIR, KB_SOCKET_DIR
    └── Functions: find_kb_project_root, get_kb_socket_path
    └── Sourced by: kb-doctor.sh, knowledge-query.sh, kb-init.sh, droid-execute.sh

session-helper.sh
    └── Exports: KLN_BASE_DIR, SESSION_DIR, SESSION_ID
    └── Functions: find_project_root, get_output_dir, generate_filename
    └── Sourced by: ALL review scripts

lib/common.sh
    └── Exports: Colors, log_* functions
    └── Functions: check_dependencies, create_venv, log_debug
    └── Sourced by: install.sh, deep-review.sh, quick-review.sh
```

### 3. Script Call Chain

```
                    ┌─────────────────────────────────────┐
                    │         ENTRY POINTS                │
                    └─────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌───────────────┐
│ session-start │          │ user-prompt   │          │ async-dispatch│
│    (hook)     │          │   (hook)      │          │   (script)    │
└───────────────┘          └───────────────┘          └───────────────┘
        │                           │                           │
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐   ┌───────────────────────────┐   ┌───────────────┐
│knowledge-server│   │ quick-review.sh          │   │parallel-deep  │
│ (auto-start)  │   │ consensus-review.sh       │   │  -review.sh   │
└───────────────┘   │ parallel-deep-review.sh   │   └───────┬───────┘
                    └───────────────────────────┘           │
                                    │                       │
                    ┌───────────────┼───────────────┐       │
                    ▼               ▼               ▼       ▼
            ┌───────────────┐ ┌─────────────┐ ┌─────────────────┐
            │fact-extract.sh│ │knowledge-   │ │session-helper.sh│
            │ (KB capture)  │ │search.py    │ │  (output dirs)  │
            └───────┬───────┘ └──────┬──────┘ └─────────────────┘
                    │                │
                    ▼                ▼
            ┌───────────────────────────────┐
            │        KNOWLEDGE DB           │
            │   knowledge_db.py (txtai)     │
            │   entries.jsonl + index/      │
            └───────────────────────────────┘
```

---

## Current Path Architecture

### Hardcoded Paths (The Problem)

| Path Pattern | Count | Used By |
|--------------|-------|---------|
| `~/.venvs/knowledge-db/bin/python` | 15+ | All KB scripts, review scripts |
| `~/.claude/scripts/*` | 30+ | All scripts calling each other |
| `~/.config/litellm/` | 3 | session-start, setup-litellm |
| `~/.factory/droids/` | 1 | install.sh |

### Current Centralization (Partial)

**kb-root.sh** (added recently):
```bash
# Good: Defines paths with fallbacks
KB_PYTHON="${KLEAN_KB_PYTHON:-$HOME/.venvs/knowledge-db/bin/python}"
KB_SCRIPTS_DIR="${KLEAN_SCRIPTS_DIR:-$HOME/.claude/scripts}"

# Good: Exports for subshells
export KB_PYTHON KB_SCRIPTS_DIR KB_SOCKET_DIR
```

**Problem**: Only 4 scripts source kb-root.sh. The other 35+ use hardcoded paths.

---

## Core Principles Identified

### 1. Per-Project Isolation
- Each project gets its own `.knowledge-db/` directory
- Each project gets unique socket: `/tmp/kb-{hash}.sock`
- Output goes to `<project>/.claude/kln/`

### 2. Auto-Start Pattern
- LiteLLM: Global, starts on session-start if not running
- KB Server: Per-project, starts on first query if not running
- Non-blocking: Uses `nohup ... &`

### 3. Layered Fallbacks
```
1. Environment variable (power users)
2. Primary path (default install location)
3. Secondary path (alternative location)
4. System python (last resort)
```

### 4. Source Chain
```
Entry script → sources session-helper.sh → sources lib/common.sh
             → sources kb-root.sh (when KB needed)
```

---

## Path Categories

### Category A: Python Interpreter
All scripts need the same Python with txtai installed.

| Current | Proposed |
|---------|----------|
| `$HOME/.venvs/knowledge-db/bin/python` | `$KB_PYTHON` (from kb-root.sh) |

**Scripts affected**: 15 files

### Category B: Script Directory
Scripts calling other scripts need to know where they are.

| Current | Proposed |
|---------|----------|
| `~/.claude/scripts/script.sh` | `$KB_SCRIPTS_DIR/script.sh` |

**Scripts affected**: 12 files

### Category C: Relative Paths (Already Good)
Scripts using `$SCRIPT_DIR` for same-directory references.

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/kb-root.sh"  # This is correct!
```

**Scripts using this correctly**: kb-doctor.sh, droid-execute.sh, knowledge-query.sh

---

## KISS Proposal

### Single Source of Truth: kb-root.sh

```bash
# kb-root.sh - THE source of truth for all paths

# 1. Python interpreter (with fallback chain)
KB_PYTHON="${KLEAN_KB_PYTHON:-}"
[ -z "$KB_PYTHON" ] && [ -x "$HOME/.venvs/knowledge-db/bin/python" ] && KB_PYTHON="$HOME/.venvs/knowledge-db/bin/python"
[ -z "$KB_PYTHON" ] && [ -x "$HOME/.local/share/klean/venv/bin/python" ] && KB_PYTHON="$HOME/.local/share/klean/venv/bin/python"
[ -z "$KB_PYTHON" ] && command -v python3 &>/dev/null && KB_PYTHON="python3"

# 2. Scripts directory
KB_SCRIPTS_DIR="${KLEAN_SCRIPTS_DIR:-$HOME/.claude/scripts}"

# 3. Validation functions
require_kb_python() {
    if [ -z "$KB_PYTHON" ] || [ ! -x "$KB_PYTHON" ]; then
        echo "ERROR: K-LEAN Python not found. Run: k-lean install" >&2
        return 1
    fi
}

export KB_PYTHON KB_SCRIPTS_DIR
```

### Migration Pattern

**Before** (hardcoded):
```bash
PYTHON="$HOME/.venvs/knowledge-db/bin/python"
~/.claude/scripts/fact-extract.sh "$CONTENT" ...
```

**After** (centralized):
```bash
source "$(dirname "${BASH_SOURCE[0]}")/kb-root.sh"
$KB_PYTHON script.py  # Uses KB_PYTHON
$KB_SCRIPTS_DIR/fact-extract.sh "$CONTENT" ...  # Uses KB_SCRIPTS_DIR
```

---

## Compatibility Matrix

| Component | Backward Compatible | Migration Needed |
|-----------|---------------------|------------------|
| kb-root.sh | Yes (already has fallbacks) | Add require_* functions |
| session-helper.sh | Yes | None (different purpose) |
| lib/common.sh | Yes | None |
| hooks/*.sh | Yes | Source kb-root.sh |
| Review scripts | Yes | Replace hardcoded paths |
| KB scripts | Partial | 4/10 done |

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Breaking existing installs | Low | Fallback chain preserves old paths |
| Missing kb-root.sh | Low | Inline fallback in critical scripts |
| Circular sourcing | None | kb-root.sh has no dependencies |
| Performance | None | Source once at script start |

---

## Proposed Fix Order

### Phase 1: Core Infrastructure (4 files)
1. Enhance `kb-root.sh` with require_* validation
2. Ensure session-helper.sh sources kb-root.sh

### Phase 2: Knowledge Scripts (6 files)
- kb-init.sh
- kb-doctor.sh ✓ (done)
- knowledge-query.sh ✓ (done)
- fact-extract.sh
- smart-capture.sh
- smart-web-capture.sh

### Phase 3: Review Scripts (7 files)
- quick-review.sh
- second-opinion.sh
- consensus-review.sh
- deep-review.sh
- parallel-deep-review.sh
- droid-review.sh
- parallel-droid-review.sh

### Phase 4: Dispatcher & Hooks (4 files)
- async-dispatch.sh (most complex - 12 occurrences)
- session-start.sh
- user-prompt-handler.sh
- post-commit-docs.sh

### Phase 5: Utility Scripts (6 files)
- auto-capture-hook.sh
- get-models.sh
- get-healthy-models.sh
- test-*.sh (optional)
- bashrc-additions.sh

---

## Success Criteria

1. **Fresh Install**: `install.sh --full` works on clean system
2. **Env Override**: Setting `KLEAN_KB_PYTHON=/custom/python` works
3. **Missing Deps**: Clear error message if Python/venv missing
4. **Backward Compatible**: Existing installs continue working
5. **Single Source**: All paths come from kb-root.sh

---

## Summary

The system has good foundations (kb-root.sh, session-helper.sh, lib/common.sh) but inconsistent adoption. The fix is mechanical:

1. Add validation functions to kb-root.sh
2. Source kb-root.sh at top of every script that needs paths
3. Replace hardcoded paths with exported variables
4. Test on fresh system

**Estimated effort**: 2-3 hours of mechanical changes + testing
**Risk**: Low (fallback chain preserves compatibility)
**Benefit**: Works on any system, easy to maintain
