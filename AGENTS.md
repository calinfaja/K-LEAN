# K-LEAN Agent Instructions

> Multi-Model Code Review & Knowledge Capture System for Claude Code

## Quick Start

```bash
pipx install k-lean    # Install
kln doctor          # Verify setup
kln status          # Check components
```

## Key Commands

| Command | Purpose |
|---------|---------|
| `kln doctor` | Validate configuration and services |
| `kln status` | Show installed components |
| `kln models` | List available LLM models |
| `kln start/stop` | Control LiteLLM & KB services |
| `kln test` | Run 27-point test suite |

## Project Structure

```
src/klean/
├── cli.py              # Main CLI (12 commands)
├── data/
│   ├── scripts/        # 36 shell + 9 Python scripts
│   ├── commands/kln/   # 9 slash commands
│   ├── hooks/          # 4 Claude Code hooks
│   ├── droids/         # 8 specialist AI personas
│   └── core/           # Review engine + prompts
└── agents/             # Agentic reviewers
```

## Do's and Don'ts

**Do:**
- Use `kb-root.sh` for path resolution (never hardcode paths)
- Check both `content` and `reasoning_content` for thinking models
- Run `kln test` before committing
- Keep CLAUDE.md minimal (K-LEAN is a plugin, not owner)

**Don't:**
- Embed API keys in code (use ~/.config/litellm/.env)
- Modify user's CLAUDE.md directly
- Skip error handling in hooks/scripts
- Use blocking operations in hooks

## Detailed Documentation

| Topic | File | When to Read |
|-------|------|--------------|
| Product overview | [.agents/project-overview.md](.agents/project-overview.md) | New to K-LEAN |
| System architecture | [.agents/architecture.md](.agents/architecture.md) | Multi-component changes |
| Development workflow | [.agents/development.md](.agents/development.md) | Before commits |
| Code style | [.agents/coding-conventions.md](.agents/coding-conventions.md) | Writing code |
| CLI reference | [.agents/cli.md](.agents/cli.md) | CLI changes |
| Knowledge DB | [.agents/knowledge-db.md](.agents/knowledge-db.md) | KB work |
| Review system | [.agents/review-system.md](.agents/review-system.md) | Review scripts |
| Factory droids | [.agents/droids.md](.agents/droids.md) | Droid changes |
| Hooks system | [.agents/hooks.md](.agents/hooks.md) | Hook development |
| LiteLLM setup | [.agents/litellm.md](.agents/litellm.md) | Model/provider work |
| Troubleshooting | [.agents/troubleshooting.md](.agents/troubleshooting.md) | Debugging issues |

## Tech Stack

- **Python 3.9+** with Rich CLI
- **LiteLLM** proxy for multi-model routing
- **txtai** for semantic embeddings (Knowledge DB)
- **Claude Code** hooks integration
- **NanoGPT / OpenRouter** as LLM providers

## PyPI Release Process

### Package Info
- **Name**: `kln-ai` (k-lean and kln were taken)
- **Install**: `pipx install kln-ai`
- **URL**: https://pypi.org/project/kln-ai/

### Release Steps

1. **Sync package data** (if scripts/commands changed):
   ```bash
   kln sync
   ```

2. **Run tests**:
   ```bash
   kln test
   ```

3. **Build package**:
   ```bash
   rm -rf dist/
   pyproject-build .
   ```

4. **Upload to PyPI**:
   ```bash
   twine upload dist/*
   ```
   Token stored in `~/.pypirc`

### Version Management

- Version defined in TWO places (keep in sync):
  - `pyproject.toml` -> `version = "x.y.z"`
  - `src/klean/__init__.py` -> `__version__ = "x.y.z"`
- PyPI rejects duplicate versions - must bump for each upload
- Use semantic versioning: `major.minor.patch-beta`

### Dependencies

All core features require these (included in base install):
- `txtai`, `sentence-transformers` - Knowledge DB
- `smolagents[litellm]`, `ddgs`, `markdownify`, `lizard` - SmolKLN agents

Optional extras:
- `[telemetry]` - Phoenix tracing
- `[agent-sdk]` - Claude Agent SDK

### Troubleshooting

| Issue | Fix |
|-------|-----|
| Name conflict | Check availability: `curl -s https://pypi.org/pypi/NAME/json` |
| Auth failed | Regenerate token at pypi.org, update `~/.pypirc` |
| Version exists | Bump version in both files |

---
*For Claude Code specific config, see [CLAUDE.md](CLAUDE.md)*
