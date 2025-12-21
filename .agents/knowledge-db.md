# K-LEAN Knowledge Database

## Overview

The Knowledge DB provides **persistent semantic memory** across Claude Code sessions using txtai embeddings.

## Key Features

- **Per-project isolation**: Each git repo gets its own KB
- **Semantic search**: Find related knowledge by meaning, not just keywords
- **Fast queries**: Unix socket server with 1hr idle timeout
- **V2 schema**: Rich metadata for quality and provenance

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Claude Code                        │
│  "SaveThis: important insight"                       │
└─────────────────────┬───────────────────────────────┘
                      │ user-prompt-handler.sh
                      ▼
┌─────────────────────────────────────────────────────┐
│               knowledge-capture.py                   │
│  Parse → V2 Schema → Append to entries.jsonl        │
└─────────────────────┬───────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────┐
│                 .knowledge-db/                       │
│  ├── entries.jsonl     # All captured knowledge     │
│  └── index/            # Semantic embeddings        │
└─────────────────────────────────────────────────────┘
                      ▲
                      │ Unix socket query
┌─────────────────────┴───────────────────────────────┐
│              knowledge-server.py                     │
│  Socket: /tmp/kb-{md5_hash}.sock                    │
│  Idle timeout: 1 hour                               │
└─────────────────────────────────────────────────────┘
```

## V2 Schema

Each knowledge entry contains:

```json
{
  "id": "uuid",
  "found_date": "ISO8601",
  "title": "Brief title",
  "summary": "Detailed description",
  "atomic_insight": "Single clear insight",
  "key_concepts": ["concept1", "concept2"],
  "tags": ["tag1", "tag2"],
  "quality": "high|medium|low",
  "source": "manual|conversation|web|file",
  "source_path": "path/to/source",
  "relevance_score": 0.85,
  "confidence_score": 0.9
}
```

| Field | Purpose |
|-------|---------|
| `atomic_insight` | Single, self-contained insight |
| `key_concepts` | Searchable concept tags |
| `quality` | Quality level (high/medium/low) |
| `source` | Origin type (manual/conversation/web/file) |
| `relevance_score` | Semantic relevance (0-1) |

## Key Scripts

| Script | Purpose |
|--------|---------|
| `knowledge-server.py` | Socket server (per-project daemon) |
| `knowledge-query.sh` | Query via socket (auto-starts server) |
| `knowledge-capture.py` | Add entries with V2 schema |
| `knowledge-search.py` | CLI search with 4 output formats |
| `kb-doctor.sh` | Diagnose and repair KB |
| `kb-init.sh` | Initialize new project KB |
| `kb-root.sh` | Path detection utilities |

## Query Formats

```bash
# Compact (default)
~/.claude/scripts/knowledge-query.sh "search term"

# Detailed
~/.claude/scripts/knowledge-search.py --format detailed "search"

# For LLM injection
~/.claude/scripts/knowledge-search.py --format inject "search"

# JSON output
~/.claude/scripts/knowledge-search.py --format json "search"
```

## Trigger Keywords

In Claude Code prompts:

| Keyword | Action |
|---------|--------|
| `SaveThis: <text>` | Capture insight to KB |
| `SaveInfo: <text>` | Smart save with LLM evaluation |
| `FindKnowledge: <query>` | Search KB |

**Note:** Use `kb-init.sh` or `k-lean install` to initialize KB for a project.

## Socket Architecture

Each project gets a unique socket:
```
/tmp/kb-{md5(project_root)}.sock
```

Benefits:
- Fast queries (no process startup)
- Project isolation
- Auto-cleanup after 1hr idle

## Troubleshooting

### KB Not Starting
```bash
k-lean doctor --auto-fix    # Auto-repair
~/.claude/scripts/kb-doctor.sh --fix  # Manual repair
```

### Corrupted Entries
```bash
~/.claude/scripts/kb-doctor.sh  # Diagnose
# Shows: X corrupted entries, Y valid
~/.claude/scripts/kb-doctor.sh --fix  # Rebuild index
```

### Check Status
```bash
k-lean status  # Shows KB status per project
```

## Implementation Files

- Server: `src/klean/data/scripts/knowledge-server.py`
- Capture: `src/klean/data/scripts/knowledge-capture.py`
- Query: `src/klean/data/scripts/knowledge-query.sh`
- Search: `src/klean/data/scripts/knowledge-search.py`
- Doctor: `src/klean/data/scripts/kb-doctor.sh`
- Utils: `src/klean/data/scripts/kb_utils.py`

---
*See [review-system.md](review-system.md) for multi-model reviews*
