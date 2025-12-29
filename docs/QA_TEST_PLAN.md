# K-LEAN QA Test Plan

**Version**: 1.0.0-beta
**Created**: 2025-12-29
**Purpose**: Comprehensive test coverage for installation and all system components

---

## Test Categories Overview

| Category | Tests | Priority | Automation |
|----------|-------|----------|------------|
| Installation | 12 | Critical | Partial |
| Provider Setup | 8 | Critical | Manual |
| Service Management | 10 | High | Full |
| CLI Commands | 15 | High | Full |
| Slash Commands | 9 | High | Manual |
| Hooks | 6 | Medium | Manual |
| Knowledge DB | 12 | High | Partial |
| SmolKLN Agents | 8 | Medium | Partial |
| Multi-Agent | 6 | Medium | Partial |
| Integration | 10 | High | Partial |

---

## 1. Installation Tests

### Prerequisites
- [ ] Python 3.9+ installed
- [ ] pipx installed and in PATH
- [ ] Internet connection
- [ ] No existing K-LEAN installation

### INST-001: Fresh Install via pipx
```bash
# Steps
pipx install k-lean

# Expected
# - No errors
# - k-lean command available
# - smol-kln command available

# Verify
which k-lean
k-lean --version
```

### INST-002: Install with All Extras
```bash
# Steps
pipx install "k-lean[all]"

# Expected
# - smolagents installed
# - txtai installed
# - phoenix installed

# Verify
pipx runpip k-lean list | grep -E "smolagents|txtai|arize"
```

### INST-003: Component Installation
```bash
# Steps
k-lean install

# Expected
# - Scripts copied to ~/.claude/scripts/
# - Hooks copied to ~/.claude/hooks/
# - Commands copied to ~/.claude/commands/
# - Rules copied to ~/.claude/rules/

# Verify
ls ~/.claude/scripts/*.sh | wc -l  # Should be 20+
ls ~/.claude/hooks/*.sh | wc -l    # Should be 4+
ls ~/.claude/commands/kln/*.md | wc -l  # Should be 9
ls ~/.claude/rules/k-lean.md        # Should exist
```

### INST-004: Upgrade Existing Installation
```bash
# Prerequisites: K-LEAN already installed

# Steps
pipx upgrade k-lean

# Expected
# - Version updated
# - Existing configs preserved

# Verify
k-lean --version
cat ~/.config/litellm/config.yaml  # Should still exist
```

### INST-005: Uninstall Clean
```bash
# Steps
k-lean uninstall
pipx uninstall k-lean

# Expected
# - ~/.claude/scripts/ K-LEAN files removed
# - ~/.claude/hooks/ K-LEAN hooks removed
# - Commands removed

# Verify
ls ~/.claude/scripts/quick-review.sh 2>/dev/null  # Should not exist
which k-lean  # Should not exist
```

### INST-006: Install Without Root
```bash
# Steps (as non-root user)
pipx install k-lean
k-lean install

# Expected
# - All operations succeed without sudo
# - Files in user directories only

# Verify
find ~/.claude -type f | head -5
```

### INST-007: Install with Missing Python
```bash
# Prerequisites: Python < 3.9 or missing

# Steps
pipx install k-lean

# Expected
# - Clear error message about Python version
# - Installation fails gracefully
```

### INST-008: Install with Missing pipx
```bash
# Prerequisites: pipx not installed

# Steps
k-lean install  # Will fail

# Expected
# - Error message suggesting: pip install pipx
```

### INST-009: Reinstall Over Existing
```bash
# Prerequisites: K-LEAN already installed

# Steps
k-lean install

# Expected
# - Existing files updated
# - Settings preserved
# - No duplicate entries

# Verify
grep -c "UserPromptSubmit" ~/.claude/settings.json  # Should be 1
```

### INST-010: Install with Custom Claude Directory
```bash
# Steps
CLAUDE_HOME=/custom/path k-lean install

# Expected
# - Files installed to custom path
# - Paths correctly configured

# Verify
ls /custom/path/scripts/
```

### INST-011: Verify Executable Permissions
```bash
# After install

# Verify
ls -la ~/.claude/scripts/*.sh | grep "^-rwx"
ls -la ~/.claude/hooks/*.sh | grep "^-rwx"
```

