# K-LEAN

Multi-model code review and knowledge capture system. Use `/kln:help` for commands.

## Behavioral Triggers

**Proactively suggest K-LEAN when:**
- User completes significant code changes → `/kln:quick` for fast review
- User is stuck debugging 10+ minutes → `/kln:rethink` for fresh perspective
- User asks for thorough review → `/kln:multi` for consensus
- User discovers important pattern/gotcha → `SaveThis <lesson>`
- User asks "how did we solve X before?" → `FindKnowledge <query>`

## Knowledge Workflow

```
SaveThis <lesson>     # Capture insight to project's knowledge DB
FindKnowledge <query> # Search past lessons (semantic)
```

Knowledge is per-project, stored in `.knowledge-db/`. Auto-initializes on first save.

## Quick Commands

| Task | Command |
|------|---------|
| Fast review | `/kln:quick <focus>` |
| Multi-model | `/kln:multi` |
| Specialist agent | `/kln:agent <role> <task>` |
| System health | `/kln:status` |

## Troubleshooting

If models unavailable: `k-lean doctor -f` (auto-fix)
