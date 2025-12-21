# K-LEAN Open Source Preparation Plan

Comprehensive guide for restructuring K-LEAN repository following open source best practices.

---

## Table of Contents

1. [Current State Analysis](#current-state-analysis)
2. [Open Source Best Practices](#open-source-best-practices)
3. [Target Structure](#target-structure)
4. [Naming Conventions](#naming-conventions)
5. [Migration Plan](#migration-plan)
6. [File-by-File Actions](#file-by-file-actions)
7. [Safety Checklist](#safety-checklist)

---

## Current State Analysis

### Repository Statistics
- **Total files**: ~280 files
- **Languages**: Python (CLI, agents), Bash (scripts, hooks), Markdown (docs, commands)
- **Package**: PyPI-ready via `pyproject.toml`

### Critical Issues

| Issue | Severity | Impact |
|-------|----------|--------|
| Build artifacts committed | 🔴 Critical | Bloats repo, confuses contributors |
| No LICENSE file | 🔴 Critical | Legally unclear, blocks adoption |
| Legacy backup directories | 🟡 Medium | Confuses structure |
| External framework mixed in (SC) | 🟡 Medium | Unclear project scope |
| Project-specific docs (TOON) | 🟡 Medium | Irrelevant to users |
| Orphan root-level files | 🟢 Low | Clutter |
| No CI/CD workflows | 🟡 Medium | No automated quality gates |
| No CHANGELOG | 🟢 Low | Hard to track releases |

### Current Directory Tree (Problematic Areas Marked)

```
k-lean/
├── build/                      # ❌ DELETE - build artifact
├── src/k_lean.egg-info/        # ❌ DELETE - build artifact
├── commands/
│   ├── kln/                    # ✅ KEEP - K-LEAN commands
│   ├── kln-v2-backup/          # ❌ DELETE - legacy backup
│   └── sc/                     # ⚠️ MOVE - external framework
├── config/
│   ├── factory-droids/         # ❌ DELETE - duplicate of droids/
│   └── litellm/                # ✅ KEEP
├── docs/
│   ├── TOON_*.md (10 files)    # ❌ DELETE - project-specific
│   └── ... (useful docs)       # ✅ KEEP
├── skills/                     # ❌ DELETE - incomplete (1 file)
├── NEXT_FEATURES/              # ⚠️ MOVE - to GitHub issues
├── bash_functions.sh           # ❌ DELETE - orphan
├── test.sh                     # ❌ DELETE - replaced by k-lean test
├── update.sh                   # ❌ DELETE - stale
├── install.sh                  # ❌ DELETE - replaced by k-lean install
├── config.yaml                 # ⚠️ MOVE - to config/
├── settings.json               # ⚠️ MOVE - to config/
├── audit-settings.json         # ❌ DELETE - project-specific
├── DOCS.md                     # ⚠️ MERGE - into docs/
├── VERSION                     # ❌ DELETE - use pyproject.toml
├── KLEAN-V3-*.txt              # ❌ DELETE - legacy
└── ... (valid files)           # ✅ KEEP
```

---

## Open Source Best Practices

### 1. Repository Root Files (Required)

| File | Purpose | Status |
|------|---------|--------|
| `README.md` | Project overview, quick start | ✅ Exists |
| `LICENSE` | Legal terms (MIT recommended) | ❌ Missing |
| `CHANGELOG.md` | Version history | ❌ Missing |
| `CONTRIBUTING.md` | How to contribute | ❌ Missing |
| `CODE_OF_CONDUCT.md` | Community guidelines | ❌ Missing |
| `pyproject.toml` | Python packaging | ✅ Exists |
| `.gitignore` | Ignored files | ⚠️ Incomplete |

### 2. Directory Structure Standards

```
project-name/
├── .github/                    # GitHub-specific
│   ├── workflows/              # CI/CD pipelines
│   │   ├── ci.yml              # Test on PR
│   │   ├── release.yml         # PyPI publish
│   │   └── lint.yml            # Code quality
│   ├── ISSUE_TEMPLATE/         # Issue templates
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── FUNDING.yml             # Sponsorship
├── src/                        # Source code (src layout)
│   └── package_name/
├── tests/                      # Test files
├── docs/                       # Documentation
├── examples/                   # Usage examples (optional)
└── scripts/                    # Development/build scripts
```

### 3. Naming Conventions

#### Files
| Type | Convention | Examples |
|------|------------|----------|
| Python modules | `snake_case.py` | `cli.py`, `knowledge_db.py` |
| Shell scripts | `kebab-case.sh` | `quick-review.sh`, `kb-init.sh` |
| Markdown docs | `UPPER-KEBAB.md` or `Title-Case.md` | `README.md`, `CONTRIBUTING.md` |
| Config files | `lowercase` | `config.yaml`, `.env.example` |
| Slash commands | `lowercase.md` | `quick.md`, `deep.md` |

#### Directories
| Type | Convention | Examples |
|------|------------|----------|
| Python packages | `snake_case` | `src/klean/`, `klean/agents/` |
| Resource dirs | `lowercase` | `scripts/`, `hooks/`, `docs/` |
| GitHub dirs | `.github/` | Standard convention |

#### Branch Names
| Type | Convention | Examples |
|------|------------|----------|
| Feature | `feat/description` | `feat/mcp-server` |
| Bug fix | `fix/description` | `fix/socket-path` |
| Docs | `docs/description` | `docs/installation` |
| Release | `release/vX.Y.Z` | `release/v1.0.0` |

### 4. Version Numbering (Semantic Versioning)

```
MAJOR.MINOR.PATCH
  │     │     └── Bug fixes, no API changes
  │     └──────── New features, backwards compatible
  └────────────── Breaking changes
```

Current: `1.0.0-beta` → First stable: `1.0.0`

### 5. Commit Message Convention

```
type(scope): description

Types: feat, fix, docs, style, refactor, test, chore
Scope: cli, scripts, hooks, kb, docs (optional)

Examples:
  feat(cli): add MCP server mode
  fix(kb): correct socket path for per-project isolation
  docs: update installation guide
  chore: remove legacy v2 backup files
```

---

## Target Structure

### Proposed Clean Structure

```
k-lean/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml              # Run tests on PR
│   │   ├── release.yml         # Publish to PyPI
│   │   └── sync-check.yml      # Verify k-lean sync
│   ├── ISSUE_TEMPLATE/
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
│
├── src/klean/                  # Python package
│   ├── __init__.py
│   ├── cli.py                  # Main CLI
│   ├── agents/                 # Claude SDK agents
│   ├── droids/                 # Droid base classes
│   ├── knowledge/              # KB integration
│   ├── tools/                  # Agent tools
│   ├── utils/                  # Utilities
│   └── data/                   # Installed resources
│       ├── scripts/            # Synced from /scripts
│       ├── hooks/              # Synced from /hooks
│       ├── commands/kln/       # Synced from /commands/kln
│       ├── droids/             # Synced from /droids
│       ├── config/             # Synced from /config
│       ├── lib/                # Synced from /lib
│       └── core/               # Core engine
│
├── scripts/                    # Source scripts (canonical)
│   ├── quick-review.sh
│   ├── deep-review.sh
│   ├── consensus-review.sh
│   ├── droid-execute.sh
│   ├── knowledge-*.py          # KB scripts
│   ├── kb-*.sh                 # KB utilities
│   └── ...
│
├── hooks/                      # Source hooks (canonical)
│   ├── session-start.sh
│   ├── user-prompt-handler.sh
│   ├── post-bash-handler.sh
│   └── post-web-handler.sh
│
├── commands/
│   └── kln/                    # K-LEAN slash commands
│       ├── quick.md
│       ├── deep.md
│       ├── multi.md
│       ├── droid.md
│       ├── remember.md
│       ├── rethink.md
│       ├── status.md
│       ├── help.md
│       └── doc.md
│
├── droids/                     # Droid specialists
│   ├── code-reviewer.md
│   ├── security-auditor.md
│   ├── debugger.md
│   ├── orchestrator.md
│   ├── arm-cortex-expert.md
│   ├── c-pro.md
│   ├── rust-expert.md
│   ├── performance-engineer.md
│   └── TEMPLATE.md
│
├── config/                     # Configuration templates
│   ├── litellm/
│   │   ├── config.yaml
│   │   ├── openrouter.yaml
│   │   └── .env.example
│   └── CLAUDE.md               # Reference CLAUDE.md
│
├── lib/                        # Shared shell libraries
│   └── common.sh
│
├── docs/                       # Documentation
│   ├── README.md               # Docs index
│   ├── INSTALLATION.md
│   ├── ARCHITECTURE.md
│   ├── COMMANDS.md
│   ├── HOOKS.md
│   ├── KNOWLEDGE-SYSTEM.md
│   ├── REVIEW-SYSTEM.md
│   ├── DROID-SYSTEM.md
│   └── DEVELOPER.md
│
├── tests/                      # Test files
│   └── (to be added)
│
├── examples/                   # Usage examples (optional)
│   └── (to be added)
│
├── .gitignore
├── LICENSE                     # MIT License
├── README.md                   # Project overview
├── CHANGELOG.md                # Version history
├── CONTRIBUTING.md             # Contribution guide
├── CODE_OF_CONDUCT.md          # Community guidelines
├── DEVELOPMENT.md              # Developer setup
├── pyproject.toml              # Python packaging
└── MANIFEST.in                 # Package manifest
```

### Files to DELETE

```bash
# Build artifacts (add to .gitignore)
rm -rf build/
rm -rf src/k_lean.egg-info/

# Legacy/backup
rm -rf commands/kln-v2-backup/
rm -f KLEAN-V3-CHECKSUMS.txt
rm -f KLEAN-V3-INVENTORY.txt

# Project-specific (TOON)
rm -f docs/TOON_*.md
rm -f docs/toon_*.md
rm -f scripts/toon_adapter.py
rm -f scripts/test-toon-adapter.sh

# Orphan root files
rm -f bash_functions.sh
rm -f test.sh
rm -f update.sh
rm -f install.sh
rm -f VERSION
rm -f DOCS.md
rm -f audit-settings.json

# Duplicate configs
rm -rf config/factory-droids/

# Incomplete
rm -rf skills/
```

### Files to MOVE

```bash
# Root configs → config/
mv config.yaml config/
mv settings.json config/

# External framework (decide: keep or separate repo)
# Option A: Keep but mark as optional
mkdir -p external/superclaude
mv commands/sc/ external/superclaude/commands/

# Option B: Remove entirely (users install separately)
rm -rf commands/sc/

# Planning docs → GitHub Issues
# Move content to issues, then delete
rm -rf NEXT_FEATURES/
```

---

## Naming Conventions

### Script Naming

| Category | Pattern | Examples |
|----------|---------|----------|
| Review scripts | `{type}-review.sh` | `quick-review.sh`, `deep-review.sh` |
| Knowledge scripts | `knowledge-{action}.{ext}` | `knowledge-query.sh`, `knowledge-capture.py` |
| KB utilities | `kb-{action}.sh` | `kb-init.sh`, `kb-doctor.sh` |
| Health checks | `health-check*.sh` | `health-check.sh`, `health-check-model.sh` |
| LiteLLM | `*-litellm.sh` or `litellm-*.sh` | `setup-litellm.sh`, `start-litellm.sh` |
| Utilities | Descriptive kebab-case | `session-helper.sh`, `async-dispatch.sh` |

### Python Module Naming

| Category | Pattern | Examples |
|----------|---------|----------|
| Database | `{thing}_db.py` | `knowledge_db.py` |
| Utilities | `{thing}_utils.py` | `kb_utils.py` |
| Server | `{thing}-server.py` | `knowledge-server.py` |
| CLI tools | `klean-{tool}.py` | `klean-statusline.py` |

### Command Naming (/kln:*)

| Category | Pattern | Examples |
|----------|---------|----------|
| Review actions | Single verb | `quick`, `deep`, `multi` |
| Agent actions | Noun | `droid`, `doc` |
| Meta actions | Verb | `remember`, `rethink`, `help` |
| Status | Noun | `status` |

### Droid Naming

| Pattern | Examples |
|---------|----------|
| `{role}.md` | `code-reviewer.md`, `security-auditor.md` |
| `{specialty}-expert.md` | `arm-cortex-expert.md`, `rust-expert.md` |
| `{specialty}-pro.md` | `c-pro.md` |

---

## Migration Plan

### Phase 1: Cleanup (No Breaking Changes)

**Goal**: Remove clutter without affecting functionality

```bash
# 1. Update .gitignore first
echo "build/" >> .gitignore
echo "*.egg-info/" >> .gitignore
echo "dist/" >> .gitignore
echo "__pycache__/" >> .gitignore
echo ".knowledge-db/" >> .gitignore

# 2. Remove build artifacts
rm -rf build/ src/k_lean.egg-info/

# 3. Remove legacy backups
rm -rf commands/kln-v2-backup/
rm -f KLEAN-V3-*.txt

# 4. Remove orphan files
rm -f bash_functions.sh test.sh update.sh install.sh VERSION DOCS.md

# 5. Remove project-specific files
rm -f docs/TOON_*.md scripts/toon_adapter.py scripts/test-toon-adapter.sh

# 6. Remove duplicates
rm -rf config/factory-droids/
rm -rf skills/
rm -f audit-settings.json
```

**Verification**: `k-lean test` should still pass

### Phase 2: Add Required Files

```bash
# 1. Create LICENSE (MIT)
cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2024-2025 K-LEAN Contributors

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

# 2. Create CHANGELOG.md
cat > CHANGELOG.md << 'EOF'
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - Unreleased

### Added
- Initial open source release
- Multi-model code review via LiteLLM proxy
- Per-project semantic knowledge database
- 8 specialized droid reviewers
- Claude Code integration via hooks and slash commands

### Changed
- Restructured repository for open source standards

### Removed
- Legacy v2 commands
- Project-specific documentation
EOF

# 3. Create CONTRIBUTING.md
# (content below)

# 4. Create CODE_OF_CONDUCT.md
# (use Contributor Covenant)
```

### Phase 3: Reorganize Configs

```bash
# Move root-level configs
mv config.yaml config/
mv settings.json config/

# Update any references in code
# (search for hardcoded paths)
```

### Phase 4: Handle SuperClaude

**Option A: Keep as Optional (Recommended)**
```bash
# Document that SC is external
# Add note in README: "SuperClaude commands are optional"
# Keep commands/sc/ as-is
```

**Option B: Separate Repository**
```bash
# Remove from K-LEAN
rm -rf commands/sc/
# Create separate repo: superclaude-commands
```

### Phase 5: Add CI/CD

Create `.github/workflows/ci.yml`:
```yaml
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
      - run: pip install -e .
      - run: k-lean sync --check
      - run: k-lean test
```

---

## File-by-File Actions

### DELETE (Safe - No Dependencies)

| File/Directory | Reason |
|----------------|--------|
| `build/` | Build artifact |
| `src/k_lean.egg-info/` | Build artifact |
| `commands/kln-v2-backup/` | Legacy backup |
| `KLEAN-V3-CHECKSUMS.txt` | Legacy |
| `KLEAN-V3-INVENTORY.txt` | Legacy |
| `docs/TOON_*.md` | Project-specific |
| `scripts/toon_adapter.py` | Project-specific |
| `scripts/test-toon-adapter.sh` | Project-specific |
| `bash_functions.sh` | Orphan, unused |
| `test.sh` | Replaced by `k-lean test` |
| `update.sh` | Stale |
| `install.sh` | Replaced by `k-lean install` |
| `VERSION` | Duplicates pyproject.toml |
| `DOCS.md` | Merge into docs/README.md |
| `audit-settings.json` | Project-specific |
| `config/factory-droids/` | Duplicate of droids/ |
| `skills/` | Incomplete (1 file) |
| `NEXT_FEATURES/` | Move to GitHub issues |

### MOVE

| From | To | Reason |
|------|-----|--------|
| `config.yaml` | `config/config.yaml` | Organize |
| `settings.json` | `config/settings.json` | Organize |

### CREATE

| File | Purpose |
|------|---------|
| `LICENSE` | MIT license |
| `CHANGELOG.md` | Version history |
| `CONTRIBUTING.md` | Contribution guide |
| `CODE_OF_CONDUCT.md` | Community guidelines |
| `.github/workflows/ci.yml` | CI pipeline |
| `.github/ISSUE_TEMPLATE/bug_report.md` | Bug template |
| `.github/ISSUE_TEMPLATE/feature_request.md` | Feature template |

### UPDATE

| File | Change |
|------|--------|
| `.gitignore` | Add build artifacts, eggs, dist |
| `README.md` | Add badges, improve quick start |
| `docs/README.md` | Merge DOCS.md content |

---

## Safety Checklist

### Before Any Changes

- [ ] Run `k-lean test` - all 27 tests pass
- [ ] Run `k-lean sync --check` - package in sync
- [ ] Commit current state with tag: `git tag pre-cleanup`

### After Phase 1 (Cleanup)

- [ ] Run `k-lean test` - all tests still pass
- [ ] Run `k-lean sync --check` - still in sync
- [ ] Verify `k-lean install` works
- [ ] Verify `k-lean status` works
- [ ] Verify `k-lean start` works

### After Phase 2 (New Files)

- [ ] LICENSE file present
- [ ] CHANGELOG.md present
- [ ] CONTRIBUTING.md present

### After Phase 3 (Reorg)

- [ ] No broken imports
- [ ] Config files found at new paths
- [ ] All features functional

### Before Release

- [ ] All CI checks pass
- [ ] `k-lean sync` runs clean
- [ ] PyPI test upload works
- [ ] README renders correctly on GitHub
- [ ] All links in docs work

---

## Summary

### Quick Stats

| Metric | Before | After |
|--------|--------|-------|
| Files | ~280 | ~180 |
| Root files | 25+ | 10 |
| Directories | 20+ | 12 |
| Legacy/backup | 17 files | 0 |
| Build artifacts | Committed | Ignored |
| License | Missing | MIT |
| CI/CD | None | GitHub Actions |

### Commit Sequence

```bash
git tag pre-cleanup

# Phase 1
git add -A && git commit -m "chore: remove build artifacts and legacy files"

# Phase 2
git add LICENSE CHANGELOG.md CONTRIBUTING.md CODE_OF_CONDUCT.md
git commit -m "docs: add required open source files"

# Phase 3
git add .github/
git commit -m "ci: add GitHub Actions workflows"

# Phase 4
git add -A && git commit -m "chore: reorganize config files"

# Final
git tag v1.0.0-rc1
```

---

*Document created: 2025-12-21*
*Status: Ready for review and execution*
