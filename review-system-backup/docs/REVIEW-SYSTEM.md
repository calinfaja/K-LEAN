# Review System

Multi-model code review architecture using LiteLLM proxy to route requests to various AI models.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     REVIEW SYSTEM                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Tier 1: Quick Review (API calls)                               │
│  ├── /kln:quickReview <model> <focus>                           │
│  │   └── Single model, ~10s, Grade + Risk + Verdict             │
│  │                                                               │
│  ├── /kln:quickCompare <focus>                                  │
│  │   └── 3 models parallel, ~30s, consensus view                │
│  │                                                               │
│  └── /kln:quickConsult <model> <question>                       │
│      └── Get second opinion on specific question                │
│                                                                  │
│  Tier 2: Deep Review (Headless Claude)                          │
│  ├── /kln:deepInspect <model> <focus>                           │
│  │   └── Single model with FULL TOOL ACCESS                     │
│  │   └── Can Read, Grep, Glob, WebSearch, git ops               │
│  │   └── Runs in audit mode (read-only)                         │
│  │                                                               │
│  └── /kln:asyncDeepAudit <focus>                                │
│      └── 3 models parallel, each with tools                     │
│      └── Background execution via subagent                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Models

| Alias | LiteLLM Model | Best For | Reliability |
|-------|---------------|----------|-------------|
| `qwen` | qwen3-coder | Code quality, bugs, security | ⭐⭐⭐ High |
| `deepseek` | deepseek-v3-thinking | Architecture, design patterns | ⭐⭐ Medium |
| `glm` | glm-4.6-thinking | Standards, MISRA, compliance | ⭐⭐⭐ High |
| `kimi` | kimi-k2-thinking | Agent tasks, planning | ⭐⭐⭐ High |
| `minimax` | minimax-m2 | Research, exploration | ⭐⭐ Medium |
| `hermes` | hermes-4-70b | Scripting, automation | ⭐⭐ Medium |

**Note:** "Thinking" models output `<think>` tags with reasoning - this is expected behavior.

## Commands

### Quick Review (Tier 1)

Single model review via LiteLLM API:

```bash
/kln:quickReview qwen security vulnerabilities
/kln:quickReview glm MISRA compliance
/kln:quickReview deepseek architecture review
```

**Output:**
- Grade (A-F)
- Risk level (CRITICAL/HIGH/MEDIUM/LOW)
- Top issues found
- Verdict (APPROVE/REQUEST_CHANGES)

**Script:** `~/.claude/scripts/quick-review.sh`

### Quick Compare (Tier 1)

Three models in parallel for consensus:

```bash
/kln:quickCompare security audit
/kln:quickCompare error handling
```

**Models used:** qwen, deepseek, glm (with health-check fallback)

**Script:** `~/.claude/scripts/consensus-review.sh`

### Deep Inspect (Tier 2)

Single model with full tool access via headless Claude:

```bash
/kln:deepInspect qwen comprehensive security audit
/kln:deepInspect glm MISRA C compliance check
```

**Capabilities:**
- Read any file in codebase
- Grep/Glob for patterns
- Git operations (diff, log, blame)
- WebSearch for documentation
- Serena memories access

**Audit Mode:** Read-only, no write/edit/delete operations allowed.

**Script:** `~/.claude/scripts/deep-review.sh`

### Async Deep Audit (Tier 2)

Three models with tools, running in background:

```bash
/kln:asyncDeepAudit security patterns
/kln:asyncDeepAudit architecture review
```

**Script:** `~/.claude/scripts/parallel-deep-review.sh`

## Persistent Output

All reviews are saved to the project's `.claude/kln/` folder:

```
<project>/.claude/kln/
├── quickReview/
│   └── 2024-12-09_14-30-25_qwen_security.md
├── quickCompare/
│   └── 2024-12-09_16-00-00_consensus_security.md
├── deepInspect/
│   └── 2024-12-09_17-00-00_qwen_architecture.md
└── asyncDeepAudit/
    └── 2024-12-09_18-00-00_parallel_security.md
```

**Filename format:** `YYYY-MM-DD_HH-MM-SS_model_focus.md`

**Output includes:**
- Markdown header with metadata (model, date, directory)
- Full review content
- Already gitignored via `.claude/` pattern

## Health Check & Fallback

Each script performs health checks before running:

```bash
# Check model health
curl -s http://localhost:4000/chat/completions \
  -d '{"model": "qwen3-coder", "messages": [{"role": "user", "content": "hi"}], "max_tokens": 5}'
```

**Fallback priority:** qwen3-coder → deepseek-v3-thinking → glm-4.6-thinking

If preferred model is unhealthy, automatically falls back to next healthy model.

## Audit Mode (Security)

Deep reviews run in **audit mode** for safe automation:

```json
{
  "permissions": {
    "allow": [
      "Read", "Glob", "Grep", "WebSearch", "WebFetch",
      "Bash(git diff:*)", "Bash(git log:*)", "Bash(find:*)",
      "mcp__serena__find_symbol", "mcp__serena__read_memory"
    ],
    "deny": [
      "Write", "Edit", "NotebookEdit",
      "Bash(rm:*)", "Bash(git commit:*)", "Bash(git push:*)"
    ]
  }
}
```

This allows full investigation capabilities while preventing any modifications.

## Knowledge Integration

Reviews automatically:
1. **Search knowledge DB** for relevant prior knowledge before reviewing
2. **Inject context** into system prompt if relevant findings exist
3. **Extract facts** from review output and store in knowledge DB

```bash
# Knowledge context injection
📚 Found relevant prior knowledge
```

## Scripts Reference

| Script | Purpose |
|--------|---------|
| `quick-review.sh` | Single model API review |
| `consensus-review.sh` | 3-model parallel API review |
| `deep-review.sh` | Headless Claude with tools |
| `parallel-deep-review.sh` | 3 headless instances parallel |
| `session-helper.sh` | Output directory management |
| `fact-extract.sh` | Extract facts from review output |

## Troubleshooting

### Model returns empty response
- Check LiteLLM proxy: `curl http://localhost:4000/v1/models`
- Verify API key in `~/.config/litellm/.env`
- Try fallback model: `qwen` is most reliable

### Deep review times out
- Default timeout: 300s for deep reviews
- Increase with `--timeout` flag in test scripts
- Check if model supports tool use (deepseek may have issues)

### Review output not saved
- Verify project is a git repository (needed for `find_project_root`)
- Check `.claude/kln/` directory exists
- Ensure write permissions on project directory
