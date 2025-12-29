# TOON Integration - Quick Summary

## The Opportunity
Current K-LEAN extracts facts using Haiku in **JSON format**.
TOON format uses **40% fewer tokens** for the same data.

## The Impact
```
Current: 1,000 extractions × 800 tokens = 800,000 tokens/month
With TOON: 1,000 extractions × 480 tokens = 480,000 tokens/month
Savings: 320,000 tokens/month (~40%)
Cost reduction: ~$0.02/month per 100 reviews
```

## The Plan (2 Weeks)

### Week 1: Foundation
```
Day 1-3: Build TOON utilities & test framework
├─ toon_utils.py (JSON↔TOON converter)
├─ Test suite (round-trip validation)
└─ Updated extraction prompt
```

### Week 2: Prototype → Deploy
```
Day 4-6: Modify extraction pipeline
├─ Update fact-extract.sh to use TOON
├─ Validate fact quality
└─ Token count comparison

Day 7-9: Optimize & test edge cases
├─ Performance benchmarking
├─ Edge case handling
└─ Rollback procedures

Day 10-12: Deploy to production
├─ Production rollout
├─ Monitor for 1 week
└─ Update documentation
```

## Architecture

### Storage Strategy (Smart)
```
Review Text
    ↓
Haiku (TOON format request)
    ↓ [40% fewer tokens used]
TOONConverter (TOON → JSON)
    ↓
Knowledge DB (stored as JSON)
    ↓ [optional]
Context Injection (as TOON)
    ↓ [additional token savings]
Review Prompt
```

**Key insight:** Use efficient TOON for LLM communication, store reliable JSON internally.

## Success Metrics

| Metric | Target | Status |
|--------|--------|--------|
| Token reduction | ≥40% | Benchmark needed |
| Fact quality | Maintained | Validation needed |
| Backward compatibility | 100% | Tests needed |
| Parse success rate | ≥95% | Tests needed |
| Data loss | 0% | Tests needed |

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Haiku doesn't understand TOON | Test with sample prompts first |
| Parser fails on edge cases | Fallback to JSON parsing |
| Token savings < 30% | Document reality; scales with volume |
| Performance regression | Benchmark extraction time before/after |

## Business Case

### Short Term (Next 3 months)
- ✅ Operational cost reduction (~$0.02/month)
- ✅ System optimization best practices
- ✅ Foundation for future improvements

### Medium Term (Next 6-12 months)
- 📈 Apply TOON to all extraction (commits, web)
- 📈 Potential 60-70% overall token reduction
- 📈 Enterprise feature: "Token-efficient reviews"

### Long Term
- 🚀 Scale to thousands of reviews/month
- 🚀 Market differentiation via cost efficiency
- 🚀 LLM optimization expertise

## Next Steps

1. **Review this plan** ← You are here
2. **Approve & kick off Phase 1** (if aligned)
3. **Build TOON utilities** (Days 1-3)
4. **Prototype on existing entries** (Days 4-6)
5. **Validate & optimize** (Days 7-9)
6. **Deploy & monitor** (Days 10-12)
7. **Document results & learnings**

## Questions to Discuss

1. **Scope:** Start with extraction only, or include context injection?
2. **Timeline:** 2-week aggressive or 3-week conservative?
3. **Rollback:** Auto-fallback to JSON or manual rollback?
4. **Monitoring:** What success metrics matter most to you?
5. **Future:** Apply TOON to other extractors (commits, web)?

---

## Document Locations

- **Full Plan:** `TOON_INTEGRATION_PLAN.md` (comprehensive)
- **This Summary:** `TOON_QUICK_SUMMARY.md` (this file)
- **Implementation:** To be created during Phase 1
