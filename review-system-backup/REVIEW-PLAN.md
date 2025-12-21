# K-LEAN System Review Plan

Manual review checklist for understanding and improving each system component.

## Current Status

| Area | Status | Key Commits |
|------|--------|-------------|
| Knowledge DB | ✅ Done | V2 Schema |
| Skills System | ✅ Done | Implementation-specific descriptions |
| CLAUDE.md | ✅ Done | Pure plugin approach |
| Directory Structure | ✅ Done | Removed v3 references |
| Package & Install | ✅ Done | `k-lean sync`, component install |
| Hooks | ✅ Done | Error surfacing, PID verification |
| Path Management | ✅ Done | 7fd7abf - 78 paths → kb-root.sh |
| Core Scripts | ✅ Done | Review/KB scripts verified |
| **Droids System** | ✅ Complete | All 8 droids standardized, template created |
| **K-LEAN Core Engine** | 🔄 Pending | klean_core.py review |
| **LiteLLM Integration** | 🔄 Pending | Config/health verification |
| **Timeline/Statusline** | 🔄 Pending | Lower priority |
| **Configuration** | 🔄 Pending | Documentation needed |

**Progress: 9/13 areas complete (~69%)**

## Completed Reviews

### Knowledge DB System
- [x] `knowledge_db.py` - Core txtai embeddings and search
- [x] `knowledge-capture.py` - Entry capture with V2 schema
- [x] `kb_utils.py` - Shared utilities
- [x] `knowledge-query.sh` - Socket-based fast search
- [x] V2 Schema: `atomic_insight`, `key_concepts`, `quality`, `source`

### Skills System (/kln: Commands)
- [x] Updated descriptions to be implementation-specific (Anthropic best practices)
- [x] Added "When to Use" sections with positive/negative triggers
- [x] Removed version numbers (v3) from all commands
- [x] Synced to `commands/kln/` and `src/klean/data/commands/kln/`

### CLAUDE.md Configuration
- [x] Switched to "pure plugin" approach - K-LEAN never touches user's CLAUDE.md
- [x] Template in `config/CLAUDE.md` for reference only

### Directory Structure Cleanup
- [x] Removed v3 version references from all documentation
- [x] Consolidated commands to single canonical source: `commands/kln/`
- [x] Deleted redundant `commands-kln-v3/` and `commands-kln/`
- [x] Renamed `src/klean-v3/` → `src/klean-core/`
- [x] Updated symlinks to point to `commands/kln/`

### Package & Install System
- [x] Added `k-lean sync` CLI command (root dirs → src/klean/data/)
- [x] Cleaned 19 stale files from package (v2 commands, old hooks/scripts)
- [x] Moved `src/klean-core/` → `src/klean/data/core/` for proper packaging
- [x] Added `core` component to `k-lean install` command
- [x] Fixed `prepare-release.sh` path bug (commands-kln → commands/kln)
- [x] Created `DEVELOPMENT.md` with release workflow for AI agents

### Hooks System Improvements
- [x] Fixed InitKB bug (same message for success/failure)
- [x] Added PID verification for async review processes
- [x] Added config file warnings in session-start.sh
- [x] Added timeline write error detection in post-bash-handler.sh
- [x] Added web capture missing script warning

### Path Management System ✅ (Commit 7fd7abf)
**Eliminated 78 hardcoded paths across 28 files**

| Category | Count | Migrated To |
|----------|-------|-------------|
| Python interpreter | 23 | `$KB_PYTHON` |
| Scripts directory | 45 | `$KB_SCRIPTS_DIR` |
| Config paths | 5 | `$KB_CONFIG_DIR` |
| Other | 5 | Inline fallbacks |

