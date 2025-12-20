#!/usr/bin/env bash
# Bash additions for the Review System
# Add these to your ~/.bashrc

# --- Deep Review Functions (Tier 3) ---
# Run thorough code reviews with LiteLLM models that have full tool access

# Main deep review function
deep-review() {
    local model="${1:-qwen}"
    local prompt="${2:-Review the codebase for issues}"
    ~/.claude/scripts/deep-review.sh "$model" "$prompt" "$(pwd)"
}

# Convenience aliases for specific review types
alias review-security='deep-review qwen "Conduct a thorough security audit focusing on buffer handling, memory safety, and input validation"'
alias review-architecture='deep-review deepseek "Analyze the module structure, coupling, and architectural patterns"'
alias review-misra='deep-review glm "Full MISRA-C:2012 compliance audit"'
alias review-memory='deep-review qwen "Find all potential memory safety issues including buffer overflows, leaks, and use-after-free"'

# Quick review (less thorough, faster)
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

# Parallel review - all 3 models with full tool access
parallel-review() {
    local prompt="${1:-Complete code review}"
    ~/.claude/scripts/parallel-deep-review.sh "$prompt" "$(pwd)"
}

# Consensus review - all 3 models via curl (faster, no tool access)
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
