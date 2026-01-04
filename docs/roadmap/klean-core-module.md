# klean.core Module Refactor

Convert `klean_core.py` from a data/script file to a proper Python module.

## Current State

`klean_core.py` is in `src/klean/data/core/` which is treated as assets (symlinked to `~/.claude/kln/`), not importable Python code.

**Problems**:
- `python -m klean.core` fails (module doesn't exist)
- `from klean.core import LLMClient` fails
- Slash commands need hardcoded script paths
- Code duplication between cli.py and klean_core.py

## Proposed Structure

```
src/klean/core/
├── __init__.py      # Exports: LLMClient, ReviewEngine, ModelResolver
├── __main__.py      # CLI entry point (python -m klean.core)
├── client.py        # LLMClient class
├── engine.py        # ReviewEngine class
├── resolver.py      # ModelResolver, ModelInfo
├── cli.py           # cli_quick, cli_multi, cli_rethink, cli_status
└── config.py        # load_config(), CONFIG dict
```

## Benefits

| Aspect | Current | After |
|--------|---------|-------|
| `python -m klean.core` | Fails | Works |
| `from klean.core import X` | Fails | Works |
| Slash commands | Hardcoded paths | `-m klean.core` |
| Code reuse | Copy/paste | Import |
| Testing | Hard | Easy |

## Changes Required

1. **Create**: `src/klean/core/` module (7 files, ~1290 lines total)
2. **Delete**: `src/klean/data/core/klean_core.py`
3. **Modify**: `src/klean/cli.py` - remove core from install components
4. **Keep**: `data/core/config.yaml` and `data/core/prompts/` as data files

## Effort

- **Estimate**: 2-4 hours
- **Risk**: Low (straightforward refactor)
- **Breaking**: None (improves compatibility)

## Status

- [ ] Not started
- Deferred from v1.0.0b2 release
- Added: 2026-01-04
