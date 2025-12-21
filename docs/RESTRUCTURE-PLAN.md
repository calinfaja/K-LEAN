# K-LEAN Open Source Restructure Plan v2.2

## Status: TESTED - READY FOR COMMIT

**Execution Date:** 2024-12-21
**Current State:** All phases executed, symlinks fixed, all tests passed, ready to commit

---

## Executive Summary

This plan transformed `review-system-backup/` into a clean, maintainable open source repository.

**Changes Made:**
- Root cleanup: 30+ items → 12 items
- Documentation reorganized with clear hierarchy (guides/reference/dev)
- Future features isolated in `roadmap/`
- SuperClaude removed (separate framework, installed independently)
- TOON moved to `roadmap/toon/` for future integration
- Open source files created (LICENSE, CHANGELOG, CONTRIBUTING, .github/)

**Critical Constraint:** Zero breaking changes - all K-LEAN functionality works identically.

---

## Current Structure (After Restructure)

```
review-system-backup/           # Can rename to k-lean/ after commit
├── README.md                   # Entry point
├── LICENSE                     # MIT license ✓ CREATED
├── CHANGELOG.md                # Version history ✓ CREATED
├── CONTRIBUTING.md             # Contribution guide ✓ CREATED
├── CLAUDE.md                   # Claude Code config
├── pyproject.toml              # Package config
├── .gitignore                  # Updated with new patterns
│
├── src/klean/                  # Core package (unchanged internally)
│   └── data/
│       ├── scripts/            # 36 active scripts
│       ├── hooks/              # 5 hooks
│       ├── commands/kln/       # 9 K-LEAN commands
│       ├── config/             # Config templates
│       └── lib/                # Shared libraries
│
├── docs/                       # Reorganized documentation
│   ├── README.md               # Documentation index ✓ UPDATED
│   ├── INSTALLATION.md
│   ├── RESTRUCTURE-PLAN.md     # This file
│   ├── guides/                 # ✓ CREATED
│   │   ├── knowledge-db.md
│   │   ├── droids.md
│   │   └── hooks.md
│   ├── reference/              # ✓ CREATED
│   │   ├── commands.md
│   │   ├── architecture.md
│   │   ├── cli.md
│   │   └── docs-index.md
│   └── dev/                    # ✓ CREATED
│       ├── development.md
│       ├── lessons-learned.md
│       ├── open-source-plan.md
│       └── review-plan.md
│
├── droids/                     # 9 Factory droid definitions
│
├── config/                     # Config templates
│   ├── klean-config.yaml       # ✓ MOVED from root
│   └── settings.json           # ✓ MOVED from root
│
├── tests/                      # Test suite
│
├── roadmap/                    # ✓ CREATED - Future features
│   ├── README.md
│   ├── toon/                   # TOON compression (moved here)
│   │   ├── README.md
│   │   ├── toon_adapter.py
│   │   ├── context_injector.py
│   │   ├── test-toon-adapter.sh
│   │   └── docs/               # 13 TOON docs
│   └── semantic-memory/
│       ├── ORIGINAL_README.md
│       └── SEMANTIC_MEMORY_SYSTEM.md
│
└── .github/                    # ✓ CREATED
    ├── workflows/ci.yml
    ├── ISSUE_TEMPLATE/
    │   ├── bug_report.md
    │   └── feature_request.md
    └── PULL_REQUEST_TEMPLATE.md
```

---

## Phases Executed

### Phase 1: Preparation ✓ COMPLETE
- Created backup branch: `pre-restructure-backup`
- Verified K-LEAN v1.0.0-beta working

### Phase 2: Delete Build Artifacts ✓ COMPLETE
```bash
# Deleted:
build/
dist/
src/k_lean.egg-info/
.pytest_cache/
__pycache__/ (all)
VERSION
```

### Phase 3: Delete Legacy Install Scripts ✓ COMPLETE
```bash
# Deleted:
install.sh      # Replaced by: pipx install k-lean
update.sh       # Replaced by: pipx upgrade k-lean
test.sh         # Replaced by: k-lean status
bash_functions.sh  # Obsolete
```

