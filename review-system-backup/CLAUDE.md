# Claude System Configuration

## Knowledge Database System

A semantic knowledge database is available for storing and retrieving valuable information found during research and development.

### Location
- Each project has its own knowledge DB at `.knowledge-db/` in the project root
- Scripts are at `~/.claude/scripts/knowledge-*.py`

### Before Web Searches
**Always check the knowledge DB first** to avoid re-researching topics:

```bash
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-search.py "<topic>"
```

### Capturing Knowledge

**Manual capture** - when you find something valuable:
- User types: `GoodJob <url>` or `GoodJob <url> <instructions>` - capture URL
- User types: `SaveThis <lesson learned>` - always save lesson
- User types: `SaveInfo <text>` - smart save with AI evaluation (Haiku)

**Automatic capture** - runs after WebFetch/WebSearch via hooks

### Searching Knowledge

User can type: `FindKnowledge <query>` to search the knowledge DB

Or you can search programmatically:
```bash
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-search.py "<query>" --format inject
```

### What Gets Stored
- Web findings (URLs, documentation, tutorials)
- Code solutions that worked
- Lessons learned
- Technical constraints discovered
- Best practices

### Schema
```json
{
  "title": "Short descriptive title",
  "summary": "What was found",
  "type": "web|code|solution|lesson",
  "url": "Source URL if applicable",
  "problem_solved": "What problem this solves",
  "key_concepts": ["searchable", "keywords"],
  "relevance_score": 0.0-1.0,
  "what_worked": "For solutions",
  "constraints": "Limitations"
}
```

## Profile System

K-LEAN supports two profiles for different API backends:

| Command | Profile | Description |
|---------|---------|-------------|
| `claude` | Native | Uses Anthropic API directly |
| `claude-nano` | NanoGPT | Uses LiteLLM proxy at localhost:4000 |

Both can run simultaneously in different terminals.

### Check Current Profile
```bash
claude-status
```

### Profile Directories
- Native: `~/.claude/`
- NanoGPT: `~/.claude-nano/` (symlinks to shared resources)

## Review System

Multi-model code review system using LiteLLM proxy at localhost:4000 with dynamic model discovery.

### Commands
- `/kln:models` - List available models from LiteLLM
- `/kln:quickReview <model> <focus>` - Single model review
- `/kln:quickCompare <focus>` - 5 healthy models in parallel
- `/kln:deepInspect <model> <focus>` - Single model with tools
- `/kln:asyncDeepAudit <focus>` - 3 models with tools (background)

### Models Available (Dynamic Discovery)

Run `/kln:models` to see available models. Common models if configured in LiteLLM:
- qwen3-coder - Code quality, bugs
- deepseek-v3-thinking - Architecture, design
- glm-4.6-thinking - Standards, compliance
- minimax-m2 - Research
- kimi-k2-thinking - Agent tasks
- hermes-4-70b - Scripting

**Note:** Use exact model names. Aliases removed in favor of auto-discovery.

## Timeline System (Chronological Progress)

A timeline log tracks all significant events across sessions.

### Location
- `.knowledge-db/timeline.txt` in each project root

### What Gets Logged Automatically
- Reviews completed (with fact count and focus)
- Git commits (hash and message)
- Facts extracted from reviews/commits

### Querying Timeline

```bash
# Last 20 events
tail -20 .knowledge-db/timeline.txt

# Events from today
grep "$(date '+%m-%d')" .knowledge-db/timeline.txt

# All commits
grep "| commit |" .knowledge-db/timeline.txt

# All security-related events
grep -i security .knowledge-db/timeline.txt

# Full timeline helper
~/.claude/scripts/timeline-query.sh [today|week|commits|reviews|<search>]
```

### Timeline Format
```
MM-DD HH:MM | type | description
12-08 17:30 | review | security audit (3 facts, score: 0.8)
12-08 17:45 | commit | abc123: Fix XSS vulnerability
```

## Serena Memories (Curated Knowledge)

For high-value, curated insights, use Serena memories:

### Available Memories
- `lessons-learned` - Gotchas, patterns, tips discovered
- `architecture-review-system` - System documentation
- `session-log` - Session progress notes (manual)

### When to Update
After significant discoveries:
```
Use mcp__serena__edit_memory to append to lessons-learned:
### NEW PATTERN: <title>
**Date**: <today>
**Context**: <what led to this>
<description>
```

## Hooks Active

- **UserPromptSubmit**: Async review dispatch, GoodJob capture, health check
- **PostToolUse (Bash)**: Post-commit documentation + timeline logging
- **PostToolUse (WebFetch/WebSearch)**: Auto-capture to knowledge DB
