#!/usr/bin/env bash
# Bash additions for the Review System
# Add these to your ~/.bashrc

# K-LEAN scripts directory (supports environment override)
KLEAN_SCRIPTS="${KLEAN_SCRIPTS_DIR:-$HOME/.claude/scripts}"

# --- Quick Review Functions (API-based, no headless Claude) ---

# Quick review via LiteLLM API
quick-review() {
    local focus="${1:-general code quality}"
    curl -s http://localhost:4000/chat/completions \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"coding-qwen\",
            \"messages\": [{\"role\": \"user\", \"content\": \"Quick review of this diff for $focus:\\n\\n$(git diff HEAD~1 | head -200)\"}],
            \"max_tokens\": 1000
        }" | jq -r '.choices[0].message.content'
}

# Consensus review - all 3 models via curl (API-based)
consensus-review() {
    local focus="${1:-general code quality}"
    local diff=$(git diff HEAD~1..HEAD 2>/dev/null | head -300)

    echo "Running 3 parallel reviews..."

    curl -s http://localhost:4000/chat/completions -H "Content-Type: application/json" \
        -d "{\"model\":\"coding-qwen\",\"messages\":[{\"role\":\"user\",\"content\":\"Quick review for $focus:\\n$diff\"}],\"max_tokens\":800}" \
        > /tmp/cons_qwen.json &

    curl -s http://localhost:4000/chat/completions -H "Content-Type: application/json" \
        -d "{\"model\":\"architecture-deepseek\",\"messages\":[{\"role\":\"user\",\"content\":\"Quick review for $focus:\\n$diff\"}],\"max_tokens\":800}" \
        > /tmp/cons_deepseek.json &

    curl -s http://localhost:4000/chat/completions -H "Content-Type: application/json" \
        -d "{\"model\":\"tools-glm\",\"messages\":[{\"role\":\"user\",\"content\":\"Quick review for $focus:\\n$diff\"}],\"max_tokens\":800}" \
        > /tmp/cons_glm.json &

    wait

    echo "=== QWEN ===" && jq -r '.choices[0].message.content' /tmp/cons_qwen.json
    echo "=== DEEPSEEK ===" && jq -r '.choices[0].message.content' /tmp/cons_deepseek.json
    echo "=== GLM ===" && jq -r '.choices[0].message.content' /tmp/cons_glm.json
}
