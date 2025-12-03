# Feature: Semantic Memory System (txtai + Serena)

## Problem Statement

When parallel agents do research (web + local disk), they find valuable information. After a few sessions, this information is lost or hard to find because:
- Serena memories are keyword-searchable only
- No semantic "find similar" capability
- Good findings get buried in files

## Goal

Create a workflow where:
1. User triggers `/hook:GoodJob` when agents find valuable info
2. System stores: source (URL/path), content, technical description
3. Later: semantic search finds related info even with different wording

---

## Solution: txtai as Semantic Index for Serena

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  SERENA + txtai Integration                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  Serena Memories (.serena/memories/)                           │
│  └── Human-readable markdown files                             │
│  └── Source of truth                                           │
│  └── Keyword search via search_for_pattern                     │
│         │                                                       │
│         │ (index/sync)                                          │
│         ▼                                                       │
│  txtai Index (~/.claude/knowledge-index/)                      │
│  └── Vector embeddings of Serena content                       │
│  └── HNSW indexing (O(log n) = fast)                          │
│  └── Semantic search capability                                │
│                                                                 │
│  SEARCH FLOW:                                                   │
│  ├── Exact match needed? → Serena                              │
│  └── "Find similar"? → txtai → returns Serena file paths       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Why txtai?

| Criteria | txtai | Mem0 | AgentDB |
|----------|-------|------|---------|
| Open source | ✅ Apache 2.0 | ✅ Apache 2.0 | ✅ MIT |
| Local/private | ✅ 100% | ⚠️ Can be | ✅ Yes |
| HNSW speed | ✅ <1ms | ✅ With Qdrant | ✅ <0.1ms |
| Simple API | ✅ 3 methods | ✅ 3 methods | ❌ 29 tools |
| Python native | ✅ Pure Python | ✅ Python | ❌ TypeScript |
| Addon to Serena | ✅ Perfect fit | ⚠️ Separate | ⚠️ Overkill |

---

## Implementation Plan

### Phase 1: Core txtai Integration

**File:** `~/.claude/scripts/serena-index.py`

```python
from txtai import Embeddings
from pathlib import Path
import frontmatter
import hashlib

class SerenaIndex:
    def __init__(self, index_path="~/.claude/knowledge-index"):
        self.index_path = Path(index_path).expanduser()
        self.embeddings = Embeddings(content=True)
        if self.index_path.exists():
            self.embeddings.load(str(self.index_path))

    def index_serena_memories(self, serena_path=".serena/memories"):
        """Index all Serena memory files"""
        documents = []
        for md_file in Path(serena_path).glob("**/*.md"):
            content = md_file.read_text()
            doc = {
                "id": hashlib.md5(str(md_file).encode()).hexdigest(),
                "text": content,
                "path": str(md_file),
                "filename": md_file.name
            }
            documents.append(doc)

        if documents:
            self.embeddings.index(documents)
            self.embeddings.save(str(self.index_path))
        return len(documents)

    def search(self, query: str, limit: int = 5):
        """Semantic search across indexed memories"""
        results = self.embeddings.search(query, limit=limit)
        return [{"score": r["score"], "path": r["path"], "text": r["text"][:200]}
                for r in results]

    def add_finding(self, source: str, description: str, content: str):
        """Add a single finding to index"""
        doc = {
            "id": hashlib.md5(f"{source}{description}".encode()).hexdigest(),
            "text": f"{description}\n\n{content}",
            "source": source,
            "description": description
        }
        self.embeddings.index([doc])
        self.embeddings.save(str(self.index_path))
```

### Phase 2: GoodJob Hook

**File:** `~/.claude/scripts/goodjob.sh`

```bash
#!/bin/bash
# Hook: Capture valuable findings

SOURCE="$1"
DESCRIPTION="$2"
CONTENT="$3"
TIMESTAMP=$(date +%Y-%m-%d-%H%M)

# 1. Write to Serena memory (human-readable)
MEMORY_FILE=".serena/memories/findings/finding-$TIMESTAMP.md"
mkdir -p "$(dirname $MEMORY_FILE)"

cat > "$MEMORY_FILE" << EOF
# Finding: $DESCRIPTION

**Source:** $SOURCE
**Date:** $(date)

## Content

$CONTENT

## Tags

- finding
- research
EOF

# 2. Index in txtai (semantic search)
python3 ~/.claude/scripts/serena-index.py add \
    --source "$SOURCE" \
    --description "$DESCRIPTION" \
    --content "$CONTENT"

echo "✅ Saved to Serena + indexed in txtai"
```

### Phase 3: Hook Configuration

**Add to:** `~/.claude/settings.json`

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/scripts/prompt-dispatch.sh"
          }
        ]
      }
    ]
  }
}
```

**Dispatch script checks for:**
- `GoodJob <source> <description>` → runs goodjob.sh
- `FindSimilar <query>` → runs txtai search
- `SyncMemories` → re-indexes Serena memories

### Phase 4: Search Integration

**Usage in Claude:**

```
# Capture finding
GoodJob "https://docs.nordicsemi.com/ble" "BLE connection interval optimization"

# Later - semantic search
FindSimilar "wireless power optimization"
# Returns: BLE finding (semantically related!)

# Re-sync after manual Serena edits
SyncMemories
```

---

## Performance Expectations

| Operation | Time | Notes |
|-----------|------|-------|
| Index 100 memories | ~5s | One-time |
| Semantic search | <1ms | HNSW |
| Add single finding | <100ms | Index + save |
| Sync all memories | ~5s | On demand |

---

## File Structure

```
~/.claude/
├── scripts/
│   ├── serena-index.py      # Core txtai integration
│   ├── goodjob.sh           # GoodJob hook
│   └── prompt-dispatch.sh   # Updated dispatcher
├── knowledge-index/         # txtai index files
│   ├── embeddings
│   └── config

.serena/memories/
├── findings/                # GoodJob findings
│   ├── finding-2024-12-02-1530.md
│   └── finding-2024-12-02-1645.md
└── (existing memories)
```

---

## Dependencies

```bash
pip install txtai
```

Optional for better performance:
```bash
pip install txtai[ann]  # HNSW acceleration
```

---

## Success Criteria

1. ✅ Can index all Serena memories in txtai
2. ✅ Semantic search returns relevant results
3. ✅ GoodJob hook saves to both Serena + txtai
4. ✅ Search time <1ms for 1000+ memories
5. ✅ Works offline, 100% local

---

## Future Enhancements

- [ ] Auto-sync on Serena memory changes (file watcher)
- [ ] MCP server wrapper for txtai (expose as tools)
- [ ] Tag extraction and filtering
- [ ] Relevance scoring thresholds
- [ ] Integration with review system (index review results)
