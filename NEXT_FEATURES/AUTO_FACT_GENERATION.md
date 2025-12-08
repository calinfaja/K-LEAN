# Automatic Fact Generation - Implementation Plan

**Status:** Planning Phase
**Priority:** Medium
**Complexity:** Medium
**Effort Estimate:** 4-6 hours

---

## Overview

Add automatic knowledge extraction from reviews and commits to K-LEAN. When code reviews complete or commits are made, automatically extract reusable facts and store them in the project knowledge database.

Similar to RedPlanetHQ/core's automatic fact generation, but triggered on **events** (commits, reviews) rather than every conversation turn. More efficient and higher-signal.

---

## Goals

1. **Tier 1 (Review-Based)**: Extract findings from completed reviews
2. **Tier 2 (Commit-Based)**: Extract learnings from commits
3. **Reduce manual knowledge capture**: Users don't need to type "GoodJob"
4. **Build institutional knowledge**: Automatically capture patterns and gotchas

---

## Architecture

### Fact Extraction Flow

```
┌──────────────────────────────────────────────────────────────┐
│  EVENT TRIGGERED                                             │
│  (Review Complete OR Commit)                                 │
├──────────────────────────────────────────────────────────────┤
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────┐            │
│  │ Extract Content                              │            │
│  │ - Review: findings + issues table            │            │
│  │ - Commit: diff + message + changed files    │            │
│  └─────────────────────────────────────────────┘            │
│           │                                                  │
│           ▼                                                  │
│  ┌─────────────────────────────────────────────┐            │
│  │ Pre-Filter (Heuristics)                      │            │
│  │ - Content length > 200 chars?                │            │
│  │ - Has findings/changes (not empty)?          │            │
│  │ - Skip if no diff/empty review               │            │
│  └─────────────────────────────────────────────┘            │
│           │                                                  │
│           ├─ [SKIP] → Exit                                   │
│           │                                                  │
│           ▼ [CONTINUE]                                      │
│  ┌─────────────────────────────────────────────┐            │
│  │ Haiku Extraction                             │            │
│  │ Input: content + context                     │            │
│  │ Output: JSON facts (score > 0.6)            │            │
│  └─────────────────────────────────────────────┘            │
│           │                                                  │
│           ├─ [score < 0.6] → Skip storing                   │
│           │                                                  │
│           ▼ [score >= 0.6]                                  │
│  ┌─────────────────────────────────────────────┐            │
│  │ Store in .knowledge-db/                      │            │
│  │ - Add to entries.jsonl                       │            │
│  │ - Index with txtai                           │            │
│  │ - Tag: "auto_review" or "auto_commit"        │            │
│  └─────────────────────────────────────────────┘            │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## TIER 1: Review-Based Learning

### Scope
Automatically extract findings from completed reviews:
- `quickReview` (single model, API)
- `quickCompare` (3 models, API)
- `deepInspect` (single model with tools)
- `deepAudit` (3 models with tools)

### Implementation Files

**New Script:** `~/.claude/scripts/review-extract.sh`
```bash
#!/bin/bash
# Extract facts from review results
# Input: Review JSON/text output
# Output: Facts JSON suitable for knowledge-db

REVIEW_CONTENT="$1"
FOCUS="$2"  # Original review focus
WORK_DIR="$3"

# Pre-filter: check if review has issues
if ! echo "$REVIEW_CONTENT" | grep -qi "issue\|error\|risk\|grade"; then
    exit 0  # No findings, skip
fi

# Haiku extraction
HAIKU_PROMPT="Extract reusable facts from this code review.

REVIEW:
$REVIEW_CONTENT

FOCUS: $FOCUS

Extract ONLY information useful for FUTURE sessions:
- Critical bugs/patterns found
- Common issues in this codebase
- Areas needing attention
- Solutions/fixes that worked

Return JSON:
{
  \"should_store\": true/false,
  \"relevance_score\": 0.0-1.0,
  \"facts\": [{
    \"title\": \"Short descriptive title\",
    \"summary\": \"What was found and why it matters\",
    \"type\": \"gotcha|pattern|solution|insight\",
    \"key_concepts\": [\"keyword1\", \"keyword2\"],
    \"context\": \"When/where this applies\",
    \"source\": \"review_$FOCUS\"
  }]
}

Skip if less than 0.6 relevance."

# Call Haiku
curl -s http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"qwen3-coder\",
    \"messages\": [{\"role\": \"user\", \"content\": \"$HAIKU_PROMPT\"}],
    \"max_tokens\": 500
  }" | jq .choices[0].message.content
```

**Modified Files:**
- `quick-review.sh` - Add extraction after review completes
- `consensus-review.sh` - Add extraction for multi-model reviews
- `deep-review.sh` - Add extraction for single model deep review
- `parallel-deep-review.sh` - Add extraction for multi-model deep review

### Integration Points

In each review script, after results are saved:

```bash
# After review completes
REVIEW_RESULT=$(cat "$OUTPUT_FILE")