### INST-012: Verify Symlinks (Dev Mode)
```bash
# Steps
k-lean install --dev

# Expected
# - Symlinks instead of copies
# - Source changes reflected immediately

# Verify
ls -la ~/.claude/scripts/quick-review.sh  # Should show ->
```

---

## 2. Provider Setup Tests

### SETUP-001: Interactive Setup (NanoGPT)
```bash
# Steps
k-lean setup
# Select: nanogpt
# Enter API key

# Expected
# - Config created at ~/.config/litellm/config.yaml
# - API key saved securely

# Verify
cat ~/.config/litellm/config.yaml | grep nanogpt
```

### SETUP-002: Interactive Setup (OpenRouter)
```bash
# Steps
k-lean setup
# Select: openrouter
# Enter API key

# Expected
# - OpenRouter models configured
# - API key in config

# Verify
cat ~/.config/litellm/config.yaml | grep openrouter
```

### SETUP-003: Setup with Invalid API Key
```bash
# Steps
k-lean setup
# Enter: invalid-key-12345

# Expected
# - Warning about key format (optional)
# - Config still created
# - First model test will fail
```

### SETUP-004: Setup Preserves Existing Config
```bash
# Prerequisites: Existing config with custom settings

# Steps
k-lean setup --provider nanogpt

# Expected
# - New provider added
# - Existing providers preserved

# Verify
cat ~/.config/litellm/config.yaml | grep -c "model_list"
```

### SETUP-005: Setup Creates Directory Structure
```bash
# Prerequisites: ~/.config/litellm/ does not exist

# Steps
k-lean setup

# Expected
# - Directory created
# - config.yaml created
# - Correct permissions (600)

# Verify
ls -la ~/.config/litellm/config.yaml
```

### SETUP-006: Re-run Setup (Change Provider)
```bash
# Prerequisites: NanoGPT configured

# Steps
k-lean setup
# Select: openrouter

# Expected
# - OpenRouter replaces NanoGPT
# - Or both coexist (user choice)
```

### SETUP-007: Setup with Environment Variable
```bash
# Steps
NANOGPT_API_KEY=xxx k-lean setup --provider nanogpt

# Expected
# - API key picked up from env
# - No interactive prompt for key
```

### SETUP-008: Validate Config After Setup
```bash
# Steps
k-lean setup
k-lean doctor

# Expected
# - No config-related issues
# - LiteLLM config valid

# Verify
k-lean doctor | grep -i "config"
```

---

## 3. Service Management Tests

### SVC-001: Start LiteLLM
```bash
# Steps
k-lean start

# Expected
# - LiteLLM proxy starts on port 4000
# - Health endpoint responds

# Verify
curl -s http://localhost:4000/health | jq .
lsof -i :4000
```

### SVC-002: Start with Custom Port
```bash
# Steps
k-lean start --port 4001

# Expected
# - LiteLLM on port 4001
# - Other components use correct port

# Verify
curl -s http://localhost:4001/health
```

### SVC-003: Stop LiteLLM
```bash
# Prerequisites: LiteLLM running

# Steps
k-lean stop

# Expected
# - Process terminated
# - Port freed

# Verify
lsof -i :4000  # Should be empty
```

### SVC-004: Start Knowledge Server
```bash
# Prerequisites: In a git project

# Steps
k-lean start knowledge

# Expected
# - Socket created at /tmp/kb-*.sock
# - Server responds to queries

# Verify
ls /tmp/kb-*.sock
```

### SVC-005: Stop Knowledge Server
```bash
# Steps
k-lean stop knowledge

# Expected
# - Socket removed
# - Process terminated

# Verify
ls /tmp/kb-*.sock 2>/dev/null  # Should not exist
```

### SVC-006: Start All Services
```bash
# Steps
k-lean start --all

# Expected
# - LiteLLM running
# - Knowledge server running (if in project)

# Verify
k-lean status
```

### SVC-007: Restart After Crash
```bash
# Simulate crash
kill -9 $(pgrep -f litellm)

# Steps
k-lean start

# Expected
# - Cleans stale PID
# - Starts fresh

# Verify
k-lean status | grep -i litellm
```

### SVC-008: Start Without Config
```bash
# Prerequisites: No ~/.config/litellm/config.yaml

# Steps
k-lean start

# Expected
# - Clear error message
# - Suggests: k-lean setup

# Verify
k-lean start 2>&1 | grep -i "setup"
```