**Key Changes:**
- [x] Enhanced `kb-root.sh` as single source of truth
- [x] Added validation functions: `require_kb_python()`, `require_kb_scripts()`
- [x] Added helper functions: `get_kb_script()`, `get_kb_py_script()`
- [x] Updated all 5 hooks with kb-root.sh sourcing + inline fallbacks
- [x] Updated all 7 review scripts (quick, consensus, deep, parallel, droid)
- [x] Updated dispatcher (async-dispatch.sh - 12 occurrences)
- [x] Updated Python scripts (kb_utils.py - environment variable support)
- [x] Updated utilities (post-commit-docs.sh, bashrc-additions.sh)

**Environment Variable Overrides:**
```bash
KLEAN_KB_PYTHON      # Custom Python path
KLEAN_SCRIPTS_DIR    # Custom scripts directory
KLEAN_SOCKET_DIR     # Custom socket directory (default: /tmp)
KLEAN_CONFIG_DIR     # Custom config directory
```

**Architecture:**
- Per-project socket isolation: `/tmp/kb-{md5_hash}.sock`
- Fallback chain: ENV → kb-root.sh detection → hardcoded defaults
- Documentation: `docs/ARCHITECTURE-ANALYSIS.md`, `docs/PATH-MANAGEMENT-PLAN.md`

---

## Pending Reviews

### Hooks System ✅
**Files:** `hooks/`
- [x] `session-start.sh` - LiteLLM + KB auto-start on session begin
- [x] `user-prompt-handler.sh` - Keyword detection (SaveThis, FindKnowledge, healthcheck)
- [x] `post-bash-handler.sh` - Post-commit docs, timeline capture
- [x] `post-web-handler.sh` - Auto-capture web content to KB

**Review Findings:**

| Hook | Trigger | Purpose |
|------|---------|---------|
| `session-start.sh` | SessionStart | Auto-start LiteLLM proxy + per-project KB server |
| `user-prompt-handler.sh` | UserPromptSubmit | 7 keywords: InitKB, SaveThis, SaveInfo, FindKnowledge, async reviews |
| `post-bash-handler.sh` | PostToolUse (Bash) | Git commit/push detection → timeline logging + fact extraction |
| `post-web-handler.sh` | PostToolUse (Web*) | Smart capture from WebFetch/WebSearch/Tavily |

**Comparison vs Best Practices (disler/claude-code-hooks-mastery, decider/claude-hooks):**

| Feature | K-LEAN | Best Practice | Gap |
|---------|--------|---------------|-----|
| PreToolUse (security) | ❌ | ✅ Block dangerous commands | **Add** |
| Stop hook (completion) | ❌ | ✅ Notifications/TTS | Nice-to-have |
| Exit code 2 blocking | ❌ | ✅ stderr to Claude | **Add** |
| JSON decision output | Partial | ✅ `{decision, reason}` | Improve |
| Web auto-capture | ✅ Unique | ❌ Not in community | K-LEAN advantage |
| KB integration | ✅ Unique | ❌ Simple logging | K-LEAN advantage |

**Recommended Improvements:**
1. Add `hooks/pre-tool-handler.sh` for security blocking (rm -rf, sudo, etc.)
2. Use exit code 2 for blocking operations
3. Consistent JSON output format: `{"decision": "block"|"approve", "reason": "..."}`

---

### 2. Scripts (Core) ✅
**Files:** `scripts/` - Priority scripts first

**Reviewed:**
- [x] `quick-review.sh` - LiteLLM API single-model review
- [x] `consensus-review.sh` - Multi-model parallel review
- [x] `deep-review.sh` - Claude SDK agent review
- [x] `droid-execute.sh` - Factory Droid orchestration
- [x] `async-dispatch.sh` - Background task runner

**Findings:**
| Script | Key Features Verified |
|--------|----------------------|
| `quick-review.sh` | Dynamic model discovery, health fallback, thinking model support |
| `consensus-review.sh` | Parallel curl for 5 models, proper temp cleanup |
| `deep-review.sh` | Claude headless read-only mode, comprehensive allow/deny lists |
| `droid-execute.sh` | 8 specialist droids, model name mapping, Factory CLI integration |
| `async-dispatch.sh` | Prompt blocking, background nohup, health pre-check |