# Extract facts
~/.claude/scripts/review-extract.sh "$REVIEW_RESULT" "$FOCUS" "$WORK_DIR"

# Extracted facts are automatically stored in .knowledge-db/
```

### Changes Required

| File | Change | Lines |
|------|--------|-------|
| `quick-review.sh` | Call review-extract.sh on completion | +5 |
| `consensus-review.sh` | Extract from all 3 models' findings | +5 |
| `deep-review.sh` | Extract from detailed review | +5 |
| `parallel-deep-review.sh` | Aggregate and extract from results | +5 |
| (new) `review-extract.sh` | Main extraction logic | ~50 |

---

## TIER 2: Commit-Based Learning

### Scope
Enhance existing `post-commit-docs.sh` to also extract facts from commits.

### Implementation Files

**New Script:** `~/.claude/scripts/commit-extract.sh`
```bash
#!/bin/bash
# Extract facts from git commits
# Input: commit hash, diff, changed files
# Output: Facts about why the change was made

COMMIT_HASH="$1"
WORK_DIR="$2"

# Get commit details
cd "$WORK_DIR"
COMMIT_MSG=$(git log -1 --pretty=%B "$COMMIT_HASH" 2>/dev/null)
COMMIT_DIFF=$(git show "$COMMIT_HASH" 2>/dev/null | head -200)
CHANGED_FILES=$(git diff-tree --no-commit-id --name-only -r "$COMMIT_HASH" 2>/dev/null | head -10)

# Pre-filter: skip merge commits, small changes
if echo "$COMMIT_MSG" | grep -qi "merge\|revert"; then
    exit 0
fi

if [ $(echo "$COMMIT_DIFF" | wc -l) -lt 5 ]; then
    exit 0  # Too small
fi

# Haiku extraction
HAIKU_PROMPT="Extract lessons from this git commit.

COMMIT MESSAGE:
$COMMIT_MSG

FILES CHANGED:
$CHANGED_FILES

DIFF (excerpt):
$COMMIT_DIFF

Extract ONLY insights useful for FUTURE sessions:
- Bug fixes/patterns (what was broken, how fixed)
- Architectural decisions (why this approach)
- Gotchas discovered (don't do X because Y)
- New patterns introduced (reusable approach)

Return JSON:
{
  \"should_store\": true/false,
  \"relevance_score\": 0.0-1.0,
  \"facts\": [{
    \"title\": \"Short descriptive title\",
    \"summary\": \"What was changed and why\",
    \"type\": \"gotcha|pattern|decision|lesson\",
    \"key_concepts\": [\"keyword1\"],
    \"context\": \"What problem this solved\",
    \"source\": \"commit_$COMMIT_HASH\"
  }]
}

Only store if relevance >= 0.6."

# Call Haiku
curl -s http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -d "{
    \"model\": \"qwen3-coder\",
    \"messages\": [{\"role\": \"user\", \"content\": \"$HAIKU_PROMPT\"}],
    \"max_tokens\": 500
  }" | jq .choices[0].message.content
```

**Modified File:** `post-commit-docs.sh`

Change from:
```bash
# Run documentation agent
claude --print "$PROMPT"
```

To:
```bash
# Run documentation agent
claude --print "$PROMPT"

# Also extract facts
~/.claude/scripts/commit-extract.sh "$COMMIT_HASH" "$WORK_DIR"
```

### Changes Required

| File | Change | Lines |
|------|--------|-------|
| `post-commit-docs.sh` | Call commit-extract.sh after docs | +2 |
| (new) `commit-extract.sh` | Main extraction logic | ~60 |

---

## Haiku Extraction Prompt Template

Both scripts use similar extraction logic:

```
CORE LOGIC:
1. Input: Content (review findings, commit diff, etc.)
2. Parse with Haiku: Extract useful facts
3. Score: relevance_score 0.0-1.0
4. Store: If score >= 0.6, add to knowledge-db

FACTS JSON SCHEMA:
{
  "should_store": boolean,
  "relevance_score": number (0.0-1.0),
  "facts": [
    {
      "title": "string",
      "summary": "string (2-3 sentences)",
      "type": "gotcha|pattern|decision|lesson|insight",
      "key_concepts": ["string[]"],
      "context": "When/where this applies",
      "source": "review_X|commit_Y"
    }
  ]
}

STORAGE:
- Each fact stored as separate entry in .knowledge-db/
- Automatically indexed by txtai
- Tagged with source for traceability
```

---

## Data Flow

### TIER 1: Review-Based

```
Review completes
    ↓
save results to /tmp/claude-reviews/
    ↓
review-extract.sh reads results
    ↓
