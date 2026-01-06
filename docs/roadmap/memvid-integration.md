# Memvid Integration - Knowledge DB Evolution

**Status**: Research Complete
**Priority**: Medium
**Effort**: 4-5 days
**Date**: January 2025

## Overview

Research into replacing K-LEAN's file-based Knowledge DB with Memvid's single-file memory format, while preserving K-LEAN's superior search quality (RRF + reranking).

## Projects Analyzed

### Memvid (github.com/memvid/memvid)
- **Description**: Single-file memory layer for AI agents
- **Storage**: `.mv2` format (video-based, compressed)
- **Search**: BM25 (Tantivy) + HNSW vector search
- **Speed**: Sub-5ms retrieval
- **Core**: Rust with Python/JS bindings

### Claude-Brain (github.com/memvid/claude-brain)
- **Description**: Claude Code plugin using Memvid
- **Storage**: `.claude/mind.mv2`
- **Commands**: `/mind stats`, `/mind search`, `/mind ask`, `/mind recent`
- **Features**: Auto-capture session context, decisions, bugs, solutions

### Mem0 (github.com/mem0ai/mem0)
- **Description**: Intelligent memory layer with graph support
- **Features**: Vector + Graph memory, multi-hop traversal, LLM query refinement
- **Use Case**: Relationships between entities ("Who is Emma's manager's boss?")

## Current K-LEAN vs Alternatives

| Feature | K-LEAN | Memvid | Claude-Brain | Mem0 |
|---------|--------|--------|--------------|------|
| **Storage** | 4 files | 1 file (.mv2) | 1 file (.mv2) | Vector DB + Graph |
| **Dense Search** | BGE (fastembed) | HNSW + ONNX | HNSW + ONNX | Configurable |
| **Sparse Search** | BM42 (learned) | BM25 (Tantivy) | BM25 (Tantivy) | None |
| **RRF Fusion** | Yes | No | No | No |
| **Cross-encoder** | Yes (MiniLM) | No | No | Optional |
| **Graph Relations** | No | No | No | Yes (Neo4j) |
| **Speed** | 100-500ms | Sub-5ms | Sub-5ms | 50-200ms |
| **Portability** | Medium | Excellent | Excellent | Low (DB dependent) |

## K-LEAN's Unique Strengths

1. **RRF Fusion** - Combines dense + sparse with Reciprocal Rank Fusion
2. **BM42 Sparse** - Learned token weights (better than classic BM25)
3. **Cross-encoder Reranking** - Final precision boost for top results
4. **Human-readable Storage** - JSONL can be manually edited/reviewed

## Implementation Options

### Option A: Use Both (Recommended Start)
```
Claude-Brain: Auto-capture session memory (.claude/mind.mv2)
K-LEAN:       Multi-model reviews + explicit learnings (.knowledge-db/)
```
- No conflict - different purposes
- claude-brain = "What happened in past sessions?"
- K-LEAN KB = "What solutions/patterns did we learn?"

### Option B: Replace K-LEAN KB with Memvid Backend
```
.knowledge-db/
└── knowledge.mv2     # Single file (Memvid)
```
- Keep K-LEAN's RRF + reranking as wrapper
- Gain: Speed, portability, crash safety
- Lose: Human-readable JSONL

### Option C: Extend Claude-Brain
- Fork/extend to add K-LEAN's search quality
- RRF fusion layer
- Cross-encoder reranking
- Structured entry types

## Proposed Architecture (Option B)

```
┌─────────────────────────────────────────────────────────────┐
│                    K-LEAN + Memvid Hybrid                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Storage: Single .mv2 file (Memvid)                        │
│  Speed: Sub-ms Rust core (Memvid)                          │
│  Search: Hybrid RRF + Reranking (K-LEAN)                   │
│  Integration: Claude Code commands (K-LEAN)                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Phases

| Phase | Task | Effort | Deliverable |
|-------|------|--------|-------------|
| **0** | Install & test Memvid | 2 hours | Working prototype |
| **1** | Create `MemvidBackend` class | 1 day | Drop-in storage replacement |
| **2** | Add RRF fusion layer | 0.5 day | Combined lex+vec results |
| **3** | Integrate cross-encoder | 0.5 day | Optional reranking |
| **4** | Migration tool | 0.5 day | Convert existing KB to .mv2 |
| **5** | Update CLI & commands | 1 day | Full integration |

## Code Sketch

```python
class KLeanMemvidRetriever:
    """K-LEAN search quality + Memvid storage speed."""

    RRF_K = 60

    def __init__(self, mv2_file: str):
        self.memvid = MemvidRetriever(mv2_file)
        self._reranker = None  # Lazy load

    def search(self, query: str, top_k: int = 5, rerank: bool = True):
        # Layer 1: Lexical search (Memvid BM25 - fast)
        lex_results = self.memvid.search_lex(query, top_k=top_k * 2)

        # Layer 2: Vector search (Memvid HNSW - fast)
        vec_results = self.memvid.search_vec(query, top_k=top_k * 2)

        # Layer 3: RRF Fusion (K-LEAN quality)
        fused = self._rrf_fusion(lex_results, vec_results)

        # Layer 4: Cross-encoder reranking (optional)
        if rerank:
            fused = self._rerank(query, fused[:top_k * 2])

        return fused[:top_k]

    @staticmethod
    def _rrf_score(ranks: list[int], k: int = 60) -> float:
        return sum(1.0 / (k + r) for r in ranks if r > 0)
```

## Expected Outcomes

| Metric | Current K-LEAN | With Memvid |
|--------|----------------|-------------|
| **Search latency** | 100-500ms | <20ms |
| **File count** | 4 files | 1 file |
| **Portability** | Medium | Excellent (git-friendly) |
| **Crash safety** | Basic | WAL + append-only |
| **Search quality** | Excellent | Excellent (preserved) |

## Dependencies

```bash
# Memvid CLI
npm install -g memvid-cli

# Or Python bindings (when available)
pip install memvid
```

## References

- Memvid: https://github.com/memvid/memvid
- Claude-Brain: https://github.com/memvid/claude-brain
- Mem0: https://github.com/mem0ai/mem0
- BM42 (Qdrant): https://qdrant.tech/articles/bm42/
- RRF Paper: https://dl.acm.org/doi/10.1145/1571941.1572114

## Decision Log

- **2025-01**: Research completed, Option A recommended as starting point
- Evaluate claude-brain for 1-2 weeks before deeper integration
- K-LEAN's RRF + reranking provides measurable quality improvement
