# Knowledge System V2 - Production Fixes Plan

## Overview

This document outlines the fixes needed to make the Knowledge System V2 production-ready based on the code analysis performed on 2025-12-20.

**Current Grade:** B+
**Target Grade:** A-
**Estimated Effort:** 2-3 hours

---

## Phase 1: Critical Security Fixes

### 1.1 SQL Injection in knowledge_db.py

**File:** `scripts/knowledge_db.py`
**Line:** 219
**Severity:** MEDIUM

**Current Code:**
```python
sql_query = f"select id, text, title, summary, ... from txtai where similar('{query}') limit {limit}"
```

**Fixed Code:**
```python
# Escape single quotes to prevent SQL injection
safe_query = query.replace("'", "''")
sql_query = f"select id, text, title, summary, ... from txtai where similar('{safe_query}') limit {limit}"
```

**Test:**
```bash
# Should not break with quotes in query
~/.claude/scripts/knowledge-query.sh "it's a test"
~/.claude/scripts/knowledge-query.sh "'; DROP TABLE txtai; --"
```

---

### 1.2 URL Scheme Validation in smart-capture.py

**File:** `scripts/smart-capture.py`
**Line:** 122
**Severity:** MEDIUM

**Current Code:**
```python
def fetch_url(url: str, max_chars: int = 15000) -> str:
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "K-LEAN-SmartCapture/1.0"}
        )
```

**Fixed Code:**
```python
def fetch_url(url: str, max_chars: int = 15000) -> str:
    """Fetch URL content with security validation."""
    from urllib.parse import urlparse

    # Validate URL scheme
    parsed = urlparse(url)
    if parsed.scheme not in ('http', 'https'):
        return f"Error: Unsupported URL scheme '{parsed.scheme}'. Only http/https allowed."

    if not parsed.netloc:
        return "Error: Invalid URL - missing domain"

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "K-LEAN-SmartCapture/1.0"}
        )
```

**Test:**
```bash
# Should reject non-http URLs
python3 ~/.claude/scripts/smart-capture.py "file:///etc/passwd" --dry-run
python3 ~/.claude/scripts/smart-capture.py "ftp://example.com" --dry-run
```

---

## Phase 2: Eliminate Hardcoded Paths

### 2.1 Files to Update

| File | Lines | Current | Fixed |
|------|-------|---------|-------|
| `kb-init.sh` | 54 | `/home/calin/.venvs/...` | `$HOME/.venvs/...` |
| `smart-capture.py` | 41 | `Path.home() / ".venvs/..."` | Already correct |
| `knowledge-capture.py` | 66-67 | Hardcoded paths | Use `Path.home()` |
| `user-prompt-handler.sh` | 58, 141 | `/home/calin/...` | `$HOME/...` |

### 2.2 kb-init.sh Fix

**Line 54:**
```bash
# Current
PYTHON="${PYTHON:-/home/calin/.venvs/knowledge-db/bin/python}"

# Fixed
PYTHON="${PYTHON:-$HOME/.venvs/knowledge-db/bin/python}"
```

### 2.3 user-prompt-handler.sh Fix

**Line 58:**
```bash
# Current
PYTHON_BIN="/home/calin/.venvs/knowledge-db/bin/python"

# Fixed
PYTHON_BIN="$HOME/.venvs/knowledge-db/bin/python"
```

**Line 141:**
```bash
# Current
PYTHON_BIN="/home/calin/.venvs/knowledge-db/bin/python"

# Fixed
PYTHON_BIN="$HOME/.venvs/knowledge-db/bin/python"
```

---

## Phase 3: Create Shared Python Module

### 3.1 Create kb_utils.py

**File:** `scripts/kb_utils.py`

