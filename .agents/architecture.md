# K-LEAN Architecture

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Claude Code                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Hooks     │  │  Commands   │  │      Statusline         │  │
│  │ (5 triggers)│  │ (/kln:*)    │  │  [model│project│git│kb] │  │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────────┘  │
└─────────┼────────────────┼──────────────────────────────────────┘
          │                │
          ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      K-LEAN Scripts                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Review       │  │ Knowledge    │  │ SmolKLN Agents       │   │
│  │ quick/deep   │  │ capture/query│  │ 8 specialists        │   │
│  │ consensus    │  │ server       │  │ orchestrator         │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
└─────────┼────────────────┼──────────────────────┼───────────────┘
          │                │                      │
          ▼                ▼                      ▼
┌─────────────────┐  ┌─────────────────┐
│  LiteLLM Proxy  │  │  Knowledge DB   │
│  localhost:4000 │  │  txtai + socket │
│  12+ models     │  │  per-project    │
└────────┬────────┘  └─────────────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│           LLM Providers                  │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │  NanoGPT    │  │  OpenRouter     │   │
│  │  12 models  │  │  6 models       │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
```

## Component Map

### Source Structure (`src/klean/`)

```
src/klean/
├── __init__.py          # Package init, path constants
├── cli.py               # Main CLI (~2300 lines, 12 commands)
├── data/                # Installable assets (symlinked to ~/.claude/)
│   ├── scripts/         # 36 .sh + 9 .py scripts
│   ├── commands/kln/    # 9 slash commands
│   ├── hooks/           # 5 Claude Code hooks
│   ├── agents/          # 8 SmolKLN specialist agents
│   ├── lib/             # Shared utilities (common.sh)
│   ├── core/            # Review engine
│   │   ├── klean_core.py    # 1190 lines
│   │   ├── config.yaml      # Settings
│   │   └── prompts/         # Review prompts
│   └── config/          # Config templates
├── smol/                # SmolKLN agent system (smolagents + LiteLLM)
├── tools/               # MCP-style tools
└── utils/               # Utilities (model_discovery.py)
```

### Symlink Architecture

After installation, `~/.claude/` contains symlinks:

```
~/.claude/
├── scripts → src/klean/data/scripts
├── commands/kln → src/klean/data/commands/kln
├── hooks → src/klean/data/hooks
└── lib → src/klean/data/lib
```

### Per-Project Isolation

Each git repository gets its own Knowledge DB:

```
/tmp/kb-{md5_hash}.sock    # Unix socket for fast queries
.knowledge-db/             # Per-project data (in .gitignore)
├── entries.jsonl          # V2 schema entries
└── index/                 # Semantic embeddings
```

## Data Flow

### Review Flow
```
User: /kln:quick → hooks detect → quick-review.sh
  → LiteLLM /chat/completions → NanoGPT → response
  → parse (content || reasoning_content) → display
```

### Knowledge Capture Flow
```
User: "SaveThis: insight" → user-prompt-handler.sh
  → knowledge-capture.py → V2 schema → entries.jsonl
  → txtai re-index (on next query)
```

### Consensus Flow
```
/kln:multi → consensus-review.sh
  → parallel curl to 5 models
  → collect responses → parse JSON
  → group by location similarity
  → classify by agreement (HIGH/MEDIUM/LOW)
  → display ranked findings
```

## Key Path Variables

Defined in `src/klean/data/scripts/kb-root.sh`:

| Variable | Default | Purpose |
|----------|---------|---------|
| `KB_PYTHON` | `~/.venvs/knowledge-db/bin/python` | Python with txtai |
| `KB_SCRIPTS_DIR` | `~/.claude/scripts` | Script location |
| `KB_SOCKET_DIR` | `/tmp` | Socket location |
| `KB_CONFIG_DIR` | `~/.config/litellm` | LiteLLM config |

## Error Handling

- All scripts source `kb-root.sh` for consistent paths
- Hooks have inline fallbacks if kb-root.sh missing
- Thinking models checked for both `content` and `reasoning_content`
- Socket timeouts: 0.5s for LiteLLM, 0.3s for KB

---
*See [development.md](development.md) for build workflow*
