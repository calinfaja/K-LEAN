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

## Patterns for Later (v2.0)

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
