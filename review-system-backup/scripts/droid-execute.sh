#!/bin/bash
#
# Droid Execute - Execute Factory droids with specialized roles and K-LEAN knowledge integration
#
# Usage:
#   droid-execute.sh <MODEL> <DROID> "<PROMPT>"
#
# Examples:
#   droid-execute.sh qwen code-reviewer "Review error handling in main.c"
#   droid-execute.sh deepseek security-auditor "Audit authentication system"
#   droid-execute.sh glm arm-cortex-expert "Review interrupt priorities"
#
# Features:
#   - Specialized droid roles (orchestrator, code-reviewer, security-auditor, etc.)
#   - Queries knowledge DB for relevant context
#   - Injects role-specific system prompts
#   - Executes droid with enriched prompt
#   - Saves output to .claude/kln/droidExecute/
#   - Returns output to stdout
#
# Supported models (short names or full):
#   qwen, deepseek, glm, kimi, minimax, hermes
#   qwen3-coder, deepseek-v3-thinking, glm-4.6-thinking,
#   kimi-k2-thinking, minimax-m2, hermes-4-70b
#
# Supported droid types:
#   orchestrator, code-reviewer, security-auditor, debugger,
#   arm-cortex-expert, c-pro, rust-expert, performance-engineer
#

set -e

# Source session helper for output management
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/session-helper.sh"

# Configuration
LITELLM_BASE_URL="${LITELLM_BASE_URL:-http://localhost:4000}"
VALID_MODELS="qwen3-coder deepseek-v3-thinking glm-4.6-thinking kimi-k2-thinking minimax-m2 hermes-4-70b"
DEFAULT_DROID="orchestrator"
KNOWLEDGE_QUERY_SCRIPT="$SCRIPT_DIR/knowledge-query.sh"
VALID_DROIDS="orchestrator code-reviewer security-auditor debugger arm-cortex-expert c-pro rust-expert performance-engineer"

# Droid role definitions
get_droid_system_prompt() {
    local droid="$1"
    case "$droid" in
        orchestrator)
            echo "You are a senior software architect specializing in system design, component orchestration, and high-level decision making. Focus on overall architecture, component interactions, scalability, and breaking down complex problems into manageable components."
            ;;
        code-reviewer)
            echo "You are an expert code reviewer with deep experience across multiple languages. Focus on code quality, readability, best practices, design patterns, error handling, testing coverage, and performance implications."
            ;;
        security-auditor)
            echo "You are a security expert specializing in vulnerability assessment and secure coding practices. Focus on OWASP Top 10, CWE/SANS Top 25, input validation, authentication/authorization, cryptographic issues, memory safety, and information disclosure risks."
            ;;
        debugger)
            echo "You are a debugging expert specializing in root cause analysis and issue resolution. Focus on identifying root causes, understanding error patterns, tracing execution flow, memory issues, race conditions, and providing actionable fixes with prevention strategies."
            ;;
        arm-cortex-expert)
            echo "You are an embedded systems expert specializing in ARM Cortex-M microcontrollers. Focus on ARM Cortex-M architecture (M0-M85), CMSIS, RTOS (FreeRTOS, Zephyr), peripheral drivers, interrupt handling (NVIC), power management, memory layout, and debugging with SWD/JTAG."
            ;;
        c-pro)
            echo "You are a C language expert specializing in embedded systems programming. Focus on C99/C11/C17 for embedded, memory management, volatile/hardware registers, bit manipulation, struct packing, MISRA C compliance, optimization without sacrificing safety, and avoiding undefined behavior."
            ;;
        rust-expert)
            echo "You are a Rust language expert specializing in safety and correctness. Focus on ownership/borrowing/lifetimes, memory safety, fearless concurrency, embedded Rust (embedded-hal, no_std), unsafe code auditing, zero-cost abstractions, error handling, and type system leverage."
            ;;
        performance-engineer)
            echo "You are a performance engineering expert specializing in optimization and profiling. Focus on algorithm complexity, memory access patterns, cache optimization, CPU/memory profiling, embedded constraints (RAM/flash/CPU), real-time guarantees, power consumption, and benchmarking."
            ;;
        *)
            echo "You are a helpful AI assistant."
            ;;
    esac
}

