#!/bin/bash
#
# Health Check - Test all LiteLLM models
#
# Usage:
#   health-check.sh           # Full check all models
#   health-check.sh --quick   # Quick proxy check only
#
# Can be triggered via:
#   - Direct: ~/.claude/scripts/health-check.sh
#   - Hook: Type "healthcheck" in Claude prompt
#

QUICK_MODE=false
[ "$1" = "--quick" ] && QUICK_MODE=true

# All available models
MODELS="coding-qwen architecture-deepseek tools-glm research-minimax agent-kimi scripting-hermes"

echo "═══════════════════════════════════════════════════════════════"
echo "  MODEL HEALTH CHECK"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check proxy first
echo "Checking LiteLLM proxy (localhost:4000)..."
if ! curl -s --max-time 3 http://localhost:4000/health > /dev/null 2>&1; then
    echo "❌ FAIL: LiteLLM proxy not responding"
    echo ""
    echo "Start it with: start-nano-proxy"
    exit 1
fi
echo "✅ Proxy is running"
echo ""

if $QUICK_MODE; then
    echo "Quick mode - skipping individual model tests"
    exit 0
fi

# Test each model
echo "Testing all models..."
echo "─────────────────────────────────────────────────────────────────"

HEALTHY=0
TOTAL=0

for model in $MODELS; do
    ((TOTAL++))
    echo -n "$model: "

    resp=$(curl -s --max-time 15 http://localhost:4000/chat/completions \
        -H "Content-Type: application/json" \
        -d "{\"model\": \"$model\", \"messages\": [{\"role\": \"user\", \"content\": \"hi\"}], \"max_tokens\": 10}" 2>/dev/null)

    # Check for content OR reasoning_content (thinking models)
    content=$(echo "$resp" | jq -r '.choices[0].message.content // empty' 2>/dev/null)
    reasoning=$(echo "$resp" | jq -r '.choices[0].message.reasoning_content // empty' 2>/dev/null)

    if [ -n "$content" ]; then
        echo "✅ OK (content)"
        ((HEALTHY++))
    elif [ -n "$reasoning" ]; then
        echo "✅ OK (thinking)"
        ((HEALTHY++))
    else
        echo "❌ FAIL"
        error=$(echo "$resp" | jq -r '.error.message // "No response"' 2>/dev/null | head -c 50)
        echo "   Error: $error"
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  RESULT: $HEALTHY/$TOTAL models healthy"
echo "═══════════════════════════════════════════════════════════════"

if [ $HEALTHY -eq $TOTAL ]; then
    echo "🎉 All models operational!"
    exit 0
elif [ $HEALTHY -gt 0 ]; then
    echo "⚠️  Some models unavailable, but system functional"
    exit 0
else
    echo "❌ No models responding - check NanoGPT API"
    exit 1
fi
