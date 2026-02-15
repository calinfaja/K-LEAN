# K-LEAN

**Style:**
- NEVER use emojis in code, commits, or responses unless explicitly requested

**Suggest these when:**
- After significant code changes → `/kln:quick`
- Stuck debugging 10+ min → `/kln:rethink`
- Need thorough review → `/kln:multi`
- Found useful info during work → `/kln:learn`
- End of session → `/kln:remember`
- "How did we solve X before?" → `/kln:find <query>`

**Knowledge Commands:**
- `/kln:learn` - Extract learnings from current context (mid-session)
- `/kln:learn "topic"` - Focused extraction on specific topic
- `/kln:remember` - End-of-session capture + Serena index
- `/kln:find <query>` - Search knowledge DB with hybrid semantic search

**Note**: Learnings are also captured automatically on `/compact` (PreCompact hook).

**CLI:** `kln status` | `kln doctor -f` | `kln model list`

**Help:** `/kln:help`