Pre-filter: has findings?
    ↓ [YES]
Haiku: extract facts
    ↓
score >= 0.6?
    ↓ [YES]
knowledge_db.py add facts
    ↓
.knowledge-db/entries.jsonl updated
```

### TIER 2: Commit-Based

```
git commit executes
    ↓
PostToolUse hook triggered
    ↓
post-commit-docs.sh runs
    ↓
post-commit-docs.sh (enhanced):
  1. Run Serena documentation
  2. Call commit-extract.sh
    ↓
commit-extract.sh:
  1. Extract commit details
  2. Pre-filter (size, type)
  3. Haiku: extract facts
  4. Score >= 0.6?
    ↓ [YES]
knowledge_db.py add facts
    ↓
.knowledge-db/entries.jsonl updated
```

---

## Configuration

### Enable/Disable Auto Extraction

Add to `~/.claude/settings.json`:

```json
{
  "autoFactGeneration": {
    "reviews": true,
    "commits": true,
    "minimumScoreThreshold": 0.6,
    "maxFactsPerEvent": 5
  }
}
```

### Feature Flags (Future)

```bash
# Disable auto-extraction for specific session
AUTO_FACTS_DISABLED=1 claude --project myproject

# Force extraction regardless of score
AUTO_FACTS_FORCE=1 git commit -m "test"
```

---

## Testing Strategy

### Unit Tests

1. **review-extract.sh**
   - Test with sample review output (high findings)
   - Test with empty review (should skip)
   - Test Haiku response parsing

2. **commit-extract.sh**
   - Test with real commit (bug fix)
   - Test with merge commit (should skip)
   - Test with tiny commit (should skip)

### Integration Tests

1. **Review flow**
   - Run quickReview → check /tmp/claude-reviews/
   - Verify facts added to .knowledge-db/
   - Search with FindKnowledge

2. **Commit flow**
   - Make test commit → check post-commit-docs.sh log
   - Verify facts added to .knowledge-db/
   - Search with FindKnowledge

---

## Implementation Steps

### Phase 1: Setup (30 min)
1. Create `review-extract.sh` skeleton
2. Create `commit-extract.sh` skeleton
3. Test Haiku prompt format
4. Verify knowledge_db.py integration

### Phase 2: Tier 1 (90 min)
1. Implement review-extract.sh fully
2. Integrate with quick-review.sh
3. Integrate with consensus-review.sh
4. Test with sample reviews
5. Integrate with deep-review.sh
6. Integrate with parallel-deep-review.sh

### Phase 3: Tier 2 (60 min)
1. Implement commit-extract.sh fully
2. Modify post-commit-docs.sh to call it
3. Test with sample commits
4. Verify facts are stored

### Phase 4: Testing & Docs (60 min)
1. Run integration tests
2. Update ARCHITECTURE.md with new system
3. Add examples to USER_GUIDE.md
4. Test disable/enable flags

---

## Success Criteria

- [ ] Review-based facts extracted and stored automatically
- [ ] Commit-based facts extracted and stored automatically
- [ ] Facts are searchable via `FindKnowledge`
- [ ] Can toggle extraction on/off in settings
- [ ] No performance impact on reviews/commits
- [ ] Facts have relevance_score for filtering
- [ ] Documentation updated

---

## Future Enhancements (Tier 3)

### Session-End Learning
- Listen for Stop hook (end of conversation)
- Scan last N messages from session file
- Pre-filter for significant exchanges
- Extract if meaningful
- **Effort:** High (requires new hook type)

### Batch Extraction
- Periodic job scans old reviews/commits
- Extracts facts retroactively from past week
- Useful for backfilling knowledge
- **Effort:** Medium

### Smarter Filtering
- Learn which fact types are most useful
- Adjust score thresholds dynamically
- Skip patterns (e.g., "TODO:", "WIP:")
- **Effort:** Low

---

## Files to Modify/Create

| File | Type | Status |
|------|------|--------|
| `~/.claude/scripts/review-extract.sh` | Create | To-Do |
| `~/.claude/scripts/commit-extract.sh` | Create | To-Do |
| `quick-review.sh` | Modify | To-Do |
| `consensus-review.sh` | Modify | To-Do |
| `deep-review.sh` | Modify | To-Do |
| `parallel-deep-review.sh` | Modify | To-Do |
| `post-commit-docs.sh` | Modify | To-Do |
| docs/ARCHITECTURE.md | Modify | To-Do |
| docs/USER_GUIDE.md | Modify | To-Do |

---

## Notes

- Use Haiku (fast, cheap) for extraction, not Opus
- Pre-filter before calling Haiku to save API calls
- Store source (review_X, commit_Y) for traceability
- Tag facts with "auto" prefix for filtering
- Consider batching multiple facts per Haiku call
- Monitor Haiku token usage

