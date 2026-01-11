<p align="center">
  <img src="assets/logo-banner.png" alt="K-LEAN" width="500">
</p>

<p align="center">
  <strong>Second opinions from multiple LLMs—right inside Claude Code</strong>
</p>

<p align="center">
  <a href="https://github.com/calinfaja/K-LEAN/actions"><img src="https://github.com/calinfaja/K-LEAN/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://pypi.org/project/kln-ai/"><img src="https://img.shields.io/pypi/v/kln-ai.svg" alt="PyPI"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-Apache%202.0-green.svg" alt="License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/python-3.9+-yellow.svg" alt="Python"></a>
</p>

<p align="center">
  <a href="#quick-start"><img src="https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-blue.svg" alt="Platform"></a>
</p>

---

## Why K-LEAN?

Need a second opinion on your code? Want validation before merging? Looking for domain expertise your model doesn't have? Stuck in a loop and need fresh eyes to break out?

One model's confidence isn't proof. K-LEAN brings in **OpenAI, Gemini, DeepSeek, Moonshot, Minimax**, and more—when multiple models agree, you ship with confidence.

- **9 slash commands** — `/kln:quick`, `/kln:multi`, `/kln:agent`, `/kln:rethink`...
- **8 specialist agents** — Security, Rust, embedded C, ARM Cortex, performance
- **4 smart hooks** — Service auto-start, keyword handling, git tracking, web capture
- **Persistent knowledge** — Insights that survive across sessions

Access any model via **NanoGPT** or **OpenRouter**, directly from Claude Code.

**Works on Windows, Linux, and macOS** — native cross-platform support, no shell scripts required.

---

## Quick Start

### 1. Get an API Key (required)

