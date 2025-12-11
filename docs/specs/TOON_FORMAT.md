# TOON vs JSON for Agent SDK Droids - Analysis & Recommendation

**Date:** 2025-12-11
**Status:** Decision Framework

---

## Executive Summary

**Recommendation:** **Hybrid Approach**
- **Direct Droid Output:** Keep JSON (for CLI, programmatic consumption, structured format)
- **Knowledge Extraction:** Use TOON (40% token savings, perfectly suited for tabular facts)
- **Tools Output:** Keep JSON (internal tool communication)

This gives us the best of both worlds: clean programmatic interfaces + token efficiency for knowledge capture.

---

## Comparison Analysis

### TOON Format
**Strengths:**
- ✅ 40% token reduction on tabular data
- ✅ Perfect for structured fact extraction
- ✅ Human-readable like CSV
- ✅ Designed by Anthropic for model efficiency
- ✅ Ideal for knowledge pipeline (extract → store → search)

**Weaknesses:**
- ❌ Limited to tabular/column-oriented data
- ❌ Requires parsing for programmatic access
- ❌ Not suitable for nested hierarchies
- ❌ Conversion overhead (JSON ↔ TOON)

**Best Use Case:**
```
Security Findings Table:
type              | location        | severity | cwe_id
SQL Injection     | query_db:line12 | critical | CWE-89
Command Injection | run_cmd:line19  | critical | CWE-78
Hardcoded Creds   | config:line25   | high     | CWE-798
```

### JSON Format
**Strengths:**
- ✅ Universal standard (all languages, frameworks)
- ✅ Supports nested hierarchies
- ✅ Direct programmatic access
- ✅ CLI-friendly (jq, python json module)
- ✅ Web APIs use JSON exclusively

**Weaknesses:**
- ❌ Higher token usage (~15% more than TOON for tables)
- ❌ Verbose for simple facts
- ❌ Requires escaping/encoding

**Best Use Case:**
```json
{
  "audit_summary": {...},
  "findings": [
    {
      "type": "SQL Injection",
      "metadata": {...}
    }
  ],
  "recommendations": [...]
}
```

---

## K-LEAN Use Cases Analysis

### Case 1: Direct Droid Output (JSON ✅)
```
SecurityAuditorDroid.execute() → JSON
├─ Used by: K-LEAN CLI, automation scripts, dashboards
├─ Structure: Nested (findings → details → recommendations)
├─ Consumer: Humans + scripts
└─ Decision: JSON (nested structure needed)

ArchitectReviewerDroid.execute() → JSON
├─ Used by: Architecture team, refactoring planning
├─ Structure: Nested (components → patterns → SOLID scores)
└─ Decision: JSON (hierarchical complexity data)

PerformanceAnalyzerDroid.execute() → JSON
├─ Used by: DevOps, optimization teams
├─ Structure: Nested (bottlenecks → analysis → recommendations)
└─ Decision: JSON (complex nested metrics)
```

### Case 2: Knowledge Extraction (TOON ✅)
```
Extract findings from droid output → TOON table → Store in KB
├─ Input: JSON findings (from droids)
├─ Format: TOON (5-10 facts per droid run)
├─ Storage: .knowledge-db/findings.toon
├─ Token usage: 40% reduction
└─ Decision: TOON (tabular, optimized for extraction)

Use Case:
1. SecurityAuditorDroid runs → JSON findings
2. Extract key findings → TOON format
3. Store with metadata → Knowledge DB
4. Search for similar issues → Fast KB lookup
```

---

## Proposed Hybrid Architecture

