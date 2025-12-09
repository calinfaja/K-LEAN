# Knowledge System

Semantic knowledge database for storing and retrieving valuable information discovered during development.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE SYSTEM                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Storage Layer                                                   │
│  ├── entries.jsonl     - All knowledge entries (JSONL format)   │
│  ├── timeline.txt      - Chronological event log                │
│  └── index/            - txtai embeddings for semantic search   │
│                                                                  │
│  Server Layer                                                    │
│  └── knowledge-server.py - Daemon keeps embeddings in memory    │
│      └── Socket: /tmp/knowledge-server.sock                     │
│      └── Fast queries: ~30ms (vs ~17s cold start)               │
│                                                                  │
│  Capture Methods                                                 │
│  ├── Manual: GoodJob <url>, SaveThis <lesson>                   │
│  ├── Auto: PostToolUse hooks on WebFetch/WebSearch              │
│  └── Review: fact-extract.sh after reviews and commits          │
│                                                                  │
│  Query Methods                                                   │
│  ├── Keyword: FindKnowledge <query>                             │
│  ├── Script: knowledge-query.sh (via server)                    │
│  └── Direct: knowledge-search.py (cold start)                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Per-Project Storage

Each project has its own knowledge database:

```
<project>/
└── .knowledge-db/
    ├── entries.jsonl    # Knowledge entries
    ├── timeline.txt     # Event timeline
    └── index/           # txtai search index
```

This keeps project-specific knowledge isolated and portable.

## Entry Schema

```json
{
  "title": "Short descriptive title",
  "summary": "What was found/learned",
  "type": "web|code|solution|lesson",
  "url": "Source URL if applicable",
  "source": "manual|auto|review|commit",
  "problem_solved": "What problem this solves",
  "key_concepts": ["searchable", "keywords"],
  "tags": ["category", "tags"],
  "relevance_score": 0.8,
  "what_worked": "For solutions",
  "constraints": "Limitations discovered",
  "timestamp": "2024-12-09T14:30:00Z"
}
```

## Capture Methods

### Manual Capture

**GoodJob** - Capture valuable URLs:
```bash
GoodJob https://docs.example.com/api
GoodJob https://blog.example.com/tutorial focus on authentication section
```

**SaveThis** - Capture lessons learned:
```bash
SaveThis connection pooling improves database performance 10x
SaveThis always validate user input before SQL queries
```

### Automatic Capture

PostToolUse hooks automatically capture knowledge from:
- WebFetch results
- WebSearch results

**Hook:** `~/.claude/hooks/post-tool-use.sh`

### Review Extraction

After each review or commit, `fact-extract.sh` extracts:
- Patterns discovered
- Issues found
- Solutions implemented
- Best practices noted

## Query Methods

### Keyword Search (User)

```bash
FindKnowledge authentication patterns
FindKnowledge database optimization
```

### Fast Query (via Server)

```bash
~/.claude/scripts/knowledge-query.sh "security best practices"
```

**Output:**
```
⚡ Search time: 126.02ms

[0.85] Authentication Best Practices
      Use bcrypt for password hashing, JWT for sessions...

[0.72] Input Validation Patterns
      Always sanitize user input before database queries...
```

### Direct Query (Cold Start)

```bash
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-search.py "query" --format inject
```

Use `--format inject` to get context suitable for LLM prompts.

## Knowledge Server

The server daemon keeps txtai embeddings in memory for fast queries.

### Auto-Start

Configured in `~/.bashrc` to start on terminal open:
```bash
# Check if running
ls -la /tmp/knowledge-server.sock

# Manual start
cd ~/claudeAgentic && ~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-server.py start &

# Stop
~/.claude/scripts/knowledge-server.py stop
```

### Performance

| Method | Time |
|--------|------|
| Via server | ~30ms |
| Cold start | ~17s |

## Timeline System

Chronological log of all significant events:

```
<project>/.knowledge-db/timeline.txt
```

### Format

```
MM-DD HH:MM | type | description
12-08 17:30 | review | security audit (3 facts, score: 0.8)
12-08 17:45 | commit | abc123: Fix XSS vulnerability
12-09 14:45 | lesson | Test entry for edge cases
```

### Query Timeline

```bash
# Today's events
~/.claude/scripts/timeline-query.sh today

# This week
~/.claude/scripts/timeline-query.sh week

# All commits
~/.claude/scripts/timeline-query.sh commits

# All reviews
~/.claude/scripts/timeline-query.sh reviews

# Search term
~/.claude/scripts/timeline-query.sh security
```

## Integration with Reviews

Reviews automatically integrate with knowledge:

1. **Before review:** Search for relevant prior knowledge
2. **Inject context:** Add findings to system prompt
3. **After review:** Extract facts and store

```bash
# In review output
📚 Found relevant prior knowledge
```

## Rebuilding Index

After adding many entries, rebuild the semantic search index:

```bash
cd <project> && ~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge_db.py rebuild
```

**Note:** New entries work immediately via grep fallback, but semantic search benefits from index rebuild.

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `knowledge_db.py` | Core database operations |
| `knowledge-search.py` | Search with formatting options |
| `knowledge-query.sh` | Fast query via server |
| `knowledge-server.py` | Daemon for fast queries |
| `fact-extract.sh` | Extract facts from text |
| `timeline-query.sh` | Query timeline events |
| `goodjob-dispatch.sh` | Handle GoodJob captures |

## Troubleshooting

### Search returns nothing
```bash
# Check entries exist
wc -l .knowledge-db/entries.jsonl

# Try grep fallback (bypasses embeddings)
grep -i "search term" .knowledge-db/entries.jsonl
```

### Server not responding
```bash
# Check socket exists
ls -la /tmp/knowledge-server.sock

# Restart server
~/.claude/scripts/knowledge-server.py stop
cd ~/claudeAgentic && ~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-server.py start &
```

### Slow searches
```bash
# Use server instead of direct query
~/.claude/scripts/knowledge-query.sh "query"  # Fast
# vs
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-search.py "query"  # Slow
```

### Dependencies missing
```bash
~/.venvs/knowledge-db/bin/pip install txtai sentence-transformers
```