```python
#!/usr/bin/env python3
"""
K-LEAN Knowledge Base Utilities

Shared utilities for KB scripts to eliminate code duplication.
This module provides:
- Project root detection (matching kb-root.sh logic)
- Socket path calculation
- Server health checks
"""

import os
import hashlib
import socket
from pathlib import Path
from typing import Optional


def find_project_root(start_dir: str = None) -> Optional[Path]:
    """
    Find project root by walking up looking for project markers.

    Priority order (matches kb-root.sh):
    1. CLAUDE_PROJECT_DIR environment variable
    2. .knowledge-db directory
    3. .serena directory
    4. .claude directory
    5. .git directory

    Args:
        start_dir: Starting directory (default: current working directory)

    Returns:
        Path to project root or None if not found
    """
    # Priority 1: Environment variable
    env_dir = os.environ.get("CLAUDE_PROJECT_DIR")
    if env_dir and Path(env_dir).is_dir():
        return Path(env_dir)

    # Priority 2-5: Walk up looking for markers
    current = Path(start_dir or os.getcwd()).resolve()
    markers = [".knowledge-db", ".serena", ".claude", ".git"]

    while current != current.parent:
        for marker in markers:
            if (current / marker).is_dir():
                return current
        current = current.parent

    return None


def get_project_hash(project_path: str) -> str:
    """
    Calculate MD5 hash of project path (first 8 chars).
    Used for unique socket/pid file naming per project.

    Args:
        project_path: Path to project root

    Returns:
        8-character hash string
    """
    abs_path = str(Path(project_path).resolve())
    return hashlib.md5(abs_path.encode()).hexdigest()[:8]


def get_socket_path(project_path: str) -> str:
    """
    Get socket path for project's knowledge server.

    Args:
        project_path: Path to project root

    Returns:
        Socket path (e.g., /tmp/kb-a1b2c3d4.sock)
    """
    import tempfile
    hash_val = get_project_hash(project_path)
    return f"{tempfile.gettempdir()}/kb-{hash_val}.sock"


def get_pid_path(project_path: str) -> str:
    """
    Get PID file path for project's knowledge server.

    Args:
        project_path: Path to project root

    Returns:
        PID file path
    """
    import tempfile
    hash_val = get_project_hash(project_path)
    return f"{tempfile.gettempdir()}/kb-{hash_val}.pid"


def is_kb_initialized(project_path: str) -> bool:
    """
    Check if knowledge DB is initialized for project.

    Args:
        project_path: Path to project root

    Returns:
        True if .knowledge-db directory exists
    """
    if not project_path:
        return False
    return (Path(project_path) / ".knowledge-db").is_dir()


def is_server_running(project_path: str, timeout: float = 2.0) -> bool:
    """
    Check if KB server is running and responsive.

    Args:
        project_path: Path to project root
        timeout: Socket timeout in seconds

    Returns:
        True if server responds to ping
    """
    socket_path = get_socket_path(project_path)

    if not os.path.exists(socket_path):
        return False

    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(socket_path)
        sock.sendall(b'{"cmd":"ping"}')
        response = sock.recv(1024).decode()
        sock.close()
        return '"pong"' in response
    except (socket.error, socket.timeout, OSError):
        return False


def clean_stale_socket(project_path: str) -> bool:
    """
    Clean stale socket if server is not responsive.

    Args:
        project_path: Path to project root

    Returns:
        True if socket was cleaned, False otherwise
    """
    socket_path = get_socket_path(project_path)
    pid_path = get_pid_path(project_path)

    if os.path.exists(socket_path):
        if not is_server_running(project_path):
            try:
                os.unlink(socket_path)
                if os.path.exists(pid_path):
                    os.unlink(pid_path)
                return True
            except OSError:
                pass
    return False


def get_python_bin() -> str:
    """
    Get path to knowledge-db Python interpreter.

    Returns:
        Path to Python binary
    """
    venv_python = Path.home() / ".venvs/knowledge-db/bin/python"
    if venv_python.exists():
        return str(venv_python)
    return "python3"


def get_scripts_dir() -> Path:
    """
    Get path to K-LEAN scripts directory.

    Returns:
        Path to scripts directory
    """
    scripts_dir = Path.home() / ".claude/scripts"
    if scripts_dir.exists():
        return scripts_dir

    # Fallback to backup location
    backup_dir = Path.home() / "claudeAgentic/review-system-backup/scripts"
    if backup_dir.exists():
        return backup_dir

    return scripts_dir  # Return default even if doesn't exist
```

### 3.2 Update Scripts to Use kb_utils.py