Choose one provider and get your API key:
- **[NanoGPT](https://nano-gpt.com)** — Subscription access to DeepSeek, Qwen, GLM, Kimi
- **[OpenRouter](https://openrouter.ai)** — Unified access to GPT, Gemini, Claude

### 2. Install

**Linux / macOS:**
```bash
# Install pipx if you don't have it
python3 -m pip install --user pipx
python3 -m pipx ensurepath

# Install K-LEAN
pipx install kln-ai
```

**Windows (PowerShell):**
```powershell
# Install pipx if you don't have it
python -m pip install --user pipx
python -m pipx ensurepath

# Restart PowerShell, then install K-LEAN
pipx install kln-ai
```

### 3. Setup

```bash
kln init                  # Select provider, enter API key
kln start                 # Start LiteLLM proxy
kln status                # Verify everything works
```

Or non-interactive:
```bash
kln init --provider nanogpt --api-key $NANOGPT_API_KEY
kln start
```

### 4. Use in Claude Code

```bash
/kln:quick "security"          # Fast review (~30s)
/kln:multi "error handling"    # 3-5 model consensus (~60s)
/kln:agent security-auditor    # Specialist agent (~2min)
```

### Optional: Add More Models

```bash
kln model add --provider openrouter "anthropic/claude-3.5-sonnet"
kln model remove "claude-3-sonnet"
kln start  # Restart to apply changes
```

---

## See It In Action

```
$ /kln:multi "review authentication flow"

GRADE: B+ | RISK: MEDIUM

HIGH CONFIDENCE (4/5 models agree):
  - auth.py:42 - SQL injection risk in user query
  - session.py:89 - Missing token expiration check

MEDIUM CONFIDENCE (2/5 models agree):
  - login.py:15 - Consider rate limiting
```

---

## What You Get

### 1. Second Opinions on Demand

Three ways to get external perspectives—pick based on speed vs depth:

| Command | What Happens | Time |
|---------|--------------|------|
| `/kln:quick` | 1 model reviews code you provide | ~30s |
| `/kln:multi` | 3-5 models vote on same code | ~60s |
| `/kln:rethink` | Contrarian techniques when you're stuck | ~20s |

**`/kln:quick`** — You gather the code (git diff, file content), one model reviews it fast.
```
/kln:quick "security review"
# Grade: B+ | Risk: MEDIUM | 3 findings
```

**`/kln:multi`** — Same code goes to 5 models in parallel. When 4/5 agree, it's real.
```
/kln:multi "check error handling"
# 4/5 AGREE: Missing null check at line 42
```

**`/kln:rethink`** — Stuck debugging 10+ minutes? Get contrarian ideas: inversion, assumption challenge, domain shift.
```
/kln:rethink
# "What if the bug isn't in the parser—what if the input is already corrupt?"
```

**How:** LiteLLM proxy routes to multiple providers (NanoGPT, OpenRouter). Dynamic model discovery, parallel async execution, response aggregation with consensus scoring.

---

### 2. Knowledge That Sticks

Your insights survive sessions. Capture mid-session or end-of-session:

**`/kln:learn`** — Extract learnings NOW, while context is fresh.
```
/kln:learn "JWT issue"
# Found 3 learnings → Saved to Knowledge DB
```

**`/kln:remember`** — End of session. Reviews git diff, extracts warnings/patterns/solutions, syncs to Serena MCP.
```
/kln:remember
# Saved 5 entries (2 warnings, 2 patterns, 1 solution)
# Synced to Serena lessons-learned
```

**`FindKnowledge`** — Search anytime. Just type the keyword.
```
FindKnowledge "JWT validation"
# Found: [2024-12-15] JWT refresh token race condition fix
```

**How:** Per-project knowledge database with hybrid search—dense embeddings (BGE-small via [fastembed](https://github.com/qdrant/fastembed)) + sparse matching (BM25) + RRF fusion + cross-encoder reranking. Runs locally via ONNX, <100ms queries.

> **No API key?** Knowledge DB works fully offline. You can still use `/kln:learn`, `/kln:remember`, and `FindKnowledge` without NanoGPT or OpenRouter—embeddings run locally on your machine.

---

### 3. Agents That Explore

Unlike models that review what you give them, **agents read your codebase themselves**.

8 specialists with tools: `read_file`, `grep`, `search_files`, `knowledge_search`, `get_complexity`.

| Agent | Expertise |
|-------|-----------|
| `code-reviewer` | OWASP Top 10, SOLID, code quality |
| `security-auditor` | Vulnerabilities, auth, crypto |
| `debugger` | Root cause analysis |
| `performance-engineer` | Profiling, optimization |
| `rust-expert` | Ownership, lifetimes, unsafe |
| `c-pro` | C99/C11, POSIX, memory |
| `arm-cortex-expert` | Embedded ARM, real-time |
| `orchestrator` | Multi-agent coordination |

```
/kln:agent security-auditor "audit payment module"
# Agent greps for payment → reads 3 files → finds 2 vulnerabilities

/kln:agent rust-expert --model qwen3-coder "review unsafe blocks"
# Want a specific LLM? Use --model to pick your expert
```

**`--parallel`** — Need multiple perspectives? Run 3 specialists at once:
```
/kln:agent --parallel "review auth system"
# code-reviewer + security-auditor + performance-engineer → unified report
```

**How:** Built on [smolagents](https://github.com/huggingface/smolagents) with LiteLLM integration. Multi-step reasoning, tool use, and memory persistence.

---

### 4. Hooks That Work in Background

4 hooks run automatically—you don't call them:

| Hook | Trigger | What It Does |
|------|---------|--------------|
| `session-start` | Claude Code opens | Starts LiteLLM + Knowledge Server |
| `user-prompt` | You type keywords | `FindKnowledge`, `SaveInfo`, `asyncConsensus` |
| `post-bash` | After git commits | Logs to timeline, extracts facts |
| `post-web` | After WebFetch | Evaluates URLs, saves if relevant |

**Keywords you can type directly** (no slash):
```
FindKnowledge "rate limiting"     # Search KB
SaveInfo https://docs.example.com # Evaluate + save if useful
asyncConsensus security           # Background 3-model review
```

**How:** Claude Code hook system with pattern matching. Services auto-start on session begin. Git commits logged to timeline. Web content evaluated and captured if relevant.

---

### 5. Status Line
```
[opus 4.5] │ claudeAgentic │ git:(main●) +27-23 │ llm:16 kb:[OK]
```
Model. Project. Branch (● = dirty). Lines changed. Models ready. KB health.

**How:** Custom statusline polling LiteLLM and Knowledge DB on each prompt.

---

## All Commands

| Command | Description | Time |
|---------|-------------|------|
| `/kln:quick <focus>` | Single model review | ~30s |
| `/kln:multi <focus>` | 3-5 model consensus | ~60s |
| `/kln:agent <role>` | Specialist agent with tools | ~2min |
| `/kln:rethink` | Contrarian debugging | ~20s |
| `/kln:learn` | Capture insights from context | ~10s |
| `/kln:remember` | End-of-session knowledge capture | ~20s |
| `/kln:doc <title>` | Generate session docs | ~30s |
| `/kln:status` | System health check | ~2s |
| `/kln:help` | Command reference | instant |

**Flags:** `--async` (background), `--models N` (count), `--output json|text`

---

## CLI Reference

```bash
# Setup (unified)
kln init             # Initialize: install + configure provider (NanoGPT, OpenRouter, skip)

# Installation & Management
kln install          # Install to ~/.claude/
kln uninstall        # Remove components
kln status           # Show component status

# Services
kln start            # Start LiteLLM proxy
kln stop             # Stop all services

# Diagnostics
kln doctor           # Check configuration
kln doctor -f        # Auto-fix issues

# Model Management (subgroup)
kln model list       # List available models
kln model list --health  # Check model health
kln model add        # Add individual model
kln model remove     # Remove model
kln model test       # Test a specific model

# Provider Management (subgroup)
kln provider list    # Show configured providers
kln provider add     # Add provider with recommended models
kln provider set-key # Update API key
kln provider remove  # Remove provider

# Review
kln multi            # Run multi-agent orchestrated review
```

---

## Requirements

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.9+ | `python3 --version` |
| Claude Code | 2.0+ | `claude --version` |
| pipx | any | `pipx --version` |
| API Key | - | NanoGPT or OpenRouter |

---

## Recommended Providers

K-LEAN comes with **curated model sets** for each provider—no manual configuration needed.

### NanoGPT

[NanoGPT](https://nano-gpt.com) — Subscription access to top-tier models.

**10 models pre-configured:**
| Model | Provider | Specialty |
|-------|----------|-----------|
| `deepseek-r1` | DeepSeek | Reasoning, code review |
| `deepseek-v3.2` | DeepSeek | Fast general purpose |
| `qwen3-coder` | Alibaba | Code-focused |
| `glm-4.7` | Zhipu | Multilingual |
| `kimi-k2` | Moonshot | Long context |
| `llama-4-maverick` | Meta | Creative |
| `llama-4-scout` | Meta | Analytical |
| `mimo-v2-flash` | Xiaomi | Fast inference |
| `gpt-oss-120b` | OpenAI-OSS | Large capacity |
| `devstral-2-123b` | Mistral | Code generation |

**+4 thinking models** (auto-configured): `deepseek-v3.2-thinking`, `glm-4.7-thinking`, `kimi-k2-thinking`, `deepseek-r1-thinking`

### OpenRouter

[OpenRouter](https://openrouter.ai) — Unified API for multiple providers.

**6 models pre-configured:**
| Model | Provider | Specialty |
|-------|----------|-----------|
| `gemini-3-flash` | Google | Fast, multimodal |
| `gemini-2.5-flash` | Google | Balanced |
| `gpt-5-mini` | OpenAI | Efficient |
| `gpt-5.1-codex-mini` | OpenAI | Code-focused |
| `qwen3-coder-plus` | Alibaba | Enhanced coding |
| `deepseek-v3.2-speciale` | DeepSeek | Specialized |

---

## Recommended Add-ons

For a complete coding experience:

| Tool | Integration |
|------|-------------|
| [SuperClaude](https://github.com/SuperClaude-Org/SuperClaude) | Use `/sc:*` and `/kln:*` together |
| [Serena MCP](https://github.com/oraios/serena) | Shared memory, code understanding |
| [Context7 MCP](https://github.com/upstash/context7) | Documentation lookup |
| [Tavily MCP](https://github.com/tavily-ai/tavily-mcp) | Web search for research |
| [Sequential Thinking MCP](https://github.com/modelcontextprotocol/servers/tree/main/src/sequentialthinking) | Step-by-step reasoning for complex problems |

**Telemetry:** Install [Phoenix](https://github.com/Arize-ai/phoenix) to watch agent steps and reviews at `localhost:6006`.

---

## Documentation

| Document | Description |
|----------|-------------|
| [Installation](docs/installation.md) | Detailed setup guide |
| [Usage](docs/usage.md) | Commands, workflows, examples |
| [Reference](docs/reference.md) | Complete config reference |
| [Architecture](docs/architecture/OVERVIEW.md) | System design |

---

## Contributing

```bash
git clone https://github.com/calinfaja/K-LEAN.git
cd k-lean
pipx install -e .
kln install --dev
kln admin test
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## License

Apache 2.0 — See [LICENSE](LICENSE)

---

<p align="center">
  <b>Get second opinions. Ship with confidence.</b>
</p>
