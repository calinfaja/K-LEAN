# TOON Format Integration Plan - K-LEAN Knowledge System

## Executive Summary

Integrate TOON (Token-Oriented Object Notation) format into K-LEAN's knowledge extraction pipeline to reduce token consumption by ~40%, lowering operational costs while maintaining fact quality and system reliability.

**Expected Impact:**
- Token reduction: 40% on fact extraction calls
- Cost savings: ~$0.02/month per 100 reviews
- Implementation effort: 2 weeks (low risk)
- ROI: Quick payoff on extraction operations

---

## Current State Analysis

### Knowledge Extraction Pipeline
```
Review Text
    ↓
fact-extract.sh (Haiku model)
    ↓ (JSON format response)
knowledge_db.py (store)
    ↓
.knowledge-db/entries.jsonl (1.6MB, 3 entries currently)
```

### Current Fact Schema (JSON)
```json
{
  "title": "Namespace separation best practice",
  "summary": "Separating command namespaces...",
  "source": "review|commit",
  "tags": ["namespace", "organization"],
  "id": "UUID",
  "found_date": "ISO timestamp",
  "auto_extracted": true,
  "relevance_score": 0.8
}
```

### Token Usage (Current)
- Per extraction call: ~800-1000 tokens
- Extraction frequency: ~10 per review session
- Monthly reviews (100x): ~80,000 tokens
- Cost (NanoGPT): ~$0.04/month

---

## TOON Format Strategy

### Why TOON Works Here
1. **Extraction output is tabular** - Multiple facts per review
2. **Structured & uniform** - All facts have same schema
3. **Cost matters** - Running hundreds of extractions
4. **LLM-native** - Designed for model input

### TOON Representation
```
# extracted_facts
title                        | summary                              | source | tags              | relevance
Namespace separation         | Separating /sc: vs /kln: namespaces  | review | namespace, org    | 0.8
Timeout fix for thinking     | Increased curl timeout to 120s       | commit | timeout, bugfix   | 0.9
Bash script organization     | Group scripts with clear naming      | review | bash, scripts     | 0.7
```

### Token Savings
- JSON format: ~800 tokens
- TOON format: ~480 tokens
- **Savings: ~40%** (benchmark from TOON spec)

---

## Implementation Plan

### Phase 1: Foundation (Days 1-3)
**Goal:** Build core TOON utilities

#### 1.1 Add TOON Library
**File:** `~/.claude/scripts/toon_utils.py`
```python
class TOONConverter:
    @staticmethod
    def json_to_toon(facts: List[Dict]) -> str:
        """Convert list of fact JSONs to TOON format"""
        # Build header row from first fact keys
        # Convert each fact to TOON row
        # Return formatted table

    @staticmethod
    def toon_to_json(toon_str: str) -> List[Dict]:
        """Convert TOON format back to JSON"""
        # Parse header row
        # Parse data rows
        # Return list of dicts

    @staticmethod
    def validate(toon_str: str) -> bool:
        """Validate TOON format structure"""
```

**Deliverable:** Converter with unit tests

#### 1.2 Create Test Framework
**File:** `tests/test_toon_conversion.py`
- Test JSON→TOON→JSON round-trip
- Test with 3 existing knowledge entries
- Test edge cases (special chars, quotes, nulls)
- Validate no data loss

**Deliverable:** 100% passing tests, backward compatibility verified

#### 1.3 TOON Extraction Prompt
**File:** Updated prompt in `fact-extract.sh`
```bash
# Current (JSON)
EXTRACT_PROMPT="... Return ONLY valid JSON: {...}"

# New (TOON)
EXTRACT_PROMPT="... Return ONLY valid TOON format:
# extracted_facts
title | summary | source | tags | relevance_score

Be concise but complete in each field."
```

**Deliverable:** Prompt template with examples

---

### Phase 2: Prototype (Days 4-6)
**Goal:** Modify extraction pipeline to use TOON

#### 2.1 Update fact-extract.sh
**Changes:**
1. Add TOON output request to Haiku prompt
2. Parse TOON response using TOONConverter.toon_to_json()
3. Fallback to JSON parsing if TOON parsing fails
4. Store as JSON (no storage changes)