### SVC-009: Check Service Status
```bash
# Steps
k-lean status

# Expected
# - LiteLLM status (running/stopped)
# - Knowledge server status
# - Model count
# - Health indicators

# Verify
k-lean status | grep -E "LiteLLM|Knowledge|Models"
```

### SVC-010: Start with Telemetry
```bash
# Prerequisites: Phoenix installed

# Steps
k-lean start --telemetry

# Expected
# - Phoenix UI on port 6006
# - Traces being collected

# Verify
curl -s http://localhost:6006 | head -1
```

---

## 4. CLI Command Tests

### CLI-001: Version Command
```bash
# Steps
k-lean --version

# Expected
# - Version number displayed
# - Format: k-lean, version X.Y.Z

# Verify
k-lean --version | grep -E "^k-lean.*[0-9]+\.[0-9]+\.[0-9]+"
```

### CLI-002: Help Command
```bash
# Steps
k-lean --help

# Expected
# - All commands listed
# - Descriptions shown

# Verify
k-lean --help | grep -E "install|setup|status|doctor|start|stop"
```

### CLI-003: Status Command
```bash
# Steps
k-lean status

# Expected
# - Component statuses
# - Health indicators
# - No crashes

# Verify
k-lean status; echo "Exit: $?"  # Should be 0
```

### CLI-004: Doctor Command
```bash
# Steps
k-lean doctor

# Expected
# - All checks run
# - Issues listed with severity
# - Suggestions provided

# Verify
k-lean doctor | grep -E "\[.*\]"  # Status indicators
```

### CLI-005: Doctor Auto-Fix
```bash
# Prerequisites: Fixable issues present

# Steps
k-lean doctor -f

# Expected
# - Issues automatically resolved
# - Summary of fixes

# Verify
k-lean doctor | grep -i "fixed"
```

### CLI-006: Models Command
```bash
# Prerequisites: LiteLLM running

# Steps
k-lean models

# Expected
# - List of available models
# - Health status per model

# Verify
k-lean models | wc -l  # Should be > 1
```

### CLI-007: Models with Health Check
```bash
# Steps
k-lean models --health

# Expected
# - Each model tested
# - Latency shown
# - Status indicators

# Verify
k-lean models --health | grep -E "ms|OK|FAIL"
```

### CLI-008: Test-Model Command
```bash
# Prerequisites: LiteLLM running

# Steps
k-lean test-model

# Expected
# - First model tested
# - Response received
# - Latency shown

# Verify
k-lean test-model | grep -i "response"
```

### CLI-009: Test Specific Model
```bash
# Steps
k-lean test-model --model qwen3-coder

# Expected
# - Specified model tested
# - Clear result

# Verify
k-lean test-model --model qwen3-coder | grep -i "qwen"
```

### CLI-010: Multi Command
```bash
# Prerequisites: LiteLLM running, in git project

# Steps
k-lean multi "security review"

# Expected
# - Multi-agent review runs
# - Output generated
# - No crashes

# Verify
echo $?  # Should be 0
```

### CLI-011: Multi with Thorough Flag
```bash
# Steps
k-lean multi --thorough "security review"

# Expected
# - 4-agent config used
# - More detailed output

# Verify
# Check output length is longer than default
```

### CLI-012: Debug Command
```bash
# Prerequisites: Services running

# Steps
k-lean debug

# Expected
# - Dashboard displayed
# - Real-time updates
# - Ctrl+C exits cleanly

# Verify (interactive)
```

### CLI-013: Sync Command
```bash
# Steps
k-lean sync --check

# Expected
# - Shows sync status
# - Lists differences

# Verify
k-lean sync --check | grep -E "synced|differs"
```

### CLI-014: Test Command (Full Suite)
```bash
# Steps
k-lean test

# Expected
# - All 27 tests run
# - Results displayed
# - Exit code reflects pass/fail

# Verify
k-lean test | grep -E "passed|failed"
```

### CLI-015: Unknown Command
```bash
# Steps
k-lean unknown-command

# Expected
# - Error message
# - Suggests --help
# - Exit code non-zero

# Verify
k-lean unknown-command; echo "Exit: $?"
```

---

## 5. Slash Command Tests (Claude Code)

