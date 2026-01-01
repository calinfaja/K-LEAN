#!/usr/bin/env bash
#
# K-LEAN Post-Headless Removal Test Suite
# Tests all affected features after removing /kln:deep and headless Claude dependencies
#
# Run: bash tests/test_headless_removal.sh
#

# Don't exit on error - we want to run all tests
# set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PASS=0
FAIL=0
WARN=0

pass() { echo -e "${GREEN}PASS${NC}: $1"; PASS=$((PASS + 1)); }
fail() { echo -e "${RED}FAIL${NC}: $1"; FAIL=$((FAIL + 1)); }
warn() { echo -e "${YELLOW}WARN${NC}: $1"; WARN=$((WARN + 1)); }
section() { echo -e "\n${YELLOW}=== $1 ===${NC}"; }

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  K-LEAN Post-Headless Removal Test Suite                       ║"
echo "║  Testing all features after /kln:deep removal                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"

# ─────────────────────────────────────────────────────────────────────
section "1. DELETED FILES (should NOT exist)"
# ─────────────────────────────────────────────────────────────────────

DELETED_FILES=(
    "$HOME/.claude/commands/kln/deep.md"
    "$HOME/.claude/scripts/deep-review.sh"
    "$HOME/.claude/scripts/parallel-deep-review.sh"
    "$HOME/.claude/scripts/test-headless.sh"
    "$HOME/.claude/scripts/test-deep-audit.sh"
    "$HOME/.claude/hooks/async-review.sh"
)

for f in "${DELETED_FILES[@]}"; do
    if [ -f "$f" ]; then
        fail "$(basename "$f") still exists: $f"
    else
        pass "$(basename "$f") removed"
    fi
done

# ─────────────────────────────────────────────────────────────────────
section "2. REQUIRED FILES (must exist and be executable)"
# ─────────────────────────────────────────────────────────────────────

REQUIRED_SCRIPTS=(
    "quick-review.sh"
    "consensus-review.sh"
    "async-dispatch.sh"
    "session-helper.sh"
    "health-check.sh"
    "start-litellm.sh"
    "knowledge-query.sh"
    "knowledge-server.py"
    "timeline-query.sh"
    "kb-doctor.sh"
)

for script in "${REQUIRED_SCRIPTS[@]}"; do
    if [ -x "$HOME/.claude/scripts/$script" ]; then
        pass "$script executable"
    else
        fail "$script missing or not executable"
    fi
done

# ─────────────────────────────────────────────────────────────────────
section "3. KLN SLASH COMMANDS (9 expected)"
# ─────────────────────────────────────────────────────────────────────

EXPECTED_COMMANDS=(
    "quick.md"
    "multi.md"
    "agent.md"
    "rethink.md"
    "status.md"
    "help.md"
    "doc.md"
    "remember.md"
    "learn.md"
)

cmd_count=$(ls "$HOME/.claude/commands/kln/"*.md 2>/dev/null | wc -l)
if [ "$cmd_count" -eq 9 ]; then
    pass "9 KLN commands present"
else
    fail "Expected 9 commands, found $cmd_count"
fi

for cmd in "${EXPECTED_COMMANDS[@]}"; do
    if [ -f "$HOME/.claude/commands/kln/$cmd" ]; then
        pass "$cmd exists"
    else
        fail "$cmd missing"
    fi
done

# deep.md must NOT exist
if [ -f "$HOME/.claude/commands/kln/deep.md" ]; then
    fail "deep.md still exists (should be deleted)"
else
    pass "deep.md correctly removed"
fi

# ─────────────────────────────────────────────────────────────────────
section "4. HOOKS (4 expected, async-review.sh removed)"
# ─────────────────────────────────────────────────────────────────────

EXPECTED_HOOKS=(
    "session-start.sh"
    "user-prompt-handler.sh"
    "post-bash-handler.sh"
    "post-web-handler.sh"
)

