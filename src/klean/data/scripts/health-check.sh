#!/usr/bin/env bash
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

echo "═══════════════════════════════════════════════════════════════"
echo "  MODEL HEALTH CHECK"
echo "═══════════════════════════════════════════════════════════════"
echo ""

# Check proxy first and get models via auto-discovery
echo "Checking LiteLLM proxy (localhost:4000)..."
MODELS_JSON=$(curl -s --max-time 5 http://localhost:4000/models 2>/dev/null)
if [ -z "$MODELS_JSON" ] || ! echo "$MODELS_JSON" | jq -e '.data' > /dev/null 2>&1; then
    echo "[ERROR] FAIL: LiteLLM proxy not responding"
    echo ""
    echo "Start it with: kln start"
    exit 1
fi

# Extract model IDs from LiteLLM response
MODELS=$(echo "$MODELS_JSON" | jq -r '.data[].id' 2>/dev/null | sort)
MODEL_COUNT=$(echo "$MODELS" | wc -l)
echo "[OK] Proxy is running ($MODEL_COUNT models discovered)"
echo ""

if $QUICK_MODE; then
    echo "Quick mode - skipping individual model tests"
    echo "Models available:"
    echo "$MODELS" | sed 's/^/  - /'
    exit 0
fi

# Test each model
echo "Testing $MODEL_COUNT models..."
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
        echo "[OK] OK (content)"
        ((HEALTHY++))
    elif [ -n "$reasoning" ]; then
        echo "[OK] OK (thinking)"
        ((HEALTHY++))
    else
        echo "[ERROR] FAIL"
        error=$(echo "$resp" | jq -r '.error.message // "No response"' 2>/dev/null | head -c 50)
        echo "   Error: $error"
    fi
done

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "  RESULT: $HEALTHY/$TOTAL models healthy"
echo "═══════════════════════════════════════════════════════════════"

if [ $HEALTHY -eq $TOTAL ]; then
    echo " All models operational!"
    exit 0
elif [ $HEALTHY -gt 0 ]; then
    echo "[WARN]  Some models unavailable, but system functional"
    exit 0
else
    echo "[ERROR] No models responding - check NanoGPT API"
    exit 1
fi