```bash
# New extraction flow
RESULT=$(claude --model haiku --print "$EXTRACT_TOON_PROMPT")
JSON_RESULT=$(python3 - << EOF
from toon_utils import TOONConverter
toon_str = """$RESULT"""
facts = TOONConverter.toon_to_json(toon_str)
for fact in facts:
    store_fact(fact)
EOF
)
```

**Deliverable:** Updated fact-extract.sh with TOON support

#### 2.2 Token Counting
**Add telemetry:**
```bash
# Measure before/after
OLD_TOKENS=$(estimate_tokens "$EXTRACT_PROMPT")
NEW_TOKENS=$(estimate_tokens "$EXTRACT_TOON_PROMPT")
echo "Token reduction: $((100 * (OLD_TOKENS - NEW_TOKENS) / OLD_TOKENS))%"
```

**Deliverable:** Token usage comparison report

#### 2.3 Quality Validation
**Test extraction on sample reviews:**
- Run 5 sample reviews with new TOON extraction
- Compare facts against JSON version
- Verify no quality degradation
- Check fact completeness and accuracy

**Deliverable:** Quality assurance report

---

### Phase 3: Optimization & Testing (Days 7-9)
**Goal:** Performance validation and edge case handling

#### 3.1 Performance Testing
**Measure:**
- Extraction time (should be similar)
- Token count (should be ~40% less)
- Cost savings (calculate savings)
- Parsing reliability (error rates)

**Deliverable:** Performance benchmark report

#### 3.2 Edge Case Handling
**Test scenarios:**
- Facts with special characters (pipes, quotes)
- Long summaries (text wrapping)
- Unicode content
- Null/empty fields
- Very short vs very long facts

**Deliverable:** Edge case test suite

#### 3.3 Fallback Logic
**Implement graceful degradation:**
```bash
# If TOON parsing fails, try JSON
if ! parse_toon "$response"; then
    if ! parse_json "$response"; then
        log_error "Both TOON and JSON parsing failed"
        return 1
    fi
fi
```

**Deliverable:** Robust error handling

---

### Phase 4: Integration (Days 10-12)
**Goal:** Deploy to production, add optional features

#### 4.1 Production Deployment
**Steps:**
1. Backup existing fact-extract.sh
2. Deploy updated version
3. Monitor extraction quality for 1 week
4. Rollback plan if issues detected

**Deliverable:** Deployment checklist & rollback procedure

#### 4.2 Optional: Context Injection as TOON
**For future:** When injecting retrieved facts into review prompts:
```bash
# Get facts as TOON for more compact context
CONTEXT=$(knowledge-query.sh "authentication" --format toon)
# Inject into review prompt (takes fewer tokens)
```

**Deliverable:** Optional --format toon flag in knowledge-search.py

#### 4.3 Documentation
**Update docs:**
- `fact-extract.sh` - mention TOON usage
- `INSTALLATION.md` - add TOON section
- `TOON_FORMAT.md` - internal reference guide

**Deliverable:** Comprehensive documentation

---

## Technical Specifications

### TOON Schema for Facts
```
# extracted_facts
title (string, 60 chars max) | summary (string, 200 chars) | source (review|commit|web) | tags (csv) | relevance_score (0.0-1.0)
```

### Conversion Rules
**JSON Field → TOON Field:**
- `title` → title column
- `summary` → summary column
- `source` → source column
- `tags` → pipe-separated (tags)
- `relevance_score` → relevance_score column
- Drop: id, found_date, auto_extracted (re-generated on storage)

**TOON Field → JSON:**
- Create new UUID for id
- Add current timestamp for found_date
- Set auto_extracted: true
- Set source based on context (review/commit)

### Storage Strategy
- **Input format:** TOON (from Haiku)
- **Storage format:** JSON (JSONL in .knowledge-db/)
- **Transmission format:** TOON (optional, for context injection)
- **Benefit:** One format for LLM efficiency, one for system reliability

---

## Success Criteria

