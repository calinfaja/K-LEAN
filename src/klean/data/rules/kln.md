# K-LEAN

**Style:**
- NEVER use emojis in code, commits, or responses unless explicitly requested

**Suggest these when:**
- After significant code changes → `/kln:quick`
- Stuck debugging 10+ min → `/kln:rethink`
- Need thorough review → `/kln:multi`
- Found useful info during work → `/kln:learn`
- End of session → `/kln:remember`
- "How did we solve X before?" → `FindKnowledge <query>`

**Knowledge Commands:**
- `/kln:learn` - Extract learnings from current context (mid-session)
- `/kln:learn "topic"` - Focused extraction on specific topic
- `/kln:remember` - Comprehensive end-of-session capture

**Hook Keywords (type directly):**
- `FindKnowledge <query>` - Search knowledge DB
- `SaveInfo <url>` - Evaluate URL with LLM and save if relevant

**Python API (cross-platform):**
```python
# Knowledge capture via TCP (server must be running)
# Use kb_utils.py or knowledge-capture.py from pipx venv

# Types: lesson, finding, solution, pattern, warning, best-practice
# Priority: low, medium, high, critical
```

**CLI:** `kln status` | `kln doctor -f` | `kln model list`

**Help:** `/kln:help`
