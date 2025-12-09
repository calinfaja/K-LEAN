# TOON Adapter

Token-Oriented Object Notation (TOON) adapter for efficient LLM transmission of knowledge facts.

## Overview

TOON is a compact serialization format optimized for LLMs. The adapter converts knowledge facts between JSON and TOON formats, achieving ~18% character reduction.

```
┌─────────────────────────────────────────────────────────────────┐
│                      TOON ADAPTER                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  JSON Input                         TOON Output                 │
│  ┌─────────────────────┐           ┌─────────────────────┐     │
│  │ {                   │           │ [1]:                │     │
│  │   "title": "Test",  │    →      │   - title: Test     │     │
│  │   "summary": "...", │           │     summary: ...    │     │
│  │   "tags": ["a","b"] │           │     tags[2]: a, b   │     │
│  │ }                   │           │     relevance: 0.8  │     │
│  └─────────────────────┘           └─────────────────────┘     │
│                                                                  │
│  Character reduction: ~18%                                      │
│  Token savings: ~10-20% (varies by tokenizer)                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Installation

TOON is installed in the knowledge-db virtual environment:

```bash
~/.venvs/knowledge-db/bin/pip install python-toon
```

**Verify:**
```bash
~/.venvs/knowledge-db/bin/pip show python-toon
```

## Usage

### Import

```python
from toon_adapter import KnowledgeTOONAdapter
```

**Note:** Must run from the scripts directory or add to PYTHONPATH:
```bash
cd ~/claudeAgentic/review-system-backup/scripts
~/.venvs/knowledge-db/bin/python
```

### JSON to TOON

```python
from toon_adapter import KnowledgeTOONAdapter

facts = [
    {
        "title": "Authentication Pattern",
        "summary": "Use bcrypt for password hashing",
        "source": "manual",
        "tags": ["security", "auth"],
        "relevance_score": 0.9
    }
]

toon = KnowledgeTOONAdapter.json_to_toon(facts)
print(toon)
```

**Output:**
```
[1]:
  - title: Authentication Pattern
    summary: Use bcrypt for password hashing
    source: manual
    tags[2]: security, auth
    relevance_score: 0.9
```

### TOON to JSON

```python
restored = KnowledgeTOONAdapter.toon_to_json(toon)
print(restored)
# [{'title': 'Authentication Pattern', ...}]
```

### Round-Trip Validation

```python
original = [{"title": "Test", "summary": "Example", "source": "manual", "tags": ["a"], "relevance_score": 0.8}]
toon = KnowledgeTOONAdapter.json_to_toon(original)
restored = KnowledgeTOONAdapter.toon_to_json(toon)
assert original == restored  # ✅ Integrity OK
```

## API Reference

### KnowledgeTOONAdapter

Static methods for knowledge fact conversion.

#### `json_to_toon(facts: List[Dict]) -> str`

Convert list of knowledge facts to TOON format.

**Parameters:**
- `facts`: List of knowledge fact dictionaries

**Returns:** TOON-formatted string

**Required fields:** `title`, `summary`, `source`, `tags`, `relevance_score`

#### `toon_to_json(toon: str) -> List[Dict]`

Convert TOON string back to JSON facts.

**Parameters:**
- `toon`: TOON-formatted string

**Returns:** List of knowledge fact dictionaries

#### `validate(facts: List[Dict]) -> Tuple[bool, List[str]]`

Validate facts have required fields.

**Returns:** `(is_valid, list_of_errors)`

## Compression Analysis

### Character Reduction

```python
import json
from toon_adapter import KnowledgeTOONAdapter

facts = [{"title": "Test", "summary": "Example summary", "source": "manual", "tags": ["a", "b"], "relevance_score": 0.8}]

json_size = len(json.dumps(facts))
toon_size = len(KnowledgeTOONAdapter.json_to_toon(facts))
reduction = (1 - toon_size / json_size) * 100

print(f"JSON: {json_size} bytes")
print(f"TOON: {toon_size} bytes")
print(f"Reduction: {reduction:.1f}%")
```

**Typical results:**
- Small payloads: ~2-5% reduction
- Medium payloads: ~15-20% reduction
- Large payloads: ~18-25% reduction

### Token Savings

Actual token savings depend on the LLM tokenizer. Estimated 10-20% with Claude/Haiku tokenizers.

## Integration Points

### Knowledge Search Output

When injecting knowledge into prompts, TOON reduces context size:

```python
# In knowledge-search.py
if format == "toon":
    return KnowledgeTOONAdapter.json_to_toon(results)
else:
    return json.dumps(results)
```

### Review Context Injection

```bash
# In review scripts
KNOWLEDGE_CONTEXT=$(python knowledge-search.py "$FOCUS" --format toon)
```

## Schema Requirements

Required fields for knowledge facts:

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Short descriptive title |
| `summary` | string | What was found/learned |
| `source` | string | manual/auto/review/commit |
| `tags` | list | Category tags |
| `relevance_score` | float | 0.0-1.0 relevance |

Optional fields are preserved but not required for TOON conversion.

## Troubleshooting

### Module not found

```bash
# Ensure using correct Python
~/.venvs/knowledge-db/bin/python -c "from toon_adapter import KnowledgeTOONAdapter"

# If not in scripts directory
cd ~/claudeAgentic/review-system-backup/scripts
```

### python-toon not installed

```bash
~/.venvs/knowledge-db/bin/pip install python-toon
```

### Round-trip mismatch

Check that all required fields are present:
```python
facts = [{"title": "...", "summary": "...", "source": "...", "tags": [...], "relevance_score": 0.0}]
```

### Validation errors

```python
valid, errors = KnowledgeTOONAdapter.validate(facts)
if not valid:
    print("Missing fields:", errors)
```

## Script Location

```
~/claudeAgentic/review-system-backup/scripts/toon_adapter.py
```

**Note:** Also symlinked/copied to `~/.claude/scripts/toon_adapter.py` during installation.
