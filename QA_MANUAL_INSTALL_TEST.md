# K-LEAN v1.0.0b1 - Manual Installation QA Test

**Tester**: Calin Faja
**Date**: 2026-01-02
**Package**: kln-ai v1.0.0b1
**Source**: PyPI (fresh install)
**OS**: Ubuntu Linux (6.14.0-37-generic)
**Python**: 3.12.3

---

## Pre-Installation State

### Current Installation
- [x] kln-ai installed via pipx: YES (1.0.0b1)
- [ ] LiteLLM running: checking...

### Backup Verification
- [x] API keys backed up to `/tmp/kln-backup/.env`
- [x] Config backed up to `/tmp/kln-backup/config.yaml`

---

## Phase 1: Clean Uninstall

### Step 1.1: Stop LiteLLM
```bash
pkill -f litellm || true
```
- [x] Command executed
- [x] Result: LiteLLM stopped (required SIGKILL)

### Step 1.2: Uninstall kln-ai
```bash
pipx uninstall kln-ai
```
- [x] Command executed
- [x] Result: uninstalled kln-ai

### Step 1.3: Remove K-LEAN directories
```bash
rm -rf ~/.klean ~/.claude/scripts ~/.claude/commands/kln ~/.claude/hooks ~/.config/litellm
```
- [x] Command executed
- [x] Result: Directories removed

### Step 1.4: Verify Clean State
```bash
ls ~/.klean 2>/dev/null && echo "EXISTS" || echo "REMOVED"
ls ~/.config/litellm 2>/dev/null && echo "EXISTS" || echo "REMOVED"
which kln 2>/dev/null && echo "EXISTS" || echo "REMOVED"
```
- [x] ~/.klean: REMOVED
- [x] ~/.config/litellm: REMOVED
- [x] kln command: REMOVED

**Phase 1 Complete: System is clean**

---

## Phase 2: Fresh Install (Following README)

### Step 2.1: Install from PyPI
```bash
pipx install kln-ai
```
- [x] Command executed
- [x] Install time: ~15 seconds
- [x] Output includes `kln` and `kln-smol` commands: YES
- [x] Version: 1.0.0b1

### Step 2.2: Verify Installation
```bash
kln --version
```
- [x] Command executed
- [x] Version shown: 1.0.0b1
- [x] Expected: 1.0.0b1 - MATCH

### Step 2.3: Run Setup Wizard
```bash
kln setup
```
- [x] Command executed
- [x] First run: Selected NanoGPT (1)
- [x] Second run: Selected OpenRouter (2)
- [x] Config backed up automatically
- [x] Result: OpenRouter configuration active

### Step 2.4: Install Components
```bash
kln install --yes
```
- [x] Command executed
- [x] Scripts installed: 38 scripts
- [x] Commands installed: 9 /kln: commands
- [x] Hooks installed: 4 hooks
- [x] SmolKLN agents installed: 9 agents
- [x] Knowledge database: Ready
- [x] Result: Installation complete

### Step 2.5: Verify Doctor
```bash
kln status
```
- [x] Scripts: OK (29)
- [x] KLN Commands: OK (9)
- [x] SuperClaude: Available (31)
- [x] Hooks: OK (4)
- [x] SmolKLN Agents: OK (8)
- [x] Knowledge DB: INSTALLED
- [x] LiteLLM Proxy: RUNNING on port 4000
- [x] Models: 12 configured

---

## Phase 3: Functional Tests

### Step 3.1: Start Services
```bash
kln start
```
- [x] Command executed
- [x] LiteLLM started: YES
- [x] Port: 4000
- [x] Result: Services started successfully

### Step 3.2: Check Models Health
```bash
kln models --health
```
- [x] Command executed
- [x] Healthy models: 8/12
  - gpt-oss-120b
  - qwen3-coder
  - llama-4-maverick
  - mimo-v2-flash
  - kimi-k2
  - glm-4.7
  - deepseek-v3.2
  - gemini-2.5-flash
- [x] Unhealthy models: 4 (thinking endpoints - auth issue)
  - kimi-k2-thinking (401)
  - glm-4.7-thinking (401)
  - deepseek-v3.2-thinking (401)
  - deepseek-r1 (401)

### Step 3.3: Test Model
```bash
kln test-model deepseek-r1
```
- [x] Command executed
- [x] Result: HTTP 401 Unauthorized (API auth issue)

---

## Summary

| Phase | Status | Notes |
|-------|--------|-------|
| Clean Uninstall | PASS | All directories removed |
| Fresh Install | PASS | PyPI install successful |
| Setup | PASS | Config created (OpenRouter) |
| Installation | PASS | All components installed |
| Services | PASS | LiteLLM running |
| Model Health | PARTIAL | 8/12 healthy, 4 thinking models need auth fix |

### Issues Found
1. Thinking model endpoints (4 models) returning 401 Unauthorized
   - These use NANOGPT_THINKING_API_BASE
   - May need separate API key or endpoint config

### Next Investigation
- Check if thinking models need special NanoGPT account setup
- Verify OpenRouter key is properly set in env
