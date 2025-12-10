# TOON Integration - Technical Specification

## System Overview

### Current Flow
```
Review Analysis
    ↓
fact-extract.sh calls Haiku
    ↓
Haiku response (JSON)
    ↓
Store in entries.jsonl
    ↓
Serve to reviews via knowledge-search.py
```

### New Flow
```
Review Analysis
    ↓
fact-extract.sh calls Haiku (TOON request)
    ↓
Haiku response (TOON format) [40% fewer tokens]
    ↓
TOONConverter.toon_to_json()
    ↓
Store in entries.jsonl (unchanged)
    ↓
Serve as TOON for context (optional)
```

---

## TOON Format Specification

### For Knowledge Facts

**Table Header:**
```
# extracted_facts
```

**Column Definitions:**
```
title | summary | source | tags | relevance_score
```

**Data Row Format:**
```
Example Title     | Example summary text    | review | tag1, tag2    | 0.85
```

### Rules
1. **Pipe delimiter:** `|` separates columns
2. **Field wrapping:** Long fields wrapped to next line with indent
3. **Escaping:** Pipes inside fields escaped as `\|`
4. **Empty fields:** Rendered as blank space
5. **Multiline support:** Summary can span multiple lines with indent

### Example

```
# extracted_facts
title                        | summary                              | source | tags              | relevance_score
Namespace separation best    | Separating command namespaces        | review | namespace, org    | 0.85
practice                     | (/sc: vs /kln:) improves            |        |                   |
                             | organization and prevents conflicts  |        |                   |
Bash script organization     | Grouping related scripts in          | review | bash, scripts     | 0.80
pattern                      | ~/.claude/scripts/ with clear        |        |                   |
                             | naming improves maintainability     |        |                   |
Timeout fix for thinking     | Increased curl timeout to 120s for  | commit | timeout, bugfix   | 0.90
models                       | GLM and DeepSeek models             |        | thinking-models   |
```

---

## Implementation Components

### 1. TOON Converter Library

**File:** `~/.claude/scripts/toon_utils.py`

```python
#!/usr/bin/env python3
"""TOON format utilities for knowledge extraction."""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class TOONField:
    name: str
    value: str
    max_width: int = 30

class TOONConverter:
    """Convert between JSON and TOON formats."""

    # SCHEMA for knowledge facts
    FACT_SCHEMA = {
        'title': 30,          # max width
        'summary': 40,
        'source': 15,
        'tags': 20,
        'relevance_score': 8
    }

    @staticmethod
    def json_to_toon(facts: List[Dict], schema: Dict = None) -> str:
        """
        Convert JSON fact objects to TOON format.

        Args:
            facts: List of fact dictionaries
            schema: Column definitions {name: width, ...}

        Returns:
            TOON formatted string

        Example:
            facts = [
                {
                    'title': 'Example',
                    'summary': 'Description',
                    'source': 'review',
                    'tags': ['tag1', 'tag2'],
                    'relevance_score': 0.8
                }
            ]
            toon = TOONConverter.json_to_toon(facts)
        """
        if not facts:
            return ""

        schema = schema or TOONConverter.FACT_SCHEMA

        # Build header
        header = "# extracted_facts\n"
        columns = " | ".join(schema.keys())
        header += columns + "\n"

        # Build rows
        rows = []
        for fact in facts:
            row = TOONConverter._build_row(fact, schema)
            rows.append(row)

        return header + "\n".join(rows)

    @staticmethod
    def toon_to_json(toon_str: str, schema: Dict = None) -> List[Dict]:
        """
        Convert TOON format back to JSON facts.

        Args:
            toon_str: TOON formatted string
            schema: Column definitions (inferred from header if not provided)

        Returns:
            List of fact dictionaries

        Raises:
            ValueError: If TOON format is invalid
        """
        schema = schema or TOONConverter.FACT_SCHEMA
        lines = toon_str.strip().split('\n')

        if not lines or not lines[0].startswith('# extracted_facts'):
            raise ValueError("Invalid TOON header")

        # Parse header row (line 1)
        if len(lines) < 2:
            raise ValueError("TOON must have header row")

        columns = [col.strip() for col in lines[1].split('|')]

        # Parse data rows (line 2+)
        facts = []
        i = 2
        while i < len(lines):
            row_text = lines[i].strip()

            # Skip empty lines
            if not row_text:
                i += 1
                continue

            # Handle multiline rows (continuation)
            while i + 1 < len(lines) and not lines[i + 1].strip().count('|'):
                i += 1
                row_text += " " + lines[i].strip()

            # Parse row
            try:
                fact = TOONConverter._parse_row(row_text, columns)
                facts.append(fact)
            except ValueError as e:
                raise ValueError(f"Error parsing row {i}: {e}")

            i += 1

        return facts

    @staticmethod
    def validate(toon_str: str) -> tuple[bool, List[str]]:
        """
        Validate TOON format.

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        try:
            lines = toon_str.strip().split('\n')
            if not lines[0].startswith('# extracted_facts'):
                errors.append("Missing '# extracted_facts' header")

            if len(lines) < 2:
                errors.append("Missing column header row")

            # Try parsing
            TOONConverter.toon_to_json(toon_str)
        except Exception as e:
            errors.append(str(e))

        return (len(errors) == 0, errors)

    @staticmethod
    def _build_row(fact: Dict, schema: Dict) -> str:
        """Build a single TOON row from fact dict."""
        cells = []
        for col in schema.keys():
            value = fact.get(col, '')

            # Format value based on type
            if isinstance(value, list):
                value = ', '.join(str(v) for v in value)
            elif isinstance(value, float):
                value = f"{value:.2f}"
            else:
                value = str(value)

            # Escape pipes in value
            value = value.replace('|', '\\|')

            # Truncate to schema width (leave room for wrapping)
            max_width = schema[col]
            if len(value) > max_width:
                value = value[:max_width-3] + "..."

            cells.append(value)

        return " | ".join(cells)

    @staticmethod
    def _parse_row(row_text: str, columns: List[str]) -> Dict:
        """Parse a TOON row into fact dict."""
        # Split by pipe (handle escaped pipes)
        parts = []
        current = ""
        i = 0
        while i < len(row_text):
            if row_text[i] == '\\' and i + 1 < len(row_text) and row_text[i+1] == '|':
                current += '|'
                i += 2
            elif row_text[i] == '|':
                parts.append(current.strip())
                current = ""
                i += 1
            else:
                current += row_text[i]
                i += 1
        parts.append(current.strip())

        if len(parts) != len(columns):
            raise ValueError(
                f"Row has {len(parts)} columns, expected {len(columns)}"
            )

        fact = {}
        for col, value in zip(columns, parts):
            # Parse specific types
            if col == 'tags':
                fact[col] = [t.strip() for t in value.split(',') if t.strip()]
            elif col == 'relevance_score':
                fact[col] = float(value) if value else 0.0
            elif col == 'source':
                fact[col] = value or 'unknown'
            else:
                fact[col] = value

        return fact
```

