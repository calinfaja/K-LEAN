# K-LEAN Lessons Learned

> Practical patterns from Claude Code community that work. KISS approach.

---

## Patterns We Already Have (Keep)

| Pattern | K-LEAN Script | Why It Works |
|---------|---------------|--------------|
| **Fanning Out** | `parallel-deep-review.sh` | Run 3+ models in parallel, no waiting |
| **Health Fallback** | `get-healthy-models.sh` | Auto-switch to working model if one fails |
| **Thinking Models** | All review scripts | Check `reasoning_content` for DeepSeek/GLM |
| **Knowledge Inject** | Review scripts | Query KB, add to prompt if relevant |

These are solid. Don't change.

---

## Patterns to Add (High Value, Low Effort)

### 1. JSON Output Mode

**What:** Add `--json` flag to scripts for pipeline chaining.

**Why:** Enables `quick-review.sh --json | jq '.grade'` for automation.

**How:**
```bash
# Add to quick-review.sh (after line 130)
if [ "$JSON_OUTPUT" = "true" ]; then
    jq -n --arg grade "$GRADE" --arg risk "$RISK" --arg content "$CONTENT" \
        '{grade: $grade, risk: $risk, content: $content}'
else
    echo "$CONTENT"
fi
```

**Effort:** 30 min per script

---

### 2. Simple Build Check (Stop Hook)

**What:** After deep review, check if build still works.

**Why:** Catches when reviewer suggests breaking changes.

**How:** Add to end of `deep-review.sh`:
```bash
# Optional build check
if [ -f "package.json" ]; then
    npm run build 2>&1 | tail -5 || echo "Build check: FAIL"
elif [ -f "Makefile" ]; then
    make 2>&1 | tail -5 || echo "Build check: FAIL"
fi
```

**Effort:** 15 min

---

### 3. Session Summary Before Clear

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

## Competitive Analysis (Dec 2025)

### K-LEAN vs Other Frameworks

| Framework | Focus | Stars | Commands |
|-----------|-------|-------|----------|
| **SuperClaude** | Full dev lifecycle | 19.3k | 30 |
| **Superpowers** | Planning workflow | ~500 | 3 |
| **K-LEAN** | Multi-model reviews | New | 10 |

### K-LEAN Unique Strengths (Keep These)

| Feature | K-LEAN | Others |
|---------|--------|--------|
| Multi-model consensus | ✅ 3-5 models parallel | ❌ |
| Knowledge DB persistence | ✅ txtai semantic search | ❌ |
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

3. **txtai for KB is solid** - Simple, local, no external dependencies.

4. **Headless Claude is powerful** - Our `deep-review.sh` with allow/deny is best practice.

5. **Top competitors focus on PR integration** - That's the gap if we want team adoption.

---

## Next Steps (Priority Order)

1. [ ] Add `--json` to quick-review.sh
2. [ ] Add build check to deep-review.sh
3. [ ] Test /kln:remember command
4. [ ] Document in README for OSS release

---

*Last updated: 2025-12-21*
