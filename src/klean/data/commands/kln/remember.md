---
name: remember
description: "Reviews git status/diff/log, extracts learnings by category (warnings/patterns/solutions), saves to Knowledge DB via knowledge-capture.py, and appends index to Serena lessons-learned. Use at session end before /clear."
allowed-tools: Bash, Read, Grep, mcp__serena__read_memory, mcp__serena__edit_memory
argument-hint: "[optional focus area]"
---

# /kln:remember - End-of-Session Knowledge Capture

Comprehensive extraction and saving of session learnings before clearing context.

## When to Use

- End of productive session, before `/clear` or `/compact`
- After solving tricky problems worth remembering
- When you've learned reusable patterns or gotchas
- Before closing a long debugging session

**NOT for:**
- Mid-session (wait until ready to clear context)
- Mid-session learnings → use `/kln:learn` instead
- Code review → use `/kln:quick`, `/kln:multi`, or `/kln:agent`

**Use this command at the END of a productive session, before running `/clear` or `/compact`.**

## Why This Works (Research-Backed)

Based on cognitive science research:
- **Spaced Retrieval** (Cohen's d = 0.38-1.41): Summaries trigger active recall
- **Progressive Summarization**: Hub notes index atomic entries
- **Zettelkasten Method**: Atomic notes (KB) linked from index (Serena)
- **Cognitive Load Theory**: Short summaries reduce mental overhead

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

Review the session and identify learnings in these categories:

#### Architecture & Design
- Pattern choices and WHY they were made
- System connections and dependencies discovered
- Design decisions with rationale

#### Gotchas & Warnings
- Problems encountered during the session
- Solutions that worked
- Things to AVOID in the future

#### Solutions & Patterns
- Working fixes for specific problems
- Reusable approaches or techniques

### Step 3: Save to Knowledge DB

For each significant learning, save using knowledge-capture.py:

The knowledge-capture.py script saves entries via TCP to the KB server.

**Format**: `"<concise description>" --type <type> --tags "<tags>" --priority <priority>`

**Types:** `lesson`, `finding`, `solution`, `pattern`, `warning`, `best-practice`

**Priorities:** `low`, `medium`, `high`, `critical`

**IMPORTANT**: Track what you save for the summary:
- Count entries by type (warnings, patterns, solutions, etc.)
- Collect all unique tags used
- Identify the single most important insight

### Step 4: Generate Auto-Summary for Serena

**This is the key step that links KB entries to Serena for future retrieval.**

After saving KB entries, append a lightweight summary to Serena's `lessons-learned`:

```markdown
### Remember: YYYY-MM-DD HH:MM
**Topics**: tag1, tag2, tag3, tag4
**Captured**: N KB entries (X warnings, Y patterns, Z solutions)
**Key insight**: [One sentence - the most important thing learned]
→ Search KB: "keyword1" "keyword2" "keyword3"
```

Use bash to append (Serena edit can be unreliable with regex):

```bash
cat >> ~/claudeAgentic/.serena/memories/lessons-learned.md << 'EOF'

---

### Remember: 2025-12-17 15:30
**Topics**: hooks, knowledge-db, jsonl, session-start
**Captured**: 5 KB entries (2 warnings, 2 patterns, 1 solution)
**Key insight**: SessionStart hook needs both startup+resume matchers
→ Search KB: "SessionStart" "per-project" "JSONL"
EOF
```

**Why this format works:**
- **Topics**: Enable future keyword search in Serena
- **Captured count**: Know something exists without reading all
- **Key insight**: Triggers spaced retrieval (forces you to recall details)
- **Search KB line**: Direct prompts for finding the atomic notes

### Step 5: Save Critical Knowledge (Optional)

For architectural decisions that need full detail in Serena (not just summary):

```markdown
### <Title>
**Date**: <today>
**Context**: <what led to this>
**Learning**: <the insight>
**Impact**: <why it matters>
```

### Step 6: Sync Serena Lessons → Knowledge DB (NEW)

**This is the bridge that makes Serena lessons searchable by SmolKLN agents.**

After updating Serena, sync the lessons to Knowledge DB so agents can find them:

```python
# Run this Python snippet to sync
import sys
sys.path.insert(0, str(__import__('pathlib').Path.home() / '.claude' / 'scripts'))
from knowledge_db import KnowledgeDB

# Read Serena lessons-learned
serena_path = __import__('pathlib').Path.home() / 'claudeAgentic' / '.serena' / 'memories' / 'lessons-learned.md'
if serena_path.exists():
    content = serena_path.read_text()

    # Import to KB using the bridge function
    sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent.parent / 'src' / 'klean' / 'smol'))
    from memory import AgentMemory
    from context import gather_project_context

    ctx = gather_project_context()
    mem = AgentMemory(ctx)
    synced = mem.sync_serena_to_kb(content)
    print(f"[OK] Synced {synced} Serena lessons to Knowledge DB")
```

Or use the quick bash command:
```bash
# Quick sync command
~/.venvs/knowledge-db/bin/python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / '.claude' / 'scripts'))

# Read Serena
serena_file = Path.home() / 'claudeAgentic' / '.serena' / 'memories' / 'lessons-learned.md'
if not serena_file.exists():
    print('No Serena lessons-learned found')
    exit(0)

content = serena_file.read_text()

# Parse and sync
from knowledge_db import KnowledgeDB
db = KnowledgeDB()

synced = 0
current_lesson = {}
current_content = []

for line in content.split('\n'):
    if line.startswith('### '):
        if current_lesson.get('title'):
            try:
                db.add_structured({
                    'title': current_lesson['title'],
                    'summary': '\n'.join(current_content).strip()[:1000],
                    'type': current_lesson.get('type', 'lesson'),
                    'source': 'serena',
                    'tags': ['serena', 'lessons-learned'],
                    'quality': 'high',
                })
                synced += 1
            except: pass

        header = line[4:].strip()
        lesson_type = 'lesson'
        if header.startswith('GOTCHA:'): lesson_type, header = 'warning', header[7:].strip()
        elif header.startswith('TIP:'): lesson_type, header = 'tip', header[4:].strip()
        elif header.startswith('PATTERN:'): lesson_type, header = 'pattern', header[8:].strip()
        current_lesson = {'title': header, 'type': lesson_type}
        current_content = []
    elif current_lesson.get('title'):
        current_content.append(line)

# Save last
if current_lesson.get('title'):
    try:
        db.add_structured({
            'title': current_lesson['title'],
            'summary': '\n'.join(current_content).strip()[:1000],
            'type': current_lesson.get('type', 'lesson'),
            'source': 'serena',
            'tags': ['serena', 'lessons-learned'],
            'quality': 'high',
        })
        synced += 1
    except: pass

print(f'[OK] Synced {synced} Serena lessons to Knowledge DB')
"
```

**Why this matters:**
- SmolKLN agents can now search Serena lessons via `knowledge_search`
- Your curated cross-project wisdom becomes available to all agents
- Agents learn from your documented gotchas, patterns, and solutions

### Step 7: Verify and Clear

1. **Verify KB saves:**
   ```
   FindKnowledge <topic from session>
   ```

2. **Verify Serena lessons synced:**
   ```
   FindKnowledge serena lessons
   ```

3. **Check Serena summary was added:**
   ```
   tail -20 ~/claudeAgentic/.serena/memories/lessons-learned.md
   ```

4. **Clear context when ready:**
   - `/compact` - Keep some context, compress the rest
   - `/clear` - Full reset (use after /kln:remember)

## Example Output

```
/kln:remember

 Reviewing session...

Git shows 6 files changed across hooks/, scripts/, settings.json
Recent commits: "Fix SessionStart for resume", "Add kb-doctor.sh"

 Extracting learnings...

**Warnings (2):**
- SessionStart hook needs BOTH startup+resume matchers
- Cross-platform paths differ between Windows/Linux/macOS

**Patterns (2):**
- Per-project KB servers with TCP port (14000 + hash offset)
- Python entry points work cross-platform via pipx

**Solutions (1):**
- `kln doctor -f` diagnoses and auto-repairs KB issues

 Saving to Knowledge DB...

[OK] Saved 5 entries to .knowledge-db/entries.jsonl

 Generating Serena auto-summary...

---
### Remember: 2025-12-17 15:45
**Topics**: hooks, knowledge-db, jsonl, session-start, kb-doctor
**Captured**: 5 KB entries (2 warnings, 2 patterns, 1 solution)
**Key insight**: SessionStart hook needs both startup+resume matchers for --resume to work
→ Search KB: "SessionStart" "per-project" "JSONL" "kb-doctor"
---

[OK] Appended to lessons-learned

🔄 Syncing Serena → Knowledge DB...

📖 Reading Serena: ~/claudeAgentic/.serena/memories/lessons-learned.md
   Found 25 lessons
📚 Knowledge DB: .knowledge-db
  [OK] [warning] Thinking models need longer timeouts
  [OK] [tip] Simpler CLI for knowledge_db.py
  [OK] [pattern] docs/ folder organization
  ... (22 more)
[OK] Synced 25 Serena lessons to Knowledge DB
   SmolKLN agents can now search these lessons!

 Session learnings captured. Ready for /clear when you are.

After /clear, you can:
- See summary: Read lessons-learned in Serena
- Get details: FindKnowledge <topic>
- Agents can search: knowledge_search("gotcha timeouts")
```

## Quick Reference

```bash
# Save entries (track counts!)
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-capture.py \
    "Description" --type warning --tags tag1,tag2 --priority critical

# Append summary to Serena
cat >> ~/claudeAgentic/.serena/memories/lessons-learned.md << 'EOF'

---

### Remember: $(date '+%Y-%m-%d %H:%M')
**Topics**: topic1, topic2
**Captured**: N KB entries (breakdown)
**Key insight**: Most important learning
→ Search KB: "keyword1" "keyword2"
EOF

# Verify
FindKnowledge <topic>
tail -20 ~/claudeAgentic/.serena/memories/lessons-learned.md
```

## After /clear - How to Use

When starting a new session after /clear:

1. **Quick check**: `tail -30 ~/claudeAgentic/.serena/memories/lessons-learned.md`
2. **See recent summaries**: Look for `### Remember:` entries
3. **Retrieve details**: Use the `→ Search KB:` keywords with FindKnowledge
4. **Read full Serena memory**: `mcp__serena__read_memory lessons-learned`

The summary acts as an **index** - you know WHAT was captured and WHERE to find details.
