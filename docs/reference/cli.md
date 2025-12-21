# K-LEAN CLI Enhancement Implementation Report

## Overview

This document summarizes the implementation of enhanced CLI features for K-LEAN, focusing on service management, health checking, and developer debugging capabilities.

**Date:** 2025-12-15
**Version:** 1.0.0
**Commit:** c3fec65

---

## Features Implemented

### 1. Enhanced Doctor Command (`k-lean doctor`)

**Purpose:** Diagnose and optionally fix K-LEAN installation issues

**Options:**
- `--auto-fix` / `-f`: Automatically start stopped services

**Behavior:**
- Checks Claude directory existence
- Validates key scripts (quick-review.sh, deep-review.sh, droid-execute.sh)
- Verifies lib/common.sh presence
- Checks LiteLLM config.yaml
- Validates Knowledge DB venv
- Detects broken symlinks
- **NEW:** Checks and optionally auto-starts LiteLLM proxy
- **NEW:** Checks and optionally auto-starts Knowledge server

**Example Output:**
```
╭────────────────────────────────────────────────────╮
│ K-LEAN Companion v1.0.0                            │
│ Multi-Model Code Review & Knowledge Capture System │
╰────────────────────────────────────────────────────╯

Running diagnostics...

Service Status:
  ✓ LiteLLM Proxy: RUNNING (6 models)
  ✓ Knowledge Server: RUNNING

No issues found!
```

---

### 2. Service Start Command (`k-lean start`)

**Purpose:** Start K-LEAN services (LiteLLM proxy and Knowledge server)

**Options:**
- `--service` / `-s`: Service to start (`all`, `litellm`, `knowledge`)
- `--port` / `-p`: LiteLLM proxy port (default: 4000)

**Behavior:**
- Checks if services are already running
- Starts services in background
- Logs events to debug log
- Reports success/failure

**Example:**
```bash
k-lean start                      # Start all services
k-lean start -s litellm -p 5000   # Start LiteLLM on port 5000
k-lean start -s knowledge         # Start only Knowledge server
```

---

### 3. Service Stop Command (`k-lean stop`)

**Purpose:** Stop K-LEAN services

**Options:**
- `--service` / `-s`: Service to stop (`all`, `litellm`, `knowledge`)

**Behavior:**
- Stops services cleanly using PID files
- Falls back to pkill if PID not found
- Logs events to debug log

---

### 4. Debug Dashboard (`k-lean debug`)

**Purpose:** Real-time monitoring dashboard showing K-LEAN activity and service status

**Options:**
- `--follow` / `-f`: Follow log output in real-time (live updates)
- `--filter` / `-F`: Filter by component (`all`, `litellm`, `knowledge`, `droid`, `cli`)
- `--lines` / `-n`: Number of lines to show (default: 20)

**Dashboard Displays:**
- Service status (LiteLLM, Knowledge)
- Available models
- Recent activity from debug log
- Full paths (Claude Dir, K-LEAN Dir, Logs, Config)

**Example Output:**
```
╭─────────────────────────── K-LEAN Debug Dashboard ───────────────────────────╮
│ Services: ✓ LiteLLM (6 models) ✓ Knowledge                                   │
│ Models: qwen3-coder, deepseek-v3-thinking, glm-4.6-thinking, minimax-m2,     │
│ kimi-k2-thinking, hermes-4-70b                                               │
│ Recent Activity:                                                             │
│   2025-12-15 17:57:51 [CLI       ] test_model                                │
│ Paths:                                                                       │
│   Claude Dir: ~/.claude                                                      │
│   K-LEAN Dir: ~/.klean                                                       │
│   Logs: ~/.klean/logs                                                        │
│   Config: ~/.config/litellm                                                  │
╰────────────────────────────────── 17:57:42 ──────────────────────────────────╯
```

---

### 5. Models Command (`k-lean models`)

**Purpose:** List available models from LiteLLM proxy with health status

**Behavior:**
- Discovers models from LiteLLM /models endpoint
- Checks health of each model via /chat/completions
- Displays status (OK, FAIL, TIMEOUT, UNKNOWN)

