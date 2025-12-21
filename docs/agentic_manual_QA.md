# K-LEAN Agentic Manual QA

Comprehensive QA checklist for AI agents testing each K-LEAN subsystem independently.

---

## Quick Smoke Test

```bash
k-lean --version && k-lean status && k-lean doctor && k-lean test
```

---

## 1. Knowledge DB System

### Files to Verify
- [ ] `knowledge_db.py` - Core txtai embeddings and search
- [ ] `knowledge-capture.py` - Entry capture with V2 schema
- [ ] `kb_utils.py` - Shared utilities
- [ ] `knowledge-query.sh` - Socket-based fast search
- [ ] `knowledge-server.py` - Per-project daemon

### V2 Schema Check
```bash
# Check schema fields in knowledge-capture.py
grep -A10 "entry = {" ~/.claude/scripts/knowledge-capture.py
```
Expected fields: `title`, `summary`, `type`, `key_concepts`, `quality`, `source`, `found_date`

### Functional Tests
| Test | Command | Expected |
|------|---------|----------|
| [ ] Server running | `ls /tmp/kb-*.sock` | Socket file exists |
| [ ] Query works | `~/.claude/scripts/knowledge-query.sh "test"` | JSON results |
| [ ] Save entry | `SaveThis test lesson` (in Claude) | Confirmation message |
| [ ] Search works | `FindKnowledge test` (in Claude) | Results displayed |
| [ ] Doctor check | `~/.claude/scripts/kb-doctor.sh` | No errors |
| [ ] Per-project isolation | Check socket hash matches project | Unique per project |

### Architecture Verification
- [ ] Socket path uses MD5 hash: `/tmp/kb-{md5_hash}.sock`
- [ ] 1 hour idle timeout configured
- [ ] Auto-repair handles corrupted JSONL

---

## 2. Hooks System

### Files to Verify
| Hook | Trigger | File |
|------|---------|------|
| [ ] `session-start.sh` | SessionStart | Auto-start LiteLLM + KB |
| [ ] `user-prompt-handler.sh` | UserPromptSubmit | 6 keywords |
| [ ] `post-bash-handler.sh` | PostToolUse (Bash) | Git events → timeline |
| [ ] `post-web-handler.sh` | PostToolUse (Web*) | Web content → KB |
| [ ] `async-review.sh` | Background | Async reviews |

### Keyword Tests
| Keyword | Test | Expected |
|---------|------|----------|
| [ ] `SaveThis` | `SaveThis lesson` | Direct save to KB |
| [ ] `SaveInfo` | `SaveInfo insight` | LLM-evaluated save |
| [ ] `FindKnowledge` | `FindKnowledge topic` | Semantic search |
| [ ] `asyncReview` | `asyncReview security` | Background quick review |
| [ ] `asyncDeepReview` | `asyncDeepReview audit` | Background deep review |
| [ ] `asyncConsensus` | `asyncConsensus check` | Background consensus |

### Hook Integration Tests
- [ ] Session start triggers LiteLLM auto-start
- [ ] Git commit writes to timeline
- [ ] Git push writes to timeline
- [ ] Web fetch triggers smart capture (if enabled)

---

## 3. Scripts (Core Review)

### Files to Verify
| Script | Purpose | Check |
|--------|---------|-------|
| [ ] `quick-review.sh` | Single model API review | Executable |
| [ ] `consensus-review.sh` | 5-model parallel review | Executable |
| [ ] `deep-review.sh` | Claude SDK agent review | Executable |
| [ ] `droid-execute.sh` | Factory Droid execution | Executable |
| [ ] `async-dispatch.sh` | Background task runner | Executable |

