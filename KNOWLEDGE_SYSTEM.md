# Semantic Knowledge System

A per-project semantic knowledge database using txtai for storing and retrieving research findings, solutions, and lessons learned.

## Overview

```
┌─────────────────────────────────────────────────────────────────┐
│  KNOWLEDGE CAPTURE FLOW                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Claude finds something valuable                                │
│         │                                                       │
│         ▼                                                       │
│  Manual: "GoodJob <url>" or Auto: PostToolUse hook             │
│         │                                                       │
│         ▼                                                       │
│  Haiku extracts structured data (title, summary, etc.)         │
│         │                                                       │
│         ▼                                                       │
│  /project/.knowledge-db/                                        │
│  ├── index/         # txtai vector embeddings                  │
│  └── entries.jsonl  # Human-readable backup                    │
│         │                                                       │
│         ▼                                                       │
│  Semantic search: "FindKnowledge <query>"                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Installation

```bash
# Create venv (already done)
python3 -m venv ~/.venvs/knowledge-db

# Install txtai
~/.venvs/knowledge-db/bin/pip install txtai[database,ann]
```

## Project Setup

Create `.knowledge-db/` in your project root:

```bash
mkdir -p .knowledge-db
```

The system auto-detects projects by looking for `.serena/`, `.claude/`, or `.knowledge-db/` directories.

## Usage

### Manual Capture

In Claude prompt:
```
GoodJob https://docs.nordicsemi.com/ble
GoodJob https://example.com focus on security patterns
SaveThis learned that connection pooling improves performance 10x
```

### Search Knowledge

In Claude prompt:
```
FindKnowledge BLE power optimization
```

CLI:
```bash
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-search.py "query"
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-search.py "query" --format inject
```

### Database Commands

```bash
# Stats
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge_db.py stats

# Search
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge_db.py search "query"

# List recent
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge_db.py recent

# Add entry
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge_db.py add '{"title": "...", "summary": "..."}'

# Rebuild index from JSONL
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge_db.py rebuild
```

## Data Schema

```json
{
  "id": "uuid",
  "title": "Short descriptive title",
  "summary": "What was found (2-3 sentences)",
  "type": "web|code|solution|lesson",
  "url": "https://source-url",
  "problem_solved": "What problem this solves",
  "key_concepts": ["keyword1", "keyword2"],
  "relevance_score": 0.0-1.0,
  "what_worked": "For solutions: what worked",
  "constraints": "Limitations or caveats",
  "found_date": "ISO timestamp"
}
```

## Files

### Scripts (`~/.claude/scripts/`)

| File | Purpose |
|------|---------|
| `knowledge_db.py` | Core KnowledgeDB class and CLI |
| `knowledge-search.py` | Search interface with output formats |
| `knowledge-extract.sh` | Haiku extraction wrapper |
| `goodjob-dispatch.sh` | Manual capture hook handler |
| `auto-capture-hook.sh` | Auto-capture PostToolUse hook |

### Configuration

`~/.claude/settings.json` hooks:
- `UserPromptSubmit`: GoodJob, SaveThis, FindKnowledge keywords
- `PostToolUse (WebFetch)`: Auto-capture valuable web findings
- `PostToolUse (WebSearch)`: Auto-capture search results

### Project Structure

```
/your-project/
├── .knowledge-db/
│   ├── index/           # txtai embeddings (SQLite)
│   └── entries.jsonl    # Human-readable backup
├── .serena/             # Serena memories
└── .claude/             # Project Claude config
```

## Integration

### Headless Agents

Review scripts automatically search knowledge DB:
- `quick-review.sh`
- `second-opinion.sh`
- `consensus-review.sh`

They inject relevant knowledge into the system prompt.

### Serena

Knowledge entries can reference Serena memories via `project_context` field.
Use the template at `~/.claude/templates/serena-knowledge-memory.md`.

## Search Formats

```bash
# Detailed (default)
knowledge-search.py "query" --format detailed

# Compact
knowledge-search.py "query" --format compact

# For injection into prompts
knowledge-search.py "query" --format inject

# JSON
knowledge-search.py "query" --json
```

## Maintenance

### Rebuild Index

If the index gets corrupted or out of sync:

```bash
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge_db.py rebuild
```

This reads `entries.jsonl` and rebuilds the txtai index.

### Storage

- ~3.5KB per entry (metadata + embedding)
- 1000 entries = ~3.5MB
- No practical storage concerns

## Troubleshooting

**"Knowledge database not available"**
- Make sure you're in a project directory with `.knowledge-db/`, `.serena/`, or `.claude/`

**"txtai not installed"**
- Run: `~/.venvs/knowledge-db/bin/pip install txtai[database,ann]`

**Search returns wrong results**
- Run rebuild: `knowledge_db.py rebuild`

**Hooks not triggering**
- Check `~/.claude/settings.json` for hook configuration
- Verify scripts are executable: `chmod +x ~/.claude/scripts/*.sh`