**smart-capture.py - Replace lines 79-99:**
```python
# Import shared utilities
try:
    from kb_utils import find_project_root, get_socket_path, is_server_running, get_python_bin
except ImportError:
    # Fallback if kb_utils not available
    # ... keep existing inline functions
```

**knowledge-capture.py - Replace lines 51-74:**
```python
try:
    from kb_utils import get_socket_path, is_server_running, find_project_root
except ImportError:
    # Fallback implementations
    ...
```

**klean-statusline.py - Replace lines 168-210:**
```python
try:
    from kb_utils import find_project_root, get_socket_path, is_kb_initialized
except ImportError:
    # Fallback implementations
    ...
```

**knowledge_db.py - Replace lines 69-84:**
```python
try:
    from kb_utils import find_project_root
except ImportError:
    # Fallback implementation
    def find_project_root(start_path=None):
        ...
```

---

## Phase 4: Improve Error Handling

### 4.1 Don't Silence Subprocess Errors

**knowledge-capture.py lines 86-102:**
```python
# Current - errors silenced
subprocess.Popen(
    [...],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)

# Fixed - log errors on failure
import tempfile
log_path = Path(tempfile.gettempdir()) / f"kb-server-{os.getpid()}.log"
log_file = open(log_path, 'w')
proc = subprocess.Popen(
    [...],
    stdout=log_file,
    stderr=subprocess.STDOUT,
)
# ... wait for server ...
if not is_server_running(project_path):
    log_file.close()
    with open(log_path) as f:
        print(f"Server failed to start. Log:\n{f.read()}", file=sys.stderr)
```

### 4.2 Add Bounds Checking for JSON Extraction

**smart-capture.py lines 175-182:**
```python
# Current - can raise IndexError
if "```json" in content:
    content = content.split("```json")[1].split("```")[0].strip()

# Fixed - with bounds checking
if "```json" in content:
    parts = content.split("```json")
    if len(parts) > 1:
        inner = parts[1].split("```")
        if inner:
            content = inner[0].strip()
elif "```" in content:
    parts = content.split("```")
    if len(parts) >= 2:
        content = parts[1].strip()
```

### 4.3 Log Skipped JSONL Lines

**knowledge_db.py lines 505-507:**
```python
# Current
except json.JSONDecodeError:
    skipped_lines += 1

# Fixed
except json.JSONDecodeError as e:
    skipped_lines += 1
    if os.environ.get("KLEAN_DEBUG"):
        import sys
        print(f"Warning: Skipped malformed JSON at line {line_num}: {e}", file=sys.stderr)
```

---

## Phase 5: Performance Improvements

### 5.1 Pre-compile Regexes in klean-statusline.py

**Add at module level (after imports):**
```python
import re

# Pre-compiled regexes for git stats parsing
RE_INSERTIONS = re.compile(r'(\d+) insertion')
RE_DELETIONS = re.compile(r'(\d+) deletion')
```

**Update get_git() function (lines 130-135):**
```python
# Current
import re
ins_match = re.search(r'(\d+) insertion', diff_out)
del_match = re.search(r'(\d+) deletion', diff_out)

# Fixed
ins_match = RE_INSERTIONS.search(diff_out)
del_match = RE_DELETIONS.search(diff_out)
```

### 5.2 Add JSONL Cache to knowledge_db.py

**Add to KnowledgeDB.__init__():**
```python
def __init__(self, project_path: str = None):
    # ... existing init code ...

    # JSONL cache for search performance
    self._jsonl_cache = None
    self._jsonl_mtime = 0
```

**Add helper method:**
```python
def _get_jsonl_entries(self) -> dict:
    """Get JSONL entries with caching."""
    if self.jsonl_path.exists():
        mtime = self.jsonl_path.stat().st_mtime
        if self._jsonl_cache is None or mtime > self._jsonl_mtime:
            self._jsonl_cache = {}
            with open(self.jsonl_path) as f:
                for line in f:
                    if line.strip():
                        try:
                            entry = json.loads(line)
                            self._jsonl_cache[entry.get("id")] = entry
                        except json.JSONDecodeError:
                            pass
            self._jsonl_mtime = mtime
    return self._jsonl_cache or {}
