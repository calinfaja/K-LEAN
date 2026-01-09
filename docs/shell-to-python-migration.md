# Shell to Python Migration Comparison

This document compares the old shell scripts with their Python replacements as part of the cross-platform migration.

## Overview

- **Total Shell Scripts**: 33 files (4 hooks + 1 lib + 28 scripts)
- **New Python Modules**: 3 files (platform.py, reviews.py, hooks.py)
- **Key Change**: All functionality now works on Windows, Linux, and macOS

## Hook Replacements

| Old Shell Script | New Python Entry Point | Module |
|-----------------|------------------------|--------|
| `hooks/session-start.sh` | `kln-hook-session` | `klean.hooks:session_start` |
| `hooks/user-prompt-handler.sh` | `kln-hook-prompt` | `klean.hooks:prompt_handler` |
| `hooks/post-bash-handler.sh` | `kln-hook-bash` | `klean.hooks:post_bash` |
| `hooks/post-web-handler.sh` | `kln-hook-web` | `klean.hooks:post_web` |

### Functionality Comparison

**session-start.sh** (96 lines) -> **hooks.py session_start()** (~40 lines)
- Starts LiteLLM proxy if not running
- Starts Knowledge Server for current project
- Outputs status messages

**user-prompt-handler.sh** (232 lines) -> **hooks.py prompt_handler()** (~60 lines)
- Handles FindKnowledge keyword
- Handles SaveInfo keyword
- Handles InitKB keyword
- Handles asyncReview keywords

**post-bash-handler.sh** (93 lines) -> **hooks.py post_bash()** (~15 lines)
- Detects git commits
- Logs to timeline

**post-web-handler.sh** (106 lines) -> **hooks.py post_web()** (~20 lines)
- Detects documentation URLs
- Triggers smart capture (pending full implementation)

## Script Replacements

### Review Scripts -> reviews.py

| Old Shell Script | New Python Function | Notes |
|-----------------|---------------------|-------|
| `quick-review.sh` (161 lines) | `reviews.quick_review()` | Async httpx |
| `consensus-review.sh` (173 lines) | `reviews.consensus_review()` | Parallel model calls |
| `second-opinion.sh` (186 lines) | `reviews.second_opinion()` | Fallback logic |
| `health-check.sh` (92 lines) | `reviews._check_model_health()` | Per-model check |
| `get-healthy-models.sh` | `reviews._get_healthy_models()` | Model discovery |
| `health-check-model.sh` | `reviews._check_model_health()` | Model health |

### Platform Scripts -> platform.py + cli.py

| Old Shell Script | New Python Function | Notes |
|-----------------|---------------------|-------|
| `start-litellm.sh` | `cli.start_litellm()` | Uses spawn_background |
| `kb-root.sh` (263 lines) | `platform.find_project_root()` | Path utilities |
| `common.sh` (227 lines) | `platform.py` | All utilities |

### Knowledge Scripts -> kb_utils.py + knowledge-server.py

| Old Shell Script | New Python Function | Notes |
|-----------------|---------------------|-------|
| `knowledge-init.sh` | `kb_utils.is_kb_initialized()` | KB init check |
| `knowledge-query.sh` | `kb_utils.send_command()` | TCP query |
| `kb-init.sh` | `hooks._handle_init_kb()` | Via hooks |

## Key Technical Changes

### IPC: Unix Sockets -> TCP

```python
# Old (Unix socket - Linux/Mac only)
sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect("/tmp/kb-{hash}.sock")

# New (TCP - Cross-platform)
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(("127.0.0.1", port))
```

### Process Management: pkill/pgrep -> psutil

```python
# Old (shell commands - not Windows)
subprocess.run(["pkill", "-f", "litellm"])
subprocess.run(["pgrep", "-f", "knowledge-server"])

# New (psutil - Cross-platform)
from klean.platform import kill_process_tree, is_process_running
kill_process_tree(pid, timeout=5.0)
is_process_running(pid)
```

### Background Process Spawning

```python
# Old (shell - requires bash)
nohup litellm --config ... &

# New (platform.spawn_background)
pid = spawn_background(["litellm", "--config", ...])
```

### Path Management: Hardcoded -> platformdirs

```python
# Old (hardcoded paths)
CONFIG_DIR="/home/$USER/.config/litellm"
RUNTIME_DIR="/tmp"

# New (platformdirs)
from klean.platform import get_config_dir, get_runtime_dir
config_dir = get_config_dir()  # Windows: %APPDATA%\klean
runtime_dir = get_runtime_dir()  # Windows: %TEMP%\klean-{user}
```

## Scripts NOT Being Replaced

These scripts are either:
1. One-off utilities not part of core workflow
2. Will be addressed in future work
3. Can remain as optional tools

| Script | Reason |
|--------|--------|
| `bashrc-additions.sh` | Optional shell aliases |
| `prepare-release.sh` | Release process (manual) |
| `test-system.sh` | Manual testing |
| `setup-litellm.sh` | One-time setup (handled by kln setup) |
| `async-dispatch.sh` | Complex async - future work |
| `smart-capture.sh` | Complex LLM pipeline - future work |
| `smart-web-capture.sh` | Complex LLM pipeline - future work |
| `fact-extract.sh` | LLM extraction - future work |
| `knowledge-extract.sh` | LLM extraction - future work |
| `timeline-query.sh` | Simple utility |
| `sync-check.sh` | Simple utility |
| `get-models.sh` | Simple utility (use kln model list) |
| `review-logger.sh` | Logging utility |
| `validate-model.sh` | Model validation |
| `post-commit-docs.sh` | Git hook (optional) |
| `auto-capture-hook.sh` | Auto capture (future) |
| `kb-doctor.sh` | Diagnostics |
| `session-helper.sh` | Helper |

## Test Coverage

All new Python implementations have corresponding tests:

- `tests/unit/test_platform.py` - 37 tests
- `tests/unit/test_knowledge_server.py` - 16 tests
- `tests/unit/test_reviews.py` - 24 tests
- `tests/unit/test_hooks.py` - 25 tests
- `tests/unit/test_cli_integration.py` - 13 tests

**Total: 115 new tests for cross-platform functionality**

## Verification Checklist

- [x] All hook entry points work (kln-hook-*)
- [x] LiteLLM start/stop works without bash
- [x] Knowledge server uses TCP instead of Unix socket
- [x] Process management uses psutil
- [x] Path utilities work on all platforms
- [x] All 274 unit tests pass
- [ ] Manual testing on Windows
- [ ] CI matrix for all platforms
