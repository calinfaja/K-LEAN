# K-LEAN Agent Instructions

> Multi-Model Code Review & Knowledge Capture System for Claude Code

## Quick Start

```bash
pipx install k-lean    # Install
k-lean doctor          # Verify setup
k-lean status          # Check components
```

## Key Commands

| Command | Purpose |
|---------|---------|
| `k-lean doctor` | Validate configuration and services |
| `k-lean status` | Show installed components |
| `k-lean models` | List available LLM models |
| `k-lean start/stop` | Control LiteLLM & KB services |
| `k-lean test` | Run 27-point test suite |

## Project Structure

```
src/klean/
├── cli.py              # Main CLI (12 commands)
├── data/
│   ├── scripts/        # 36 shell + 11 Python scripts
│   ├── commands/kln/   # 9 slash commands
│   ├── hooks/          # 5 Claude Code hooks
│   ├── droids/         # 8 specialist AI personas
│   └── core/           # Review engine + prompts
└── agents/             # Agentic reviewers
```

## Do's and Don'ts

**Do:**
- Use `kb-root.sh` for path resolution (never hardcode paths)
- Check both `content` and `reasoning_content` for thinking models
- Run `k-lean test` before committing
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

## Tech Stack

- **Python 3.9+** with Rich CLI
- **LiteLLM** proxy for multi-model routing
- **txtai** for semantic embeddings (Knowledge DB)
- **Claude Code** hooks integration
- **NanoGPT / OpenRouter** as LLM providers

---
*For Claude Code specific config, see [CLAUDE.md](CLAUDE.md)*
