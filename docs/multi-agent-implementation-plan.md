# Multi-Agent Architecture (SmolKLN)

**Status: IMPLEMENTED** (2024-12-23)

## Overview

K-LEAN SmolKLN supports multi-agent orchestration via the `k-lean multi` command. A manager agent coordinates specialist agents using smolagents `managed_agents` feature.

## Architecture Variants

### 3-Agent Architecture (Default)

```
┌─────────────────────────────────────────────────────┐
│ Manager (glm-4.6-thinking)                          │
│ Orchestration only - delegates all work             │
└──────────────────┬──────────────────────────────────┘
                   │
         ┌─────────┴─────────┐
         ▼                   ▼
   ┌───────────┐       ┌───────────┐
   │file_scout │       │ analyzer  │
   │qwen3-coder│       │deepseek-  │
   │           │       │v3-thinking│
   │Tools:     │       │Tools:     │
   │- read_file│       │- read_file│
   │- search   │       │- grep     │
   │- grep     │       │           │
   │- knowledge│       │           │
   └───────────┘       └───────────┘
```

| Agent | Model | Tools | Role |
|-------|-------|-------|------|
| **manager** | `glm-4.6-thinking` | None (delegates only) | Orchestration |
| **file_scout** | `qwen3-coder` | read_file, search_files, grep, knowledge_search | Fast file discovery |
| **analyzer** | `deepseek-v3-thinking` | read_file, grep | Deep code analysis |

### 4-Agent Architecture (--thorough)

```
┌─────────────────────────────────────────────────────┐
│ Manager (glm-4.6-thinking)                          │
│ Orchestration only - delegates all work             │
└──────────────────┬──────────────────────────────────┘
                   │
     ┌─────────────┼─────────────┬─────────────┐
     ▼             ▼             ▼             ▼
┌─────────┐  ┌──────────┐  ┌──────────┐  ┌───────────┐
│file_    │  │code_     │  │security_ │  │synthesizer│
│scout    │  │analyzer  │  │auditor   │  │           │
│qwen3-   │  │deepseek- │  │deepseek- │  │qwen3-     │
│coder    │  │v3-think  │  │v3-think  │  │coder      │
│         │  │          │  │          │  │           │
│Tools:   │  │Tools:    │  │Tools:    │  │Tools:     │
│- read   │  │- read    │  │- read    │  │- read     │
│- search │  │- grep    │  │- grep    │  │           │
│- grep   │  │          │  │- web     │  │           │
│- KB     │  │          │  │          │  │           │
└─────────┘  └──────────┘  └──────────┘  └───────────┘
```

| Agent | Model | Tools | Role |
|-------|-------|-------|------|
| **manager** | `glm-4.6-thinking` | None | Orchestration |
| **file_scout** | `qwen3-coder` | read_file, search_files, grep, knowledge_search | File discovery |
| **code_analyzer** | `deepseek-v3-thinking` | read_file, grep | Bug detection, code quality |
| **security_auditor** | `deepseek-v3-thinking` | read_file, grep, web_search | Security analysis |
| **synthesizer** | `qwen3-coder` | read_file | Report formatting |

---

## Usage

```bash
# 3-agent (default) - fast
k-lean multi "Review src/klean/smol/cli.py for bugs"

# 4-agent (thorough) - comprehensive
k-lean multi --thorough "Security audit of the auth module"

# With telemetry (Phoenix at localhost:6006)
k-lean multi --thorough "Review recent changes" --telemetry

# Override manager model
k-lean multi --manager-model kimi-k2-thinking "Review cli.py"

# JSON output
k-lean multi --output json "Check for security issues"
```

### CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `--thorough`, `-t` | False | Use 4-agent architecture |
| `--manager-model`, `-m` | glm-4.6-thinking | Override manager model |
| `--output`, `-o` | text | Output format: text, json |
| `--telemetry` | False | Enable Phoenix tracing |

---

## Implementation Files

