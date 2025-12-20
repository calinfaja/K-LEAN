#!/usr/bin/env bash
#
# Test Deep Audit - Comprehensive model testing framework
# Tests each LiteLLM model by analyzing git diff between commits
#
# Usage: test-deep-audit.sh [OPTIONS]
#
# Options:
#   --all           Test all 6 models (default: 3 reliable)
#   --unsafe        Disable audit mode (allow write operations - NOT RECOMMENDED)
#   --commits N     Use last N commits for diff (default: 1)
#   --model MODEL   Test single model only
#   --parallel      Run all tests in parallel
#   --timeout SECS  Timeout per model (default: 300)
#   --compare A B   Compare specific commits (e.g., HEAD~2 HEAD)
#
# Examples:
#   test-deep-audit.sh                    # Test 3 reliable models on last commit
#   test-deep-audit.sh --all              # Test all 6 models
#   test-deep-audit.sh --unsafe           # Test without audit restrictions (NOT RECOMMENDED)
#   test-deep-audit.sh --model qwen       # Test qwen only
#   test-deep-audit.sh --compare HEAD~3 HEAD  # Custom commit range

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="${PWD}"
OUTPUT_DIR="/tmp/deep-audit-test-$(date +%Y%m%d-%H%M%S)"
TIMEOUT=300
AUDIT_MODE=true  # Default: read-only audit mode (safe)
PARALLEL_MODE=false
TEST_ALL=false
SINGLE_MODEL=""
COMMIT_RANGE="HEAD~1 HEAD"

# Models configuration
# Reliable models (proven for tool use)
RELIABLE_MODELS="qwen kimi glm"
# All models (including experimental)
ALL_MODELS="qwen deepseek kimi glm minimax hermes"

# Model to LiteLLM name mapping
declare -A MODEL_MAP=(
    ["qwen"]="qwen3-coder"
    ["deepseek"]="deepseek-v3-thinking"
    ["kimi"]="kimi-k2-thinking"
    ["glm"]="glm-4.6-thinking"
    ["minimax"]="minimax-m2"
    ["hermes"]="hermes-4-70b"
)

# Model descriptions
declare -A MODEL_DESC=(
    ["qwen"]="Code quality, bugs (RELIABLE)"
    ["deepseek"]="Architecture, design (EXPERIMENTAL)"
    ["kimi"]="Agent tasks, planning (RELIABLE)"
    ["glm"]="Standards, compliance (RELIABLE)"
    ["minimax"]="Research, analysis (EXPERIMENTAL)"
    ["hermes"]="Scripting, automation (EXPERIMENTAL)"
)

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "\n${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}$1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════════════${NC}"
}

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Usage
usage() {
    head -35 "$0" | tail -n +2 | sed 's/^# //' | sed 's/^#//'
    exit 0
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --all)
            TEST_ALL=true
            shift
            ;;
        --unsafe)
            AUDIT_MODE=false
            shift
            ;;
        --parallel)
            PARALLEL_MODE=true
            shift
            ;;
        --timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        --model)
            SINGLE_MODEL="$2"
            shift 2
            ;;
        --commits)
            COMMIT_RANGE="HEAD~$2 HEAD"
            shift 2
            ;;
        --compare)
            COMMIT_RANGE="$2 $3"
            shift 3
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Check LiteLLM is running
check_litellm() {
    if ! curl -s http://localhost:4000/health > /dev/null 2>&1; then
        print_error "LiteLLM proxy not running on localhost:4000"
        echo "Start it with: ~/.claude/scripts/litellm-start.sh"
        exit 1
    fi
    print_success "LiteLLM proxy is running"
}

# Check model health
check_model_health() {
    local model="$1"
    local litellm_name="${MODEL_MAP[$model]}"

    local resp=$(curl -s --max-time 10 http://localhost:4000/chat/completions \
        -H "Content-Type: application/json" \
        -d "{\"model\": \"$litellm_name\", \"messages\": [{\"role\": \"user\", \"content\": \"hi\"}], \"max_tokens\": 5}" 2>/dev/null)

    echo "$resp" | jq -e '.choices[0]' > /dev/null 2>&1
}

