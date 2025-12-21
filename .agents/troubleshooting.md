# K-LEAN Troubleshooting

## Diagnostic Commands

| Command | Purpose |
|---------|---------|
| `k-lean doctor` | Full system diagnostics |
| `k-lean doctor -f` | Diagnose + auto-fix |
| `k-lean status` | Component status |
| `k-lean models --health` | Check model health |
| `healthcheck` | Quick model health (in Claude) |

## Common Issues

### LiteLLM Proxy Not Running

**Symptoms:**
- `ERROR: LiteLLM proxy not running on localhost:4000`
- Reviews fail immediately

**Diagnosis:**
```bash
curl -s http://localhost:4000/models
```

**Fixes:**
```bash
k-lean start                           # Start proxy
~/.claude/scripts/start-litellm.sh     # Direct script
lsof -i :4000                          # Check if port in use
```

### No Healthy Models

**Symptoms:**
- `ERROR: No healthy models available`
- Health check shows all models failing

**Diagnosis:**
```bash
~/.claude/scripts/health-check.sh       # Full health check
~/.claude/scripts/get-models.sh         # List available models
~/.claude/scripts/health-check-model.sh qwen3-coder  # Single model
```

**Fixes:**
```bash
# Check API key
cat ~/.config/litellm/.env

# Re-run setup wizard
k-lean setup

# Check NanoGPT subscription status
k-lean doctor
```

### Model Validation Errors

**Symptoms:**
- `ERROR: Invalid model 'xyz'`

**Diagnosis:**
```bash
~/.claude/scripts/validate-model.sh <model>
~/.claude/scripts/get-models.sh
```

**Fix:** Use exact model names from `get-models.sh` output.

### Knowledge Server Issues

**Symptoms:**
- Slow queries (~17s instead of ~30ms)
- `FindKnowledge` timeouts

**Diagnosis:**
```bash
# Check socket exists
ls -la /tmp/kb-*.sock

# Check server running (via kb-root.sh)
source ~/.claude/scripts/kb-root.sh
is_kb_server_running
```

**Fixes:**
```bash
k-lean start -s knowledge              # Start KB server
~/.claude/scripts/knowledge-server.py start  # Direct start

# Clean stale socket
rm /tmp/kb-*.sock
```

### Python Environment Issues

**Symptoms:**
- `ERROR: K-LEAN Python not executable`
- Knowledge DB operations fail

**Diagnosis:**
```bash
ls -la ~/.venvs/knowledge-db/bin/python
~/.venvs/knowledge-db/bin/python --version
```

**Fixes:**
```bash
k-lean install --component knowledge   # Reinstall KB component
python3 -m venv ~/.venvs/knowledge-db  # Create venv manually
~/.venvs/knowledge-db/bin/pip install txtai sentence-transformers
```

### Review Output Not Saved

**Symptoms:**
- Reviews complete but no file saved
- Can't find review history

**Diagnosis:**
```bash
# Check output directories exist
ls -la .claude/kln/

# Check session directory (fallback)
ls -la /tmp/claude-reviews/
```

**Fix:** Ensure you're in a git repository (required for `find_project_root`).

### Config Validation Errors

**Symptoms:**
- `os.environ` not substituting
- API key not found

**Diagnosis:**
```bash
k-lean doctor  # Checks for quoted os.environ
cat ~/.config/litellm/config.yaml | grep os.environ
```

**Fix:** Remove quotes from `os.environ/KEY`:
```yaml
# Wrong
api_key: "os.environ/NANOGPT_API_KEY"

# Correct
api_key: os.environ/NANOGPT_API_KEY
```

## Log Locations

| Log | Path |
|-----|------|
| LiteLLM | `~/.klean/logs/litellm.log` |
| KB Server | `~/.klean/logs/kb-server.log` |
| Debug | `~/.klean/logs/debug.jsonl` |
| Timeline | `.knowledge-db/timeline.txt` (per-project) |

## Quick Recovery

```bash
# Full restart
k-lean stop
k-lean start -s all

# Reset knowledge DB (per-project)
rm -rf .knowledge-db/
# Will auto-recreate on next SaveThis

# Reinstall components
k-lean uninstall
pipx install k-lean
k-lean install
```

---
*Back to [AGENTS.md](../AGENTS.md)*