hook_count=$(ls "$HOME/.claude/hooks/"*.sh 2>/dev/null | wc -l)
if [ "$hook_count" -eq 4 ]; then
    pass "4 hooks present"
else
    fail "Expected 4 hooks, found $hook_count"
fi

for hook in "${EXPECTED_HOOKS[@]}"; do
    if [ -x "$HOME/.claude/hooks/$hook" ]; then
        pass "$hook executable"
    else
        fail "$hook missing or not executable"
    fi
done

# async-review.sh must NOT exist
if [ -f "$HOME/.claude/hooks/async-review.sh" ]; then
    fail "async-review.sh still exists (should be deleted)"
else
    pass "async-review.sh correctly removed"
fi

# ─────────────────────────────────────────────────────────────────────
section "5. NO DEEP REFERENCES IN HOOKS"
# ─────────────────────────────────────────────────────────────────────

if grep -q "asyncDeepReview" "$HOME/.claude/hooks/user-prompt-handler.sh" 2>/dev/null; then
    fail "asyncDeepReview still in user-prompt-handler.sh"
else
    pass "asyncDeepReview removed from user-prompt-handler.sh"
fi

if grep -q "asyncDeepAudit" "$HOME/.claude/scripts/async-dispatch.sh" 2>/dev/null; then
    fail "asyncDeepAudit still in async-dispatch.sh"
else
    pass "asyncDeepAudit removed from async-dispatch.sh"
fi

# ─────────────────────────────────────────────────────────────────────
section "6. REMAINING KEYWORDS IN HOOKS"
# ─────────────────────────────────────────────────────────────────────

EXPECTED_KEYWORDS=("SaveThis" "SaveInfo" "FindKnowledge" "asyncReview" "asyncConsensus")

for kw in "${EXPECTED_KEYWORDS[@]}"; do
    if grep -q "$kw" "$HOME/.claude/hooks/user-prompt-handler.sh" 2>/dev/null; then
        pass "Keyword '$kw' present"
    else
        warn "Keyword '$kw' not found"
    fi
done

# ─────────────────────────────────────────────────────────────────────
section "7. K-LEAN CLI"
# ─────────────────────────────────────────────────────────────────────

if command -v kln &>/dev/null; then
    pass "kln command available"

    version=$(kln --version 2>&1)
    if [[ "$version" =~ "1.0.0" ]]; then
        pass "kln version: $version"
    else
        warn "Unexpected version: $version"
    fi
else
    fail "kln command not found"
fi

# ─────────────────────────────────────────────────────────────────────
section "8. LITELLM PROXY"
# ─────────────────────────────────────────────────────────────────────

if curl -s localhost:4000/health | grep -q "healthy_endpoints"; then
    model_count=$(curl -s localhost:4000/health | grep -o '"model"' | wc -l)
    pass "LiteLLM running ($model_count models)"
else
    warn "LiteLLM not responding (may need: kln start)"
fi

# ─────────────────────────────────────────────────────────────────────
section "9. KNOWLEDGE DATABASE"
# ─────────────────────────────────────────────────────────────────────

if [ -d "$HOME/.venvs/knowledge-db" ]; then
    pass "Knowledge DB venv exists"
else
    fail "Knowledge DB venv missing"
fi

if ls /tmp/kb-*.sock &>/dev/null; then
    pass "Knowledge server socket exists"
else
    warn "Knowledge server not running"
fi

# Test query (if server running)
if "$HOME/.claude/scripts/knowledge-query.sh" "test" &>/dev/null; then
    pass "Knowledge query works"
else
    warn "Knowledge query failed"
fi

# ─────────────────────────────────────────────────────────────────────
section "10. SMOLKLN AGENTS"
# ─────────────────────────────────────────────────────────────────────

