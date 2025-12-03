# Development Workflow

This document explains where files live and how we keep everything in sync.

## File Locations

```
ACTIVE (what Claude uses)              BACKUP (git tracked)
~/.claude/                             ~/claudeAgentic/review-system-backup/
├── scripts/                           ├── scripts/
│   ├── quick-review.sh                │   ├── quick-review.sh
│   ├── second-opinion.sh              │   ├── second-opinion.sh
│   ├── consensus-review.sh            │   ├── consensus-review.sh
│   ├── deep-review.sh                 │   ├── deep-review.sh
│   ├── parallel-deep-review.sh        │   ├── parallel-deep-review.sh
│   ├── async-dispatch.sh              │   ├── async-dispatch.sh
│   ├── health-check.sh                │   ├── health-check.sh
│   ├── session-helper.sh              │   ├── session-helper.sh
│   ├── start-litellm.sh               │   ├── start-litellm.sh
│   ├── test-system.sh                 │   └── test-system.sh
│   └── post-commit-docs.sh            │
├── commands/sc/                       ├── commands/
│   └── *.md (slash commands)          │   └── *.md
├── settings.json                      └── config/
└── mcp.json                               └── settings.json
```

## Output Structure

Reviews are saved in session-based folders:

```
/tmp/claude-reviews/
├── 2024-12-03-143005/      # Session 1 (Claude instance 1)
│   ├── quick-qwen-143022.json
│   └── consensus-all-144500.json
└── 2024-12-03-150000/      # Session 2 (Claude instance 2)
    └── deep-glm-150030.txt
```

Each Claude instance gets its own folder based on start time.

## Workflow

### When Editing Scripts

1. **Edit in active location**: `~/.claude/scripts/`
2. **Test the script**: Run it manually or trigger via Claude
3. **Backup to repo**: `cp ~/.claude/scripts/<script> ~/claudeAgentic/review-system-backup/scripts/`
4. **Commit**: `cd ~/claudeAgentic && git add . && git commit -m "message"`

### Quick Backup Command

```bash
# Backup all scripts at once
cp ~/.claude/scripts/*.sh ~/claudeAgentic/review-system-backup/scripts/
```

### Quick Sync (if repo has newer version)

```bash
# Restore from backup to active
cp ~/claudeAgentic/review-system-backup/scripts/*.sh ~/.claude/scripts/
chmod +x ~/.claude/scripts/*.sh
```

## Why Two Locations?

| Location | Purpose |
|----------|---------|
| `~/.claude/` | Active config - Claude reads from here |
| `~/claudeAgentic/` | Git repository - version control, documentation |

Claude doesn't support custom config directories, so scripts must live in `~/.claude/` to work. We backup to `~/claudeAgentic/` for:
- Version history
- Easy restoration
- Documentation alongside code

## Commit Convention

```
<action> <what>

<details>
```

Examples:
- `Add health check fallback to review scripts`
- `Fix GLM empty response by testing actual model completion`
- `Update test-system.sh with model health verification`

## Testing After Changes

```bash
# Check all models
~/.claude/scripts/health-check.sh

# Run full system test
~/.claude/scripts/test-system.sh

# Test specific script
~/.claude/scripts/quick-review.sh qwen "test"
```

## Starting LiteLLM

```bash
# Use the alias (ensures port 4000 is free)
start-nano-proxy

# Or directly
~/.claude/scripts/start-litellm.sh
```
