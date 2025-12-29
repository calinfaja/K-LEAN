# K-LEAN

Use `/kln:help` for full command reference.

## Quick Reference

| When you want to... | Use |
|---------------------|-----|
| Fast code review | `/kln:quick <focus>` |
| Multi-model consensus | `/kln:multi <focus>` |
| Run specialist agent | `/kln:agent <role> <task>` |
| Check system health | `/kln:status` |
| Capture a lesson | `SaveThis <lesson>` |
| Search knowledge | `FindKnowledge <query>` |

## CLI

```
k-lean status    # Health check
k-lean models    # List available models
k-lean doctor    # Diagnose issues
```

Models: Discovered from LiteLLM. Configure in `~/.config/litellm/config.yaml`