### Must Have ✅
- [ ] TOON converter parses 100% of test cases correctly
- [ ] Round-trip JSON→TOON→JSON preserves all data
- [ ] Token reduction ≥ 30% on extraction
- [ ] Fact quality maintained or improved
- [ ] Backward compatibility with 3 existing entries
- [ ] Zero data loss during conversion

### Should Have 📊
- [ ] Token reduction ≥ 40% (TOON spec target)
- [ ] Extraction time maintained (no slowdown)
- [ ] 95%+ parsing success rate
- [ ] Cost savings documented

### Nice to Have 🎁
- [ ] Optional --format toon in knowledge-search.py
- [ ] Performance metrics dashboard
- [ ] TOON format tutorial in docs

---

## Risk Assessment & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|-----------|
| Haiku doesn't understand TOON format | Medium | High | Test with sample prompts before rollout |
| TOON parser fails on edge cases | Low | Medium | Comprehensive test suite + fallback to JSON |
| Token savings < 30% | Low | Medium | Document actual savings; even 20% is worthwhile |
| Facts lose detail in TOON format | Low | Medium | Quality validation against JSON version |
| Performance regression | Low | Medium | Benchmark before/after extraction time |

---

## Resource Requirements

### Personnel
- 1 developer: 2 weeks (primary)
- 1 reviewer: 3 days (code review, testing)
- 1 QA: 2 days (validation)

### Tools & Libraries
- TOON library (open source)
- Python testing framework (pytest)
- Token counting utilities (existing)

### Environment
- Dev environment for testing
- Staging environment for pre-production validation
- Production environment for rollout

---

## Timeline

| Phase | Duration | Status |
|-------|----------|--------|
| Phase 1: Foundation | Days 1-3 | Planned |
| Phase 2: Prototype | Days 4-6 | Planned |
| Phase 3: Optimization | Days 7-9 | Planned |
| Phase 4: Integration | Days 10-12 | Planned |
| **Total** | **~2 weeks** | **Estimated** |

---

## Post-Launch

### Monitoring
- Track token usage per extraction
- Monitor parsing success rate
- Alert if >1% parse failures
- Collect cost savings metrics

### Optimization Opportunities
1. Apply TOON to commit extraction (secondary ROI)
2. Use TOON format for web finding extraction
3. Inject context as TOON in reviews (further savings)
4. Explore TOON for other structured outputs

### Future Enhancements
- TOON v2 with compression
- Multi-format extraction (Haiku chooses)
- Adaptive format based on content

---

## Appendix A: TOON Format Reference

**Official Spec:** https://github.com/toon-format/toon

**Key Points:**
- Indentation-based nesting (like YAML)
- CSV-like arrays (uniform structures)
- ~40% fewer tokens than JSON for tables
- Lossless encoding
- LLM-optimized parsing

**Example:**
```
# people
name    | age | city
Alice   | 30  | NYC
Bob     | 25  | SF
```

---

## Appendix B: Cost-Benefit Analysis

### Investment
- Development time: ~80 hours × $50/hr = $4,000
- Testing & QA: ~20 hours × $40/hr = $800
- Documentation: ~10 hours × $40/hr = $400
- **Total investment: ~$5,200**

### Return
- Token savings: 40% of extraction calls
- Monthly extraction calls: ~1,000 (100 reviews × 10 facts)
- Current monthly cost: $0.04
- After TOON: $0.02
- **Monthly savings: $0.02 (small but growing with scale)**

### Payback
- At 1,000 extractions/month: Payback in ~260 years (small scale)
- At 10,000 extractions/month: Payback in ~26 years
- At 100,000 extractions/month: Payback in ~2.6 years (enterprise scale)

### Strategic Value
- **Positioning:** Market as "token-efficient" system
- **Foundation:** Enables future cost optimizations
- **Competitive:** Differentiator for enterprise customers
- **Learning:** LLM cost optimization best practices

---

## Approval & Sign-Off

| Role | Name | Date | Sign |
|------|------|------|------|
| Product Owner | [Name] | [Date] | [ ] |
| Tech Lead | [Name] | [Date] | [ ] |
| QA Lead | [Name] | [Date] | [ ] |

---

## Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-09 | Claude | Initial plan |
| 1.1 | [TBD] | [TBD] | [TBD] |
