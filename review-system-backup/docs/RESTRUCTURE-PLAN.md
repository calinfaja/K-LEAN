# K-LEAN Open Source Restructure Plan v2.0

## Executive Summary

This plan transforms `review-system-backup/` into a clean, maintainable open source repository named `k-lean/`.

**Key Changes:**
- Repository rename: `review-system-backup` → `k-lean`
- Root cleanup: 30+ items → 10 items
- Documentation reorganization with clear hierarchy
- Future features isolated in `roadmap/`
- SuperClaude removed (separate framework, installed independently)
- TOON moved to `roadmap/toon/` for future integration

**Critical Constraint:** Zero breaking changes - all K-LEAN functionality must work identically after restructure.

---

## Final Target Structure

```
k-lean/
├── README.md                    # Entry point (updated)
├── LICENSE                      # MIT license (create)
├── CHANGELOG.md                 # Version history (create)
├── CONTRIBUTING.md              # Contribution guide (create)
├── CLAUDE.md                    # Claude Code config (keep)
├── pyproject.toml               # Package config (keep)
├── .gitignore                   # Updated with new patterns
│
├── src/klean/                   # Core package (unchanged internally)
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   └── data/
│       ├── scripts/             # All bash/python scripts
│       ├── hooks/               # Claude Code hooks
│       ├── commands/kln/        # K-LEAN slash commands
│       ├── config/              # Config templates
│       └── lib/                 # Shared libraries
│
├── docs/                        # All documentation
│   ├── README.md                # Documentation index
│   ├── QUICK_START.md           # 5-minute getting started
│   ├── INSTALLATION.md          # Full installation guide
│   ├── guides/                  # User guides
│   │   ├── knowledge-db.md
│   │   ├── reviews.md
│   │   ├── droids.md
│   │   └── hooks.md
│   ├── reference/               # Technical reference
│   │   ├── commands.md
│   │   ├── architecture.md
│   │   └── cli.md
│   └── dev/                     # Developer documentation
│       ├── development.md
│       ├── lessons-learned.md
│       └── review-plan.md       # Internal planning
│
├── droids/                      # Factory droid definitions (keep at root)
│
├── config/                      # User config templates
│   ├── litellm-config.yaml
│   └── settings.json
│
├── tests/                       # Test suite
│
├── roadmap/                     # Future features (not installed)
│   ├── README.md                # Roadmap overview
│   ├── toon/                    # TOON compression feature
│   │   ├── README.md
│   │   ├── toon_adapter.py
│   │   ├── context_injector.py
│   │   └── docs/                # TOON documentation
│   └── semantic-memory/         # Semantic memory system
│       ├── README.md
│       └── SEMANTIC_MEMORY_SYSTEM.md
│
└── .github/                     # GitHub configuration
    ├── workflows/
    │   └── ci.yml
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   └── feature_request.md
    └── PULL_REQUEST_TEMPLATE.md
```

---

## Phase 1: Preparation

### 1.1 Verify Current State
```bash
cd /home/calin/claudeAgentic/review-system-backup

# Check git status is clean
git status

# Verify K-LEAN works before changes
k-lean --version
k-lean status
```

### 1.2 Create Backup Branch
```bash
git checkout -b pre-restructure-backup
git checkout main
```

---

## Phase 2: Delete Build Artifacts & Generated Files

**Rationale:** These are regenerated on build, should not be in repo.

```bash
# Build artifacts
rm -rf build/
rm -rf dist/
rm -rf src/k_lean.egg-info/
rm -rf .pytest_cache/
rm -rf __pycache__/
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# Duplicate VERSION file (version is in pyproject.toml)
rm -f VERSION
```

**Verification:**
```bash
ls build/ 2>&1 | grep -q "No such file" && echo "✓ build/ deleted"
```

---

## Phase 3: Delete Legacy Installation Scripts

**Rationale:** Replaced by `pipx install k-lean` and k-lean CLI.

| File | Replacement |
|------|-------------|
| `install.sh` | `pipx install k-lean` |
| `update.sh` | `pipx upgrade k-lean` |
| `test.sh` | `k-lean status` |
| `bash_functions.sh` | Obsolete |

```bash
rm -f install.sh
rm -f update.sh
rm -f test.sh
rm -f bash_functions.sh
```

**Verification:**
```bash
k-lean --version && echo "✓ CLI still works"
```

---

## Phase 4: Delete TOON Project Files (Move to roadmap/)