### SLASH-001: /kln:status
```
# In Claude Code session
/kln:status

# Expected
# - System status displayed
# - LiteLLM status
# - Knowledge DB status
# - Model list
```

### SLASH-002: /kln:help
```
# In Claude Code session
/kln:help

# Expected
# - Command reference shown
# - All commands listed
# - Examples provided
```

### SLASH-003: /kln:quick
```
# In Claude Code session (in git project)
/kln:quick security

# Expected
# - Quick review runs
# - Single model used
# - Results displayed

# Verify
# Check /tmp/claude-reviews/ for output
```

### SLASH-004: /kln:multi
```
# In Claude Code session
/kln:multi --models 3 architecture

# Expected
# - 3 models used
# - Consensus generated
# - Results formatted
```

### SLASH-005: /kln:deep
```
# In Claude Code session
/kln:deep security

# Expected
# - Deep analysis runs
# - Multiple passes
# - Comprehensive output
```

### SLASH-006: /kln:agent
```
# In Claude Code session
/kln:agent --role security-auditor

# Expected
# - SmolKLN agent runs
# - Output saved to file
# - Results displayed
```

### SLASH-007: /kln:rethink
```
# In Claude Code session
/kln:rethink "stuck on bug"

# Expected
# - Fresh perspective analysis
# - Alternative approaches suggested
```

### SLASH-008: /kln:remember
```
# In Claude Code session (end of session)
/kln:remember

# Expected
# - Session learnings captured
# - Saved to knowledge DB
```

### SLASH-009: /kln:doc
```
# In Claude Code session
/kln:doc "Sprint Review"

# Expected
# - Documentation generated
# - Saved to appropriate location
```

---

## 6. Hook Tests

### HOOK-001: SaveThis Command
```
# In Claude Code session
SaveThis "Always check for null before dereferencing"

# Expected
# - Entry saved to knowledge DB
# - Confirmation message
# - Entry searchable

# Verify
FindKnowledge null
```

### HOOK-002: SaveThis with Type
```
# In Claude Code session
SaveThis "Use --no-verify sparingly" --type warning --priority high

# Expected
# - Entry with correct type
# - Priority recorded
```

### HOOK-003: FindKnowledge
```
# Prerequisites: Entries in knowledge DB

# In Claude Code session
FindKnowledge authentication

# Expected
# - Matching entries displayed
# - Relevance scores shown
```

### HOOK-004: asyncReview
```
# In Claude Code session
asyncReview qwen3-coder security

# Expected
# - Background process started
# - PID returned
# - Log file created

# Verify
ls /tmp/claude-reviews/review-*.log
```

### HOOK-005: asyncConsensus
```
# In Claude Code session
asyncConsensus architecture

# Expected
# - 3-model consensus in background
# - Log file created
```

### HOOK-006: Post-Commit Hook
```
# After git commit

# Expected
# - Timeline entry created
# - Commit documented

# Verify
cat .knowledge-db/timeline.txt | tail -5
```

---

## 7. Knowledge Database Tests

### KB-001: Initialize Knowledge DB
```bash
# In project directory (first time)
SaveThis "Test entry"

# Expected
# - .knowledge-db/ created
# - entries.jsonl created
# - Server started

# Verify
ls -la .knowledge-db/
```

### KB-002: Add Entry
```bash
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-capture.py "Test lesson"

# Expected
# - Entry added to entries.jsonl
# - Entry has ID, timestamp, type

# Verify
tail -1 .knowledge-db/entries.jsonl | jq .
```

### KB-003: Search Entries
```bash
~/.claude/scripts/knowledge-query.sh "test"

# Expected
# - Matching entries returned
# - Relevance scores shown
# - Formatted output

# Verify
~/.claude/scripts/knowledge-query.sh "test" | head -5
```

### KB-004: Hybrid Search
```bash
~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-hybrid-search.py "authentication security"

# Expected
# - BM25 + semantic results
# - Combined ranking
# - Relevant entries first
```

### KB-005: Server Query (Fast Path)
```bash
# Prerequisites: Server running

# Steps
time ~/.claude/scripts/knowledge-query.sh "test"

# Expected
# - Response < 100ms
# - Uses socket connection

# Verify
# Compare with cold start (~17s)
```