if command -v smol-kln &>/dev/null; then
    pass "smol-kln command available"

    agent_count=$(smol-kln --list 2>&1 | grep -c "  - ")
    if [ "$agent_count" -ge 8 ]; then
        pass "$agent_count agents available"
    else
        warn "Expected 8+ agents, found $agent_count"
    fi
else
    fail "smol-kln command not found"
fi

# ─────────────────────────────────────────────────────────────────────
section "11. NO STALE REFERENCES IN SOURCE"
# ─────────────────────────────────────────────────────────────────────

REPO_ROOT="${1:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

# Check for kln:deep references (excluding benchmark historical data)
deep_refs=$(grep -r "kln:deep" "$REPO_ROOT/src" "$REPO_ROOT/docs" --include="*.md" --include="*.py" --include="*.sh" 2>/dev/null | grep -v "agent-benchmark-results.md" | grep -v "\.pyc" | wc -l)
if [ "$deep_refs" -eq 0 ]; then
    pass "No kln:deep references in source (excluding benchmarks)"
else
    fail "$deep_refs stale kln:deep references found"
    grep -r "kln:deep" "$REPO_ROOT/src" "$REPO_ROOT/docs" --include="*.md" --include="*.py" --include="*.sh" 2>/dev/null | grep -v "agent-benchmark-results.md" | head -5
fi

# Check for asyncDeepReview/asyncDeepAudit
async_deep_refs=$(grep -rE "asyncDeepReview|asyncDeepAudit" "$REPO_ROOT/src" "$REPO_ROOT/docs" --include="*.md" --include="*.py" --include="*.sh" 2>/dev/null | grep -v "\.pyc" | wc -l)
if [ "$async_deep_refs" -eq 0 ]; then
    pass "No asyncDeepReview/asyncDeepAudit references"
else
    fail "$async_deep_refs stale async deep references found"
fi

# ─────────────────────────────────────────────────────────────────────
section "12. K-LEAN TEST SUITE"
# ─────────────────────────────────────────────────────────────────────

if kln test 2>&1 | grep -q "All.*tests passed"; then
    pass "kln test suite passes"
else
    warn "kln test suite has issues"
fi

# ─────────────────────────────────────────────────────────────────────
section "13. BASHRC ADDITIONS (API-only functions)"
# ─────────────────────────────────────────────────────────────────────

bashrc_file="$HOME/.claude/scripts/bashrc-additions.sh"

if [ -f "$bashrc_file" ]; then
    pass "bashrc-additions.sh exists"

    # Should NOT have deep-review or parallel-review functions
    if grep -q "deep-review()" "$bashrc_file"; then
        fail "deep-review() still in bashrc-additions.sh"
    else
        pass "deep-review() removed from bashrc-additions.sh"
    fi

    if grep -q "parallel-review()" "$bashrc_file"; then
        fail "parallel-review() still in bashrc-additions.sh"
    else
        pass "parallel-review() removed from bashrc-additions.sh"
    fi

    # Should have quick-review and consensus-review
    if grep -q "quick-review()" "$bashrc_file"; then
        pass "quick-review() present"
    else
        warn "quick-review() missing"
    fi

    if grep -q "consensus-review()" "$bashrc_file"; then
        pass "consensus-review() present"
    else
        warn "consensus-review() missing"
    fi
else
    fail "bashrc-additions.sh missing"
fi

# ─────────────────────────────────────────────────────────────────────
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  TEST RESULTS                                                  ║"
echo "╠════════════════════════════════════════════════════════════════╣"
printf "║  ${GREEN}PASSED${NC}: %-5d                                               ║\n" $PASS
printf "║  ${RED}FAILED${NC}: %-5d                                               ║\n" $FAIL
printf "║  ${YELLOW}WARNED${NC}: %-5d                                               ║\n" $WARN
echo "╚════════════════════════════════════════════════════════════════╝"

if [ $FAIL -eq 0 ]; then
    echo -e "\n${GREEN}All critical tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed. Review output above.${NC}"
    exit 1
fi