**Rationale:** TOON is future feature, not current functionality. Move to roadmap/.

### 4.1 Create roadmap structure
```bash
mkdir -p roadmap/toon/docs
mkdir -p roadmap/semantic-memory
```

### 4.2 Move TOON code to roadmap
```bash
# Move TOON adapter
mv src/klean/data/scripts/toon_adapter.py roadmap/toon/
mv src/klean/data/scripts/test-toon-adapter.sh roadmap/toon/

# Move context injector (uses TOON)
mv src/klean/data/scripts/knowledge-context-injector.py roadmap/toon/context_injector.py
```

### 4.3 Move TOON documentation
```bash
# Move all TOON docs
mv docs/TOON*.md roadmap/toon/docs/
mv docs/TOON-ADAPTER.md roadmap/toon/docs/

# Move PHASE docs (TOON project phases)
mv docs/PHASE3_RESULTS.md roadmap/toon/docs/
mv docs/PHASE4_DEPLOYMENT.md roadmap/toon/docs/
mv docs/PHASE4_VALIDATION_REPORT.md roadmap/toon/docs/
```

### 4.4 Move existing NEXT_FEATURES content
```bash
mv NEXT_FEATURES/SEMANTIC_MEMORY_SYSTEM.md roadmap/semantic-memory/
mv NEXT_FEATURES/README.md roadmap/semantic-memory/ORIGINAL_README.md
rm -rf NEXT_FEATURES/
```

### 4.5 Create roadmap README
```bash
cat > roadmap/README.md << 'EOF'
# K-LEAN Roadmap

Future features planned for K-LEAN.

## Features

### TOON Compression (`toon/`)
Token-Oriented Object Notation for ~18% reduction in LLM token usage.
- Status: Implemented, not integrated
- Dependency: `python-toon` library

### Semantic Memory (`semantic-memory/`)
Advanced semantic memory system for cross-session context.
- Status: Design phase

## Contributing
See [CONTRIBUTING.md](../CONTRIBUTING.md) for how to help implement these features.
EOF
```

### 4.6 Create TOON README
```bash
cat > roadmap/toon/README.md << 'EOF'
# TOON Compression Feature

Token-Oriented Object Notation adapter for efficient LLM transmission.

## Status
- [x] toon_adapter.py - Standalone JSON↔TOON conversion
- [x] context_injector.py - Auto-inject KB context with TOON
- [ ] Integration into knowledge-query.sh
- [ ] Integration into droid-execute.sh

## Benefits
- ~18% character reduction
- ~10-20% token savings (varies by tokenizer)

## Installation (when ready)
```bash
~/.venvs/knowledge-db/bin/pip install python-toon
```

## Usage
See `docs/` for detailed documentation.
EOF
```

**Verification:**
```bash
ls roadmap/toon/toon_adapter.py && echo "✓ TOON moved to roadmap"
ls src/klean/data/scripts/toon_adapter.py 2>&1 | grep -q "No such file" && echo "✓ TOON removed from scripts"
```

---

## Phase 5: Remove SuperClaude

**Rationale:** SuperClaude is a separate framework installed independently. Zero coupling with K-LEAN.

```bash
# Remove SuperClaude commands
rm -rf src/klean/data/commands/sc/

# Remove skills directory (incomplete feature)
rm -rf src/klean/data/skills/
rm -rf skills/
```

**Verification:**
```bash
# K-LEAN commands still work
ls src/klean/data/commands/kln/ && echo "✓ K-LEAN commands intact"

# SuperClaude removed
ls src/klean/data/commands/sc/ 2>&1 | grep -q "No such file" && echo "✓ SuperClaude removed"
```

---

## Phase 6: Delete Orphan Scripts

**Rationale:** Scripts with no references from hooks, commands, or documentation.

### 6.1 Verify orphan status first
```bash
# These should return NO results (excluding self-references)
grep -r "litellm-review" src/klean/data/ --include="*.sh" --include="*.md" | grep -v "litellm-review.sh:"
grep -r "knowledge-fast" src/klean/data/ --include="*.sh" --include="*.md" | grep -v "knowledge-fast.sh:"
grep -r "knowledge-migrate-schema" src/klean/data/ --include="*.sh" --include="*.md"
```

### 6.2 Delete verified orphans
```bash
rm -f src/klean/data/scripts/litellm-review.sh
rm -f src/klean/data/scripts/knowledge-fast.sh
rm -f src/klean/data/scripts/knowledge-migrate-schema.py
```

