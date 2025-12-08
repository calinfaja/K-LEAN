#!/usr/bin/env bash
# K-LEAN Test Suite

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

TESTS_PASSED=0
TESTS_FAILED=0

test_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    TESTS_PASSED=$((TESTS_PASSED + 1))
}

test_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    TESTS_FAILED=$((TESTS_FAILED + 1))
}

echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║              K-LEAN Test Suite                            ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Test 1: Installation structure
echo "=== Test 1: Installation Structure ==="
[ -d "$HOME/.claude/scripts" ] && test_pass "Scripts directory exists" || test_fail "Scripts directory missing"
[ -d "$HOME/.claude/commands" ] && test_pass "Commands directory exists" || test_fail "Commands directory missing"
[ -f "$HOME/.claude/CLAUDE.md" ] && test_pass "CLAUDE.md exists" || test_fail "CLAUDE.md missing"

# Test 2: Scripts are executable
echo -e "\n=== Test 2: Scripts Executable ==="
for script in quick-review.sh knowledge-init.sh async-dispatch.sh fact-extract.sh; do
    if [ -x "$HOME/.claude/scripts/$script" ]; then
        test_pass "$script is executable"
    else
        test_fail "$script not executable"
    fi
done

# Test 3: LiteLLM connectivity
echo -e "\n=== Test 3: LiteLLM Connectivity ==="
if curl -s --max-time 5 http://localhost:4000/v1/models &>/dev/null; then
    test_pass "LiteLLM is running"
else
    test_fail "LiteLLM not running on port 4000"
fi

# Test 4: Model availability
echo -e "\n=== Test 4: Model Availability ==="
MODELS=$(curl -s http://localhost:4000/v1/models 2>/dev/null | grep -o '"id":"[^"]*"' | cut -d'"' -f4)
if [ -n "$MODELS" ]; then
    MODEL_COUNT=$(echo "$MODELS" | wc -l)
    test_pass "$MODEL_COUNT models available"
else
    test_fail "No models available"
fi

# Test 5: Python environment
echo -e "\n=== Test 5: Python Environment ==="
VENV="$HOME/.venvs/knowledge-db"
if [ -d "$VENV" ]; then
    test_pass "Virtual environment exists"
    if "$VENV/bin/python" -c "import txtai" 2>/dev/null; then
        test_pass "txtai is installed"
    else
        test_fail "txtai not installed"
    fi
else
    test_fail "Virtual environment missing"
fi

# Test 6: Knowledge init
echo -e "\n=== Test 6: Knowledge System ==="
TEST_DIR="/tmp/klean-test-$$"
mkdir -p "$TEST_DIR" && cd "$TEST_DIR" && git init -q
if "$HOME/.claude/scripts/knowledge-init.sh" "$TEST_DIR" &>/dev/null; then
    if [ -d "$TEST_DIR/.knowledge-db" ]; then
        test_pass "Knowledge init creates directory"
    else
        test_fail "Knowledge init failed to create directory"
    fi
else
    test_fail "Knowledge init script error"
fi
rm -rf "$TEST_DIR"

# Test 7: Timeline system
echo -e "\n=== Test 7: Timeline System ==="
TIMELINE="$HOME/claudeAgentic/.knowledge-db/timeline.txt"
if [ -f "$TIMELINE" ]; then
    test_pass "Timeline file exists"
    ENTRIES=$(wc -l < "$TIMELINE")
    test_pass "Timeline has $ENTRIES entries"
else
    test_fail "Timeline file missing"
fi

# Test 8: Nano profile
echo -e "\n=== Test 8: Nano Profile ==="
NANO_DIR="$HOME/.claude-nano"
if [ -d "$NANO_DIR" ]; then
    test_pass "Nano profile directory exists"
    if [ -f "$NANO_DIR/settings.json" ]; then
        test_pass "Nano settings.json exists"
    else
        test_fail "Nano settings.json missing"
    fi
    if [ -L "$NANO_DIR/commands" ]; then
        test_pass "Commands symlink exists"
    else
        test_fail "Commands symlink missing"
    fi
    if [ -L "$NANO_DIR/scripts" ]; then
        test_pass "Scripts symlink exists"
    else
        test_fail "Scripts symlink missing"
    fi
else
    test_fail "Nano profile directory missing"
fi

# Summary
echo ""
echo "═══════════════════════════════════════════════════════════"
echo -e "Results: ${GREEN}$TESTS_PASSED passed${NC}, ${RED}$TESTS_FAILED failed${NC}"
echo "═══════════════════════════════════════════════════════════"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "\n${GREEN}All tests passed!${NC}"
    exit 0
else
    echo -e "\n${RED}Some tests failed. Review the output above.${NC}"
    exit 1
fi
