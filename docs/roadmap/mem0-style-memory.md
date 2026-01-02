# Mem0-Style Intelligent Memory System

> **Status**: PLANNED
> **Priority**: High
> **Effort**: 2-3 days
> **Dependencies**: Current A+B implementation (completed Dec 2024)

---

## Executive Summary

Implement automatic memory extraction and learning, inspired by [Mem0](https://github.com/mem0ai/mem0), to make SmolKLN agents truly learn and improve over time without manual intervention.

**Current State (A+B - Completed)**:
- Session memory persists to KB after agent execution
- Serena lessons sync to KB via `/kln:remember`
- Agents can search prior learnings

**Future State (Mem0-Style)**:
- Automatic fact extraction after every significant action
- Memory compression (90% token reduction like Mem0)
- Cross-session learning without manual `/kln:remember`
- Episodic/Semantic/Procedural memory separation

---

## Research Findings

### What Mem0 Does Well

| Feature | Description | Value |
|---------|-------------|-------|
| **Auto-extraction** | LLM extracts facts from conversations | No manual SaveThis needed |
| **Compression** | 90% token reduction via summarization | Cheaper, faster context |
| **Scoped memory** | user_id, agent_id, run_id, app_id | Multi-tenant isolation |
| **Deduplication** | Checks before saving | No redundant entries |
| **Categories** | diet, preferences, work, etc. | Better retrieval |

### Memory Taxonomy (Industry Standard)

```
┌─────────────────────────────────────────────────────────────────┐
│                    COGNITIVE MEMORY TYPES                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  EPISODIC MEMORY                                                 │
│  "What happened"                                                 │
│  ├── Last time I debugged auth, the issue was in JWT validation │
│  ├── User asked about BLE optimization on Dec 15                │
│  └── Security audit found 3 issues in payment module            │
│                                                                  │
│  SEMANTIC MEMORY                                                 │
│  "What I know" (facts)                                          │
│  ├── This project uses React 18 + TypeScript                    │
│  ├── User prefers detailed explanations                         │
│  └── JWT tokens expire after 1 hour in this system              │
│                                                                  │
│  PROCEDURAL MEMORY                                               │
│  "How to do things"                                             │
│  ├── To deploy: run tests → build → push to registry            │
│  ├── To debug BLE: check connection interval first              │
│  └── Security review process: OWASP top 10 → auth → crypto      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Framework Comparison

| Framework | Memory Persistence | Auto-Extract | Compression |
|-----------|-------------------|--------------|-------------|
| **Mem0** | Vector DB + Graph | ✅ Yes | ✅ 90% reduction |
| **LangGraph** | SQLite checkpoints | ❌ No | ❌ No |
| **CrewAI** | ChromaDB + SQLite | ❌ No | ❌ No |
| **Smolagents** | None (in-memory) | ❌ No | ❌ No |
| **K-LEAN (current)** | fastembed + Serena | Manual | ❌ No |
| **K-LEAN (planned)** | fastembed + Serena | ✅ Yes | ✅ Yes |

---

## Implementation Plan

### Phase 1: Auto-Extraction (1 day)

**Goal**: Extract facts automatically after agent actions without manual SaveThis.

#### New Class: `SmartMemory`

```python
# src/klean/smol/smart_memory.py

class SmartMemory:
    """Mem0-inspired automatic memory extraction."""

    EXTRACTION_PROMPT = '''
    Analyze this agent interaction and extract key facts.

    ACTION: {action}
    RESULT: {result}

    Extract ONLY if valuable for future reference:
    - Specific file:line findings
    - Patterns or gotchas discovered
    - Solutions that worked
    - User preferences learned

    Return JSON:
    {
      "facts": [
        {
          "type": "episodic|semantic|procedural",
          "title": "short title",
          "content": "the insight",
          "confidence": 0.0-1.0
        }
      ],
      "should_save": true/false
    }

    Return {"facts": [], "should_save": false} if nothing worth saving.
    '''

    def __init__(self, memory: AgentMemory, extraction_model: str = "qwen3-coder"):
        self.memory = memory
        self.extraction_model = extraction_model
        self._extraction_cache = {}  # Prevent duplicate extractions

    async def auto_capture(self, action: str, result: str) -> int:
        """Extract and store learnings automatically."""
        # Skip if too short or already processed
        content_hash = hash(f"{action}:{result[:100]}")
        if content_hash in self._extraction_cache:
            return 0

        # Use fast model for extraction
        facts = await self._extract_facts(action, result)

        saved = 0
        for fact in facts:
            if fact["confidence"] < 0.6:
                continue

            # Check for duplicates
            if self._is_duplicate(fact):
                continue

            self.memory.knowledge_db.add_structured({
                "title": fact["title"],
                "summary": fact["content"],
                "type": fact["type"],
                "source": "auto_extract",
                "tags": ["auto", fact["type"]],
                "quality": "medium" if fact["confidence"] < 0.8 else "high",
                "confidence_score": fact["confidence"],
            })
            saved += 1

        self._extraction_cache[content_hash] = saved
        return saved
```

#### Integration Point

```python
# In executor.py, after agent completes

# Current (manual)
self.memory.persist_session_to_kb(agent_name)

# New (auto-extraction)
if self.smart_memory:
    extracted = await self.smart_memory.auto_capture(
        action=f"Agent {agent_name}: {task}",
        result=output
    )
    result["auto_extracted"] = extracted
```

### Phase 2: Memory Compression (0.5 days)

**Goal**: Reduce token usage when injecting context, like Mem0's 90% reduction.

#### Compression Strategy

```python
class MemoryCompressor:
    """Compress memories for efficient context injection."""

    def compress_for_context(self, memories: List[Dict], max_tokens: int = 500) -> str:
        """Convert memories to compressed context string."""

        # Group by type
        episodic = [m for m in memories if m.get("type") == "episodic"]
        semantic = [m for m in memories if m.get("type") == "semantic"]
        procedural = [m for m in memories if m.get("type") == "procedural"]

        parts = []

        # Semantic: Just facts
        if semantic:
            facts = [f"- {m['title']}" for m in semantic[:5]]
            parts.append(f"KNOWN FACTS:\n" + "\n".join(facts))

        # Episodic: Brief references
        if episodic:
            refs = [f"- {m['title']} ({m.get('source_path', 'recent')})"
                    for m in episodic[:3]]
            parts.append(f"PRIOR EXPERIENCES:\n" + "\n".join(refs))

        # Procedural: Condensed workflows
        if procedural:
            procs = [f"- {m['title']}: {m['summary'][:50]}..."
                     for m in procedural[:2]]
            parts.append(f"KNOWN PROCEDURES:\n" + "\n".join(procs))

        return "\n\n".join(parts)
```

**Before (verbose)**:
```
## Prior Knowledge
- Thinking models need longer timeouts: Thinking models (deepseek, glm,
  minimax, kimi) take 60+ seconds to process complex prompts. Default 60s
  timeout is insufficient. Timeouts by model: coding-qwen: 90s (fast,
  non-thinking), architecture-deepseek: 120s (thinking model)...
```

**After (compressed)**:
```
KNOWN FACTS:
- Thinking models need 120s timeout
- Use jq -r '// empty' for null handling
- Per-project KB sockets: /tmp/kb-{hash}.sock

PRIOR EXPERIENCES:
- Security audit found SQL injection (agent_security-auditor)
- BLE optimization solved with 100ms intervals (Dec 2024)
```

### Phase 3: Memory Scoping (0.5 days)

**Goal**: Isolate memories by agent, session, and project for better retrieval.

#### Scoped Search

```python
def search_scoped(
    self,
    query: str,
    agent_id: str = None,
    session_id: str = None,
    memory_type: str = None,
    min_confidence: float = 0.5
) -> List[Dict]:
    """Search with scope filters like Mem0."""

    results = self.knowledge_db.search(query, limit=20)

    # Filter by scope
    filtered = []
    for r in results:
        if agent_id and r.get("source") != f"agent_{agent_id}":
            continue
        if session_id and session_id not in r.get("source_path", ""):
            continue
        if memory_type and r.get("type") != memory_type:
            continue
        if r.get("confidence_score", 0.7) < min_confidence:
            continue
        filtered.append(r)

    return filtered[:10]
```

### Phase 4: Step Callbacks (0.5 days)

**Goal**: Extract learnings after each agent step, not just at the end.

#### Smolagents Integration

```python
def step_callback(step: ActionStep) -> None:
    """Called after each agent step - extract learnings."""

    # Only process significant steps
    if step.tool_calls and step.observations:
        for tool_call, observation in zip(step.tool_calls, step.observations):
            # Extract if tool found something interesting
            if "error" in observation.lower() or "found" in observation.lower():
                smart_memory.queue_extraction(
                    action=f"{tool_call.name}({tool_call.arguments})",
                    result=observation
                )

# In executor.py
smol_agent = CodeAgent(
    tools=tools,
    model=model,
    step_callbacks=[step_callback]  # NEW
)
```

---

## Configuration

### New Settings

```yaml
# ~/.klean/config.yaml

memory:
  auto_extract: true           # Enable Mem0-style extraction
  extraction_model: qwen3-coder  # Fast model for extraction
  compression: true            # Compress context injection
  max_context_tokens: 500      # Limit injected context

  # Scoping
  scope_by_agent: true         # Isolate agent memories
  scope_by_session: false      # Keep cross-session learning

  # Quality thresholds
  min_confidence: 0.6          # Skip low-confidence extractions
  dedup_threshold: 0.85        # Skip if 85% similar exists

  # Cost control
  extract_every_n_steps: 3     # Don't extract every step
  max_extractions_per_run: 10  # Limit per agent run
```

### Cost Estimation

| Operation | Model | Tokens | Cost (NanoGPT) |
|-----------|-------|--------|----------------|
| Extract facts | qwen3-coder | ~500 | Included in $15/mo |
| Compress context | Local | 0 | Free |
| Search KB | fastembed | 0 | Free |

**Per agent run**: ~500-1000 tokens for extraction = negligible cost

---

## Migration Path

### From Current to Mem0-Style

```
PHASE 1 (Completed):
├── Session memory persists to KB ✅
├── Serena lessons sync to KB ✅
└── Manual SaveThis/FindKnowledge ✅

PHASE 2 (This Plan):
├── Auto-extraction after agent runs
├── Memory compression for context
├── Scoped search filters
└── Step callbacks (optional)

PHASE 3 (Future):
├── Graph-based relationships (like Mem0 + Neptune)
├── Memory decay and cleanup
└── Cross-project memory sharing
```

---

## Success Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Manual SaveThis needed | Every insight | Only special cases |
| Context injection tokens | ~2000 | ~500 (75% reduction) |
| Agent learns from prior runs | Sometimes | Always |
| Time to find prior solution | Manual search | Automatic |

---

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Extraction cost | Medium | Use fast model, limit frequency |
| False positives | Low | Confidence threshold + dedup |
| Slow extraction | Medium | Async, batch processing |
| Over-extraction | Low | Max extractions per run |

---

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1: Auto-Extract | 1 day | `SmartMemory` class, integration |
| Phase 2: Compression | 0.5 day | `MemoryCompressor`, reduced tokens |
| Phase 3: Scoping | 0.5 day | Filtered search, agent isolation |
| Phase 4: Callbacks | 0.5 day | Step-level extraction |
| Testing & Polish | 0.5 day | E2E tests, docs |
| **Total** | **3 days** | Full Mem0-style memory |

---

## References

- [Mem0 GitHub](https://github.com/mem0ai/mem0) - Core inspiration
- [Mem0 Docs](https://docs.mem0.ai) - API patterns
- [Cognitive Architectures for Language Agents](https://arxiv.org/abs/2309.02427) - Memory taxonomy
- [LangChain Memory Types 2025](https://sparkco.ai/blog/exploring-langchain-memory-types-in-2025-a-deep-dive)
- [CrewAI Memory Docs](https://docs.crewai.com/en/concepts/memory)

---

## Appendix: API Design

### SmartMemory API

```python
# Initialize
smart_memory = SmartMemory(
    agent_memory=agent_memory,
    extraction_model="qwen3-coder",
    auto_extract=True
)

# Auto-capture (called automatically)
extracted = await smart_memory.auto_capture(action, result)

# Manual capture with type
smart_memory.save(
    content="Use 120s timeout for thinking models",
    memory_type="semantic",
    confidence=0.9
)

# Scoped search
memories = smart_memory.search(
    "timeout issues",
    agent_id="security-auditor",
    memory_type="episodic"
)

# Compressed context for prompt
context = smart_memory.get_compressed_context(
    query="debugging auth",
    max_tokens=500
)
```

---

*Created: 2024-12-23*
*Author: K-LEAN Development*
*Based on: Mem0, LangChain, CrewAI memory research*