### Feature Verification
| Script | Feature | Test |
|--------|---------|------|
| [ ] quick-review.sh | Dynamic model discovery | Uses get-models.sh |
| [ ] quick-review.sh | Health fallback | Falls back if model unhealthy |
| [ ] quick-review.sh | Thinking model support | Checks `reasoning_content` |
| [ ] consensus-review.sh | Parallel curl | Queries 5 models |
| [ ] consensus-review.sh | Temp cleanup | No leftover temp files |
| [ ] deep-review.sh | Read-only mode | Uses allow/deny permissions |
| [ ] deep-review.sh | Audit config | Creates `/tmp/claude-audit-$$` |
| [ ] droid-execute.sh | Reads .md files | Uses `~/.factory/droids/` |
| [ ] async-dispatch.sh | Background nohup | Runs without blocking |

### Common Patterns Check
- [ ] All use `session-helper.sh` for output directories
- [ ] All handle thinking models (`reasoning_content` fallback)
- [ ] All use `kb-root.sh` for paths

---

## 4. Scripts (Knowledge)

### Files to Verify
| Script | Key Features |
|--------|--------------|
| [ ] `knowledge-init.sh` | Git root detection, .gitignore auto-add |
| [ ] `knowledge-query.sh` | Socket auto-start, fallback (socat/nc/python) |
| [ ] `knowledge-server.py` | Per-project hash, threading, idle cleanup |
| [ ] `knowledge-search.py` | 4 formats: compact, detailed, inject, json |
| [ ] `kb-doctor.sh` | 5-point diagnosis, --fix auto-repair |
| [ ] `kb-root.sh` | Unified project detection |

### Functional Tests
| Test | Command | Expected |
|------|---------|----------|
| [ ] Init KB | `~/.claude/scripts/knowledge-init.sh` | Creates .knowledge-db/ |
| [ ] Fast query | `~/.claude/scripts/knowledge-query.sh "test"` | ~30ms response |
| [ ] Search formats | `--format inject` | LLM-ready output |
| [ ] Doctor fix | `~/.claude/scripts/kb-doctor.sh --fix` | Auto-repairs issues |

---

## 5. Droids System

### Files to Verify (8 droids)
| Droid | Lines | Check |
|-------|-------|-------|
| [ ] `orchestrator.md` | ~765 | Master coordinator |
| [ ] `code-reviewer.md` | ~258 | OWASP, SOLID |
| [ ] `security-auditor.md` | ~89 | Vulnerabilities |
| [ ] `debugger.md` | ~99 | Root cause analysis |
| [ ] `arm-cortex-expert.md` | ~320 | Embedded ARM |
| [ ] `c-pro.md` | ~275 | C99/C11/POSIX |
| [ ] `rust-expert.md` | ~170 | Ownership, lifetimes |
| [ ] `performance-engineer.md` | ~175 | Profiling |

### Structure Verification (each droid)
- [ ] YAML frontmatter with tools list
- [ ] Identity section
- [ ] Immediate Actions with bash commands
- [ ] Review Framework table
- [ ] Output Format (🔴 🟡 🟢 📊)
- [ ] Orchestrator Integration

### Functional Test
```bash
# Verify droids exist
ls ~/.factory/droids/*.md | wc -l  # Should be 8

# Test droid execution
/kln:droid code-reviewer
```

---

## 6. K-LEAN Core Engine

### File: `src/klean/data/core/klean_core.py` (~1190 lines)

### Classes to Verify
| Class | Lines | Purpose |
|-------|-------|---------|
| [ ] `ModelResolver` | 52-218 | Dynamic discovery, latency caching |
| [ ] `ReviewEngine` | 224-610 | Quick + multi-model reviews |

### Features Check
- [ ] Async parallel execution via `asyncio.gather`
- [ ] Thinking model support (`reasoning_content` fallback)
- [ ] Robust JSON parsing (direct → markdown → raw braces)
- [ ] Latency caching (disk-based, 24h expiry)
- [ ] Consensus algorithm (groups by location similarity)
- [ ] Model diversity (limits thinking models to 50%)

