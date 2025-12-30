#!/usr/bin/env bash
#
# Test Script - Verify the review system works
#
# Usage: test-system.sh
#

echo "═══════════════════════════════════════════════════════════════"
echo "  REVIEW SYSTEM TEST"
echo "═══════════════════════════════════════════════════════════════"
echo ""

PASS=0
FAIL=0

test_pass() { echo "✅ PASS: $1"; ((PASS++)); }
test_fail() { echo "❌ FAIL: $1"; ((FAIL++)); }

# 1. Check proxy + models (if any model works, proxy is up)
echo "1. Proxy & Model Health (localhost:4000)"
echo "─────────────────────────────────────────────────────────────────"
HEALTHY_COUNT=0

# All 6 models from nanogpt.yaml
MODELS="qwen3-coder deepseek-v3-thinking glm-4.6-thinking minimax-m2 kimi-k2-thinking hermes-4-70b"

for model in $MODELS; do
    resp=$(curl -s --max-time 15 http://localhost:4000/chat/completions \
        -H "Content-Type: application/json" \
        -d "{\"model\": \"$model\", \"messages\": [{\"role\": \"user\", \"content\": \"hi\"}], \"max_tokens\": 10}" 2>/dev/null)

    # Check for content OR reasoning_content (thinking models use reasoning_content)
    content=$(echo "$resp" | jq -r '.choices[0].message.content // empty' 2>/dev/null)
    reasoning=$(echo "$resp" | jq -r '.choices[0].message.reasoning_content // empty' 2>/dev/null)

    if [ -n "$content" ] || [ -n "$reasoning" ]; then
        test_pass "$model"
        ((HEALTHY_COUNT++))
    else
        test_fail "$model"
        ERROR=$(echo "$resp" | jq -r '.error.message // .error // "No response"' 2>/dev/null | head -c 60)
        echo "   Error: $ERROR"
    fi
done

if [ $HEALTHY_COUNT -eq 0 ]; then
    echo ""
    echo "   ⚠️  No models responding. Is proxy running? (start-nano-proxy)"
fi
echo ""

# 2. Check scripts exist
echo "2. Scripts"
echo "─────────────────────────────────────────────────────────────────"
for script in quick-review.sh second-opinion.sh consensus-review.sh async-dispatch.sh health-check.sh session-helper.sh start-litellm.sh; do
    if [ -x ~/.claude/scripts/$script ]; then
        test_pass "$script exists and executable"
    else
        test_fail "$script missing or not executable"
    fi
done
echo ""

# 3. Check settings.json has hooks
echo "3. Hooks Configuration"
echo "─────────────────────────────────────────────────────────────────"
if [ -f ~/.claude/settings.json ]; then
    if jq -e '.hooks.UserPromptSubmit' ~/.claude/settings.json > /dev/null 2>&1; then
        test_pass "UserPromptSubmit hook configured"
    else
        test_fail "UserPromptSubmit hook missing"
    fi

    if jq -e '.hooks.PostToolUse' ~/.claude/settings.json > /dev/null 2>&1; then
        test_pass "PostToolUse hook configured"
    else
        test_fail "PostToolUse hook missing"
    fi
else
    test_fail "settings.json not found"
fi
echo ""

# 4. Check output directory
echo "4. Output Directory"
echo "─────────────────────────────────────────────────────────────────"
mkdir -p /tmp/claude-reviews
if [ -d /tmp/claude-reviews ]; then
    test_pass "/tmp/claude-reviews exists"
    SESSIONS=$(ls -d /tmp/claude-reviews/*/ 2>/dev/null | wc -l)
    FILES=$(find /tmp/claude-reviews -name "*.json" -o -name "*.txt" -o -name "*.log" 2>/dev/null | wc -l)
    echo "   Sessions: $SESSIONS folders"
    echo "   Review files: $FILES total"
else
    test_fail "/tmp/claude-reviews cannot be created"
fi
echo ""

# 5. Check dependencies
echo "5. Dependencies"
echo "─────────────────────────────────────────────────────────────────"
if command -v jq > /dev/null 2>&1; then
    test_pass "jq installed"
else
    test_fail "jq not installed (required for JSON parsing)"
fi

if command -v curl > /dev/null 2>&1; then
    test_pass "curl installed"
else
    test_fail "curl not installed"
fi
echo ""

# Summary
echo "═══════════════════════════════════════════════════════════════"
echo "  SUMMARY: $PASS passed, $FAIL failed"
echo "═══════════════════════════════════════════════════════════════"

if [ $FAIL -eq 0 ]; then
    echo ""
    echo "🎉 All tests passed! System ready."
    echo ""
    echo "Try these commands:"
    echo "  ~/.claude/scripts/quick-review.sh qwen 'test review'"
    echo "  ~/.claude/scripts/second-opinion.sh deepseek 'is this ok?'"
    echo "  ~/.claude/scripts/consensus-review.sh 'general check'"
else
    echo ""
    echo "⚠️  Some tests failed. Fix issues above before using."
fi
