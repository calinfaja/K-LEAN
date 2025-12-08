---
name: help
description: List all /kln: custom commands and their functionality
allowed-tools: Read, Glob
argument-hint: ""
---

# /kln:help - K-LEAN Code Review System

Display the complete reference for all `/kln:` commands.

---

```
═══════════════════════════════════════════════════════════════════════════════
  K-LEAN Code Review System v1.0
  Multi-model review framework powered by NanoGPT + LiteLLM
═══════════════════════════════════════════════════════════════════════════════

QUICK REVIEWS ─────────────────────────────────────────── API calls, no tools
┌───────────────────────────┬────────┬────────┬────────┬──────────────────────┐
│ Command                   │ Models │ Method │ Time   │ Description          │
├───────────────────────────┼────────┼────────┼────────┼──────────────────────┤
│ /kln:quickReview <m> <f>  │ 1      │ API    │ ~30s   │ Fast code check      │
│ /kln:quickConsult <m> <q> │ 1      │ API    │ ~60s   │ Get expert opinion   │
│ /kln:quickCompare <focus> │ 3      │ API    │ ~60s   │ Multi-model compare  │
└───────────────────────────┴────────┴────────┴────────┴──────────────────────┘

DEEP REVIEWS ──────────────────────────────────── Headless Claude, full tools
┌───────────────────────────┬────────┬────────┬────────┬──────────────────────┐
│ Command                   │ Models │ Method │ Time   │ Description          │
├───────────────────────────┼────────┼────────┼────────┼──────────────────────┤
│ /kln:deepInspect <m> <f>  │ 1      │ CLI    │ ~3min  │ Thorough inspection  │
│ /kln:deepAudit <focus>    │ 3      │ CLI    │ ~5min  │ Comprehensive audit  │
└───────────────────────────┴────────┴────────┴────────┴──────────────────────┘

ASYNC VARIANTS ────────────────────────────────────── Background execution
┌───────────────────────────┬───────────────────────────┬──────────────────────┐
│ Sync Command              │ Async Variant             │ Use Case             │
├───────────────────────────┼───────────────────────────┼──────────────────────┤
│ /kln:quickReview          │ /kln:asyncQuickReview     │ Quick check + go     │
│ /kln:quickConsult         │ /kln:asyncQuickConsult    │ Get opinion + go     │
│ /kln:quickCompare         │ /kln:asyncQuickCompare    │ Compare + go         │
│ /kln:deepAudit            │ /kln:asyncDeepAudit       │ Full audit + go      │
└───────────────────────────┴───────────────────────────┴──────────────────────┘

DOCUMENTATION ─────────────────────────────────────────── Session reports
┌───────────────────────────┬──────────────────────────────────────────────────┐
│ /kln:createReport <title> │ Create session review document (saves to Serena) │
│ /kln:asyncCreateReport    │ Create report in background                      │
│ /kln:backgroundReport     │ Spawn report creation in separate subagent       │
└───────────────────────────┴──────────────────────────────────────────────────┘

MODELS ────────────────────────────────────────────────────────────────────────
  ✅ RELIABLE (Deep + Quick reviews)
     qwen .......... qwen3-coder ........... Code quality, bugs, memory safety
     kimi .......... kimi-k2-thinking ...... Architecture, planning, design
     glm ........... glm-4.6-thinking ...... Standards, MISRA, compliance

  ⚠️  QUICK ONLY (API calls, no tool support)
     deepseek ...... deepseek-v3-thinking .. Architecture (fails with tools)
     minimax ....... minimax-m2 ............ Research (timeout issues)
     hermes ........ hermes-4-70b .......... Scripting (may hallucinate)

EXECUTION METHODS ─────────────────────────────────────────────────────────────
  API = curl → LiteLLM:4000 → NanoGPT
        Fast (~30-60s), no file access, all 6 models work

  CLI = claude --model → Headless Claude instance
        Slower (~3-5min), full tools (Read, Grep, Bash, Serena)
        Only reliable: qwen, kimi, glm

KNOWLEDGE SYSTEM ──────────────────────────────────────────────────────────────
  GoodJob <url> [focus] .... Capture knowledge from URL to database
  SaveThis <lesson> ........ Save a lesson learned
  FindKnowledge <query> .... Search semantic knowledge database

UTILITIES ─────────────────────────────────────────────────────────────────────
  healthcheck .............. Type in prompt to check all 6 models
  /kln:help ................ This reference guide

EXAMPLES ──────────────────────────────────────────────────────────────────────
  /kln:quickReview qwen "check null pointer handling"
  /kln:quickCompare "review error handling patterns"
  /kln:deepInspect glm "MISRA-C compliance check"
  /kln:deepAudit "full security audit before release"
  /kln:asyncDeepAudit "comprehensive review" → continue coding → check later

═══════════════════════════════════════════════════════════════════════════════
  Output:  /tmp/claude-reviews/{session}/
  Docs:    ~/claudeAgentic/docs/REVIEW_SYSTEM.md
  Scripts: ~/.claude/scripts/
═══════════════════════════════════════════════════════════════════════════════
```

---

## Related Commands

- `/sc:help` - SuperClaude framework commands
- `healthcheck` - Check all 6 models (type in prompt)
- `~/.claude/scripts/sync-check.sh` - Verify scripts synced to backup
