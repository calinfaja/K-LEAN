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

---

## Pending Reviews

### 1. Hooks System
**Files:** `hooks/`
- [ ] `session-start.sh` - LiteLLM + KB auto-start on session begin
- [ ] `user-prompt-handler.sh` - Keyword detection (SaveThis, FindKnowledge, healthcheck)
- [ ] `post-bash-handler.sh` - Post-commit docs, timeline capture
- [ ] `post-web-handler.sh` - Auto-capture web content to KB

**Review Goals:**
- Understand trigger conditions and execution flow
- Verify error handling and edge cases
- Check for redundant or conflicting handlers

---

### 2. Scripts (Core)
**Files:** `scripts/` - Priority scripts first

**Review Queue:**
- [ ] `quick-review.sh` - LiteLLM API single-model review
- [ ] `consensus-review.sh` - Multi-model parallel review
- [ ] `deep-review.sh` - Claude SDK agent review
- [ ] `droid-execute.sh` - Factory Droid orchestration
- [ ] `async-dispatch.sh` - Background task runner

**Review Goals:**
- Understand LiteLLM API integration patterns
- Verify model routing and error handling
- Check for hardcoded values that should be configurable

---

### 3. Scripts (Knowledge)
**Files:** `scripts/knowledge-*.sh|py`
- [ ] `knowledge-init.sh` - Per-project KB initialization
- [ ] `knowledge-extract.sh` - Content extraction from URLs
- [ ] `knowledge-hybrid-search.py` - Combined semantic + keyword search
- [ ] `knowledge-context-injector.py` - Context injection for reviews
- [ ] `kb-doctor.sh` - Diagnosis and auto-repair
- [ ] `kb-root.sh` - Project root detection

**Review Goals:**
- Understand search strategies and ranking
- Verify cross-project isolation
- Check socket server lifecycle management

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
**Files:** `src/klean-v3/`
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

### 7. Install & Update System
**Files:** Root
- [ ] `install.sh` - Full installation (~18KB)
- [ ] `update.sh` - Update existing installation
- [ ] `test.sh` - Test suite

**Review Goals:**
- Understand installation modes (--full, --minimal)
- Verify idempotency (re-run safety)
- Check uninstall capability

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
