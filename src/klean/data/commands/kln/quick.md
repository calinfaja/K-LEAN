---
name: quick
description: "Fast code review via LiteLLM (~60s). Returns GRADE, RISK, findings."
allowed-tools: Bash, Read, Glob, Grep
argument-hint: "<what to review> [--model MODEL]"
---

# /kln:quick

You gather the code, script does the review.

## Your Job

Understand what user wants reviewed and gather the relevant code:

| User wants | You gather |
|------------|------------|
| "current changes" / "my changes" | `git diff` (unstaged) + `git diff --cached` (staged) |
| "last commit" | `git diff HEAD~1..HEAD` |
| "last N commits" | `git diff HEAD~N..HEAD` |
| "feature X" / "the auth module" | Read relevant files, get recent changes |
| "this file" / "file.py" | Read the file content |
| "PR" / "branch changes" | `git diff main..HEAD` |

Be smart - if user says "review the auth changes", find auth-related files and their diffs.

## Execute

```bash
PYTHON=~/.local/share/pipx/venvs/kln-ai/bin/python
CORE=~/.claude/kln/klean_core.py

# Option A: Pipe via stdin
git diff HEAD~1..HEAD | head -500 > /tmp/kln-review.txt
cat /tmp/kln-review.txt | $PYTHON $CORE quick -m "MODEL" "FOCUS"

# Option B: Use --context-file flag
$PYTHON $CORE quick -m "MODEL" -c /tmp/kln-review.txt "FOCUS"
```

**MODEL**: `--model` flag or "auto"
**FOCUS**: Extract from user request (e.g., "security", "performance") or "code quality"

**Model names:** If user gives partial name (e.g. "qwen"), run `$PYTHON $CORE status` to list available models and find full match. The core module handles partial name resolution automatically.

## Flags

- `-m, --model` - Model to use (default: "auto")
- `-c, --context-file` - File containing code to review (alternative to stdin)
- `-o, --output` - Output format: text (default), json, markdown
- `--telemetry` - Enable Phoenix telemetry tracing
- `--async, -a` - Run in background (continue working, check results later)

## Background Execution

To run reviews in background:
- Add `--async` flag: `/kln:quick --async "security review"`
- Or say: "run this in background"
- Press `Ctrl+B` while command is running to background it

Background tasks return immediately with a task ID. Check status with `/tasks` or ask "what's the review status?"
