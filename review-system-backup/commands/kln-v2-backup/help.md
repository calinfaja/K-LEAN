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
  K-LEAN Code Review System v2.0
  Multi-model review framework powered by NanoGPT + LiteLLM

  NEW: Unified prompts - all models review ALL areas
═══════════════════════════════════════════════════════════════════════════════

COMMAND CATEGORIES ───────────────────────────────────────────────────────────
  REVIEW .... Find issues in code (Grade, Risk, Issues)
  CONSULT ... Challenge decisions (Verdict, Alternatives)
  DOCUMENT .. Capture knowledge (Lessons, TODOs)

REVIEW COMMANDS ──────────────────────────────────────── All models, all areas
┌───────────────────────────┬────────┬────────┬────────┬──────────────────────┐
│ Command                   │ Models │ Method │ Time   │ Description          │
├───────────────────────────┼────────┼────────┼────────┼──────────────────────┤
│ /kln:quickReview <m> <f>  │ 1      │ API    │ ~30s   │ Fast code review     │
│ /kln:quickCompare <f>     │ 3      │ API    │ ~60s   │ Multi-model consensus│
│ /kln:deepInspect <m> <f>  │ 1      │ CLI    │ ~3min  │ Thorough with tools  │
│ /kln:deepAudit <f>        │ 3      │ CLI    │ ~5min  │ Full audit with tools│
└───────────────────────────┴────────┴────────┴────────┴──────────────────────┘

CONSULT COMMAND ──────────────────────────────────────── Challenge decisions
┌───────────────────────────┬────────┬────────┬────────┬──────────────────────┐
│ /kln:quickConsult <m> <q> │ 1      │ API    │ ~60s   │ Get second opinion   │
└───────────────────────────┴────────┴────────┴────────┴──────────────────────┘

DOCUMENT COMMAND ─────────────────────────────────────── Capture knowledge
┌───────────────────────────┬──────────────────────────────────────────────────┐
│ /kln:createReport <title> │ Create session documentation (saves to Serena)   │
└───────────────────────────┴──────────────────────────────────────────────────┘

ASYNC VARIANTS ────────────────────────────────────────── Background execution
┌───────────────────────────┬───────────────────────────┬──────────────────────┐
│ Sync Command              │ Async Variant             │ Use Case             │
├───────────────────────────┼───────────────────────────┼──────────────────────┤
│ /kln:quickReview          │ /kln:asyncQuickReview     │ Review + keep coding │
│ /kln:quickConsult         │ /kln:asyncQuickConsult    │ Opinion + keep coding│
│ /kln:quickCompare         │ /kln:asyncQuickCompare    │ Compare + keep coding│
│ /kln:deepAudit            │ /kln:asyncDeepAudit       │ Full audit + go      │
│ /kln:createReport         │ /kln:asyncCreateReport    │ Document + keep going│
└───────────────────────────┴───────────────────────────┴──────────────────────┘

MODELS ────────────────────────────────────────────────────────────────────────
  All 6 models use the SAME unified prompt - review ALL areas:

  qwen ........... qwen3-coder ............. Default model
  deepseek ....... deepseek-v3-thinking .... Good for architecture
  kimi ........... kimi-k2-thinking ........ Good for planning
  glm ............ glm-4.6-thinking ........ Good for standards
  minimax ........ minimax-m2 .............. Research focus
  hermes ......... hermes-4-70b ............ Scripting focus

  Default for single-model: qwen
  Default for multi-model: qwen, kimi, glm

REVIEW CHECKLIST (All models check ALL areas) ─────────────────────────────────
  CORRECTNESS ... Logic errors, edge cases, algorithm correctness
  MEMORY SAFETY . Buffer overflows, null pointers, leaks
  ERROR HANDLING  Validation, propagation, resource cleanup
  CONCURRENCY ... Race conditions, ISR safety, shared data
  ARCHITECTURE .. Coupling, cohesion, API consistency
  HARDWARE ...... I/O correctness, volatile usage, timing
  STANDARDS ..... Coding style, MISRA guidelines

EXECUTION METHODS ─────────────────────────────────────────────────────────────
  API = curl → LiteLLM:4000 → NanoGPT
        Fast (~30-60s), no file access, all 6 models

  CLI = claude --model → Headless Claude instance
        Slower (~3-5min), full tools (Read, Grep, Bash, Serena)

KNOWLEDGE SYSTEM ──────────────────────────────────────────────────────────────
  GoodJob <url> [focus] .... Capture knowledge from URL to database
  SaveThis <lesson> ........ Save a lesson learned
  FindKnowledge <query> .... Search semantic knowledge database

UTILITIES ─────────────────────────────────────────────────────────────────────
  healthcheck .............. Type in prompt to check all 6 models
  /kln:help ................ This reference guide

EXAMPLES ──────────────────────────────────────────────────────────────────────
  # Quick review with default model
  /kln:quickReview check memory safety

  # Quick review with specific model
  /kln:quickReview deepseek review architecture patterns

  # Multi-model comparison
  /kln:quickCompare security audit

  # Custom model selection for comparison
  /kln:quickCompare qwen,deepseek,glm check error handling

  # Get second opinion
  /kln:quickConsult kimi Is this state machine approach correct?

  # Deep inspection
  /kln:deepInspect qwen full security audit of crypto module

  # Full audit with tools
  /kln:deepAudit pre-release quality check

  # Async (background) review
  /kln:asyncDeepAudit comprehensive review → continue coding → check later

  # Document session
  /kln:createReport BLE Implementation Complete

═══════════════════════════════════════════════════════════════════════════════
  Output:  /tmp/claude-reviews/{session}/
  Docs:    ~/claudeAgentic/docs/
  Scripts: ~/.claude/scripts/
═══════════════════════════════════════════════════════════════════════════════
```

---

## Related Commands

- `/sc:help` - SuperClaude framework commands
- `healthcheck` - Check all 6 models (type in prompt)
- `~/.claude/scripts/sync-check.sh` - Verify scripts synced to backup
