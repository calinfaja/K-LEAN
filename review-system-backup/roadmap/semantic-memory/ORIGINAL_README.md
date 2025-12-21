# Next Features - Roadmap

## Overview

Enhancement ideas for the Claude Code review and memory system based on research into AgentDB, vector databases, and AI agent memory systems.

---

## Feature List

| # | Feature | Priority | Complexity | Status |
|---|---------|----------|------------|--------|
| 1 | [Semantic Memory System](#1-semantic-memory-system) | High | Medium | Planned |
| 2 | [Review Metrics Logging](#2-review-metrics-logging) | Medium | Low | Idea |
| 3 | [Smart Model Routing](#3-smart-model-routing) | Low | High | Research |
| 4 | [MCP Server for txtai](#4-mcp-server-for-txtai) | Medium | Medium | Idea |

---

## 1. Semantic Memory System

**File:** [SEMANTIC_MEMORY_SYSTEM.md](./SEMANTIC_MEMORY_SYSTEM.md)

**Problem:** Research findings get lost across sessions. Serena is keyword-only.

**Solution:** Add txtai as semantic index for Serena memories.

**Key Components:**
- `serena-index.py` - Index Serena memories in txtai
- `GoodJob` hook - Capture valuable findings
- `FindSimilar` search - Semantic retrieval

**Dependencies:** `pip install txtai`

---

## 2. Review Metrics Logging

**Problem:** No visibility into which models perform best for which types of reviews.

**Solution:** Log review outcomes and track success rates.

**What to Track:**
```
| Metric | Purpose |
|--------|---------|
| Model used | qwen/deepseek/glm |
| Review type | security/architecture/standards |
| Grade given | A-F |
| Issues found | Count |
| Time taken | Seconds |
| User accepted? | Y/N (if tracked) |
```

**Implementation:**
- Add logging to review scripts
- Store in SQLite or JSON
- Dashboard script to view stats

---

## 3. Smart Model Routing

**Problem:** Currently manual selection of qwen/deepseek/glm.

**Solution:** Auto-route based on code/query type.

**Routing Logic:**
```
If query contains "security", "buffer", "memory" → qwen
If query contains "architecture", "design", "coupling" → deepseek
If query contains "MISRA", "standard", "compliance" → glm
```

**Advanced:** Use embeddings to classify query intent.

**Research:** See [LLM Cascade Routing paper](https://arxiv.org/pdf/2410.10347)

---

## 4. MCP Server for txtai

**Problem:** txtai is Python scripts, not integrated as MCP tools.

**Solution:** Wrap txtai in MCP server for native Claude integration.

**Tools to Expose:**
```
mcp__txtai__search - Semantic search
mcp__txtai__index - Add to index
mcp__txtai__sync - Re-index Serena memories
```

**Benefit:** Use in Claude naturally: "search my knowledge for BLE patterns"

---

## Research Findings Summary

### Evaluated Tools

| Tool | Type | Best For | Decision |
|------|------|----------|----------|
| AgentDB | Vector DB + RL | Full agent system | Too complex (29 tools) |
| txtai | Vector DB | Semantic search addon | ✅ **Selected** |
| Mem0 | Memory layer | Conversation memory | Good, but txtai simpler |
| Qdrant | Vector DB | High performance | Overkill for our needs |

### Key Insight

> "The performance comes from HNSW indexing, not tool count."
>
> AgentDB's 29 tools provide same performance as txtai's 3 methods.
> Both use HNSW = O(log n) = <1ms search.

### Architecture Pattern Validated

Our system follows industry best practices:
- Claude (primary) → LiteLLM → Local models (fallback)
- This matches [ICLR 2025 LLM Routing research](https://proceedings.iclr.cc/paper_files/paper/2025/file/5503a7c69d48a2f86fc00b3dc09de686-Paper-Conference.pdf)

---

## Implementation Priority

```
Week 1: Semantic Memory System (txtai + Serena)
        └── Core value: don't lose research findings

Week 2: Review Metrics Logging
        └── Understand which models work best

Week 3: MCP Server wrapper (if needed)
        └── Smoother integration

Future: Smart Model Routing
        └── Auto-select best model for query type
```

---

## Quick Start (When Ready)

```bash
# Install txtai
pip install txtai

# Index existing Serena memories
python ~/.claude/scripts/serena-index.py sync

# Capture a finding
GoodJob "https://example.com" "Technical description here"

# Search semantically
FindSimilar "wireless optimization techniques"
```