**Common Patterns:**
- All use `session-helper.sh` for output directories
- All handle thinking models (`reasoning_content` fallback)
- Knowledge DB integration where relevant
- Consistent logging via `log_debug`

---

### 3. Scripts (Knowledge) ✅
**Files:** `scripts/knowledge-*.sh|py`

**Reviewed:**
- [x] `knowledge-init.sh` - Per-project KB initialization (auto-detect git root, gitignore setup)
- [x] `knowledge-query.sh` - Unix socket fast search with auto-start
- [x] `knowledge-server.py` - Per-project daemon with 1hr idle timeout
- [x] `knowledge-search.py` - CLI with 4 output formats (compact, detailed, inject, json)
- [x] `kb-doctor.sh` - 5-point diagnosis with --fix auto-repair
- [x] `kb-root.sh` - Unified project detection

**Findings:**
| Script | Key Features Verified |
|--------|----------------------|
| `knowledge-init.sh` | Git root detection, .gitignore auto-add |
| `knowledge-query.sh` | Socket auto-start, socat/nc/python fallback |
| `knowledge-server.py` | Per-project hash isolation, threading, idle cleanup |
| `knowledge-search.py` | `--format inject` for LLM prompts, min-score filter |
| `kb-doctor.sh` | JSONL validation, index rebuild, stale socket cleanup |

**Architecture:**
- Each project gets unique socket: `/tmp/kb-{md5_hash}.sock`
- 1 hour idle timeout conserves memory
- Auto-repair handles corrupted entries, missing index

---

### 4. Droids System ✅ COMPLETE
**Files:** `droids/`
- [x] `orchestrator.md` - Master coordinator (765 lines)
- [x] `code-reviewer.md` - OWASP, SOLID, quality (259 lines)
- [x] `security-auditor.md` - Vulnerabilities, auth, encryption (90 lines)
- [x] `debugger.md` - Root cause analysis (100 lines)
- [x] `arm-cortex-expert.md` - Embedded ARM specialty (320 lines)
- [x] `c-pro.md` - C99/C11/POSIX (276 lines) ✨ Expanded
- [x] `rust-expert.md` - Ownership, lifetimes (171 lines) ✨ Expanded
- [x] `performance-engineer.md` - Profiling, optimization (176 lines) ✨ Expanded
- [x] `TEMPLATE.md` - Research-based template guide (240 lines)

**All Issues Resolved (Commits: 1a3a222, 4e8839e):**

| Droid | Quality | Status |
|-------|---------|--------|
| orchestrator | ⭐⭐⭐⭐⭐ | ✅ Fixed hardcoded paths → `~/.factory/` |
| code-reviewer | ⭐⭐⭐⭐⭐ | ✅ Added orchestrator integration |
| security-auditor | ⭐⭐⭐⭐⭐ | ✅ Complete with orchestrator integration |
| debugger | ⭐⭐⭐⭐⭐ | ✅ Complete with orchestrator integration |
| arm-cortex-expert | ⭐⭐⭐⭐⭐ | ✅ Added tools + orchestrator integration |
| c-pro | ⭐⭐⭐⭐⭐ | ✅ Expanded 35→276 lines |
| rust-expert | ⭐⭐⭐⭐⭐ | ✅ Added framework + orchestrator integration |
| performance-engineer | ⭐⭐⭐⭐⭐ | ✅ Added framework + orchestrator integration |

**Standardized Toolset (Read-Only for Review Droids):**
```yaml
tools: ["Read", "LS", "Grep", "Glob", "Execute", "WebSearch", "FetchUrl", "TodoWrite", "Task", "GenerateDroid"]
```