### Phase 4: Move TOON to roadmap/ ✓ COMPLETE
```bash
# Moved to roadmap/toon/:
toon_adapter.py
test-toon-adapter.sh
knowledge-context-injector.py → context_injector.py

# Moved to roadmap/toon/docs/:
TOON*.md (10 files)
PHASE3_RESULTS.md
PHASE4_DEPLOYMENT.md
PHASE4_VALIDATION_REPORT.md

# Moved to roadmap/semantic-memory/:
NEXT_FEATURES/ contents
```

### Phase 5: Remove SuperClaude ✓ COMPLETE
```bash
# Deleted:
src/klean/data/commands/sc/    # 32 files - separate framework
src/klean/data/skills/         # Incomplete feature
skills/                        # Root duplicate
```

### Phase 6: Delete Orphan Scripts ✓ COMPLETE
```bash
# Deleted (verified no references):
litellm-review.sh
knowledge-fast.sh
knowledge-migrate-schema.py

# PRESERVED (has active reference from auto-capture-hook.sh):
knowledge-extract.sh
```

### Phase 7: Delete Duplicate Configs ✓ COMPLETE
```bash
# Deleted:
src/klean/data/config/factory-droids/
src/klean/data/config/code-reviewer.md
src/klean/data/config/security-auditor.md
audit-settings.json
KLEAN-V3-CHECKSUMS.txt
KLEAN-V3-INVENTORY.txt
MANIFEST.in
```

### Phase 8: Reorganize Documentation ✓ COMPLETE
```bash
# Created structure:
docs/guides/
docs/reference/
docs/dev/

# Moved files to appropriate subdirectories
# Updated docs/README.md with new navigation
# Deleted obsolete docs (IMPLEMENTATION-*, IMPROVEMENT-*, etc.)
```

### Phase 9: Clean Up Root Directory ✓ COMPLETE
```bash
# Deleted root duplicates (canonical is src/klean/data/):
commands/
hooks/
scripts/
lib/

# Moved to config/:
config.yaml → config/klean-config.yaml
settings.json → config/settings.json
```

### Phase 10: Update .gitignore ✓ COMPLETE
- Added build artifacts patterns
- Added testing patterns
- Added IDE patterns
- Added local config override patterns

### Phase 11: Create Open Source Files ✓ COMPLETE
```bash
# Created:
LICENSE                              # MIT
CHANGELOG.md                         # v1.0.0-beta
CONTRIBUTING.md                      # Contribution guide
.github/workflows/ci.yml             # CI pipeline
.github/ISSUE_TEMPLATE/bug_report.md
.github/ISSUE_TEMPLATE/feature_request.md
.github/PULL_REQUEST_TEMPLATE.md
```

### Phase 12: Verification ✓ COMPLETE
```
✓ k-lean --version         → 1.0.0-beta
✓ k-lean status            → All components OK
✓ Root items               → 12 (was 30+)
✓ Commands                 → 9 K-LEAN commands
✓ Hooks                    → 5 hooks present
✓ Scripts                  → 36 active scripts
✓ Droids                   → 9 droids present
✓ TOON                     → Moved to roadmap/
✓ SuperClaude              → Removed
✓ Critical scripts         → All present
```

---

## Critical Fix: Symlinks

**Issue Discovered:** After deleting root directories (scripts/, hooks/, commands/, lib/),
the symlinks in `~/.claude/` were broken because they pointed to those deleted directories.

**Fix Applied:**
```bash
# Remove broken symlinks and create new ones pointing to src/klean/data/

# Scripts (36 .sh + 11 .py)
find ~/.claude/scripts -maxdepth 1 -type l ! -exec test -e {} \; -delete
for f in /path/to/src/klean/data/scripts/*.sh *.py; do
    ln -sf "$f" ~/.claude/scripts/$(basename "$f")
done

# Hooks (5 files)
find ~/.claude/hooks -maxdepth 1 -type l ! -exec test -e {} \; -delete
for f in /path/to/src/klean/data/hooks/*.sh; do
    ln -sf "$f" ~/.claude/hooks/$(basename "$f")
done

# Commands (9 files)
find ~/.claude/commands/kln -maxdepth 1 -type l ! -exec test -e {} \; -delete
for f in /path/to/src/klean/data/commands/kln/*.md; do
    ln -sf "$f" ~/.claude/commands/kln/$(basename "$f")
done

# Lib (1 file)
find ~/.claude/lib -maxdepth 1 -type l ! -exec test -e {} \; -delete
for f in /path/to/src/klean/data/lib/*.sh; do
    ln -sf "$f" ~/.claude/lib/$(basename "$f")
done
```