### 2. Updated fact-extract.sh

**Key Changes:**
```bash
# Before
EXTRACT_PROMPT="... Return ONLY valid JSON: {...}"

# After
EXTRACT_PROMPT_TOON="Extract ONLY the most valuable lessons from this review.

CONTENT:
$TRUNCATED_CONTENT

Return ONLY valid TOON format (no markdown, no code blocks):
# extracted_facts
title | summary | source | tags | relevance_score

Rules:
- title: 30 chars max
- summary: 2-3 sentences, clear and actionable
- source: 'review' or 'commit'
- tags: comma-separated, 2-3 tags max
- relevance_score: 0.0-1.0, only include if ≥0.6
- Be concise and specific
- Do NOT include field headers or examples in output"

# Extraction
RESULT=$(claude --model haiku --print "$EXTRACT_PROMPT_TOON" 2>/dev/null)

# Parse with fallback
JSON=$(python3 - << EOF
import sys
sys.path.insert(0, os.path.expanduser('~/.claude/scripts'))
from toon_utils import TOONConverter

toon_str = """$RESULT"""

try:
    # Try TOON first
    facts = TOONConverter.toon_to_json(toon_str)
    import json
    print(json.dumps(facts))
except Exception as e:
    # Fallback to JSON parsing
    try:
        json_obj = json.loads(toon_str)
        print(json.dumps(json_obj))
    except:
        print("[]")  # Empty on total failure
EOF
)
```

### 3. Updated knowledge-search.py

