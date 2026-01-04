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
# 1. Gather code into temp file (adapt based on what user wants)
git diff HEAD~1..HEAD | head -500 > /tmp/kln-review.txt

# 2. Send to review
cat /tmp/kln-review.txt | ~/.local/share/pipx/venvs/kln-ai/bin/python \
    ~/.claude/kln/klean_core.py quick -m "MODEL" "FOCUS"
```

**MODEL**: `--model` flag or "auto"
**FOCUS**: Extract from user request (e.g., "security", "performance") or "code quality"

**Model names:** If user gives partial name (e.g. "qwen"), run `curl -s localhost:4000/models | jq -r '.data[].id'` to find full match.
