# K-LEAN System Review Plan

Manual review checklist for understanding and improving each system component.

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

### 4. Droids System
**Files:** `droids/`
- [ ] `orchestrator.md` - Master coordinator (30KB - largest)
- [ ] `code-reviewer.md` - OWASP, SOLID, quality
- [ ] `security-auditor.md` - Vulnerabilities, auth, encryption
- [ ] `debugger.md` - Root cause analysis
- [ ] `arm-cortex-expert.md` - Embedded ARM specialty
- [ ] `c-pro.md` - C99/C11/POSIX
- [ ] `rust-expert.md` - Ownership, lifetimes
- [ ] `performance-engineer.md` - Profiling, optimization

**Review Goals:**
- Understand prompt engineering patterns
- Verify role boundaries don't overlap
- Check for outdated references or techniques

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