### KB-006: Server Health Check
```bash
# Steps
curl --unix-socket /tmp/kb-*.sock http://localhost/health

# Expected
# - Status: ok
# - Entry count
# - Uptime
```

### KB-007: Timeline Query
```bash
~/.claude/scripts/timeline-query.sh today

# Expected
# - Today's entries shown
# - Chronological order
# - Formatted output
```

### KB-008: Timeline Query - Commits
```bash
~/.claude/scripts/timeline-query.sh commits

# Expected
# - Recent commits shown
# - Commit messages included
```

### KB-009: Concurrent Access
```bash
# Steps (two terminals)
# Terminal 1: SaveThis "Entry 1"
# Terminal 2: SaveThis "Entry 2"

# Expected
# - Both entries saved
# - No corruption
# - No race conditions

# Verify
wc -l .knowledge-db/entries.jsonl
```

### KB-010: Large Entry Handling
```bash
# Steps
SaveThis "$(cat large_file.txt)"  # 10KB content

# Expected
# - Entry saved (or truncated gracefully)
# - No crash
# - Searchable
```

### KB-011: Unicode Support
```bash
SaveThis "Test with emoji and unicode"

# Expected
# - Entry saved correctly
# - Searchable
# - Displayed correctly

# Verify
FindKnowledge emoji
```

### KB-012: Corrupted DB Recovery
```bash
# Prerequisites: Corrupt entries.jsonl

# Steps
~/.claude/scripts/knowledge-query.sh "test"

# Expected
# - Graceful error handling
# - Suggestion to run kb-doctor.sh
```

---

## 8. SmolKLN Agent Tests

### SMOL-001: List Available Agents
```bash
smol-kln --list

# Expected
# - All agents listed
# - Descriptions shown
# - Model info (if applicable)
```

### SMOL-002: Run Security Auditor
```bash
smol-kln security-auditor "audit authentication module"

# Expected
# - Agent runs
# - Output generated
# - Saved to file

# Verify
ls .claude/kln/agentExecute/*security-auditor*.md
```

### SMOL-003: Run with Specific Model
```bash
smol-kln code-reviewer "review main.py" --model qwen3-coder

# Expected
# - Specified model used
# - Agent completes
```

### SMOL-004: Run with Telemetry
```bash
smol-kln debugger "investigate crash" --telemetry

# Expected
# - Traces sent to Phoenix
# - Visible in dashboard
```

### SMOL-005: Agent Not Found
```bash
smol-kln nonexistent-agent "task"

# Expected
# - Clear error message
# - Suggests --list
```

### SMOL-006: Agent with Tools
```bash
# Run agent that uses read_file, grep

smol-kln code-reviewer "find security issues in src/"

# Expected
# - Tools executed
# - Files read
# - Results synthesized
```

### SMOL-007: Agent Timeout
```bash
smol-kln performance-engineer "analyze entire codebase" --timeout 30

# Expected
# - Graceful timeout
# - Partial results returned
```

### SMOL-008: Custom Agent Definition
```bash
# Prerequisites: Custom agent in ~/.klean/agents/

smol-kln custom-agent "task"

# Expected
# - Custom agent loaded
# - Runs with specified config
```

---

## 9. Multi-Agent System Tests

### MULTI-001: 3-Agent Default
```bash
k-lean multi "code review"

# Expected
# - Manager, file_scout, analyzer used
# - Coordinated output
# - Complete review
```

### MULTI-002: 4-Agent Thorough
```bash
k-lean multi --thorough "security audit"

# Expected
# - All 4 agents used
# - Security auditor included
# - Synthesized report
```

### MULTI-003: Agent Communication
```bash
# Steps
k-lean multi "review authentication" --verbose

# Expected
# - Agent handoffs visible
# - File scout finds files
# - Analyzer processes them
# - Manager coordinates
```

### MULTI-004: Agent Failure Recovery
```bash
# Prerequisites: One model unavailable

k-lean multi "review"

# Expected
# - Graceful degradation
# - Remaining agents complete
# - Warning about failed agent
```

### MULTI-005: Output Format - Text
```bash
k-lean multi --output text "review"

# Expected
# - Plain text output
# - Readable format
```

### MULTI-006: Output Format - JSON
```bash
k-lean multi --output json "review"

# Expected
# - Valid JSON output
# - Structured data

# Verify
k-lean multi --output json "review" | jq .
```