# Usage message
usage() {
    cat <<EOF
Usage: $(basename "$0") <MODEL> <DROID> "<PROMPT>"

Arguments:
  MODEL    Required. One of: $VALID_MODELS
  DROID    Required. One of: $VALID_DROIDS
  PROMPT   Required. Task prompt for the droid

Droid Types:
  orchestrator        System architect & high-level design
  code-reviewer       Code quality & best practices expert
  security-auditor    Security vulnerability specialist
  debugger            Root cause analysis & bug hunting
  arm-cortex-expert   ARM Cortex-M embedded systems specialist
  c-pro               C language expert for embedded systems
  rust-expert         Rust language & safety expert
  performance-engineer Performance optimization & profiling

Examples:
  $(basename "$0") qwen code-reviewer "Review error handling in main.c"
  $(basename "$0") deepseek security-auditor "Audit authentication system"
  $(basename "$0") glm arm-cortex-expert "Review interrupt priorities"

Environment:
  LITELLM_BASE_URL   Base URL for LiteLLM proxy (default: http://localhost:4000)
  FACTORY_API_KEY    Factory API key (required)

Output:
  Saved to: <project_root>/.claude/kln/droidExecute/
EOF
    exit 1
}

# Error handler
error() {
    echo "ERROR: $1" >&2
    exit 1
}

# Parse arguments
if [ $# -lt 3 ]; then
    usage
fi

MODEL="$1"
DROID="$2"
shift 2
PROMPT="$*"

# Map short model names to full LiteLLM names
case "$MODEL" in
    qwen) MODEL="qwen3-coder" ;;
    deepseek) MODEL="deepseek-v3-thinking" ;;
    glm) MODEL="glm-4.6-thinking" ;;
    kimi) MODEL="kimi-k2-thinking" ;;
    minimax) MODEL="minimax-m2" ;;
    hermes) MODEL="hermes-4-70b" ;;
esac

# Validate model
if ! echo "$VALID_MODELS" | grep -qw "$MODEL"; then
    error "Invalid model '$MODEL'. Valid models: $VALID_MODELS (or short names: qwen, deepseek, glm, kimi, minimax, hermes)"
fi

# Validate droid type
if ! echo "$VALID_DROIDS" | grep -qw "$DROID"; then
    error "Invalid droid type '$DROID'. Valid droids: $VALID_DROIDS"
fi

# Validate prompt
if [ -z "$PROMPT" ]; then
    error "Prompt cannot be empty"
fi

# Check for Factory API key
if [ -z "$FACTORY_API_KEY" ]; then
    source ~/.bashrc 2>/dev/null || true
    source ~/.profile 2>/dev/null || true
fi

if [ -z "$FACTORY_API_KEY" ]; then
    error "FACTORY_API_KEY not set. Run: export FACTORY_API_KEY=fk-YOUR_KEY"
fi

# Check if droid command exists
if ! command -v droid &> /dev/null; then
    error "droid command not found. Install Factory: https://github.com/yourusername/factory"
fi

# Get output directory
OUTPUT_DIR=$(get_output_dir "droidExecute")
WORK_DIR=$(pwd)
PROJECT_ROOT=$(find_project_root "$WORK_DIR")

echo "=== Droid Execute ===" >&2
echo "Model:    $MODEL" >&2
echo "Droid:    $DROID" >&2
echo "Project:  $PROJECT_ROOT" >&2
echo "Output:   $OUTPUT_DIR" >&2
echo "====================" >&2
echo "" >&2

# Step 1: Query knowledge DB for context
echo "[1/3] Querying knowledge DB..." >&2
KNOWLEDGE_CONTEXT=""