**DO NOT DELETE** (has active reference):
- `knowledge-extract.sh` - Used by `auto-capture-hook.sh`

**Verification:**
```bash
# Hooks still work
ls src/klean/data/hooks/*.sh && echo "✓ Hooks intact"
```

---

## Phase 7: Delete Duplicate/Orphan Config Files

```bash
# Duplicate droids (canonical is /droids/ at root)
rm -rf src/klean/data/config/factory-droids/
rm -f src/klean/data/config/code-reviewer.md
rm -f src/klean/data/config/security-auditor.md

# Project-specific settings
rm -f audit-settings.json

# Inventory files (not needed in repo)
rm -f KLEAN-V3-CHECKSUMS.txt
rm -f KLEAN-V3-INVENTORY.txt
rm -f MANIFEST.in
```

**Verification:**
```bash
ls droids/*.md && echo "✓ Canonical droids intact"
```

---

## Phase 8: Reorganize Documentation

### 8.1 Create docs structure
```bash
mkdir -p docs/guides
mkdir -p docs/reference
mkdir -p docs/dev
```

### 8.2 Move and rename documentation files

```bash
# Guides (user-facing how-to)
mv docs/KNOWLEDGE-SYSTEM.md docs/guides/knowledge-db.md
mv docs/DROID-SYSTEM.md docs/guides/droids.md
mv docs/HOOKS.md docs/guides/hooks.md

# Reference (technical specs)
mv docs/COMMANDS.md docs/reference/commands.md
mv docs/ARCHITECTURE.md docs/reference/architecture.md
mv docs/KLEAN_CLI_IMPLEMENTATION_REPORT.md docs/reference/cli.md

# Developer docs
mv docs/DEVELOPER.md docs/dev/development.md
mv docs/DEVELOPMENT.md docs/dev/development-advanced.md 2>/dev/null || true
mv docs/LESSONS-LEARNED.md docs/dev/lessons-learned.md
mv docs/REVIEW-PLAN.md docs/dev/review-plan.md 2>/dev/null || true
mv REVIEW-PLAN.md docs/dev/review-plan.md 2>/dev/null || true

# Move root markdown files to docs
mv DEVELOPMENT.md docs/dev/ 2>/dev/null || true
mv DOCS.md docs/reference/docs-index.md 2>/dev/null || true
mv OPEN-SOURCE-PLAN.md docs/dev/open-source-plan.md 2>/dev/null || true
```

### 8.3 Delete obsolete/redundant docs
```bash
# Implementation docs (internal, completed)
rm -f docs/IMPLEMENTATION-PLAN.md
rm -f docs/IMPLEMENTATION-AUTO-DETECTION.md
rm -f docs/PATH-MANAGEMENT-PLAN.md

# Redundant/outdated
rm -f docs/IMPROVEMENT-GUIDE.md
rm -f docs/ARCHITECTURE-ANALYSIS.md
rm -f docs/agent_droids_comparison.md
rm -f docs/performance_analyzer_droid.md
rm -f docs/QUICK_START_PERFORMANCE_ANALYZER.md
rm -f docs/SYSTEM_SUMMARY.md
```

### 8.4 Create docs index
```bash
cat > docs/README.md << 'EOF'
# K-LEAN Documentation

## Quick Links
- [Quick Start](QUICK_START.md) - Get started in 5 minutes
- [Installation](INSTALLATION.md) - Full installation guide

## Guides
- [Knowledge Database](guides/knowledge-db.md) - Semantic search for your knowledge
- [Code Reviews](guides/reviews.md) - Multi-model code review
- [Droids](guides/droids.md) - Factory droid integration
- [Hooks](guides/hooks.md) - Claude Code automation

## Reference
- [Commands](reference/commands.md) - All `/kln:*` commands
- [Architecture](reference/architecture.md) - System design
- [CLI](reference/cli.md) - `k-lean` command reference

## Developer
- [Development](dev/development.md) - Contributing guide
- [Lessons Learned](dev/lessons-learned.md) - Design decisions
EOF
```

---

## Phase 9: Clean Up Root Directory

### 9.1 Move config files
```bash
# Move root configs to config/
mv config.yaml config/klean-config.yaml 2>/dev/null || true
mv settings.json config/settings.json 2>/dev/null || true
```