```
┌─────────────────────────────────────────────────────────┐
│          Droid Execution & Output Layer                │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ SecurityAuditorDroid.execute()                          │
│     ↓                                                    │
│ Returns: JSON (nested, hierarchical)                    │
│     ├─ Finding 1: {type, severity, cwe, ...}          │
│     ├─ Finding 2: {type, severity, cwe, ...}          │
│     └─ Recommendations: [{...}]                         │
│                                                         │
│ Format: application/json (programmatic)                 │
│ Usage: K-LEAN CLI, scripts, dashboards                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────────────┐
│        Knowledge Extraction & Storage Layer             │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Extract Facts from JSON                                 │
│     ↓                                                    │
│ Convert to TOON (40% token savings)                     │
│     ↓                                                    │
│ TOON Table:                                             │
│ finding_type | severity | cwe | recommendation | source │
│ SQL Injection| critical |89   | Use parameterized ...   │
│ ...          | ...      | ... | ...            | ...    │
│     ↓                                                    │
│ Store in Knowledge DB (.knowledge-db/findings.toon)    │
│ Format: TOON (tabular, optimized)                      │
│ Usage: Semantic search, fact retrieval                 │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Phase 1: Keep Current JSON Implementation
1. **No changes** to droid output format (already optimal)
2. Droids continue returning JSON
3. JSON is perfect for programmatic consumption
4. CLI tools parse JSON natively

### Phase 2: Add TOON Extraction Layer (Optional, Future)
1. Create `extract_to_toon()` utility function
2. Transforms droid JSON output → TOON facts
3. Stores in knowledge DB with TOON format
4. Enables efficient knowledge search

### Phase 3: Knowledge Integration with TOON
1. When droids search knowledge, they find TOON facts
2. Convert back to JSON for droid processing
3. 40% token savings on knowledge queries

---

## Token Savings Calculation

### Current State (JSON everywhere)
```
1 droid execution (JSON output):      ~2000 tokens
Knowledge extraction (JSON):           ~800 tokens
Per droid run:                         ~2800 tokens

100 droid runs/month:                  ~280,000 tokens
Cost (NanoGPT @$0.50/1M):              ~$0.14/month
```

### With Hybrid Approach (JSON + TOON)
```
1 droid execution (JSON output):      ~2000 tokens (unchanged)
Knowledge extraction (TOON):           ~480 tokens (40% savings)
Per droid run:                         ~2480 tokens

100 droid runs/month:                  ~248,000 tokens
Savings:                               ~32,000 tokens (11% overall)
Cost reduction:                        ~$0.016/month
```

**Note:** Token savings are modest for droid operations, but significant if we scale knowledge extraction to hundreds of analyses.

---

## Decision Matrix

| Aspect | JSON | TOON | Decision |
|--------|------|------|----------|
| **Droid Output Format** | Ideal | Not suitable | JSON |
| **Structure Support** | Nested ✅ | Flat ❌ | JSON |
| **Programmatic Use** | Native ✅ | Requires parsing ❌ | JSON |
| **CLI Consumption** | jq tools ✅ | Custom parser | JSON |
| **Knowledge Storage** | Works but verbose | Perfect ✅ | TOON |
| **Token Efficiency** | Standard | 40% savings ✅ | TOON |
| **Human Readability** | Medium | High ✅ | TOON |

---

## Recommendation: Implementation Order

### Priority 1: Current State (Complete)
- ✅ Keep JSON for all droid outputs
- ✅ Production-ready, fully tested
- ✅ Programmatically sound

### Priority 2: Future Enhancement (Post-v2.0)
- ⏳ Add optional TOON extraction for knowledge
- ⏳ Implement fact-to-TOON conversion
- ⏳ Store extracted facts as TOON in knowledge DB
- ⏳ Gain 40% token efficiency on knowledge extraction

### Priority 3: Long-term
- ⏳ If knowledge DB grows to 1000+ facts, TOON savings become significant
- ⏳ Consider native TOON format for fact tables

---

## Conclusion

**Best approach for K-LEAN v2.0:**

1. **Keep JSON for droid outputs** - It's optimal for our use case
   - Nested structure required
   - Programmatic consumption essential
   - Token cost is negligible (main cost is Claude thinking, not output format)
   - Standard format everyone understands

2. **Plan TOON integration for knowledge layer** - Future optimization
   - When knowledge DB grows, extract to TOON format
   - Use TOON for fact storage (40% savings)
   - Conversion overhead is minimal
   - Can be added post-v2.0 without breaking changes

**Bottom Line:**
Keep JSON for now, plan TOON for knowledge extraction as a v2.1 optimization. The structured hierarchy in droid outputs makes JSON essential for the immediate use case.

---

## References

- **TOON Spec:** TOON (Token-Oriented Object Notation) - Anthropic format for token-efficient structured data
- **K-LEAN TOON Plan:** `/home/calin/claudeAgentic/review-system-backup/docs/TOON_INTEGRATION_PLAN.md`
- **Python Toon Lib:** `python-toon>=0.1.0` (already in pyproject.toml)
