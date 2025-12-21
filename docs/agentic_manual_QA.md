# K-LEAN Agentic Manual QA

Manual QA checklist for AI agents reviewing K-LEAN system.

---

## Quick Verification

```bash
k-lean --version          # Should show version
k-lean status             # 36 scripts, 9 commands, 5 hooks, 8 droids
k-lean doctor             # All checks pass
k-lean test               # 27/27 tests pass
```

---

## 1. CLI Commands

| Test | Command | Expected |
|------|---------|----------|
| [ ] Version | `k-lean --version` | Version number |
| [ ] Status | `k-lean status` | Component counts |
| [ ] Doctor | `k-lean doctor` | No errors |
| [ ] Models | `k-lean models` | 6+ models listed |
| [ ] Health | `k-lean models --health` | Models responding |
| [ ] Test suite | `k-lean test` | All tests pass |

---

## 2. LiteLLM Proxy

| Test | Check | Expected |
|------|-------|----------|
| [ ] Proxy running | `curl http://localhost:4000/models` | JSON response |
| [ ] Models available | `~/.claude/scripts/get-models.sh` | Model list |
| [ ] Health check | `~/.claude/scripts/health-check.sh` | ✅ for each model |
| [ ] Config valid | `k-lean doctor` | No config errors |

---

## 3. Knowledge DB

| Test | Check | Expected |
|------|-------|----------|
| [ ] Server running | `ls /tmp/kb-*.sock` | Socket exists |
| [ ] Query works | `~/.claude/scripts/knowledge-query.sh "test"` | Results or empty |
| [ ] Save works | Type `SaveThis test entry` in Claude | Confirmation |
| [ ] Search works | Type `FindKnowledge test` in Claude | Results |
| [ ] Doctor | `~/.claude/scripts/kb-doctor.sh` | No errors |

---

## 4. Review System

### Quick Review
| Test | Command | Expected |
|------|---------|----------|
| [ ] Single model | `/kln:quick security` | Grade + findings |
| [ ] Output saved | `ls .claude/kln/quickReview/` | .md file |

### Consensus Review
| Test | Command | Expected |
|------|---------|----------|
| [ ] Multi-model | `/kln:multi architecture` | Consensus findings |
| [ ] 5 models queried | Check output | Multiple perspectives |

### Deep Review
| Test | Command | Expected |
|------|---------|----------|
| [ ] With tools | `/kln:deep "full audit"` | Detailed investigation |
| [ ] Read-only mode | Check output | No modifications made |
| [ ] Output saved | `ls .claude/kln/deepInspect/` | .md file |

---

## 5. Hooks System

| Hook | Trigger | Test |
|------|---------|------|
| [ ] session-start | New session | LiteLLM auto-starts |
| [ ] user-prompt | `SaveThis lesson` | KB capture works |
| [ ] user-prompt | `FindKnowledge topic` | Search works |
| [ ] user-prompt | `healthcheck` | Model health shown |
| [ ] post-bash | `git commit` | Timeline updated |

---

## 6. Droids System

| Droid | Test | Expected |
|-------|------|----------|
| [ ] code-reviewer | `/kln:droid code-reviewer` | Quality findings |
| [ ] security-auditor | `/kln:droid security-auditor` | Security findings |
| [ ] Files exist | `ls ~/.factory/droids/` | 8 .md files |

---

## 7. Scripts Verification

```bash
# Count scripts
ls ~/.claude/scripts/*.sh | wc -l    # Should be 36+
ls ~/.claude/scripts/*.py | wc -l    # Should be 9+

# Key scripts executable
[ -x ~/.claude/scripts/quick-review.sh ] && echo "✅"
[ -x ~/.claude/scripts/deep-review.sh ] && echo "✅"
[ -x ~/.claude/scripts/knowledge-query.sh ] && echo "✅"
```

| Category | Scripts | Check |
|----------|---------|-------|
| [ ] Review | quick-review.sh, consensus-review.sh, deep-review.sh | Executable |
| [ ] Knowledge | knowledge-query.sh, knowledge-server.py | Executable |
| [ ] Health | health-check.sh, get-models.sh | Executable |

---

## 8. Configuration

| File | Check |
|------|-------|
| [ ] `~/.config/litellm/config.yaml` | Models defined |
| [ ] `~/.config/litellm/.env` | API key set (chmod 600) |
| [ ] `~/.claude/settings.json` | Valid JSON |

---

## 9. Output Locations

| Type | Path | Check |
|------|------|-------|
| [ ] Reviews | `.claude/kln/` | Directory exists |
| [ ] Knowledge | `.knowledge-db/` | Directory exists |
| [ ] Timeline | `.knowledge-db/timeline.txt` | File exists |
| [ ] Logs | `~/.klean/logs/` | Directory exists |

---

## 10. Security Checks

| Check | Command | Expected |
|-------|---------|----------|
| [ ] No secrets in src/ | `grep -r "sk-" src/` | No matches |
| [ ] No hardcoded paths | `grep -r "/home/" src/klean/` | No matches |
| [ ] .env protected | `ls -la ~/.config/litellm/.env` | 600 permissions |

---

## Troubleshooting

If tests fail:

```bash
# Full diagnostics
k-lean doctor -f          # Auto-fix common issues

# Check logs
cat ~/.klean/logs/litellm.log
cat ~/.klean/logs/debug.jsonl

# Restart services
k-lean stop && k-lean start -s all
```

---

## QA Sign-off

| Area | Status | Notes |
|------|--------|-------|
| CLI Commands | [ ] Pass | |
| LiteLLM Proxy | [ ] Pass | |
| Knowledge DB | [ ] Pass | |
| Review System | [ ] Pass | |
| Hooks | [ ] Pass | |
| Droids | [ ] Pass | |
| Scripts | [ ] Pass | |
| Config | [ ] Pass | |
| Output | [ ] Pass | |
| Security | [ ] Pass | |

**Overall:** [ ] PASSED / [ ] FAILED

**Tester:** _______________
**Date:** _______________
