# K-LEAN Lessons Learned

> Practical patterns from Claude Code community that work. KISS approach.

---

## Patterns We Already Have (Keep)

| Pattern | Implementation | Why It Works |
|---------|----------------|--------------|
| **Multi-Model Consensus** | `reviews.consensus_review()` | Run 3+ models in parallel via async httpx |
| **Health Fallback** | `reviews._get_healthy_models()` | Auto-switch to working model if one fails |
| **Thinking Models** | `reviews._extract_content()` | Check `reasoning_content` for DeepSeek/GLM, strip `<think>` tags |
| **Knowledge Inject** | `hooks.py` prompt handler | Query KB, add to prompt if relevant |
| **SmolKLN Agents** | `kln-smol` | Tool-equipped specialist agents |

These are solid. Don't change.

---

## Patterns to Add (High Value, Low Effort)

### 1. JSON Output Mode

**What:** Add structured JSON output to review commands.

**Why:** Enables pipeline chaining and automation of review results.

**How:** The `/kln:quick` and `/kln:multi` slash commands already support `--output json` flag. The `reviews.py` module returns structured dicts that can be serialized.

**Status:** Partially implemented via slash command flags. Full CLI support pending.

---

### 2. Session Summary Before Clear

**What:** Quick command to dump session learnings to KB.

**Why:** Don't lose knowledge on `/clear`.

**How:** We already have `/kln:remember` command in `commands/kln/remember.md`.

**Check:** Verify it works: `cat commands/kln/remember.md`

**Effort:** Already done, just test it.

---

## Patterns to Skip (Over-Engineering)

| Pattern | Why Skip |
|---------|----------|
| Context Monitor Hook | Claude already warns. Adds noise. |
| TDD Enforcer Hook | Annoying in practice. Trust the developer. |
| MCP Funnel | Only useful with 5+ MCP servers. We have 4. |
| Cipher MCP | We already have txtai KB. Duplicate functionality. |
| Post-edit Linting Hook | Breaks flow. Run linter manually. |

---

## Competitive Analysis (Jan 2026)

### K-LEAN vs Other Frameworks

| Framework | Focus | Stars | Commands |
|-----------|-------|-------|----------|
| **SuperClaude** | Full dev lifecycle | 19.3k | 30 |
| **Superpowers** | Planning workflow | ~500 | 3 |
| **K-LEAN** | Multi-model reviews | New | 9 |

### K-LEAN Unique Strengths (Keep These)

| Feature | K-LEAN | Others |
|---------|--------|--------|
| Multi-model consensus | ✅ 3-5 models parallel | ❌ |
| Knowledge DB persistence | ✅ fastembed semantic search | ❌ |
| LiteLLM cost routing | ✅ Multi-provider | ❌ |
| Rethink (contrarian debug) | ✅ 4 techniques | ❌ |
| Thinking model support | ✅ DeepSeek, GLM, Kimi | Limited |
| Embedded/systems droids | ✅ arm-cortex, c-pro, rust | ❌ |

### Strategic Position

**K-LEAN is an ADDON, not a competitor.**

Works alongside SuperClaude/Superpowers:
- SuperClaude → Workflow orchestration (30 commands)
- K-LEAN → Review engine + knowledge (multi-model consensus)

```
SuperClaude /sc:implement → K-LEAN reviews → SuperClaude /sc:test
```

---

## Patterns for Later (v2.0)

### K-LEAN as MCP Server (Future Enhancement)

**What:** Expose K-LEAN as MCP tools instead of slash commands.

**Why:**
- Claude can call K-LEAN **proactively** (not just when user asks)
- Seamless chaining with other MCP tools (Serena → K-LEAN → Context7)
- Structured JSON responses instead of parsing stdout
- Works with any framework (SuperClaude, Superpowers, vanilla)

**Current (Reactive):**
```
User types: /kln:quick security
Hook intercepts → Spawns bash → Returns stdout
```

**With MCP (Proactive):**
```
Claude decides: "I wrote auth code, should review"
Calls: mcp__klean__consensus_review(focus="security")
Returns: Structured JSON
```

**Proposed MCP Tools:**
```python
mcp__klean__quick_review(focus, model)
mcp__klean__consensus_review(focus, models)
mcp__klean__rethink(context)
mcp__klean__search_knowledge(query)
mcp__klean__save_knowledge(insight)
mcp__klean__get_models()
mcp__klean__health_check()
```

**Effort:** ~5 hours total
**Priority:** Low (current system works fine)
**Trigger:** When team adoption requires tighter integration

---

### GitHub PR Integration

**What:** Post review comments directly to PR.

**Why:** Real value for teams. Top tools (CodeRabbit, Qodo) do this.

**How:** `gh pr comment $PR_NUM --body "$(cat review.md)"`

**Effort:** 2 hours for wrapper script

---

### ~~Lightweight Install: fastembed + numpy~~ DONE

**Status:** Completed January 2026

**What was done:**
- Replaced txtai + sentence-transformers with fastembed + numpy
- Install size: ~7GB -> ~200MB (97% reduction)
- Uses BAAI/bge-small-en-v1.5 (better than MiniLM on MTEB benchmarks)
- Added entry caching for 35x faster repeated searches
- Auto-migration from txtai index format

**Files Modified:**
| File | Change |
|------|--------|
| `knowledge_db.py` | fastembed + numpy backend |
| `knowledge-server.py` | Updated to use new KnowledgeDB |
| `pyproject.toml` | fastembed>=0.3.0, numpy>=1.24.0 |

---

### Cost Tracking

**What:** Log tokens used per model per review.

**Why:** Know what models cost. LiteLLM has this built-in.

**How:** Query `http://localhost:4000/spend/logs`

**Effort:** 1 hour for logging script

---

### Feedback Loop

**What:** Save which reviews were useful.

**Why:** Learn what models/prompts work best.

**How:** Add to review output: "Was this helpful? (y/n)" → save to KB

**Effort:** 2 hours

---

## Key Takeaways from Research

1. **Multi-model consensus is unique** - No other tool does this. Keep it.

2. **LiteLLM is the right choice** - Production-ready, active development, MIT license.

3. **fastembed for KB is solid** - Lightweight ONNX-based, local, no external dependencies.

4. **SmolKLN agents are powerful** - Tool-equipped agents with structured output.

5. **Top competitors focus on PR integration** - That's the gap if we want team adoption.

---

## Next Steps (Priority Order)

1. [ ] Full JSON output support for CLI review commands
2. [x] Test /kln:remember command (validated in QA v1.0.0b7)
3. [x] Document in README for OSS release (done)
4. [ ] GitHub PR integration for team adoption
5. [ ] Cost tracking via LiteLLM spend logs

---

*Last updated: 2026-02*
