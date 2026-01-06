# K-LEAN Roadmap

Future features and enhancements.

## Planned Features

### [Mem0-Style Intelligent Memory](mem0-style-memory.md) ⭐ HIGH PRIORITY
Automatic memory extraction and learning, inspired by Mem0.
- **Status**: Planned (foundation completed Dec 2024)
- **Effort**: 2-3 days
- **Features**:
  - Auto-extraction after agent actions (no manual SaveThis)
  - Memory compression (90% token reduction)
  - Episodic/Semantic/Procedural memory types
  - Scoped search by agent, session, type

### [Future Features](future-features.md)
Ideas for v2.0:
- K-LEAN as MCP Server (proactive reviews)
- GitHub PR Integration
- Cost Tracking
- JSON output mode

### [klean.core Module Refactor](klean-core-module.md)
Convert klean_core.py to proper importable Python module.
- **Status**: Planned
- **Effort**: 2-4 hours
- **Benefits**:
  - `python -m klean.core` works
  - `from klean.core import LLMClient` works
  - Slash commands use standard module syntax

### [SWE-bench Integration](swe-bench-integration.md)
Benchmarking SmolKLN agents against industry-standard evaluations.
- **Status**: Planned
- **Effort**: 1-2 weeks
- **Features**:
  - SWE-bench Verified (500 instances)
  - Terminal-Bench support
  - Multi-agent strategies (consensus, routing)
  - Cost tracking per benchmark run

### [Memvid Integration](memvid-integration.md)
Replace file-based Knowledge DB with Memvid's single-file format.
- **Status**: Research Complete
- **Effort**: 4-5 days
- **Features**:
  - Single .mv2 file storage (portable, git-friendly)
  - Sub-5ms search (Rust core)
  - Keep K-LEAN's RRF fusion + cross-encoder reranking
  - Migration tool for existing knowledge bases
- **Alternatives Analyzed**: Memvid, Claude-Brain, Mem0

## Completed

- ~~Mem0 Foundation (A+B)~~ → Session persistence + Serena sync (Dec 2024)
- ~~Semantic Memory~~ → Implemented as Knowledge DB
- ~~Open Source Prep~~ → Released under Apache 2.0
