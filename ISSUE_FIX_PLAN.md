# K-LEAN Issue Fix Plan

**Date**: 2025-12-09
**Total Issues**: 6 open (4 medium, 2 low)

---

## 8-Step Fix Plan

### Step 1: Fix ISS-005 - Update Model Names in Slash Commands
**Priority**: High | **Effort**: Low

Update all slash command templates to use correct model names:
- `qwen` → `qwen3-coder`
- `kimi` → `kimi-k2-thinking`
- `glm` → `glm-4.6-thinking`
- `deepseek` → `deepseek-v3-thinking`
- `minimax` → `minimax-m2`
- `hermes` → `hermes-4-70b`

**Files to update**:
- `~/.claude/commands/kln:quickReview.md`
- `~/.claude/commands/kln:quickCompare.md`
- `~/.claude/commands/kln:deepInspect.md`
- `~/.claude/commands/kln:deepAudit.md`

---

### Step 2: Fix ISS-006 - Repair quickCompare Bash Syntax
**Priority**: High | **Effort**: Medium

Fix the `build_payload` function syntax error in quickCompare.md:
- Escape special characters properly in heredoc
- Fix function definition syntax for bash
- Test with: `/kln:quickCompare qwen3-coder,kimi-k2-thinking,glm-4.6-thinking code quality`

---

### Step 3: Fix ISS-008 - Strip Kimi `<think>` Tags
**Priority**: Low | **Effort**: Low

Add post-processing to review scripts to strip thinking tags:
```bash
# Add to output processing
OUTPUT=$(echo "$RESPONSE" | sed 's/<think>.*<\/think>//g')
```

**Files to update**:
- `~/.claude/scripts/quick-review.sh`
- `~/.claude/scripts/deep-review.sh`
- `~/.claude/scripts/consensus-review.sh`
- `~/.claude/scripts/parallel-deep-review.sh`

---

### Step 4: Fix ISS-007 - Debug Headless Claude Tool Integration
**Priority**: Medium | **Effort**: High

Investigate why headless Claude returns incomplete output:
1. Check timeout settings in deep-review.sh
2. Verify LiteLLM streaming vs non-streaming response handling
3. Test with increased `--max-time` in curl calls
4. Add verbose logging to capture full response

**Diagnostic steps**:
```bash
# Test direct LiteLLM call with verbose output
curl -v --max-time 300 http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen3-coder", "messages": [{"role": "user", "content": "Hello"}]}'
```

---

### Step 5: Fix ISS-004 - Implement Embedding Auto-Regeneration
**Priority**: Low | **Effort**: Medium

Add automatic embedding regeneration when new entries are added:

**Option A**: Regenerate on each add (slow but always current)
```python
# In knowledge-capture.py after save_entry()
subprocess.run(['python', 'knowledge-search.py', '--rebuild-index'])
```

**Option B**: Scheduled regeneration (faster, periodic updates)
```bash
# Add cron job
*/30 * * * * cd ~/project && ~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-search.py --rebuild-index
```

**Option C**: Hybrid - regenerate if >10 new entries since last rebuild

---

### Step 6: Fix ISS-001 - Add claude-status Alias
**Priority**: Medium | **Effort**: Low

Add alias to `~/.bashrc`:
```bash
# K-LEAN status alias
alias claude-status='echo "=== K-LEAN Status ===" && \
  echo "Profile: ${CLAUDE_PROFILE:-native}" && \
  echo "LiteLLM: $(curl -s http://localhost:4000/health 2>/dev/null && echo "running" || echo "stopped")" && \
  echo "Knowledge Server: $(test -S /tmp/knowledge-server.sock && echo "running" || echo "stopped")"'
```

Then run: `source ~/.bashrc`

---

### Step 7: Create Model Name Mapping Utility
**Priority**: Medium | **Effort**: Low

Create a central model mapping file to avoid future mismatches:

**File**: `~/.claude/config/models.json`
```json
{
  "aliases": {
    "qwen": "qwen3-coder",
    "kimi": "kimi-k2-thinking",
    "glm": "glm-4.6-thinking",
    "deepseek": "deepseek-v3-thinking",
    "minimax": "minimax-m2",
    "hermes": "hermes-4-70b"
  }
}
```

**Helper script**: `~/.claude/scripts/resolve-model.sh`
```bash
#!/bin/bash
# Resolve model alias to actual LiteLLM model name
ALIAS="$1"
jq -r ".aliases[\"$ALIAS\"] // \"$ALIAS\"" ~/.claude/config/models.json
```

Update all scripts to use: `MODEL=$(~/.claude/scripts/resolve-model.sh "$1")`

---

### Step 8: Validation and Regression Testing
**Priority**: High | **Effort**: Medium

After all fixes, run complete test suite:

```bash
# 1. Health check
healthcheck

# 2. Quick review (single model)
/kln:quickReview qwen security

# 3. Quick compare (3 models parallel)
/kln:quickCompare qwen,kimi,glm code quality

# 4. Deep inspect (with tools)
/kln:deepInspect deepseek architecture

# 5. Async operations
asyncDeepReview performance

# 6. Knowledge system
SaveThis Test entry for validation
FindKnowledge validation

# 7. Verify no <think> tags in output
grep -r "<think>" /tmp/claude-reviews/
```

Update TEST_RESULTS.md with regression test results.

---

## Execution Order

| Step | Issue | Priority | Effort | Dependencies |
|------|-------|----------|--------|--------------|
| 1 | ISS-005 | High | Low | None |
| 2 | ISS-006 | High | Medium | Step 1 |
| 3 | ISS-008 | Low | Low | None |
| 4 | ISS-007 | Medium | High | Steps 1-2 |
| 5 | ISS-004 | Low | Medium | None |
| 6 | ISS-001 | Medium | Low | None |
| 7 | - | Medium | Low | Step 1 |
| 8 | - | High | Medium | All above |

**Estimated Total Effort**: 2-3 hours

---

## Success Criteria

After completing all steps:
- [ ] All 6 models accessible via short aliases
- [ ] quickCompare runs without bash errors
- [ ] No `<think>` tags in any review output
- [ ] Headless Claude returns complete reviews
- [ ] New knowledge entries searchable immediately
- [ ] `claude-status` command works
- [ ] All 17 tests pass (100% pass rate)

*Plan Created: 2025-12-09*