**Example Output:**
```
        Available Models
┏━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Model ID             ┃ Status ┃
┡━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ qwen3-coder          │ OK     │
│ deepseek-v3-thinking │ OK     │
│ glm-4.6-thinking     │ FAIL   │
│ minimax-m2           │ FAIL   │
│ kimi-k2-thinking     │ FAIL   │
│ hermes-4-70b         │ FAIL   │
└──────────────────────┴────────┘

Total: 6 models available
```

---

### 6. Test Model Command (`k-lean test-model`)

**Purpose:** Test a model with a quick prompt

**Usage:**
```bash
k-lean test-model                          # List available models
k-lean test-model qwen3-coder              # Test with default prompt
k-lean test-model qwen3-coder "Say hello"  # Test with custom prompt
```

**Example Output:**
```
Testing model: qwen3-coder
Prompt: Say hello in 3 words

Response: Hello there!
Latency: 0.62s
```

---

## Debug Infrastructure

### Directory Structure
```
~/.klean/
├── logs/
│   ├── debug.log      # Unified debug log (JSON Lines)
│   └── litellm.log    # LiteLLM proxy output
└── pids/
    ├── litellm.pid    # LiteLLM process ID
    └── knowledge.pid  # Knowledge server PID
```

### Debug Log Format (JSON Lines)
```json
{"ts": "2025-12-15T17:57:51.870537", "component": "cli", "event": "test_model", "model": "qwen3-coder", "latency_ms": 617}
{"ts": "2025-12-15T17:58:00.123456", "component": "cli", "event": "service_start", "service": "litellm", "port": 4000}
{"ts": "2025-12-15T17:58:05.654321", "component": "droid", "event": "execute", "droid": "security-auditor"}
```

### Components Logged
- `cli`: CLI operations (test_model, service_start, service_stop)
- `litellm`: LiteLLM proxy operations (planned)
- `knowledge`: Knowledge DB operations (planned)
- `droid`: Droid execution (planned)

---

## Technical Implementation

### New Functions Added to cli.py

1. **ensure_klean_dirs()** - Creates ~/.klean directory structure
2. **get_litellm_pid_file()** / **get_knowledge_pid_file()** - PID file paths
3. **check_litellm_detailed()** - Detailed LiteLLM status with model list
4. **start_litellm()** - Start LiteLLM proxy in background
5. **stop_litellm()** - Stop LiteLLM proxy
6. **stop_knowledge_server()** - Stop Knowledge server
7. **log_debug_event()** - Write to unified debug log
8. **read_debug_log()** - Read recent debug entries
9. **discover_models()** - Get model list from LiteLLM
10. **get_model_health()** - Check health of each model

### Dependencies
- `rich` - For beautiful console output (Panel, Table, Live, Text)
- `click` - For CLI framework
- Standard library: json, signal, urllib.request

---

## Testing Results

| Command | Status | Notes |
|---------|--------|-------|
| `k-lean --version` | ✅ PASS | Returns 1.0.0 |
| `k-lean --help` | ✅ PASS | Shows all commands |
| `k-lean status` | ✅ PASS | Full component table |
| `k-lean doctor` | ✅ PASS | Shows service status |
| `k-lean doctor --auto-fix` | ✅ PASS | Auto-starts services |
| `k-lean start` | ✅ PASS | Starts both services |
| `k-lean stop` | ✅ PASS | Stops services |
| `k-lean debug` | ✅ PASS | Shows dashboard |
| `k-lean debug -f` | ✅ PASS | Live updates (Ctrl+C to exit) |
| `k-lean models` | ✅ PASS | Lists 6 models with health |
| `k-lean test-model qwen3-coder` | ✅ PASS | Response in 0.62s |

---

## Research Insights (from Tavily)

### Claude Code Monitoring Best Practices

1. **OpenTelemetry Integration**
   - Claude Code now supports OTEL for metrics export
   - Can send to Datadog, Grafana, SigNoz
   - Metrics: session.count, code_edit_tool.decision, cost.usage

2. **Local CLI Tools**
   - `ccusage` - Fast usage reports from .jsonl logs
   - `Claude-Code-Usage-Monitor` - Interactive terminal dashboard