**Consistent Structure Applied to All 8 Droids:**
- ✅ YAML frontmatter with explicit tools
- ✅ Immediate Actions section with bash commands
- ✅ Review Framework with tables
- ✅ Output Format (🔴 Critical, 🟡 Warnings, 🟢 Suggestions, 📊 Summary)
- ✅ Orchestrator Integration (Before/During/After sections)
- ✅ Example Orchestrated Output

**Template Guide:** `droids/TEMPLATE.md` (moved from docs/)

Based on Factory.ai docs, Anthropic's context engineering, and industry best practices:
- Factory.ai: "A droid is only as good as its plan" - subtask decomposition
- Anthropic: "Goldilocks zone" - not too brittle, not too vague
- AGENTS.md standard: 300-1000 token prompts are optimal

---

### 5. K-LEAN Core Engine
**Files:** `src/klean/data/core/` (moved from src/klean-core/)
- [ ] `klean_core.py` - 1190-line execution engine
  - [ ] `ModelResolver` class - Auto-discovery from LiteLLM
  - [ ] `ReviewEngine` class - Review execution
  - [ ] CLI entry points (`cli_quick`, `cli_multi`, etc.)
- [ ] `prompts/review.md` - Review template (GRADE/RISK/findings)
- [ ] `prompts/rethink.md` - Contrarian debugging prompt

**Review Goals:**
- Understand asyncio parallel execution
- Verify consensus algorithm
- Check model health caching

---

### 6. LiteLLM Integration
**Files:** Various
- [ ] `~/.config/litellm/config.yaml` - Model definitions
- [ ] `scripts/setup-litellm.sh` - Provider setup
- [ ] `scripts/health-check.sh` - Model health verification
- [ ] `scripts/get-models.sh` - Model discovery

**Review Goals:**
- Understand provider routing (NanoGPT, OpenRouter, Ollama)
- Verify rate limiting and retry logic
- Check cost tracking if any

---

### 7. Install & Update System ✅
**Files:** Root
- [x] `install.sh` - Full installation (~18KB) - Reviewed, works
- [x] `k-lean install` - CLI installer with component selection
- [x] `k-lean sync` - Package sync command (NEW)
- [ ] `update.sh` - Update existing installation (if needed)
- [ ] `test.sh` - Test suite

**Completed:**
- Dual install: `install.sh` for shell, `k-lean install` for pip/pipx
- `k-lean sync` keeps root dirs and package data in sync
- `DEVELOPMENT.md` documents release workflow

---

### 8. Timeline System
**Files:** `scripts/`
- [ ] `timeline-query.sh` - Query chronological log
- [ ] Timeline capture in `post-bash-handler.sh`

**Review Goals:**
- Understand event types captured
- Verify query filters (today, week, commits, reviews)

---

### 9. Statusline Integration
**Files:** `scripts/`
- [ ] `klean-statusline.py` - Claude Code statusline provider

**Review Goals:**
- Understand status indicators (kb:✓, kb:init, kb:off)
- Verify socket health checking
- Check performance (called frequently)

---

### 10. Configuration Files
**Files:** Various
- [ ] `settings.json` - Claude hooks configuration
- [ ] `config.yaml` - LiteLLM proxy config
- [ ] `pyproject.toml` - Python package metadata

**Review Goals:**
- Document all configuration options
- Identify sensible defaults
- Check for secrets/credentials handling

---

## Review Process

For each component:
1. **Read** - Understand what it does
2. **Trace** - Follow execution path
3. **Test** - Verify with edge cases
4. **Improve** - Apply learnings from research
5. **Document** - Update docs if needed

## Priority Order

1. **Hooks** - Entry points, most impactful
2. **Core Scripts** - Review/droid execution
3. **K-LEAN Engine** - Central logic
4. **Install System** - User first experience
5. **Droids** - Prompt quality
6. **Configuration** - Documentation
7. **Timeline/Statusline** - Lower priority utilities
