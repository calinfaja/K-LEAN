# K-LEAN

**Style:**
- NEVER use emojis in code, commits, or responses unless explicitly requested

**Suggest these when:**
- After significant code changes → `/kln:quick`
- Stuck debugging 10+ min → `/kln:rethink`
- Need thorough review → `/kln:multi`
- Found useful info during work → `/kln:learn`
- End of session → `/kln:remember`
- "How did we solve X before?" → `FindKnowledge <query>`

**Knowledge Commands:**
- `/kln:learn` - Extract learnings from current context (mid-session)
- `/kln:learn "topic"` - Focused extraction on specific topic
- `/kln:remember` - Comprehensive end-of-session capture

**Hook Keywords (type directly):**
- `FindKnowledge <query>` - Search knowledge DB
- `SaveInfo <url>` - Evaluate URL with LLM and save if relevant

**Script Syntax (when calling directly):**
```bash
# Knowledge capture - NO "add" subcommand
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-capture.py \
    "lesson text" --type lesson --tags tag1,tag2 --priority medium

# Types: lesson, finding, solution, pattern, warning, best-practice
# Priority: low, medium, high, critical

# Search
~/.claude/scripts/knowledge-query.sh "<query>"
```

**CLI:** `kln status` | `kln doctor -f` | `kln model list`

**Help:** `/kln:help`