3. **Key Metrics to Track**
   - Token usage per session
   - Model latency
   - Cost per operation
   - Tool usage patterns

4. **LLM Observability Patterns**
   - Trace trees for multi-step workflows
   - Span-based tracking
   - Correlation IDs for request chains
   - Timeline views for performance analysis

### Recommendations for Future Enhancement

1. **Add OTEL Export** - Export K-LEAN metrics to OpenTelemetry
2. **Token Tracking** - Track tokens used per review/droid operation
3. **Cost Analysis** - Estimate costs based on NanoGPT pricing
4. **Trace Visualization** - Add trace view for multi-model operations

---

## Files Modified

1. **review-system-backup/src/klean/__init__.py**
   - Added: KLEAN_DIR, LOGS_DIR, PIDS_DIR paths

2. **review-system-backup/src/klean/cli.py**
   - Added: 584 lines of new functionality
   - New commands: start, stop, debug, models, test-model
   - Enhanced: doctor command with auto-fix
   - New infrastructure: debug logging, PID management

---

## Quick Reference

```bash
# Service Management
k-lean start                    # Start all services
k-lean stop                     # Stop all services
k-lean doctor -f                # Diagnose and auto-fix

# Debugging
k-lean debug                    # Show dashboard
k-lean debug -f                 # Live monitoring
k-lean debug -F litellm         # Filter by component

# Models
k-lean models                   # List with health status
k-lean test-model qwen3-coder   # Quick test

# Status
k-lean status                   # Full component status
k-lean doctor                   # Diagnostic check
```

---

## Conclusion

The K-LEAN CLI has been significantly enhanced with:
- **Service Management**: Auto-start/stop for LiteLLM and Knowledge server
- **Debug Dashboard**: Real-time monitoring with filtering
- **Model Management**: Discovery, health checks, and testing
- **Unified Logging**: JSON Lines format for programmatic analysis

These features make K-LEAN production-ready and provide developers with full visibility into the system's operation.

---

## 80/20 Improvements (Phase 2)

Based on Claude Code skills and rules best practices research, the following high-impact improvements were implemented:

### 1. Unified Debug Logging for Shell Scripts

Added `log_debug()` function to `lib/common.sh` for consistent logging across all scripts:

```bash
# Usage
log_debug "component" "event" "key1=val1" "key2=val2"

# Example
log_debug "droid" "execute_start" "model=qwen3-coder" "droid=security-auditor"
```

**Scripts Updated:**
- `droid-execute.sh` - Logs execute_start, execute_complete
- `quick-review.sh` - Logs quick_start, quick_complete
- `deep-review.sh` - Logs deep_start, deep_complete
- `parallel-droid-review.sh` - Logs parallel_start, parallel_complete

### 2. Optimized CLAUDE.md

Reduced from 193 lines to 87 lines (55% reduction) while adding quick command shortcuts:

| Shortcut | Action |
|----------|--------|
| `healthcheck` | Check all 6 LiteLLM models |
| `qreview <model> <focus>` | Quick single-model review |
| `dreview <model> <focus>` | Deep review with tools |
| `droid <model> <type> <task>` | Execute Factory droid |
| `GoodJob <url>` | Capture web knowledge |
| `SaveThis <lesson>` | Save a lesson learned |
| `FindKnowledge <query>` | Search knowledge DB |

### 3. Best Practices Applied

From Claude Code community research:
- **CLAUDE.md under 150 lines** - Keeps context focused
- **Quick shortcuts at top** - Fastest access to common operations
- **Tables for structured data** - Better scanning
- **Code blocks for commands** - Easy copy-paste

---

## Files Modified (Phase 2)

1. **lib/common.sh** - Added `log_debug()` function
2. **scripts/droid-execute.sh** - Added debug logging
3. **scripts/quick-review.sh** - Added debug logging
4. **scripts/deep-review.sh** - Added debug logging
5. **scripts/parallel-droid-review.sh** - Added debug logging
6. **~/.claude/CLAUDE.md** - Optimized (193→87 lines)
7. **CLAUDE.md** (project) - Synced with global