# Get git diff for testing
get_git_diff() {
    local from_commit=$(echo "$COMMIT_RANGE" | cut -d' ' -f1)
    local to_commit=$(echo "$COMMIT_RANGE" | cut -d' ' -f2)

    git diff "$from_commit" "$to_commit" 2>/dev/null || {
        print_error "Failed to get git diff for $COMMIT_RANGE"
        exit 1
    }
}

# Run single model test
run_model_test() {
    local model="$1"
    local litellm_name="${MODEL_MAP[$model]}"
    local output_file="$OUTPUT_DIR/test-$model.txt"
    local timing_file="$OUTPUT_DIR/timing-$model.txt"
    local config_dir="/tmp/claude-test-$model-$$"

    print_info "Testing $model (${MODEL_DESC[$model]})"

    # Check if model is healthy
    if ! check_model_health "$model"; then
        print_warn "$model is not healthy, skipping"
        echo "SKIPPED: Model unhealthy" > "$output_file"
        echo "0" > "$timing_file"
        return 1
    fi

    # Create isolated config directory with audit permissions
    mkdir -p "$config_dir"

    # Build settings with or without audit mode
    if [ "$AUDIT_MODE" = true ]; then
        cat > "$config_dir/settings.json" << EOF
{
  "defaultModel": "$litellm_name",
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_AUTH_TOKEN": "sk-litellm-static-key",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "$litellm_name",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "$litellm_name",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "$litellm_name"
  },
  "permissions": {
    "allow": [
      "Read", "Glob", "Grep", "LS", "Agent", "Task",
      "WebFetch", "WebSearch",
      "mcp__tavily__tavily-search", "mcp__tavily__tavily-extract",
      "mcp__context7__resolve-library-id", "mcp__context7__get-library-docs",
      "mcp__sequential-thinking__sequentialthinking",
      "mcp__serena__list_dir", "mcp__serena__find_file", "mcp__serena__search_for_pattern",
      "mcp__serena__get_symbols_overview", "mcp__serena__find_symbol",
      "mcp__serena__find_referencing_symbols", "mcp__serena__list_memories",
      "mcp__serena__read_memory", "mcp__serena__get_current_config",
      "mcp__serena__think_about_collected_information",
      "Bash(git diff:*)", "Bash(git log:*)", "Bash(git status:*)",
      "Bash(git show:*)", "Bash(git blame:*)", "Bash(git branch:*)",
      "Bash(cat:*)", "Bash(head:*)", "Bash(tail:*)", "Bash(wc:*)",
      "Bash(find:*)", "Bash(ls:*)", "Bash(tree:*)", "Bash(grep:*)",
      "Bash(rg:*)", "Bash(jq:*)", "Bash(curl -s:*)"
    ],
    "deny": [
      "Write", "Edit", "NotebookEdit",
      "Bash(rm:*)", "Bash(mv:*)", "Bash(cp:*)", "Bash(mkdir:*)",
      "Bash(chmod:*)", "Bash(chown:*)",
      "Bash(git add:*)", "Bash(git commit:*)", "Bash(git push:*)",
      "Bash(git checkout:*)", "Bash(git reset:*)", "Bash(git revert:*)",
      "Bash(npm install:*)", "Bash(pip install:*)", "Bash(sudo:*)",
      "mcp__serena__replace_symbol_body", "mcp__serena__insert_after_symbol",
      "mcp__serena__insert_before_symbol", "mcp__serena__rename_symbol",
      "mcp__serena__write_memory", "mcp__serena__delete_memory", "mcp__serena__edit_memory"
    ]
  }
}
EOF
    else
        cat > "$config_dir/settings.json" << EOF
{
  "defaultModel": "$litellm_name",
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4000",
    "ANTHROPIC_AUTH_TOKEN": "sk-litellm-static-key",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "$litellm_name",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "$litellm_name",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "$litellm_name"
  }
}
EOF
    fi

    # Symlink shared resources
    ln -sf ~/.claude/commands "$config_dir/commands" 2>/dev/null || true
    ln -sf ~/.claude/scripts "$config_dir/scripts" 2>/dev/null || true
    ln -sf ~/.claude/hooks "$config_dir/hooks" 2>/dev/null || true
    ln -sf ~/.claude/CLAUDE.md "$config_dir/CLAUDE.md" 2>/dev/null || true
    ln -sf ~/.claude/.credentials.json "$config_dir/.credentials.json" 2>/dev/null || true

    # Get git diff
    local diff_content
    diff_content=$(get_git_diff)

    # Build prompt
    local prompt="You are a code reviewer. Analyze this git diff and provide:

## Grade: [A-F]
## Risk Level: [CRITICAL/HIGH/MEDIUM/LOW]
## Summary
[Brief summary of changes]

## Issues Found
| File | Line | Severity | Issue |
|------|------|----------|-------|

## Verdict: [APPROVE/REQUEST_CHANGES]

---
GIT DIFF ($COMMIT_RANGE):
\`\`\`diff
$diff_content
\`\`\`

Be concise. Focus on actual issues, not style."

    # Build claude command - always use --dangerously-skip-permissions
    # Security is enforced by allowed/denied tools in settings.json (audit mode)
    local claude_cmd="claude --model $litellm_name --dangerously-skip-permissions --print"

    # Run with timing
    local start_time=$(date +%s.%N)

    cd "$WORK_DIR"
    if timeout "$TIMEOUT" bash -c "CLAUDE_CONFIG_DIR='$config_dir' $claude_cmd '$prompt'" > "$output_file" 2>&1; then
        local end_time=$(date +%s.%N)
        local duration=$(echo "$end_time - $start_time" | bc)
        echo "$duration" > "$timing_file"
        print_success "$model completed in ${duration}s"
    else
        local exit_code=$?
        local end_time=$(date +%s.%N)
        local duration=$(echo "$end_time - $start_time" | bc)
        echo "$duration" > "$timing_file"

        if [ $exit_code -eq 124 ]; then
            print_warn "$model timed out after ${TIMEOUT}s"
            echo -e "\n[TIMEOUT after ${TIMEOUT}s]" >> "$output_file"
        else
            print_error "$model failed with exit code $exit_code"
            echo -e "\n[FAILED with exit code $exit_code]" >> "$output_file"
        fi
    fi

    # Cleanup
    rm -rf "$config_dir"
}

# Generate comparison report
generate_report() {
    local report_file="$OUTPUT_DIR/comparison-report.md"

    print_header "GENERATING COMPARISON REPORT"

    cat > "$report_file" << EOF
# Deep Audit Model Test Report

**Date**: $(date '+%Y-%m-%d %H:%M:%S')
**Working Directory**: $WORK_DIR
**Commit Range**: $COMMIT_RANGE
**Audit Mode** (read-only): $AUDIT_MODE
**Timeout**: ${TIMEOUT}s

## Performance Summary

| Model | Time (s) | Status | Grade | Risk | Verdict |
|-------|----------|--------|-------|------|---------|
EOF

    # Parse each model result
    local models_to_test
    if [ -n "$SINGLE_MODEL" ]; then
        models_to_test="$SINGLE_MODEL"
    elif [ "$TEST_ALL" = true ]; then
        models_to_test="$ALL_MODELS"
    else
        models_to_test="$RELIABLE_MODELS"
    fi

    for model in $models_to_test; do
        local output_file="$OUTPUT_DIR/test-$model.txt"
        local timing_file="$OUTPUT_DIR/timing-$model.txt"

        if [ -f "$timing_file" ]; then
            local duration=$(cat "$timing_file")
            local status="OK"
            local grade="N/A"
            local risk="N/A"
            local verdict="N/A"

            if [ -f "$output_file" ]; then
                # Check for timeout/failure
                if grep -q "TIMEOUT" "$output_file"; then
                    status="TIMEOUT"
                elif grep -q "FAILED" "$output_file"; then
                    status="FAILED"
                elif grep -q "SKIPPED" "$output_file"; then
                    status="SKIPPED"
                else
                    # Extract grade, risk, verdict
                    grade=$(grep -E "^## Grade:" "$output_file" | head -1 | sed 's/## Grade: *//' | tr -d '[]' || echo "N/A")
                    risk=$(grep -E "^## Risk" "$output_file" | head -1 | sed 's/## Risk.*: *//' | tr -d '[]' || echo "N/A")
                    verdict=$(grep -E "^## Verdict:" "$output_file" | head -1 | sed 's/## Verdict: *//' | tr -d '[]' || echo "N/A")
                fi
            fi

            echo "| $model | ${duration} | $status | $grade | $risk | $verdict |" >> "$report_file"
        fi
    done

    # Add detailed outputs
    cat >> "$report_file" << EOF

## Detailed Outputs

EOF

    for model in $models_to_test; do
        local output_file="$OUTPUT_DIR/test-$model.txt"
        if [ -f "$output_file" ]; then
            cat >> "$report_file" << EOF
### $model (${MODEL_DESC[$model]})

\`\`\`
$(head -100 "$output_file")
\`\`\`

EOF
        fi
    done

    # Add audit mode information
    if [ "$AUDIT_MODE" = true ]; then
        cat >> "$report_file" << EOF
## Audit Mode (Read-Only)

Tests run with \`--dangerously-skip-permissions\` + restricted allowedTools.
This provides safe, fast automation with read-only access.

**Security:**
- ALLOWED: Read, Grep, Glob, WebSearch, WebFetch, git read ops, MCP search tools
- DENIED: Write, Edit, rm, mv, git commit/push, any destructive operations

**Benefits:**
- No permission prompts (fast execution)
- Cannot modify code or files
- Safe for automated reviews

EOF
    else
        cat >> "$report_file" << EOF
## Unsafe Mode (NOT RECOMMENDED)

Tests run WITHOUT audit mode restrictions.
Claude has full access to all tools including destructive operations.

**Warning:** Only use in isolated test environments!

EOF
    fi

    print_success "Report saved to: $report_file"
    echo ""
    cat "$report_file"
}

# Main execution
main() {
    print_header "DEEP AUDIT MODEL TEST"

    echo "Configuration:"
    echo "  Working Dir: $WORK_DIR"
    echo "  Output Dir: $OUTPUT_DIR"
    echo "  Commit Range: $COMMIT_RANGE"
    echo "  Audit Mode: $AUDIT_MODE (read-only with full search/research access)"
    echo "  Parallel: $PARALLEL_MODE"
    echo "  Timeout: ${TIMEOUT}s"
    echo ""

    # Check prerequisites
    check_litellm

    # Determine which models to test
    local models_to_test
    if [ -n "$SINGLE_MODEL" ]; then
        models_to_test="$SINGLE_MODEL"
        print_info "Testing single model: $SINGLE_MODEL"
    elif [ "$TEST_ALL" = true ]; then
        models_to_test="$ALL_MODELS"
        print_info "Testing ALL 6 models"
    else
        models_to_test="$RELIABLE_MODELS"
        print_info "Testing 3 reliable models (use --all for all 6)"
    fi

    # Get commit info
    print_header "GIT DIFF INFO"
    local from_commit=$(echo "$COMMIT_RANGE" | cut -d' ' -f1)
    local to_commit=$(echo "$COMMIT_RANGE" | cut -d' ' -f2)
    echo "From: $from_commit"
    git log --oneline -1 "$from_commit" 2>/dev/null || echo "  (not a valid commit ref)"
    echo "To: $to_commit"
    git log --oneline -1 "$to_commit" 2>/dev/null || echo "  (not a valid commit ref)"
    echo ""
    echo "Diff stats:"
    git diff --stat "$from_commit" "$to_commit" 2>/dev/null | tail -5

    # Run tests
    print_header "RUNNING MODEL TESTS"

    if [ "$PARALLEL_MODE" = true ]; then
        print_info "Running tests in parallel..."
        local pids=""
        for model in $models_to_test; do
            run_model_test "$model" &
            pids="$pids $!"
        done
        # Wait for all
        for pid in $pids; do
            wait $pid 2>/dev/null || true
        done
    else
        for model in $models_to_test; do
            run_model_test "$model"
            echo ""
        done
    fi

    # Generate report
    generate_report

    print_header "TEST COMPLETE"
    echo "Results saved to: $OUTPUT_DIR"
    echo ""
    echo "Files:"
    ls -la "$OUTPUT_DIR"
}

main "$@"