**Verification:** `k-lean doctor` shows "No issues found!"

---

## Completed Steps

### Phase 13: Final Complete Test ✓ COMPLETE
```
k-lean test    → All 27 tests passed!
k-lean doctor  → No issues found!
k-lean status  → All components OK
```

### Phase 14: Git Commit ⏳ PENDING
```bash
git add -A
git status  # Review all changes

git commit -m "$(cat <<'EOF'
Restructure for open source release

Root cleanup:
- Reduced root from 30+ to 12 items
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

### Phase 15: Repository Rename (Optional) ⏳ PENDING
```bash
cd /home/calin/claudeAgentic
mv review-system-backup k-lean
```

---

## Rollback Instructions

If issues arise:

```bash
# Full reset (discard all changes)
git checkout .
git clean -fd

# Or restore from backup branch
git checkout pre-restructure-backup
```

---

## Verification Checklist (For Final Test)

### Core Functionality
- [ ] `k-lean --version` returns 1.0.0-beta
- [ ] `k-lean status` shows all components green
- [ ] `k-lean doctor` passes all checks

### Knowledge DB
- [ ] `InitKB` initializes database
- [ ] `SaveThis "test lesson"` saves successfully
- [ ] `FindKnowledge "test"` returns results

### Reviews (requires LiteLLM)
- [ ] `healthcheck` tests all models
- [ ] `/kln:quick qwen test` executes

### Hooks
- [ ] Session start hook triggers
- [ ] User prompt handler responds to keywords

### Droids
- [ ] Droids listed in `k-lean status`
- [ ] Droid execution works (if Factory installed)

### Structure
- [ ] Root has 12 items
- [ ] docs/ has guides/, reference/, dev/
- [ ] roadmap/ has toon/, semantic-memory/
- [ ] No TOON files in src/klean/data/scripts/
- [ ] No SuperClaude in src/klean/data/commands/

---

## Files Summary

### Deleted (~100 files)
| Category | Count | Examples |
|----------|-------|----------|
| Build artifacts | ~10 | build/, dist/, *.egg-info |
| Legacy scripts | 4 | install.sh, update.sh, test.sh |
| SuperClaude | 32 | commands/sc/*.md |
| V2 backup | 17 | commands/kln-v2-backup/*.md |
| Orphan scripts | 3 | litellm-review.sh, knowledge-fast.sh |
| TOON (moved) | 16 | toon_adapter.py, TOON*.md |
| Duplicate dirs | 4 | commands/, hooks/, scripts/, lib/ |
| Obsolete docs | 10 | IMPLEMENTATION-*.md, IMPROVEMENT-*.md |

### Created (~15 files)
| File | Purpose |
|------|---------|
| LICENSE | MIT license |
| CHANGELOG.md | Version history |
| CONTRIBUTING.md | Contribution guide |
| docs/README.md | Documentation index |
| docs/guides/*.md | User guides |
| docs/reference/*.md | Technical reference |
| docs/dev/*.md | Developer docs |
| roadmap/README.md | Roadmap overview |
| roadmap/toon/README.md | TOON feature docs |
| .github/workflows/ci.yml | CI pipeline |
| .github/ISSUE_TEMPLATE/*.md | Issue templates |
| .github/PULL_REQUEST_TEMPLATE.md | PR template |

### Moved (~20 files)
| From | To |
|------|-----|
| toon_adapter.py | roadmap/toon/ |
| knowledge-context-injector.py | roadmap/toon/context_injector.py |
| TOON*.md | roadmap/toon/docs/ |
| NEXT_FEATURES/* | roadmap/semantic-memory/ |
| config.yaml | config/klean-config.yaml |
| settings.json | config/settings.json |
| Various docs | docs/guides/, docs/reference/, docs/dev/ |

---

*Plan Version: 2.2*
*Last Updated: 2024-12-21*
*Status: Tested - Ready for Commit*
