# /kln:remember - End-of-Session Knowledge Capture

Comprehensive extraction and saving of session learnings before clearing context.

**Use this command at the END of a productive session, before running `/clear` or `/compact`.**

## Difference from SaveThis

| SaveThis | /kln:remember |
|----------|---------------|
| Single insight during work | Full session review at end |
| Quick inline capture | Comprehensive structured extraction |
| One KB entry | Multiple entries + Serena memory |
| "Bookmark this now" | "Journal everything I learned" |

## Process

### Step 1: Review Session Accomplishments

First, understand what was done in this session:

```bash
# See uncommitted changes
git status

# See what files changed
git diff --stat

# Recent commits from this session
git log --oneline -5
```

### Step 2: Extract Learnings by Category

Review the session mentally and identify learnings in these categories:

#### Architecture & Design
- Pattern choices and WHY they were made
- System connections and dependencies discovered
- Integration points identified
- Design decisions with rationale

#### Implementation Details
- Key file locations (use file:line format)
- Upstream/downstream dependencies
- Configuration requirements discovered
- API contracts or interfaces

#### Decisions & Trade-offs
- What was decided and WHY
- Alternatives that were considered
- Constraints that influenced the choice
- Future implications

#### Gotchas & Warnings
- Problems encountered during the session
- Solutions that worked
- Things to AVOID in the future
- Edge cases discovered

#### Testing Insights
- Test patterns that were effective
- Edge cases that need testing
- Test data requirements
- Coverage gaps identified

### Step 3: Save to Knowledge DB

For each significant learning, save using knowledge-capture.py:

```bash
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-capture.py \
    "<concise description of the learning>" \
    --type <type> \
    --tags "<tag1>,<tag2>" \
    --priority <priority>
```

**Types:**
- `lesson` - General learning or insight
- `finding` - Discovery during exploration
- `solution` - Working fix for a specific problem
- `pattern` - Reusable approach or technique
- `warning` - Gotcha or thing to avoid
- `best-practice` - Recommended approach

**Priorities:**
- `low` - Nice to know
- `medium` - Generally useful (default)
- `high` - Important for this project
- `critical` - Must remember, affects correctness

### Step 4: Save Critical Knowledge to Serena Memory

For architectural decisions or critical patterns that should persist across ALL sessions, also save to Serena:

```
Use mcp__serena__edit_memory to append to 'lessons-learned':

### <Title>
**Date**: <today>
**Context**: <what led to this>
**Learning**: <the insight>
**Impact**: <why it matters>
```

### Step 5: Verify and Clear

1. **Verify saves worked:**
   ```
   FindKnowledge <topic from session>
   ```

2. **Check Serena memory:**
   ```
   Use mcp__serena__read_memory for 'lessons-learned'
   ```

3. **Clear context when ready:**
   - `/compact` - Keep some context, compress the rest
   - `/clear` - Full reset (use after /kln:remember)

## Example Output

```
/kln:remember

📋 Reviewing session...

Git status shows 3 modified files in hooks/
Recent commits: "Fix SaveThis hook interface"

🧠 Extracting learnings...

**Architecture (1 item):**
- Hook system design: handlers should be modular, one concern per file

**Gotchas (2 items):**
- Hooks MUST exit 0 even on error, or Claude hangs
- Use jq -Rs for proper JSON escaping in bash

**Solutions (1 item):**
- knowledge-capture.py with argparse handles all SaveThis variations

💾 Saving to Knowledge DB...

✅ Saved: "Hook handlers should be modular..." (pattern, hooks)
✅ Saved: "Hooks must exit 0 even on error..." (warning, hooks,critical)
✅ Saved: "Use jq -Rs for JSON escaping..." (solution, bash,json)
✅ Saved: "knowledge-capture.py argparse pattern..." (solution, hooks)

📝 Updating Serena memory (lessons-learned)...

✅ Appended critical gotcha to lessons-learned

Session learnings captured. Ready for /clear when you are.
```

## Quick Reference

```bash
# Save a lesson
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-capture.py \
    "Description here" --type lesson --tags tag1,tag2

# Save a warning (critical)
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-capture.py \
    "Don't do X because Y" --type warning --tags gotcha --priority critical

# Save a solution
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-capture.py \
    "Fixed Z by doing W" --type solution --tags topic1,topic2

# Verify saves
FindKnowledge <search term>
```
