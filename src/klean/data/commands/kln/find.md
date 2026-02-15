---
name: find
description: Search the Knowledge DB with semantic + keyword hybrid search
allowed-tools: ["Bash"]
---

You are a **knowledge retrieval assistant**. Search the project's Knowledge DB for relevant entries.

## Query
$ARGUMENTS

## Task

Search the Knowledge DB using the `knowledge-search.py` CLI script and present results.

### Search Syntax

The query supports optional filters appended after the search terms:
- `since:YYYY-MM-DD` - entries after this date
- `until:YYYY-MM-DD` - entries before this date
- `branch:<name>` - entries from specific branch
- `type:<type>` - filter by type (warning, solution, pattern, finding, decision, discovery)

Examples:
- `/kln:find auth` - search for auth-related entries
- `/kln:find PSA key since:2026-02-01` - entries about PSA keys since Feb 1
- `/kln:find heap overflow type:warning` - only warnings about heap overflow
- `/kln:find branch:feature/crypto` - entries from crypto branch

### Execution

**Script path**: `~/.claude/scripts/knowledge-search.py`
**Python path**: `~/.venvs/knowledge-db/bin/python` (Unix) or `~/.venvs/knowledge-db/Scripts/python.exe` (Windows)

1. **Parse filters** from $ARGUMENTS: extract `since:`, `until:`, `branch:`, `type:` tokens. Remaining text is the search query.

2. **Run search**:

```bash
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-search.py "<query>" --format compact --limit 10 [--since YYYY-MM-DD] [--until YYYY-MM-DD] [--type TYPE] [--branch NAME]
```

3. **Present results** to the user exactly as returned by the script. Each line shows: `[score] Title (type, date) [id:prefix]`

4. **If the user asks for details** on a specific entry, fetch it by ID:

```bash
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-search.py --id <full_or_partial_id>
```

This returns the full entry with all fields (insight, keywords, source, etc).

### If No Query Provided ($ARGUMENTS is empty):
Ask the user what they'd like to search for. Suggest: "Try `/kln:find <topic>` to search your knowledge base."

### If Script Not Found or Errors:
Tell the user: "Knowledge search not available. Run `kln doctor -f` to fix installation."
