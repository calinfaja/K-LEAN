# K-LEAN Project Overview

## What is K-LEAN?

**K-LEAN** (Knowledge-Lean) is a Multi-Model Code Review & Knowledge Capture System designed as an addon for Claude Code.

### The Problem

Claude Code uses a single AI model for all tasks. This creates:
- Single point of view on code quality
- No persistent memory across sessions
- Limited specialized expertise

### The Solution

K-LEAN adds:
1. **Multi-Model Reviews** - Get consensus from 3-5 different LLMs in parallel
2. **Persistent Knowledge DB** - Semantic search across sessions with txtai embeddings
3. **Specialist Droids** - 8 expert personas (security, performance, Rust, ARM, etc.)
4. **LiteLLM Routing** - Access 12+ models via NanoGPT/OpenRouter

## Target Users

- Claude Code power users who want deeper code reviews
- Developers working on security-critical or performance-sensitive code
- Teams wanting persistent project knowledge across AI sessions

## Key Differentiators

| Feature | Claude Code Alone | With K-LEAN |
|---------|-------------------|-------------|
| Review perspectives | 1 model | 3-5 models consensus |
| Session memory | None | Semantic KB with 1hr idle timeout |
| Specialist review | Generic | 8 domain experts |
| Model flexibility | Claude only | 12+ models via LiteLLM |

## Positioning

**K-LEAN is an ADDON, not a replacement.**

- Works alongside Claude Code (not instead of)
- Compatible with SuperClaude, Superpowers, etc.
- Pure plugin approach - never modifies user's CLAUDE.md
- Enhances Claude's capabilities without replacing its core

## Unique Strengths (No Other Tool Has)

1. **Multi-model consensus** - Parallel reviews with agreement scoring
2. **Per-project Knowledge DB** - Isolated semantic search per git repo
3. **Rethink command** - Contrarian debugging with 4 techniques
4. **Thinking model support** - Handles DeepSeek, GLM, Kimi response formats
5. **Factory droid integration** - 8 specialist reviewers

## Version

- **Current:** 1.0.0-beta
- **License:** Apache 2.0
- **Status:** Open source release ready

---
*See [architecture.md](architecture.md) for system design*
