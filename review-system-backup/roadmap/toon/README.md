# TOON Compression Feature

Token-Oriented Object Notation adapter for efficient LLM transmission.

## Status
- [x] toon_adapter.py - Standalone JSON-TOON conversion
- [x] context_injector.py - Auto-inject KB context with TOON
- [ ] Integration into knowledge-query.sh
- [ ] Integration into droid-execute.sh

## Benefits
- ~18% character reduction
- ~10-20% token savings (varies by tokenizer)

## Installation (when ready)
```bash
~/.venvs/knowledge-db/bin/pip install python-toon
```

## Usage
See `docs/` for detailed documentation.