### 9.2 Clean up remaining root files
```bash
# Remove obsolete root directories
rm -rf commands/     # Moved to src/klean/data/commands
rm -rf hooks/        # Moved to src/klean/data/hooks
rm -rf scripts/      # Moved to src/klean/data/scripts
rm -rf lib/          # Moved to src/klean/data/lib
```

**Note:** The above directories at root may be symlinks or duplicates of src/klean/data/. Verify before deletion.

---

## Phase 10: Update .gitignore

```bash
cat > .gitignore << 'EOF'
# Build artifacts
build/
dist/
*.egg-info/
.eggs/

# Python
__pycache__/
*.py[cod]
*$py.class
.Python

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/
.nox/

# IDE
.idea/
.vscode/
*.swp
*.swo
*~

# Knowledge DB (per-project, not repo)
.knowledge-db/

# Environment
.env
.env.local
.venv/
venv/
ENV/

# OS
.DS_Store
Thumbs.db

# Local config overrides
*.local.yaml
*.local.json
EOF
```

---

## Phase 11: Create Open Source Files

### 11.1 LICENSE (MIT)
```bash
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2024 K-LEAN Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
```

### 11.2 CHANGELOG.md
```bash
cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to K-LEAN will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [3.0.0] - 2024-XX-XX

### Added
- Initial open source release
- K-LEAN CLI (`k-lean status`, `k-lean doctor`, `k-lean start`)
- Knowledge DB with per-project semantic search
- Multi-model code review via LiteLLM proxy
- Factory droids integration
- `/kln:*` slash commands for Claude Code

### Changed
- Restructured for PyPI distribution (`pipx install k-lean`)
- All paths now relative/environment-based for portability

### Removed
- Legacy shell-based installation scripts
- Project-specific files
EOF
```

### 11.3 CONTRIBUTING.md
```bash
cat > CONTRIBUTING.md << 'EOF'
# Contributing to K-LEAN

Thank you for your interest in contributing to K-LEAN!

## Getting Started

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/k-lean.git
   cd k-lean
   ```
3. Install in development mode:
   ```bash
   pipx install -e .
   ```
4. Verify installation:
   ```bash
   k-lean status
   ```

## Development Workflow

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
2. Make your changes
3. Test your changes:
   ```bash
   k-lean doctor
   ```
4. Commit with clear messages
5. Push and create a Pull Request

## Code Style

- **Python**: Follow PEP 8
- **Bash**: Use shellcheck, quote variables
- **Documentation**: Update relevant docs with changes

## Pull Request Guidelines

- One feature/fix per PR
- Update documentation as needed
- Add tests for new functionality
- Ensure `k-lean doctor` passes

## Reporting Issues

Use GitHub Issues with:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- K-LEAN version (`k-lean --version`)

## Questions?

Open a Discussion on GitHub.
EOF
```

### 11.4 GitHub Templates
```bash
mkdir -p .github/workflows
mkdir -p .github/ISSUE_TEMPLATE

# CI workflow
cat > .github/workflows/ci.yml << 'EOF'
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install
        run: pip install -e .
      - name: Version check
        run: k-lean --version
EOF

# Bug report template
cat > .github/ISSUE_TEMPLATE/bug_report.md << 'EOF'
---
name: Bug Report
about: Report a bug in K-LEAN
---

## Description
[Clear description of the bug]

## Steps to Reproduce
1.
2.
3.

## Expected Behavior
[What should happen]

## Actual Behavior
[What actually happens]

## Environment
- K-LEAN version: `k-lean --version`
- OS:
- Python version:
EOF

# Feature request template
cat > .github/ISSUE_TEMPLATE/feature_request.md << 'EOF'
---
name: Feature Request
about: Suggest a new feature
---

## Feature Description
[What feature would you like?]

## Use Case
[Why do you need this feature?]

## Proposed Solution
[How might this work?]
EOF

# PR template
cat > .github/PULL_REQUEST_TEMPLATE.md << 'EOF'
## Description
[What does this PR do?]

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation
- [ ] Refactoring

## Checklist
- [ ] `k-lean doctor` passes
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
EOF
```

---

## Phase 12: Final Verification

### 12.1 Core Functionality Tests
```bash
# CLI works
k-lean --version
k-lean status
k-lean doctor

# Knowledge DB works
InitKB  # (if in Claude Code session)