### Prompts Verification
| Prompt | Lines | Check |
|--------|-------|-------|
| [ ] `prompts/review.md` | ~86 | 7-area checklist |
| [ ] `prompts/rethink.md` | ~92 | 4 contrarian techniques |
| [ ] `prompts/format-json.md` | ~28 | JSON schema |
| [ ] `prompts/format-text.md` | ~27 | Human-readable |
| [ ] `prompts/droid-base.md` | ~54 | Droid template |

---

## 7. LiteLLM Integration

### Files to Verify
| File | Purpose |
|------|---------|
| [ ] `~/.config/litellm/config.yaml` | Model definitions |
| [ ] `~/.config/litellm/.env` | API keys (chmod 600) |
| [ ] `setup-litellm.sh` | Interactive wizard |
| [ ] `start-litellm.sh` | Validated startup |
| [ ] `health-check.sh` | Full health check |
| [ ] `health-check-model.sh` | Single model health |
| [ ] `get-models.sh` | Dynamic discovery |
| [ ] `get-healthy-models.sh` | Filter healthy models |
| [ ] `validate-model.sh` | Model existence check |

### Functional Tests
| Test | Command | Expected |
|------|---------|----------|
| [ ] Proxy running | `curl http://localhost:4000/models` | JSON response |
| [ ] List models | `~/.claude/scripts/get-models.sh` | 6+ models |
| [ ] Health check | `~/.claude/scripts/health-check.sh` | ✅ for models |
| [ ] Single health | `~/.claude/scripts/health-check-model.sh qwen3-coder` | OK |
| [ ] Validate model | `~/.claude/scripts/validate-model.sh qwen3-coder` | Valid |

### Config Validation
- [ ] No quoted `os.environ/` in config.yaml
- [ ] `.env` has NANOGPT_API_KEY
- [ ] `.env` has NANOGPT_API_BASE
- [ ] `.env` permissions are 600

---

## 8. Path Management System

### Central File: `kb-root.sh`

### Environment Variables
| Variable | Default | Check |
|----------|---------|-------|
| [ ] `KB_PYTHON` | `~/.venvs/knowledge-db/bin/python` | Executable |
| [ ] `KB_SCRIPTS_DIR` | `~/.claude/scripts` | Directory exists |
| [ ] `KB_SOCKET_DIR` | `/tmp` | Writable |
| [ ] `KB_CONFIG_DIR` | `~/.config/litellm` | Directory exists |

### Validation Functions Test
```bash
source ~/.claude/scripts/kb-root.sh
require_kb_python && echo "✅ Python OK"
require_kb_scripts && echo "✅ Scripts OK"
```

### No Hardcoded Paths Check
```bash
# Should return no matches in src/
grep -r "/home/" src/klean/ | grep -v ".pyc"
```

---

## 9. CLI Commands (12 total)

### Command Tests
| Command | Test | Expected |
|---------|------|----------|
| [ ] `k-lean --version` | Run | Version number |
| [ ] `k-lean status` | Run | Component table |
| [ ] `k-lean doctor` | Run | All checks pass |
| [ ] `k-lean doctor -f` | Run | Auto-fixes issues |
| [ ] `k-lean models` | Run | Model list |
| [ ] `k-lean models --health` | Run | Health status each model |
| [ ] `k-lean start` | Run | LiteLLM starts |
| [ ] `k-lean start -s all` | Run | LiteLLM + KB start |
| [ ] `k-lean stop` | Run | Services stop |
| [ ] `k-lean install` | Run (dev) | Components installed |
| [ ] `k-lean uninstall` | Run (dev) | Components removed |
| [ ] `k-lean test` | Run | 27/27 tests pass |

### Status Output Verification
```
Scripts: OK (36+)
KLN Commands: OK (9)
Hooks: OK (5)
Factory Droids: OK (8)
Knowledge DB: INSTALLED/RUNNING
LiteLLM Proxy: RUNNING (12 models)
```

---

## 10. Timeline System

### File: `timeline-query.sh`