```
src/klean/smol/
├── multi_config.py     # Agent configurations (MODELS, get_3_agent_config, get_4_agent_config)
├── multi_agent.py      # MultiAgentExecutor class
└── tools.py            # get_tools_for_agent() - project-aware tools

src/klean/data/multi-agents/
├── manager.md          # Manager orchestration prompt
├── file_scout.md       # File discovery prompt
├── analyzer.md         # 3-agent deep analysis prompt
├── code_analyzer.md    # 4-agent code quality prompt
├── security_auditor.md # 4-agent security prompt
└── synthesizer.md      # 4-agent report formatting prompt

src/klean/cli.py        # 'multi' command at line 2522
```

---

## Model Configuration

From `src/klean/smol/multi_config.py`:

```python
MODELS = {
    "manager": "glm-4.6-thinking",      # 90.6% tool-calling success
    "file-scout": "qwen3-coder",         # Fastest for file navigation
    "analyzer": "deepseek-v3-thinking",  # Best for code analysis
    "code-analyzer": "deepseek-v3-thinking",  # Bug detection
    "security-auditor": "deepseek-v3-thinking",  # Security analysis
    "synthesizer": "qwen3-coder",        # Reliable report output
}
```

**Model Selection Rationale:**
- **GLM-4.6-thinking**: 90.6% tool-calling success rate (best for orchestration)
- **Qwen3-coder**: Fastest response times (file operations, formatting)
- **DeepSeek-v3-thinking**: Best reasoning quality (code analysis, security)

---

## Output

Reports are saved to:
```
.claude/kln/multiAgent/YYYY-MM-DD_HH-MM-SS_multi-[3|4]-agent_<task-slug>.md
```

---

## Telemetry

With `--telemetry` flag, all agent execution is traced via Phoenix:

1. Start Phoenix: `k-lean start --telemetry` or it auto-starts
2. Run with tracing: `k-lean multi "task" --telemetry`
3. View traces at: `http://localhost:6006`

Shows:
- Agent execution tree
- LLM calls with prompts/responses
- Tool invocations
- Timing breakdown
- Multi-agent coordination flow

---

## Performance

| Variant | Typical Time | API Calls |
|---------|--------------|-----------|
| 3-agent | 30-90s | 3-10 |
| 4-agent | 60-180s | 5-15 |

---

## Technical Details

### Agent Creation (multi_agent.py)

```python
class MultiAgentExecutor:
    def execute(self, task: str, thorough: bool = False, ...):
        config = get_4_agent_config() if thorough else get_3_agent_config()

        # Create specialist agents
        specialists = []
        for name, agent_config in config.items():
            if name == "manager":
                continue
            agent = CodeAgent(
                model=create_model(agent_config.model, self.api_base),
                tools=get_tools_for_agent(agent_config.tools, self.project_root),
                name=agent_config.name,
                description=agent_config.description,
                max_steps=agent_config.max_steps,
            )
            specialists.append(agent)

        # Manager with managed_agents
        manager = CodeAgent(
            model=create_model(manager_config.model, self.api_base),
            tools=[],
            managed_agents=specialists,
            max_steps=manager_config.max_steps,
        )

        result = manager.run(full_prompt)
```

### Project-Aware Tools (tools.py)

Tools resolve paths relative to project root:

```python
def get_tools_for_agent(tool_names: List[str], project_path: str = None) -> list:
    def make_read_file(root: str):
        @tool
        def project_read_file(file_path: str) -> str:
            path = Path(file_path)
            if not path.is_absolute():
                path = Path(root) / path  # Resolve to project root
            return path.read_text()
        return project_read_file
```

---

## Comparison: Single vs Multi-Agent

| Aspect | Single Agent (`k-lean agent`) | Multi-Agent (`k-lean multi`) |
|--------|-------------------------------|------------------------------|
| Speed | Faster (~30s) | Slower (~60-180s) |
| Depth | Good | Better (specialized focus) |
| Cost | Lower | Higher (more API calls) |
| Coverage | Single perspective | Multiple perspectives |
| Use case | Quick reviews | Thorough audits |