# Commands available
ls src/klean/data/commands/kln/*.md

# Hooks present
ls src/klean/data/hooks/*.sh

# Scripts present
ls src/klean/data/scripts/*.sh | head -10

# Droids present
ls droids/*.md
```

### 12.2 File Count Verification
```bash
# Root should have ~10 items
ls -1 | wc -l  # Should be ~10-12

# No TOON in scripts
ls src/klean/data/scripts/*toon* 2>&1 | grep -q "No such file" && echo "✓ TOON moved"

# No SuperClaude
ls src/klean/data/commands/sc 2>&1 | grep -q "No such file" && echo "✓ SuperClaude removed"
```

### 12.3 Verify No Broken References
```bash
# Check for broken script references in hooks
for hook in src/klean/data/hooks/*.sh; do
  echo "Checking $hook..."
  grep -o '\$SCRIPTS_DIR/[a-z-]*\.sh' "$hook" | while read script; do
    script_name=$(echo "$script" | sed 's/\$SCRIPTS_DIR\///')
    if [ ! -f "src/klean/data/scripts/$script_name" ]; then
      echo "  WARNING: Missing $script_name"
    fi
  done
done
```

---

## Phase 13: Repository Rename

**After all phases complete and verified:**

```bash
cd /home/calin/claudeAgentic
mv review-system-backup k-lean

# Update any local references
# (pyproject.toml already has name = "k-lean")
```

---

## Phase 14: Git Commit

```bash
cd /home/calin/claudeAgentic/k-lean

git add -A
git status  # Review all changes

git commit -m "$(cat <<'EOF'
Restructure for open source release v3.0

Root cleanup:
- Reduced root from 30+ to 10 items
- Removed legacy install scripts (use pipx install k-lean)
- Removed build artifacts and generated files

Documentation:
- Reorganized docs/ with guides/, reference/, dev/ structure
- Created docs index and navigation

Features:
- Moved TOON to roadmap/toon/ (future feature)
- Removed SuperClaude (separate framework)
- Deleted orphan scripts and duplicate configs

Open source:
- Added LICENSE (MIT)
- Added CHANGELOG.md
- Added CONTRIBUTING.md
- Added GitHub templates and CI workflow

No breaking changes - all K-LEAN functionality preserved.
EOF
)"
```

---

## Rollback Plan

If issues arise during restructuring:

```bash
# Full reset
git checkout .
git clean -fd

# Or restore from backup branch
git checkout pre-restructure-backup
```

---

## Summary Checklist

### Files to DELETE (Total: ~50 files)
- [ ] `build/`, `dist/`, `*.egg-info/` - Build artifacts
- [ ] `install.sh`, `update.sh`, `test.sh`, `bash_functions.sh` - Legacy scripts
- [ ] `VERSION`, `MANIFEST.in`, `KLEAN-V3-*.txt` - Inventory files
- [ ] `audit-settings.json` - Project-specific
- [ ] `src/klean/data/commands/sc/` - SuperClaude (separate repo)
- [ ] `skills/` - Incomplete feature
- [ ] Orphan scripts: `litellm-review.sh`, `knowledge-fast.sh`, `knowledge-migrate-schema.py`
- [ ] Duplicate configs in `src/klean/data/config/`
- [ ] TOON docs from `docs/` (moved to roadmap)
- [ ] Implementation/planning docs (obsolete)

### Files to MOVE
- [ ] `toon_adapter.py` → `roadmap/toon/`
- [ ] `knowledge-context-injector.py` → `roadmap/toon/`
- [ ] `TOON*.md` → `roadmap/toon/docs/`
- [ ] `NEXT_FEATURES/` → `roadmap/`
- [ ] Root `.md` files → `docs/dev/`
- [ ] User docs → `docs/guides/` and `docs/reference/`

### Files to CREATE
- [ ] `LICENSE` - MIT
- [ ] `CHANGELOG.md` - Version history
- [ ] `CONTRIBUTING.md` - Contribution guide
- [ ] `docs/README.md` - Documentation index
- [ ] `roadmap/README.md` - Roadmap overview
- [ ] `.github/workflows/ci.yml` - CI pipeline
- [ ] `.github/ISSUE_TEMPLATE/*.md` - Issue templates
- [ ] `.github/PULL_REQUEST_TEMPLATE.md` - PR template

### Final Verification
- [ ] `k-lean --version` works
- [ ] `k-lean status` shows all green
- [ ] `k-lean doctor` passes
- [ ] Knowledge DB initializes
- [ ] Droids execute
- [ ] Hooks trigger correctly
- [ ] Root has ~10 items
- [ ] No broken script references

---

*Plan Version: 2.0*
*Created: 2024-12-21*
*Status: Ready for execution*