### Command Tests
| Command | Test |
|---------|------|
| [ ] `timeline-query.sh last` | Last 20 events |
| [ ] `timeline-query.sh today` | Today's events |
| [ ] `timeline-query.sh week` | Last 7 days |
| [ ] `timeline-query.sh commits` | All git commits |
| [ ] `timeline-query.sh reviews` | All reviews |
| [ ] `timeline-query.sh stats` | Statistics |

### Event Capture Test
- [ ] Git commit creates timeline entry
- [ ] Git push creates timeline entry
- [ ] Review creates timeline entry

### Storage Check
```bash
cat .knowledge-db/timeline.txt | tail -5
```

---

## 11. Statusline Integration

### File: `klean-statusline.py` (~266 lines)

### Fields Verification
| Field | Source | Check |
|-------|--------|-------|
| [ ] Model | Claude API | Shows [opus]/[sonnet]/[haiku] |
| [ ] Project | Workspace | Project name |
| [ ] Git | subprocess | Branch + dirty state |
| [ ] LLM | HTTP | Model count |
| [ ] KB | Socket | ✓ or status |

### Performance Check
- [ ] LiteLLM timeout: 0.5s
- [ ] KB socket timeout: 0.3s

---

## 12. Configuration Files

### Files to Verify
| File | Location | Check |
|------|----------|-------|
| [ ] `settings.json` | `~/.claude/` | Valid JSON |
| [ ] `config.yaml` | `~/.config/litellm/` | Models defined |
| [ ] `.env` | `~/.config/litellm/` | Keys set, 600 perms |
| [ ] `pyproject.toml` | repo root | Version correct |

---

## 13. Security Checks

| Check | Command | Expected |
|-------|---------|----------|
| [ ] No secrets in src/ | `grep -r "sk-" src/` | No matches |
| [ ] No hardcoded paths | `grep -r "/home/" src/klean/` | No matches |
| [ ] .env protected | `stat ~/.config/litellm/.env` | 600 perms |
| [ ] Doctor detects keys | `k-lean doctor` | Would warn if exposed |

---

## 14. Review System End-to-End

### Quick Review
```bash
/kln:quick security
```
- [ ] Returns grade (A-F)
- [ ] Returns risk level
- [ ] Returns findings
- [ ] Saves to `.claude/kln/quickReview/`

### Consensus Review
```bash
/kln:multi architecture
```
- [ ] Queries 5 models
- [ ] Shows consensus (HIGH/MEDIUM/LOW)
- [ ] Groups similar findings

### Deep Review
```bash
/kln:deep "full audit"
```
- [ ] Uses Claude headless
- [ ] Read-only mode (no writes)
- [ ] Full codebase access
- [ ] Saves to `.claude/kln/deepInspect/`

### Rethink
```bash
/kln:rethink
```
- [ ] Uses 4 contrarian techniques
- [ ] Challenges assumptions

---

## 15. Output Locations

| Type | Path | Check |
|------|------|-------|
| [ ] Reviews | `.claude/kln/` | Directory exists |
| [ ] Knowledge | `.knowledge-db/` | Directory exists |
| [ ] Timeline | `.knowledge-db/timeline.txt` | File exists |
| [ ] Logs | `~/.klean/logs/` | Directory exists |
| [ ] Index | `.knowledge-db/index/` | Directory exists |

---

## QA Sign-off

| Area | Status | Notes |
|------|--------|-------|
| Knowledge DB | [ ] Pass | |
| Hooks System | [ ] Pass | |
| Core Scripts | [ ] Pass | |
| Knowledge Scripts | [ ] Pass | |
| Droids System | [ ] Pass | |
| Core Engine | [ ] Pass | |
| LiteLLM Integration | [ ] Pass | |
| Path Management | [ ] Pass | |
| CLI Commands | [ ] Pass | |
| Timeline | [ ] Pass | |
| Statusline | [ ] Pass | |
| Configuration | [ ] Pass | |
| Security | [ ] Pass | |
| Review E2E | [ ] Pass | |
| Output Locations | [ ] Pass | |

**Overall:** [ ] PASSED / [ ] FAILED

**Tester:** _______________
**Date:** _______________
