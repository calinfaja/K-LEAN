# K-LEAN Improvement Guide: Lessons from claude-codepro

**Date**: 2025-12-15
**Purpose**: Detailed implementation guide for priority improvements

---

## Table of Contents
1. [Priority Improvements Implementation](#priority-improvements)
2. [Hook System Improvements](#hook-improvements)
3. [MCP Servers Explained](#mcp-servers)

---

## Priority Improvements Implementation {#priority-improvements}

### 1. Context Monitor Hook (Priority: CRITICAL)

**What it does:**
Monitors Claude's context window usage and warns you before you run out of space. Without this, you can lose work when context fills up unexpectedly.

**How it helps:**
- Prevents lost work from context overflow
- Enables proactive context management
- Warns at 85% (caution) and 95% (critical) thresholds
- Allows time to `/compact` or save state before overflow

**Implementation:**

Create `~/.claude/hooks/context-monitor-hook.sh`:
```bash
#!/bin/bash
#
# Context Monitor Hook - PostToolUse
# Warns at 85% and 95% context usage
#

INPUT=$(cat)

# Extract context info from Claude's response metadata
# Note: Actual implementation depends on Claude's context reporting
CONTEXT_USED=$(echo "$INPUT" | jq -r '.context_used // 0' 2>/dev/null)
CONTEXT_MAX=$(echo "$INPUT" | jq -r '.context_max // 200000' 2>/dev/null)

if [ "$CONTEXT_USED" != "0" ] && [ "$CONTEXT_USED" != "null" ]; then
    PERCENT=$((CONTEXT_USED * 100 / CONTEXT_MAX))

    if [ "$PERCENT" -ge 95 ]; then
        echo "{\"systemMessage\": \"🚨 CRITICAL: Context at ${PERCENT}%! Run /compact or /clear NOW to avoid losing work.\"}"
    elif [ "$PERCENT" -ge 85 ]; then
        echo "{\"systemMessage\": \"⚠️ WARNING: Context at ${PERCENT}%. Consider running /compact or saving important state.\"}"
    fi
fi

exit 0
```

**Alternative: Tool-count based estimation:**
```bash
#!/bin/bash
# Estimate context by counting tool calls in session
# Simpler but less accurate

TOOL_COUNT_FILE="/tmp/claude-tool-count-$$"
if [ -f "$TOOL_COUNT_FILE" ]; then
    COUNT=$(cat "$TOOL_COUNT_FILE")
else
    COUNT=0
fi

COUNT=$((COUNT + 1))
echo "$COUNT" > "$TOOL_COUNT_FILE"

# Rough estimate: warn after 50 tool calls (typical session)
if [ "$COUNT" -ge 80 ]; then
    echo "{\"systemMessage\": \"🚨 CRITICAL: ~${COUNT} tool calls. Context likely near limit. Consider /compact.\"}"
elif [ "$COUNT" -ge 50 ]; then
    echo "{\"systemMessage\": \"⚠️ ~${COUNT} tool calls. Monitor context usage.\"}"
fi

exit 0
```

**Add to settings.json:**
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/context-monitor-hook.sh",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

---

### 2. /kln:remember Command (Priority: HIGH)

**What it does:**
Saves session learnings to the knowledge database in a structured format before clearing context. Enables continuity across sessions.

**How it helps:**
- Preserves architectural decisions across sessions
- Captures gotchas and solutions before they're lost
- Enables `/clear` without losing critical knowledge
- Structured format makes retrieval easier

**Implementation:**

Create `~/.claude/commands/kln/remember.md`:
```markdown
# /kln:remember - Save Session Learnings

Save important session learnings to the knowledge database before clearing context.

## Process

1. **Review Session**: Use `git status` and `git diff` to assess what was accomplished
2. **Identify Learnings**: Focus on knowledge with lasting value:
   - Architecture & Design decisions
   - Implementation patterns that worked
   - Critical file locations and entry points
   - Gotchas and their solutions
   - Testing insights

3. **Save to Knowledge DB**: For each learning, use this format:

```bash
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-capture.py \
    "<concise description>" \
    --type <lesson|finding|solution|pattern|warning|best-practice> \
    --tags "<tag1>,<tag2>" \
    --priority <low|medium|high|critical>
```

## Categories to Capture

### Architecture & Design
- Why patterns were chosen over alternatives
- System connections and dependencies
- Integration points

### Implementation Details
- File references with line numbers
- Upstream/downstream impacts
- Configuration requirements

### Decisions & Trade-offs
- What was decided and WHY
- Alternatives considered
- Constraints that influenced decisions

### Gotchas & Solutions
- Problems encountered
- How they were solved
- Prevention strategies

### Testing Insights
- Effective test patterns
- Edge cases discovered
- Test data requirements

## Example

```bash
# Save an architectural decision
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-capture.py \
    "Use txtai for embeddings because it has SQLite backend, no external DB needed" \
    --type decision \
    --tags "architecture,knowledge-db,txtai" \
    --priority high

# Save a gotcha
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-capture.py \
    "Hook scripts must exit 0 even on error, otherwise Claude hangs" \
    --type warning \
    --tags "hooks,gotcha" \
    --priority critical
```

After saving all learnings, you can safely run `/clear` and continue with `/compact` context.
```

---

### 3. Modular Rules Separation (Priority: MEDIUM-HIGH)

**What it does:**
Separates rules into `standard/` (auto-updated) and `custom/` (preserved) directories, so updates don't overwrite your project-specific rules.

**How it helps:**
- Updates don't destroy custom rules
- Clear separation of concerns
- Easier to share standard rules across projects
- Custom rules are always preserved

**Implementation:**

**Step 1: Create directory structure:**
```bash
mkdir -p ~/.claude/rules/standard
mkdir -p ~/.claude/rules/custom
```

**Step 2: Move existing rules:**
```bash
# Move framework rules to standard/
mv ~/.claude/rules/tdd-enforcement.md ~/.claude/rules/standard/
mv ~/.claude/rules/context-management.md ~/.claude/rules/standard/
mv ~/.claude/rules/code-quality.md ~/.claude/rules/standard/

# Move project-specific rules to custom/
mv ~/.claude/rules/project-conventions.md ~/.claude/rules/custom/
mv ~/.claude/rules/my-preferences.md ~/.claude/rules/custom/
```

**Step 3: Update install.sh to respect custom/:**
```bash
# In install.sh, add:
install_rules() {
    # Update standard rules (overwrite OK)
    cp -r "$SOURCE/rules/standard/"* ~/.claude/rules/standard/

    # Never touch custom rules
    if [ ! -d ~/.claude/rules/custom ]; then
        mkdir -p ~/.claude/rules/custom
        echo "# Add your project-specific rules here" > ~/.claude/rules/custom/.gitkeep
    fi

    echo "Standard rules updated. Custom rules preserved."
}
```

---

### 4. MCP Funnel Integration (Priority: MEDIUM)

**What it does:**
Filters which MCP tools are exposed to Claude, reducing context consumption from tool descriptions.

**How it helps:**
- Reduces context used by tool descriptions
- Allows more MCP servers without context bloat
- Selective tool exposure per task
- Cleaner tool list for Claude

**Implementation:**

**Step 1: Install MCP Funnel:**
```bash
npm install -g mcp-funnel
```

**Step 2: Create `.mcp-funnel.json`:**
```json
{
  "defaultMode": "allowlist",
  "rules": [
    {
      "server": "serena",
      "tools": [
        "find_symbol",
        "search_for_pattern",
        "get_symbols_overview",
        "read_memory",
        "write_memory"
      ]
    },
    {
      "server": "tavily",
      "tools": [
        "tavily-search",
        "tavily-extract"
      ]
    },
    {
      "server": "context7",
      "tools": [
        "resolve-library-id",
        "get-library-docs"
      ]
    }
  ]
}
```

**Step 3: Update `.mcp.json`:**
```json
{
  "mcpServers": {
    "mcp-funnel": {
      "command": "npx",
      "args": ["-y", "mcp-funnel@0.0.6"]
    }
  }
}
```

---

### 5. Cipher MCP for Cross-Session Memory (Priority: MEDIUM)

**What it does:**
Provides vector database storage for memories that persist across Claude sessions, surviving `/clear` commands.

**How it helps:**
- Memory survives `/clear` and `/compact`
- Cross-session continuity
- Vector search for relevant memories
- Automatic context injection

**Implementation:**

**Step 1: Install Cipher:**
```bash
npm install -g @byterover/cipher
```

**Step 2: Create `.cipher/config.yml`:**
```yaml
storage:
  type: local
  path: .cipher/memories

embedding:
  provider: local  # or openai
  model: all-MiniLM-L6-v2

retrieval:
  topK: 5
  threshold: 0.7
```

**Step 3: Add to `.mcp.json`:**
```json
{
  "mcpServers": {
    "cipher": {
      "command": "npx",
      "args": ["-y", "@byterover/cipher", "--mode", "mcp", "--agent", ".cipher/config.yml"]
    }
  }
}
```

**Step 4: Integration with K-LEAN:**
Create a sync script that mirrors knowledge-db entries to Cipher:
```bash
#!/bin/bash
# sync-to-cipher.sh - Sync knowledge-db to Cipher

KNOWLEDGE_DIR=".knowledge-db"
CIPHER_DIR=".cipher/memories"

# Export recent entries to Cipher format
tail -20 "$KNOWLEDGE_DIR/entries.jsonl" | while read -r entry; do
    TITLE=$(echo "$entry" | jq -r '.title')
    SUMMARY=$(echo "$entry" | jq -r '.summary')

    # Store via Cipher MCP
    # (Implementation depends on Cipher's API)
done
```

---

## Hook System Improvements {#hook-improvements}

### Current K-LEAN Hooks vs claude-codepro Hooks

| Hook Type | K-LEAN | claude-codepro | Gap |
|-----------|--------|----------------|-----|
| **UserPromptSubmit** | Keywords: healthcheck, GoodJob, SaveThis, FindKnowledge, async reviews | Not used | K-LEAN ahead |
| **PostToolUse (Bash)** | Git commit detection, timeline logging | Not used | K-LEAN ahead |
| **PostToolUse (Web)** | Auto-capture URLs, searches, Tavily | Not used | K-LEAN ahead |
| **PostToolUse (All)** | None | Context monitoring | Gap to fill |
| **Post-Edit** | None | Qlty formatting, Python linting | Gap to fill |
| **Pre-Edit** | None | TDD enforcement | Gap to fill |
| **Stop** | None | Rules supervisor (AI compliance check) | Nice to have |

### Recommended Hook Additions

#### A. Universal Context Monitor (PostToolUse - All Tools)

Add to existing hooks system:
```json
{
  "PostToolUse": [
    {
      "matcher": ".*",
      "hooks": [
        {
          "type": "command",
          "command": "~/.claude/hooks/context-monitor-hook.sh",
          "timeout": 5
        }
      ]
    }
  ]
}
```

#### B. Quality Hook (Post-Edit)

```bash
#!/bin/bash
# post-edit-quality.sh

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.file_path // ""' 2>/dev/null)

# Skip if no file
[ -z "$FILE_PATH" ] && exit 0

# Get file extension
EXT="${FILE_PATH##*.}"

case "$EXT" in
    py)
        # Python: ruff format + check
        if command -v ruff &>/dev/null; then
            ruff format "$FILE_PATH" 2>/dev/null
            ISSUES=$(ruff check "$FILE_PATH" 2>&1 | head -5)
            if [ -n "$ISSUES" ]; then
                echo "{\"systemMessage\": \"⚠️ Ruff issues:\\n$ISSUES\"}"
            fi
        fi
        ;;
    js|ts|tsx)
        # JavaScript/TypeScript: prettier + eslint
        if command -v prettier &>/dev/null; then
            prettier --write "$FILE_PATH" 2>/dev/null
        fi
        ;;
    sh)
        # Shell: shellcheck
        if command -v shellcheck &>/dev/null; then
            ISSUES=$(shellcheck "$FILE_PATH" 2>&1 | head -5)
            if [ -n "$ISSUES" ]; then
                echo "{\"systemMessage\": \"⚠️ ShellCheck:\\n$ISSUES\"}"
            fi
        fi
        ;;
esac

exit 0
```

#### C. TDD Enforcer Hook (Pre-Edit) - Advanced

```bash
#!/bin/bash
# pre-edit-tdd.sh
# Warns if editing code without a failing test

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.file_path // ""' 2>/dev/null)

# Skip test files themselves
if echo "$FILE_PATH" | grep -qE "(test_|_test\.|\.spec\.|\.test\.)"; then
    exit 0
fi

# Skip non-code files
EXT="${FILE_PATH##*.}"
case "$EXT" in
    py|js|ts|go|rs|java) ;;
    *) exit 0 ;;
esac

# Check if tests were run recently (within last 5 minutes)
LAST_TEST_RUN="/tmp/claude-last-test-run"
if [ -f "$LAST_TEST_RUN" ]; then
    LAST_RUN=$(cat "$LAST_TEST_RUN")
    NOW=$(date +%s)
    AGE=$((NOW - LAST_RUN))

    if [ "$AGE" -gt 300 ]; then
        echo "{\"systemMessage\": \"⚠️ TDD Reminder: No tests run in ${AGE}s. Consider writing/running tests first.\"}"
    fi
else
    echo "{\"systemMessage\": \"💡 TDD Tip: Write a failing test before implementing code.\"}"
fi

exit 0
```

### Improved Hook Architecture

```
~/.claude/hooks/
├── user-prompt-handler.sh      # Keywords: SaveThis, GoodJob, etc.
├── post-bash-handler.sh        # Git commits, timeline
├── post-web-handler.sh         # Auto-capture URLs
├── context-monitor-hook.sh     # NEW: Context warnings
├── post-edit-quality.sh        # NEW: Auto-format/lint
├── pre-edit-tdd.sh            # NEW: TDD reminder
└── lib/
    └── common.sh              # Shared functions
```

---

## MCP Servers Explained {#mcp-servers}

### Current K-LEAN MCP Servers

#### 1. Serena (`mcp__serena__*`)

**Purpose:** Semantic code analysis and project memory

**Key Tools:**
| Tool | Purpose |
|------|---------|
| `find_symbol` | Find code symbols by name pattern |
| `get_symbols_overview` | Get file structure without reading full content |
| `search_for_pattern` | Regex search across codebase |
| `read_memory` / `write_memory` | Persistent project memories |
| `find_referencing_symbols` | Find all usages of a symbol |
| `replace_symbol_body` | Semantic code editing |

**Why It's Valuable:**
- Token-efficient code exploration (don't read full files)
- Persistent memories across sessions
- Semantic understanding of code structure

#### 2. Tavily (`mcp__tavily__*`)

**Purpose:** AI-powered web search and content extraction

**Key Tools:**
| Tool | Purpose |
|------|---------|
| `tavily-search` | Web search with AI summarization |
| `tavily-extract` | Extract content from URLs |

**Why It's Valuable:**
- Better than raw web search (AI-filtered results)
- Handles JavaScript-heavy sites
- Returns structured, relevant content

#### 3. Context7 (`mcp__context7__*`)

**Purpose:** Up-to-date library documentation retrieval

**Key Tools:**
| Tool | Purpose |
|------|---------|
| `resolve-library-id` | Find library ID for documentation |
| `get-library-docs` | Fetch current documentation |

**Why It's Valuable:**
- Always current documentation (not training data)
- Covers many popular libraries
- Code examples and API references

#### 4. Sequential Thinking (`mcp__sequential-thinking__*`)

**Purpose:** Structured reasoning for complex problems

**Key Tools:**
| Tool | Purpose |
|------|---------|
| `sequentialthinking` | Step-by-step reasoning with revision |

**Why It's Valuable:**
- Forces deliberate thinking
- Supports branching and revision
- Good for complex architectural decisions

---

### claude-codepro MCP Servers (For Reference)

#### 1. Cipher

**Purpose:** Cross-session vector memory

**Why They Use It:**
- Memory survives `/clear`
- Vector search for relevant memories
- Structured storage (Architecture, Decisions, Gotchas)

**K-LEAN Equivalent:** Our knowledge-db + txtai (but doesn't survive /clear)

#### 2. Claude Context (Zilliz)

**Purpose:** Semantic code search

**Why They Use It:**
- Find relevant code without full file reads
- Embeddings-based code retrieval

**K-LEAN Equivalent:** Serena's `find_symbol` and `search_for_pattern`

#### 3. Exa

**Purpose:** AI-powered web search

**Why They Use It:**
- Code-aware web search
- Better than raw search for technical queries

**K-LEAN Equivalent:** Tavily (similar capability)

#### 4. MCP Funnel

**Purpose:** Tool filtering

**Why They Use It:**
- Reduce context from tool descriptions
- Allow many MCP servers without bloat
- Selective tool exposure

**K-LEAN Gap:** We don't have this - should add if using many MCPs

---

### Recommended MCP Configuration for K-LEAN

```json
{
  "mcpServers": {
    "serena": {
      "command": "uvx",
      "args": ["--from", "serena-ai", "serena", "--config", "..."]
    },
    "tavily": {
      "command": "npx",
      "args": ["-y", "@tavily/mcp-server"]
    },
    "context7": {
      "command": "npx",
      "args": ["-y", "@context7/mcp-server"]
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "cipher": {
      "command": "npx",
      "args": ["-y", "@byterover/cipher", "--mode", "mcp", "--agent", ".cipher/config.yml"],
      "comment": "ADD THIS: Cross-session memory"
    },
    "mcp-funnel": {
      "command": "npx",
      "args": ["-y", "mcp-funnel@0.0.6"],
      "comment": "ADD THIS: Tool filtering"
    }
  }
}
```

---

## Summary: What to Implement First

| Priority | Item | Effort | Impact | Status |
|----------|------|--------|--------|--------|
| 1 | Context Monitor Hook | 1 hour | Prevents lost work | TODO |
| 2 | /kln:remember command | 1 hour | Uses existing KB | TODO |
| 3 | Modular rules separation | 30 min | Better updates | TODO |
| 4 | Post-edit quality hook | 2 hours | Auto-formatting | TODO |
| 5 | MCP Funnel | 1 hour | Reduce context | TODO |
| 6 | Cipher MCP | 4 hours | Cross-session memory | TODO |
| 7 | TDD enforcer hook | 2 hours | Better discipline | TODO |

**Start with #1 and #2** - they provide immediate value with minimal effort.