if [ -f "$KNOWLEDGE_QUERY_SCRIPT" ] && [ -S "/tmp/knowledge-server.sock" ]; then
    # Extract key terms from prompt for knowledge search
    SEARCH_QUERY="$PROMPT"

    # Query knowledge DB (capture output, suppress errors)
    KB_RESULTS=$("$KNOWLEDGE_QUERY_SCRIPT" "$SEARCH_QUERY" 5 2>/dev/null || echo "")

    if [ -n "$KB_RESULTS" ] && ! echo "$KB_RESULTS" | grep -q "❌"; then
        # Parse results and format as context
        KNOWLEDGE_CONTEXT=$(echo "$KB_RESULTS" | tail -n +3 | head -n 5)
        if [ -n "$KNOWLEDGE_CONTEXT" ]; then
            echo "  Found relevant knowledge:" >&2
            echo "$KNOWLEDGE_CONTEXT" | sed 's/^/    /' >&2
        fi
    else
        echo "  No relevant knowledge found" >&2
    fi
else
    echo "  Knowledge DB unavailable (server not running)" >&2
fi

# Step 2: Create enriched prompt
echo "" >&2
echo "[2/3] Preparing prompt..." >&2

# Get droid system prompt
DROID_SYSTEM_PROMPT=$(get_droid_system_prompt "$DROID")

TEMP_PROMPT_FILE=$(mktemp)
trap "rm -f $TEMP_PROMPT_FILE" EXIT

cat > "$TEMP_PROMPT_FILE" <<EOF
# Your Role
$DROID_SYSTEM_PROMPT

# Task
$PROMPT

# Working Directory
$WORK_DIR
EOF

# Add knowledge context if available
if [ -n "$KNOWLEDGE_CONTEXT" ]; then
    cat >> "$TEMP_PROMPT_FILE" <<EOF

# Relevant Knowledge from Database
The following information may be helpful for this task:

$KNOWLEDGE_CONTEXT

Please consider this context when completing the task.
EOF
fi

cat >> "$TEMP_PROMPT_FILE" <<EOF

# Instructions
IMPORTANT: You MUST use your tools to examine the actual files before providing feedback.

Required Steps:
1. Use Glob to find relevant files based on the task
2. Use Read to examine each file's actual content
3. Use Grep to search for specific patterns if needed

Output Requirements:
- Provide specific file:line references for ALL findings
- Grade the code A-F with detailed justification from your role's perspective
- List concrete issues found with severity (CRITICAL/WARNING/SUGGESTION)
- Provide actionable recommendations

DO NOT provide generic feedback. Read the files first, then provide specific analysis tailored to your role.
EOF

echo "  Prompt prepared with $(wc -l < "$TEMP_PROMPT_FILE") lines" >&2

# Step 3: Execute droid
echo "" >&2
echo "[3/3] Executing droid..." >&2
echo "" >&2

# Generate output filename
FILENAME=$(generate_filename "$MODEL" "$(echo "$PROMPT" | head -c 50)" ".txt")
OUTPUT_FILE="$OUTPUT_DIR/$FILENAME"

# Set LiteLLM environment
export LITELLM_BASE_URL

# Execute droid and capture output
EXEC_START=$(date +%s)

# All droid types use exec mode with specialized prompts
droid exec --model "custom:$MODEL" -f "$TEMP_PROMPT_FILE" 2>&1 | tee "$OUTPUT_FILE"

EXEC_END=$(date +%s)
EXEC_TIME=$((EXEC_END - EXEC_START))

# Add metadata footer to output file
cat >> "$OUTPUT_FILE" <<EOF


---
Execution Details:
- Model: $MODEL
- Droid: $DROID
- Duration: ${EXEC_TIME}s
- Timestamp: $(date '+%Y-%m-%d %H:%M:%S')
- Working Directory: $WORK_DIR
EOF

echo "" >&2
echo "====================" >&2
echo "Completed in ${EXEC_TIME}s" >&2
echo "Output saved to: $OUTPUT_FILE" >&2
echo "====================" >&2

exit 0