**Add TOON output:**
```python
# Add to search command
def search_facts(query: str, format: str = 'json') -> str:
    """
    Search knowledge DB.

    Args:
        query: Search query
        format: 'json' or 'toon'

    Returns:
        Formatted results
    """
    facts = # ... search logic ...

    if format == 'toon':
        from toon_utils import TOONConverter
        return TOONConverter.json_to_toon(facts)
    else:
        return json.dumps(facts)
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_toon_conversion.py

def test_json_to_toon_single_fact():
    fact = {
        'title': 'Example title',
        'summary': 'Example summary text',
        'source': 'review',
        'tags': ['tag1', 'tag2'],
        'relevance_score': 0.85
    }
    toon = TOONConverter.json_to_toon([fact])
    assert '# extracted_facts' in toon
    assert 'Example title' in toon

def test_toon_to_json_roundtrip():
    original = [
        {
            'title': 'Example',
            'summary': 'Description',
            'source': 'review',
            'tags': ['tag1'],
            'relevance_score': 0.8
        }
    ]
    toon = TOONConverter.json_to_toon(original)
    parsed = TOONConverter.toon_to_json(toon)
    assert parsed == original

def test_special_characters():
    fact = {
        'title': 'Test | pipe',
        'summary': 'Test "quotes" and \\backslash',
        'source': 'commit',
        'tags': ['special'],
        'relevance_score': 0.75
    }
    toon = TOONConverter.json_to_toon([fact])
    parsed = TOONConverter.toon_to_json(toon)
    assert parsed[0]['title'] == 'Test | pipe'

def test_existing_entries():
    """Ensure 3 existing entries parse correctly."""
    # Load from .knowledge-db/entries.jsonl
    # Convert to TOON and back
    # Validate no data loss
```

### Integration Tests
```bash
# Test extraction with real Haiku
~/.claude/scripts/fact-extract.sh "sample review text" "review" "test" /tmp/test-kdb

# Verify JSON written to DB
jq . /tmp/test-kdb/entries.jsonl

# Verify round-trip
python3 toon_utils.py validate "$(cat /tmp/test-kdb/entries.jsonl)"
```

---

## Performance Metrics

### Before TOON
```
Extraction call: 1,000 tokens
- Prompt: 200 tokens
- Response: 800 tokens
```

### After TOON
```
Extraction call: 600 tokens
- Prompt: 200 tokens
- Response: 400 tokens (40% reduction)
```

### Benchmark
```
10 facts extracted:
- Before: 8,000 tokens
- After: 4,800 tokens
- Savings: 3,200 tokens (40%)

100 extractions/month:
- Before: 80,000 tokens
- After: 48,000 tokens
- Savings: 32,000 tokens
- Cost savings: ~$0.016/month
```

---

## Error Handling

### Parsing Failures
```
If TOON parsing fails:
1. Log error with context
2. Try JSON parsing
3. If both fail, return empty facts []
4. Alert on >1% failure rate
```

### Edge Cases
```
1. Empty response → return []
2. Malformed TOON → fallback to JSON
3. Unicode content → handle UTF-8
4. Very long fields → truncate with ...
5. Special chars → escape properly
```

---

## Backward Compatibility

### Storage
- No changes to .knowledge-db structure
- Existing entries.jsonl untouched
- Can mix old (JSON) and new (from TOON) entries

### API
- Optional --format toon flag (default: json)
- Existing code continues working
- Gradual adoption possible

### Testing
- All 3 existing entries must parse correctly
- No data loss on round-trip
- Quality metrics maintained

---

## Rollback Plan

### If Issues Detected
```bash
# Quick rollback
git revert <commit>
cd ~/.claude/scripts
git checkout HEAD~1 fact-extract.sh

# Return to JSON extraction
# Continue normal operation
```

### Monitoring Checklist
- [ ] Parsing success rate ≥95%
- [ ] Token reduction ≥30%
- [ ] Fact quality maintained
- [ ] No data corruption
- [ ] Extraction time similar

---

## Future Enhancements

### Phase 2 (Optional)
1. Apply TOON to commit extraction
2. Apply TOON to web finding extraction
3. Use TOON for context injection in reviews

### Phase 3 (Optional)
1. TOON compression format
2. Adaptive format selection
3. Performance optimizations

---

## Dependencies

```
# No external TOON library needed
# Pure Python implementation
# Only requirements:
- Python 3.7+
- json (stdlib)
- re (stdlib)
- dataclasses (stdlib, or backport)
```

---

## Security Considerations

1. **Input validation:** Sanitize TOON input
2. **Escape handling:** Properly handle escaped pipes
3. **Size limits:** Reject oversized entries
4. **Type safety:** Validate field types after parsing

---

## Documentation Requirements

### User-Facing
- [ ] Update fact-extract.sh comments
- [ ] Add TOON section to INSTALLATION.md
- [ ] Document --format toon flag

### Developer
- [ ] toon_utils.py docstrings
- [ ] Test documentation
- [ ] Performance notes

### Operations
- [ ] Monitoring dashboard
- [ ] Rollback procedures
- [ ] Cost savings report template