```

**Update search() to use cache (line 227):**
```python
# Current
jsonl_entries = {}
if self.jsonl_path.exists():
    with open(self.jsonl_path) as f:
        for line in f:
            ...

# Fixed
jsonl_entries = self._get_jsonl_entries()
```

---

## Phase 6: Update Comments

### 6.1 Remove Redundant Comments

**knowledge_db.py line 191:**
```python
# Remove this comment (obvious from context):
# Upsert in txtai - format: (id, {"text": ..., ...metadata}, None)
```

**knowledge-capture.py line 172:**
```python
# Remove this comment (obvious from field names):
# V2 schema fields
```

### 6.2 Update Stale Comments

**klean-statusline.py lines 174-197:**
```python
# Current comment duplicates kb-root.sh explanation
# Fixed: Reference the source
def find_project_root(start_dir: str) -> str | None:
    """Find project root. See kb-root.sh for priority order."""
```

---

## Implementation Checklist

### Phase 1: Critical Security
- [ ] Fix SQL injection in knowledge_db.py:219
- [ ] Add URL scheme validation in smart-capture.py:122
- [ ] Test with malicious inputs

### Phase 2: Hardcoded Paths
- [ ] Update kb-init.sh:54
- [ ] Update user-prompt-handler.sh:58,141
- [ ] Verify all `$HOME` references work

### Phase 3: Shared Module
- [ ] Create kb_utils.py
- [ ] Update smart-capture.py to use kb_utils
- [ ] Update knowledge-capture.py to use kb_utils
- [ ] Update klean-statusline.py to use kb_utils
- [ ] Update knowledge_db.py to use kb_utils
- [ ] Test all scripts still work

### Phase 4: Error Handling
- [ ] Fix subprocess error logging in knowledge-capture.py
- [ ] Add bounds checking in smart-capture.py
- [ ] Add KLEAN_DEBUG logging in knowledge_db.py

### Phase 5: Performance
- [ ] Pre-compile regexes in klean-statusline.py
- [ ] Add JSONL cache to knowledge_db.py
- [ ] Benchmark search performance before/after

### Phase 6: Comments
- [ ] Remove redundant comments
- [ ] Update stale comments

### Final Validation
- [ ] Run `k-lean status` - all components OK
- [ ] Test `InitKB` on new project
- [ ] Test `SaveThis` command
- [ ] Test `SaveInfo` command
- [ ] Test `FindKnowledge` command
- [ ] Verify statusline shows correct KB status
- [ ] Sync all changes to backup directory

---

## Rollback Plan

If issues occur after applying fixes:

```bash
# Restore from git
cd ~/claudeAgentic
git checkout HEAD~1 -- review-system-backup/scripts/

# Re-sync to ~/.claude/scripts
cp review-system-backup/scripts/*.py ~/.claude/scripts/
cp review-system-backup/scripts/*.sh ~/.claude/scripts/
```

---

## Post-Fix Validation Commands

```bash
# 1. Check all scripts load without errors
python3 -c "import sys; sys.path.insert(0, '$HOME/.claude/scripts'); import kb_utils; print('OK')"

# 2. Test SQL injection fix
~/.claude/scripts/knowledge-query.sh "test'; DROP TABLE--" 2>&1 | grep -v "DROP"

# 3. Test URL validation
python3 ~/.claude/scripts/smart-capture.py "file:///etc/passwd" --dry-run 2>&1 | grep "Unsupported"

# 4. Verify no hardcoded paths
grep -r "/home/calin" ~/.claude/scripts/*.py ~/.claude/scripts/*.sh 2>/dev/null | grep -v "^Binary"

# 5. Full integration test
k-lean status
```

---

## Estimated Timeline

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1: Security | 15 min | None |
| Phase 2: Paths | 10 min | None |
| Phase 3: kb_utils | 30 min | None |
| Phase 4: Errors | 20 min | Phase 3 |
| Phase 5: Performance | 20 min | Phase 3 |
| Phase 6: Comments | 10 min | None |
| Validation | 15 min | All phases |
| **Total** | **~2 hours** | |

---

*Document created: 2025-12-20*
*Based on: Production Readiness Analysis*