---

## 10. Integration Tests

### INT-001: Full Installation Flow
```bash
# Fresh system
pipx install k-lean
k-lean install
k-lean setup  # nanogpt
k-lean start
k-lean status
k-lean models
k-lean test

# Expected
# - All steps succeed
# - System fully functional
```

### INT-002: Claude Code Integration
```
# In Claude Code session
1. /kln:status
2. SaveThis "Test lesson"
3. FindKnowledge test
4. /kln:quick security

# Expected
# - All commands work
# - Knowledge persists
# - Reviews complete
```

### INT-003: Cross-Session Knowledge
```
# Session 1
SaveThis "Important pattern for auth"

# Session 2 (new session)
FindKnowledge auth

# Expected
# - Entry found in new session
# - Knowledge persists
```

### INT-004: Model Failover
```bash
# Prerequisites: Primary model down

k-lean models --health
k-lean multi "review"

# Expected
# - Unhealthy model skipped
# - Next available used
```

### INT-005: Concurrent Reviews
```bash
# Two terminals
# Terminal 1: k-lean multi "security"
# Terminal 2: k-lean multi "performance"

# Expected
# - Both complete
# - No interference
# - Separate outputs
```

### INT-006: Large Codebase
```bash
# Prerequisites: Project with 1000+ files

k-lean multi "architecture review"

# Expected
# - Handles scale
# - Reasonable time
# - Complete output
```

### INT-007: No LiteLLM Fallback
```bash
# Prerequisites: LiteLLM not running

/kln:status
k-lean models

# Expected
# - Clear error message
# - Suggests: k-lean start
```

### INT-008: Upgrade Path
```bash
# Prerequisites: Old version installed

pipx upgrade k-lean
k-lean install
k-lean doctor -f

# Expected
# - Smooth upgrade
# - Old configs preserved
# - New features available
```

### INT-009: Multiple Projects
```bash
# Project A
cd ~/project-a
SaveThis "Project A pattern"

# Project B
cd ~/project-b
SaveThis "Project B pattern"

# Expected
# - Separate knowledge DBs
# - No cross-contamination

# Verify
ls ~/project-a/.knowledge-db/
ls ~/project-b/.knowledge-db/
```

### INT-010: Telemetry End-to-End
```bash
k-lean start --telemetry
k-lean multi "review"

# Expected
# - Traces in Phoenix
# - Agent calls visible
# - Timing data captured

# Verify
# Check Phoenix UI at localhost:6006
```

---

## Test Execution Checklist

### Smoke Test (5 min)
- [ ] `k-lean --version`
- [ ] `k-lean status`
- [ ] `k-lean models`
- [ ] `k-lean test`

### Quick Validation (15 min)
- [ ] INST-001, INST-003
- [ ] SETUP-001 or SETUP-002
- [ ] SVC-001, SVC-009
- [ ] CLI-001 through CLI-005
- [ ] KB-001, KB-003

### Full Regression (2 hours)
- [ ] All Installation tests
- [ ] All Setup tests
- [ ] All Service tests
- [ ] All CLI tests
- [ ] All Slash Command tests
- [ ] All Hook tests
- [ ] All Knowledge DB tests
- [ ] All SmolKLN tests
- [ ] All Multi-Agent tests
- [ ] All Integration tests

---

## Known Issues / Edge Cases

1. **First-time txtai download**: Initial knowledge search is slow (~17s) while models download
2. **Port conflicts**: LiteLLM may fail if port 4000 in use
3. **Socket cleanup**: Stale sockets may need manual cleanup after crashes
4. **Unicode in paths**: Some scripts may fail with unicode in project paths
5. **WSL networking**: LiteLLM may need special config for WSL

---

## Automation Notes

### Automated (via `k-lean test`)
- CLI command parsing
- Config validation
- Model discovery
- Basic LLM client

### Manual Testing Required
- Claude Code slash commands
- Hook integration
- Interactive setup
- Phoenix telemetry UI

### CI/CD Integration
```yaml
# Example GitHub Actions
- name: Install K-LEAN
  run: pipx install k-lean

- name: Run Tests
  run: k-lean test

- name: Smoke Test
  run: |
    k-lean --version
    k-lean status
```

---

*Last updated: 2025-12-29*
