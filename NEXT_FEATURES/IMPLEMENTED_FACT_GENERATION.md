# Automatic Fact Generation - IMPLEMENTED

**Status:** ✅ Complete (Tier 1 & 2)
**Commit:** b163166
**Date:** Dec 8, 2024

## What It Does

Automatically extracts reusable patterns, gotchas, and lessons from:
- **Tier 1**: Completed code reviews (all review scripts)
- **Tier 2**: Git commits (via post-commit hook)

Uses native Claude Haiku for fast, cost-efficient extraction.

## Implementation

### New Script
- `~/.claude/scripts/fact-extract.sh` - Shared extraction logic

### Modified Scripts
- `quick-review.sh` - Extracts after single-model review
- `consensus-review.sh` - Combines 3 models + extracts
- `deep-review.sh` - Extracts from full-tool review
- `parallel-deep-review.sh` - Combines 3 headless instances + extracts
- `post-commit-docs.sh` - Tier 2 commit-based extraction

## How It Works

```
Review/Commit → fact-extract.sh → Claude Haiku
                                    ↓
                        Extract JSON with facts
                                    ↓
                            Validate & Score (>= 0.6)
                                    ↓
                        Store in .knowledge-db/txtai
                                    ↓
                    Auto-inject into future reviews
```

## Filtering

- **Content length**: Skip if < 100 chars
- **Relevance score**: Skip if < 0.6 (0-1 scale)
- **Storage**: Only if project has `.knowledge-db/`

## Filtering

- Content < 100 chars: skipped
- Relevance score < 0.6: not stored
- No knowledge-db directory: skipped

## Future (Tier 3)

- Session-end summaries (needs `stop` hook)
- Cross-project knowledge synthesis
- Fact recall in system prompts

## Testing

Ready for testing with actual reviews/commits. Runs in background, non-blocking.
