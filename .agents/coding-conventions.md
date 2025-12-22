# K-LEAN Coding Conventions

## Python Style

### General
- **Formatter**: Black (default settings)
- **Linter**: Ruff or flake8
- **Type hints**: Required for public functions
- **Docstrings**: Google style

### Naming
```python
# Classes: PascalCase
class ModelResolver:

# Functions/methods: snake_case
def get_healthy_models():

# Constants: UPPER_SNAKE_CASE
CLAUDE_DIR = Path.home() / ".claude"

# Private: leading underscore
def _parse_response():
```

### Imports
```python
# Standard library first
import os
from pathlib import Path

# Third party
import httpx
from rich.console import Console

# Local
from klean import CLAUDE_DIR
```

## Shell Style

### General
- **Linter**: ShellCheck
- **Shebang**: `#!/usr/bin/env bash`
- **Safety**: `set -euo pipefail` for scripts (not hooks)

### Naming
```bash
# Scripts: kebab-case
quick-review.sh
knowledge-query.sh

# Functions: snake_case
get_agent_system_prompt() {

# Variables: UPPER_SNAKE_CASE for exports
export KB_PYTHON="..."

# Local vars: lower_snake_case
local model_name="$1"
```

### Path Handling

**Always use kb-root.sh:**
```bash
# Good
source "$SCRIPT_DIR/kb-root.sh" 2>/dev/null || true
"$KB_PYTHON" "$KB_SCRIPTS_DIR/knowledge_db.py"

# Bad - hardcoded paths
/home/user/.venvs/knowledge-db/bin/python
~/.claude/scripts/knowledge_db.py
```

### Error Handling
```bash
# Check command exists
if ! command -v curl &>/dev/null; then
    echo "Error: curl required" >&2
    exit 1
fi

# Check file exists
if [ ! -f "$config_file" ]; then
    log_debug "Config not found, using defaults"
fi
```

## Do's and Don'ts

### Do

- **Use kb-root.sh** for all path resolution
- **Check thinking models** for both response formats:
  ```bash
  content=$(echo "$response" | jq -r '.choices[0].message.content // empty')
  if [ -z "$content" ]; then
      content=$(echo "$response" | jq -r '.choices[0].message.reasoning_content // empty')
  fi
  ```
- **Handle errors gracefully** in hooks (they run silently)
- **Use log_debug** for debugging output
- **Test with `k-lean test`** before committing

### Don't

- **Hardcode paths** like `/home/calin/...`
- **Embed secrets** in code (use .env files)
- **Modify user's CLAUDE.md** directly
- **Use blocking operations** in hooks
- **Skip error handling** in scripts
- **Assume model response format** (check both content types)

## File Organization

### data/ Directory Structure
```
src/klean/data/
├── scripts/         # Executable scripts (chmod +x)
├── commands/kln/    # Slash command definitions (.md)
├── hooks/           # Claude Code hooks (.sh)
├── agents/          # SmolKLN agent definitions (.md)
├── lib/             # Shared utilities
├── core/            # Review engine
└── config/          # Config templates
```

### Adding New Files

1. Place in appropriate `data/` subdirectory
2. Make scripts executable: `chmod +x`
3. Source `kb-root.sh` in shell scripts
4. Run `k-lean sync` to update package

## Commit Messages

Follow conventional commits:
```
feat: add new droid for database review
fix: handle empty response from thinking models
docs: update architecture diagram
refactor: extract common path logic to kb-root.sh
test: add integration test for KB server
```

## Code Review Checklist

Before committing, verify:

- [ ] No hardcoded paths (grep for `/home/`)
- [ ] No embedded secrets (grep for `api_key`, `token`)
- [ ] Scripts source kb-root.sh
- [ ] Thinking model response handling
- [ ] Error handling present
- [ ] `k-lean test` passes

---
*See [cli.md](cli.md) for CLI command reference*
