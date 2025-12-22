# SmolKLN - Smolagents Integration for K-LEAN

## Overview

Create a **new, independent agent system** using Smolagents, completely separate from Factory droids.

**Goal**: K-LEAN agents work without Factory CLI, using only LiteLLM + NanoGPT.

**Strategy**:
1. Build SmolKLN as independent system (copies files, doesn't reference)
2. Run both systems in parallel during testing
3. Delete entire droid system when ready (no broken references)

---

## Key Smolagents Capabilities to Leverage

| Feature | What It Does | K-LEAN Integration |
|---------|--------------|-------------------|
| **Multi-Agent** | Manager orchestrates specialized sub-agents | Orchestrator droid manages specialized droids |
| **Agentic RAG** | Agent with retrieval tool for iterative search | Knowledge DB as custom retriever tool |
| **Memory System** | Step-by-step history, replay, dynamic modification | Serena memories integration |
| **Custom Tools** | `@tool` decorator for functions, `Tool` class | File tools, KB search, web search |
| **LiteLLMModel** | Native LiteLLM support for 100+ providers | localhost:4000 proxy to NanoGPT |
| **CodeAgent** | Python code generation for complex tasks | Default agent type for droids |

---

## Current State vs New Architecture

```
CURRENT (Factory Droids)              NEW (SmolKLN - Independent)
========================              ==========================
~/.factory/droids/*.md       COPY→    ~/.klean/agents/*.md
src/klean/droids/                     src/klean/smol/
droid-execute.sh → Factory CLI        smol-kln.py → Smolagents
FACTORY_API_KEY required              LiteLLM only (no API key)
```

| Component | Old Location | New Location (COPY) | Status |
|-----------|--------------|---------------------|--------|
| Agent prompts | `src/klean/data/droids/*.md` | `src/klean/data/agents/*.md` | 📋 Copy |
| Python executor | `droid-execute.sh` | `src/klean/smol/` | 🆕 New |
| Install path | `~/.factory/droids/` | `~/.klean/agents/` | 🆕 New |
| Base classes | `src/klean/droids/base.py` | `src/klean/smol/` | 🆕 New |

**Key Principle**: SmolKLN is 100% independent. When droids are deleted, SmolKLN continues working.

---

## Target Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Claude Code                                 │
│                          │                                       │
│              /kln:agent security "audit auth"                   │
│                          │                                       │
│                          ▼                                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                   SmolKLN Executor                         │  │
│  │                                                            │  │
│  │  1. Load ~/.klean/agents/security-auditor.md              │  │
│  │  2. Parse YAML frontmatter (model, tools, description)    │  │
│  │  3. Extract system prompt (markdown content)              │  │
│  │  4. Query knowledge DB for context (Agentic RAG)          │  │
│  │  5. Create Smolagents CodeAgent with:                     │  │
│  │     - LiteLLMModel → localhost:4000                       │  │
│  │     - System prompt from agent.md                         │  │
│  │     - Tools: knowledge_search, read_file, search_files    │  │
│  │  6. Execute and return results                            │  │
│  └───────────────────────────────────────────────────────────┘  │
│                          │                                       │
│                          ▼                                       │
│                 LiteLLM (localhost:4000)                        │
│                          │                                       │
│                          ▼                                       │
│                 NanoGPT / OpenRouter                            │
└─────────────────────────────────────────────────────────────────┘

INDEPENDENCE GUARANTEE:
  src/klean/smol/       ← No imports from src/klean/droids/
  src/klean/data/agents/ ← Copied files, not symlinks
  ~/.klean/agents/       ← Separate from ~/.factory/droids/
```

---

## Smolagents Architecture for K-LEAN

### Multi-Agent System (Orchestrator Pattern)

The orchestrator droid becomes a **manager agent** that can delegate to specialized droids:

```python
from smolagents import CodeAgent, LiteLLMModel

# Specialized droids as sub-agents
security_droid = CodeAgent(
    tools=[knowledge_retriever, file_reader],
    model=LiteLLMModel(model_id="openai/glm-4.6-thinking", api_base="http://localhost:4000"),
    name="security-auditor",
    description="Security vulnerability analysis specialist"
)

code_reviewer_droid = CodeAgent(
    tools=[knowledge_retriever, file_reader],
    model=LiteLLMModel(model_id="openai/qwen3-coder", api_base="http://localhost:4000"),
    name="code-reviewer",
    description="Code quality and best practices expert"
)

# Manager (orchestrator) that delegates
orchestrator = CodeAgent(
    tools=[],  # Manager doesn't need tools
    model=LiteLLMModel(model_id="openai/deepseek-v3-thinking", api_base="http://localhost:4000"),
    managed_agents=[security_droid, code_reviewer_droid],
    name="orchestrator"
)

# Manager decides which specialist to use
result = orchestrator.run("Review the authentication module for security and code quality")
```

### Agentic RAG with Knowledge DB

The Knowledge DB becomes a **retriever tool** that droids can query iteratively:

```python
from smolagents import Tool

class KnowledgeRetrieverTool(Tool):
    """Retriever tool for K-LEAN knowledge database."""

    name = "knowledge_search"
    description = "Search the project's knowledge database for relevant prior solutions, lessons learned, and documentation."
    inputs = {
        "query": {
            "type": "string",
            "description": "The search query. Use affirmative statements rather than questions for better retrieval."
        }
    }
    output_type = "string"

    def __init__(self, project_path: str = None):
        super().__init__()
        from knowledge_db import KnowledgeDB
        self.db = KnowledgeDB(project_path)

    def forward(self, query: str) -> str:
        """Execute knowledge search."""
        results = self.db.search(query, limit=5)

        if not results:
            return "No relevant prior knowledge found."

        output = "RELEVANT PRIOR KNOWLEDGE:\n\n"
        for r in results:
            score = r.get("score", 0)
            if score < 0.3:
                continue
            output += f"### {r.get('title', 'Untitled')} (relevance: {score:.0%})\n"
            if r.get("summary"):
                output += f"{r['summary']}\n"
            if r.get("what_worked"):
                output += f"Solution: {r['what_worked']}\n"
            output += "\n"

        return output

# Usage in agent
knowledge_retriever = KnowledgeRetrieverTool()
agent = CodeAgent(
    tools=[knowledge_retriever],
    model=model,
)
```

### Serena Memories Integration

Read Serena memories as additional context:

```python
from smolagents import tool

@tool
def read_serena_memory(memory_name: str) -> str:
    """
    Read a Serena memory file for context.

    Args:
        memory_name: Name of the memory (e.g., "lessons-learned", "architecture-review-system")

    Returns:
        Content of the memory file.
    """
    import subprocess
    result = subprocess.run(
        ["claude", "--print", f"mcp__serena__read_memory('{memory_name}')"],
        capture_output=True, text=True
    )
    return result.stdout if result.returncode == 0 else f"Memory not found: {memory_name}"
```

### Smolagents Tools for K-LEAN

| Tool | Type | Description |
|------|------|-------------|
| `knowledge_search` | Custom Tool class | Query Knowledge DB with semantic search |
| `read_serena_memory` | @tool decorator | Read Serena curated memories |
| `DuckDuckGoSearchTool` | Built-in | Web search (replaces WebSearchTool) |
| `VisitWebpageTool` | Built-in | Fetch and parse web pages |
| `PythonInterpreterTool` | Built-in | Execute Python code safely |
| File access | `add_base_tools=True` | Read files from codebase |

**Minimal vs Full Tool Access:**

```python
# Minimal (read-only analysis)
agent = CodeAgent(tools=[knowledge_retriever], model=model)

# Full tool access (with web search)
from smolagents import DuckDuckGoSearchTool, VisitWebpageTool
agent = CodeAgent(
    tools=[knowledge_retriever, DuckDuckGoSearchTool(), VisitWebpageTool()],
    model=model,
    add_base_tools=True,  # Adds file reading
)
```

### Memory System

Smolagents provides memory inspection and modification:

```python
# After agent runs
for step in agent.memory.steps:
    if isinstance(step, ActionStep):
        print(f"Step {step.step_number}: {step.observations}")

# Replay last execution
agent.replay()

# Step-by-step execution with intervention
final_answer = None
while final_answer is None:
    memory_step = ActionStep(step_number=step_number)
    final_answer = agent.step(memory_step)
    agent.memory.steps.append(memory_step)
    # Can modify memory here before next step
```

---

## Implementation Phases

### Phase 1: SmolKLN Core Package

**Files to create:**

```
src/klean/
├── smol/                          # NEW independent package
│   ├── __init__.py                # Package exports
│   ├── executor.py                # SmolKLN executor
│   ├── loader.py                  # Agent .md file parser
│   ├── models.py                  # LiteLLM model wrapper
│   └── tools.py                   # Knowledge retriever + file tools
├── data/
│   ├── agents/                    # COPIED agent definitions (not symlinks!)
│   │   ├── security-auditor.md
│   │   ├── code-reviewer.md
│   │   ├── debugger.md
│   │   ├── orchestrator.md
│   │   ├── performance-engineer.md
│   │   ├── arm-cortex-expert.md
│   │   ├── c-pro.md
│   │   └── rust-expert.md
│   └── scripts/
│       └── smol-kln.py            # CLI entry point
```

**Note**: Agent .md files are **copied** from `src/klean/data/droids/`, not symlinked. This ensures SmolKLN works even after droids are deleted.

#### 1.1 Agent Loader (`src/klean/smol/loader.py`)

```python
"""Load and parse SmolKLN agent .md files.

This module is INDEPENDENT - no imports from src/klean/droids/.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
import yaml
import re


@dataclass
class AgentConfig:
    """Parsed agent configuration from YAML frontmatter."""
    name: str
    description: str
    model: str = "qwen3-coder"
    tools: List[str] = field(default_factory=lambda: ["knowledge_search", "read_file", "search_files"])

    def __post_init__(self):
        if self.tools is None:
            self.tools = ["knowledge_search", "read_file", "search_files"]


@dataclass
class Agent:
    """Complete agent with config and system prompt."""
    config: AgentConfig
    system_prompt: str
    source_path: Path


def parse_agent_file(path: Path) -> Agent:
    """Parse an agent .md file into config and system prompt.

    File format:
    ---
    name: security-auditor
    description: Security audit specialist
    model: glm-4.6-thinking
    tools: ["knowledge_search", "read_file"]
    ---

    # System Prompt Content
    You are a security auditor...
    """
    content = path.read_text()

    # Split on YAML frontmatter delimiters
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)

    if match:
        yaml_content = match.group(1)
        markdown_content = match.group(2).strip()
        config_dict = yaml.safe_load(yaml_content)
    else:
        # No frontmatter, use defaults
        config_dict = {"name": path.stem, "description": ""}
        markdown_content = content

    config = AgentConfig(
        name=config_dict.get("name", path.stem),
        description=config_dict.get("description", ""),
        model=config_dict.get("model", "qwen3-coder"),
        tools=config_dict.get("tools"),
    )

    # Handle "inherit" model - default to qwen3-coder
    if config.model == "inherit":
        config.model = "qwen3-coder"

    return Agent(
        config=config,
        system_prompt=markdown_content,
        source_path=path,
    )


def list_available_agents(agents_dir: Path = None) -> List[str]:
    """List all available agent names."""
    if agents_dir is None:
        agents_dir = Path.home() / ".klean" / "agents"

    if not agents_dir.exists():
        return []

    return [p.stem for p in agents_dir.glob("*.md")]


def load_agent(name: str, agents_dir: Path = None) -> Agent:
    """Load an agent by name."""
    if agents_dir is None:
        agents_dir = Path.home() / ".klean" / "agents"

    path = agents_dir / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Agent not found: {name}")

    return parse_agent_file(path)
```

#### 1.2 Model Wrapper (`src/klean/smol/models.py`)

```python
"""LiteLLM model wrapper for Smolagents."""

from smolagents import LiteLLMModel
from typing import Optional
import os


# Model name mappings (short name -> LiteLLM model ID)
MODEL_ALIASES = {
    "qwen": "qwen3-coder",
    "deepseek": "deepseek-v3-thinking",
    "glm": "glm-4.6-thinking",
    "kimi": "kimi-k2-thinking",
    "minimax": "minimax-m2",
    "hermes": "hermes-4-70b",
}

# Role -> Best model mapping
ROLE_MODELS = {
    "security-auditor": "glm-4.6-thinking",
    "debugger": "qwen3-coder",
    "code-reviewer": "qwen3-coder",
    "orchestrator": "deepseek-v3-thinking",
    "architect": "deepseek-v3-thinking",
    "performance-engineer": "deepseek-v3-thinking",
    "arm-cortex-expert": "qwen3-coder",
    "c-pro": "qwen3-coder",
    "rust-expert": "qwen3-coder",
}


def resolve_model_name(model: str) -> str:
    """Resolve model alias to full LiteLLM model ID."""
    return MODEL_ALIASES.get(model, model)


def get_model_for_role(role: str) -> str:
    """Get the best model for a given droid role."""
    return ROLE_MODELS.get(role, "qwen3-coder")


def create_model(
    model_id: str,
    api_base: str = "http://localhost:4000",
    temperature: float = 0.7,
) -> LiteLLMModel:
    """Create a LiteLLM model for Smolagents.

    Args:
        model_id: Model name (e.g., "qwen3-coder" or "glm")
        api_base: LiteLLM proxy URL
        temperature: Sampling temperature

    Returns:
        Configured LiteLLMModel instance
    """
    resolved_model = resolve_model_name(model_id)

    return LiteLLMModel(
        model_id=f"openai/{resolved_model}",
        api_base=api_base,
        api_key="not-needed",  # LiteLLM proxy handles auth
        temperature=temperature,
    )
```

#### 1.3 Tools (`src/klean/smol/tools.py`)

```python
"""Custom tools for K-LEAN SmolDroids."""

from smolagents import Tool, tool
from pathlib import Path
from typing import Optional
import sys


class KnowledgeRetrieverTool(Tool):
    """Retriever tool for K-LEAN knowledge database (Agentic RAG)."""

    name = "knowledge_search"
    description = (
        "Search the project's knowledge database for relevant prior solutions, "
        "lessons learned, patterns, and documentation. Use affirmative statements "
        "for better retrieval (e.g., 'BLE power optimization techniques' not "
        "'how to optimize BLE power?')."
    )
    inputs = {
        "query": {
            "type": "string",
            "description": "Search query - use affirmative statements for best results"
        }
    }
    output_type = "string"

    def __init__(self, project_path: str = None):
        super().__init__()
        self.project_path = project_path
        self._db = None

    @property
    def db(self):
        """Lazy-load knowledge DB."""
        if self._db is None:
            # Add scripts dir to path
            scripts_dir = Path(__file__).parent.parent / "data" / "scripts"
            sys.path.insert(0, str(scripts_dir))
            from knowledge_db import KnowledgeDB
            self._db = KnowledgeDB(self.project_path)
        return self._db

    def forward(self, query: str) -> str:
        """Execute knowledge search."""
        try:
            results = self.db.search(query, limit=5)
        except Exception as e:
            return f"Knowledge DB unavailable: {e}"

        if not results:
            return "No relevant prior knowledge found for this query."

        output = "RELEVANT PRIOR KNOWLEDGE:\n\n"
        for r in results:
            score = r.get("score", 0)
            if score < 0.3:
                continue
            output += f"### {r.get('title', 'Untitled')} (relevance: {score:.0%})\n"
            if r.get("url"):
                output += f"Source: {r['url']}\n"
            if r.get("summary"):
                output += f"{r['summary']}\n"
            if r.get("problem_solved"):
                output += f"Problem: {r['problem_solved']}\n"
            if r.get("what_worked"):
                output += f"Solution: {r['what_worked']}\n"
            output += "\n"

        return output if len(output) > 50 else "No highly relevant prior knowledge found."


@tool
def read_file(file_path: str) -> str:
    """
    Read contents of a file from the project.

    Args:
        file_path: Path to the file (relative to project root or absolute)

    Returns:
        File contents as string, or error message if file not found.
    """
    path = Path(file_path)
    if not path.exists():
        return f"File not found: {file_path}"
    try:
        return path.read_text()
    except Exception as e:
        return f"Error reading file: {e}"


@tool
def search_files(pattern: str, path: str = ".") -> str:
    """
    Search for files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g., "*.py", "src/**/*.ts")
        path: Directory to search in (default: current directory)

    Returns:
        List of matching file paths.
    """
    from pathlib import Path
    base = Path(path)
    if not base.exists():
        return f"Path not found: {path}"

    matches = list(base.glob(pattern))
    if not matches:
        return f"No files matching '{pattern}' in {path}"

    return "\n".join(str(m) for m in matches[:50])  # Limit to 50 results


def get_default_tools(project_path: str = None) -> list:
    """Get the default tool set for droids."""
    return [
        KnowledgeRetrieverTool(project_path),
        read_file,
        search_files,
    ]
```

#### 1.4 Executor (`src/klean/smol/executor.py`)

```python
"""SmolKLN executor - runs agents using Smolagents.

This module is INDEPENDENT - no imports from src/klean/droids/.
"""

from smolagents import CodeAgent
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
import time

from .loader import load_agent, Agent
from .models import create_model, get_model_for_role
from .tools import get_default_tools, KnowledgeRetrieverTool


class SmolKLNExecutor:
    """Execute K-LEAN agents using Smolagents.

    This is 100% independent from Factory droids.
    When droids are deleted, SmolKLN continues working.
    """

    def __init__(
        self,
        agents_dir: Path = None,
        api_base: str = "http://localhost:4000",
    ):
        """Initialize executor.

        Args:
            agents_dir: Path to agent .md files (default: ~/.klean/agents/)
            api_base: LiteLLM proxy URL
        """
        self.agents_dir = agents_dir or (Path.home() / ".klean" / "agents")
        self.api_base = api_base

    def execute(
        self,
        agent_name: str,
        task: str,
        model_override: str = None,
        context: str = None,
    ) -> Dict[str, Any]:
        """Execute an agent with the given task.

        Args:
            agent_name: Name of the agent (e.g., "security-auditor")
            task: Task description/prompt
            model_override: Override the agent's default model
            context: Additional context (e.g., from knowledge DB)

        Returns:
            Dict with:
                - output: str (the analysis results)
                - agent: str (agent name)
                - model: str (model used)
                - duration_s: float
                - success: bool
        """
        # Load agent configuration
        agent = load_agent(agent_name, self.agents_dir)

        # Determine model to use
        if model_override:
            model_name = model_override
        elif agent.config.model and agent.config.model != "inherit":
            model_name = agent.config.model
        else:
            model_name = get_model_for_role(agent_name)

        # Create model
        model = create_model(model_name, self.api_base)

        # Build full prompt
        full_prompt = self._build_prompt(agent, task, context)

        # Get tools for this agent
        tools = get_default_tools()

        # Create smolagents CodeAgent with agent's system prompt
        smol_agent = CodeAgent(
            tools=tools,
            model=model,
            system_prompt=agent.system_prompt,
            max_steps=10,
        )

        try:
            # Execute with timing
            start_time = time.time()
            result = smol_agent.run(full_prompt)
            duration = time.time() - start_time

            return {
                "output": result,
                "agent": agent_name,
                "model": model_name,
                "duration_s": round(duration, 1),
                "success": True,
            }
        except Exception as e:
            return {
                "output": f"Error: {str(e)}",
                "agent": agent_name,
                "model": model_name,
                "duration_s": 0,
                "success": False,
            }

    def _build_prompt(
        self,
        agent: Agent,
        task: str,
        context: str = None,
    ) -> str:
        """Build the full prompt with task and context."""
        prompt_parts = [f"# Task\n{task}"]

        if context:
            prompt_parts.append(f"\n# Relevant Context\n{context}")

        prompt_parts.append("""
# Instructions
IMPORTANT: You MUST examine actual files before providing feedback.

Required Steps:
1. Use knowledge_search to find relevant prior solutions
2. Use search_files to find relevant files
3. Use read_file to examine actual content

Output Requirements:
- Provide specific file:line references for ALL findings
- Use severity levels: 🔴 Critical | 🟡 Warning | 🟢 Suggestion
- List concrete issues with actionable recommendations
""")

        return "\n".join(prompt_parts)

    def list_agents(self) -> list:
        """List available agents."""
        from .loader import list_available_agents
        return list_available_agents(self.agents_dir)
```

#### 1.5 CLI Entry Point (`src/klean/data/scripts/smol-kln.py`)

```python
#!/usr/bin/env python3
"""SmolKLN CLI - Execute K-LEAN agents using Smolagents.

Usage:
    smol-kln.py <agent> "<task>" [--model MODEL]
    smol-kln.py --list

Examples:
    smol-kln.py security-auditor "audit authentication module"
    smol-kln.py code-reviewer "review error handling" --model deepseek
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from klean.smol.executor import SmolKLNExecutor
from klean.smol.loader import list_available_agents


def main():
    parser = argparse.ArgumentParser(
        description="Execute K-LEAN agents using Smolagents (SmolKLN)"
    )
    parser.add_argument("agent", nargs="?", help="Agent name")
    parser.add_argument("task", nargs="?", help="Task description")
    parser.add_argument("--model", "-m", help="Override model")
    parser.add_argument("--list", "-l", action="store_true", help="List agents")
    parser.add_argument("--json", "-j", action="store_true", help="JSON output")
    parser.add_argument("--output", "-o", help="Save output to file")

    args = parser.parse_args()

    executor = SmolKLNExecutor()

    if args.list:
        agents = executor.list_agents()
        if args.json:
            print(json.dumps(agents))
        else:
            print("Available SmolKLN agents:")
            for a in agents:
                print(f"  - {a}")
        return 0

    if not args.agent or not args.task:
        parser.print_help()
        return 1

    result = executor.execute(
        agent_name=args.agent,
        task=args.task,
        model_override=args.model,
    )

    # Format output (same format as droid-execute.sh for compatibility)
    if args.json:
        print(json.dumps(result))
    else:
        print(result["output"])
        print(f"\n\n---")
        print(f"Execution Details:")
        print(f"- Agent: {result['agent']}")
        print(f"- Model: {result['model']}")
        print(f"- Duration: {result['duration_s']}s")
        print(f"- Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result["output"])
        print(f"\nOutput saved to: {args.output}", file=sys.stderr)

    return 0 if result["success"] else 1


if __name__ == "__main__":
    sys.exit(main())
```

---

### Phase 2: Installation Updates

**Key principle**: SmolKLN installs to its own locations, completely separate from droids.

**Changes to `src/klean/cli.py`:**

```python
# NEW constants (add to cli.py)
SMOL_AGENTS_DIR = KLEAN_DIR / "agents"  # ~/.klean/agents/

def install_smolkln():
    """Install SmolKLN agent system (independent from droids)."""

    # 1. Copy agent .md files from package to ~/.klean/agents/
    # These are COPIES, not references to droids/
    agents_src = DATA_DIR / "agents"  # src/klean/data/agents/
    agents_dst = SMOL_AGENTS_DIR

    agents_dst.mkdir(parents=True, exist_ok=True)

    for agent_file in agents_src.glob("*.md"):
        dst_file = agents_dst / agent_file.name
        if not dst_file.exists():
            shutil.copy2(agent_file, dst_file)
            log(f"  Installed agent: {agent_file.stem}")

    # 2. Install smol-kln.py script
    scripts_dst = SCRIPTS_DIR / "smol-kln.py"
    scripts_src = DATA_DIR / "scripts" / "smol-kln.py"
    shutil.copy2(scripts_src, scripts_dst)
    scripts_dst.chmod(0o755)

    log(f"✓ SmolKLN installed to {SMOL_AGENTS_DIR}")
```

**Update `pyproject.toml`:**

```toml
[project]
dependencies = [
    # ... existing deps ...
    "smolagents[litellm]>=1.0.0",  # Add smolagents with LiteLLM support
    "pyyaml>=6.0",                 # For YAML frontmatter parsing
]
```

**Initial copy of droid files to agents:**

```bash
# One-time copy during development (not symlinks!)
mkdir -p src/klean/data/agents/
cp src/klean/data/droids/*.md src/klean/data/agents/
```

---

### Phase 3: New Slash Command

**Create `/kln:agent` command (`src/klean/data/commands/kln/agent.md`):**

This is a NEW command, not an update to `/kln:droid`. Both can exist during transition.

```markdown
---
name: agent
description: "Execute SmolKLN agents for specialized analysis. Use /kln:agent <role> \"<task>\" [--model MODEL]"
allowed-tools: [Bash, Read, Glob, Grep]
argument-hint: "<role> \"<task>\""
---

# SmolKLN Agent Executor

Execute specialized agents using Smolagents + LiteLLM.

## Available Agents

| Agent | Focus | Default Model |
|-------|-------|---------------|
| `security-auditor` | Security vulnerabilities | glm-4.6-thinking |
| `code-reviewer` | Code quality & best practices | qwen3-coder |
| `debugger` | Bug hunting & root cause analysis | qwen3-coder |
| `performance-engineer` | Performance optimization | deepseek-v3-thinking |
| `orchestrator` | High-level coordination | deepseek-v3-thinking |

## Execution

```bash
~/.claude/scripts/smol-kln.py "$ROLE" "$TASK" --model "$MODEL"
```

## Usage Examples

```
/kln:agent security-auditor "audit the authentication module"
/kln:agent code-reviewer "review error handling in src/"
/kln:agent debugger "investigate memory leak in worker.py" --model deepseek
```
```

**Keep `/kln:droid` working during transition** - it continues to use Factory CLI.

---

### Phase 4: Testing & Validation

#### 4.1 Test Script

```bash
#!/bin/bash
# test-smol-droids.sh

echo "=== SmolDroid Test Suite ==="

# Test 1: List droids
echo "[1/4] Listing droids..."
python -m klean.smol.executor --list

# Test 2: Security auditor
echo "[2/4] Security auditor..."
python -m klean.smol.executor security-auditor "audit the authentication module" --model glm

# Test 3: Code reviewer
echo "[3/4] Code reviewer..."
python -m klean.smol.executor code-reviewer "review error handling in src/" --model qwen

# Test 4: Parallel execution
echo "[4/4] Parallel droids..."
python -m klean.smol.executor security-auditor "audit" &
python -m klean.smol.executor code-reviewer "review" &
wait

echo "=== Tests Complete ==="
```

#### 4.2 Comparison Test

Run same task with both executors:

```bash
# Factory CLI (old)
droid-execute.sh qwen security-auditor "audit auth" > /tmp/factory-result.txt

# SmolDroid (new)
smol-droid.py security-auditor "audit auth" --model qwen > /tmp/smol-result.txt

# Compare
diff /tmp/factory-result.txt /tmp/smol-result.txt
```

---

### Phase 5: Deprecation Path

#### 5.1 Parallel Operation (Current Phase)

Both systems available:

| Command | Executor | Status |
|---------|----------|--------|
| `droid-execute.sh` | Factory CLI | ⚠️ Deprecated |
| `smol-droid.py` | Smolagents | ✅ New default |
| `/kln:droid` | Auto-detect | ✅ Uses SmolDroid |

#### 5.2 Factory Deprecation (Future)

1. Add deprecation warning to `droid-execute.sh`
2. Remove Factory CLI checks from `k-lean doctor`
3. Update documentation
4. Remove `~/.factory/` path references

#### 5.3 Full Removal (Post-validation)

1. Delete `droid-execute.sh`
2. Remove Factory references from `cli.py`
3. Update all documentation
4. Remove `FACTORY_DIR` constant

---

## File Changes Summary

### New Files

| File | Purpose |
|------|---------|
| `src/klean/smol/__init__.py` | Package init |
| `src/klean/smol/loader.py` | Parse droid .md files |
| `src/klean/smol/models.py` | LiteLLM model wrapper |
| `src/klean/smol/executor.py` | SmolDroid executor |
| `src/klean/data/scripts/smol-droid.py` | CLI entry point |

### Modified Files

| File | Changes |
|------|---------|
| `src/klean/__init__.py` | Add `SMOL_DROIDS_DIR` constant |
| `src/klean/cli.py` | Update install path, add smolagents dep |
| `pyproject.toml` | Add smolagents dependency |
| `src/klean/data/commands/kln/droid.md` | Use SmolDroid executor |

### Deprecated Files (Phase 5)

| File | Action |
|------|--------|
| `src/klean/data/scripts/droid-execute.sh` | Deprecate, then remove |
| `src/klean/data/scripts/droid-review.sh` | Deprecate, then remove |

---

## Dependencies

```toml
# pyproject.toml additions
smolagents = ">=1.0.0"
litellm = ">=1.0.0"  # Already required by K-LEAN
```

**Install command:**
```bash
pip install smolagents[litellm]
```

---

## Rollback Plan

If issues arise:

1. Keep Factory CLI as fallback (environment variable switch)
2. `KLEAN_USE_FACTORY=1` forces old executor
3. Both droid directories remain valid during transition

```python
# In executor selection
if os.environ.get("KLEAN_USE_FACTORY") == "1":
    return use_factory_cli(droid, task)
else:
    return use_smolagents(droid, task)
```

---

## Timeline

| Phase | Description | Effort |
|-------|-------------|--------|
| Phase 1 | Core Smolagents integration | 1-2 days |
| Phase 2 | Installation updates | 0.5 day |
| Phase 3 | Slash command update | 0.5 day |
| Phase 4 | Testing & validation | 1 day |
| Phase 5 | Deprecation & cleanup | 0.5 day |

**Total: ~4-5 days**

---

## Success Criteria

- [ ] All 8 droids execute via SmolDroid
- [ ] No Factory CLI or FACTORY_API_KEY required
- [ ] YAML frontmatter (model, tools) is respected
- [ ] Output quality matches or exceeds Factory CLI
- [ ] `/kln:droid` command works seamlessly
- [ ] `k-lean doctor` validates SmolDroid setup
- [ ] Documentation updated

---

## Open Questions (Resolved)

| Question | Decision |
|----------|----------|
| Tool restrictions from YAML? | ✅ Yes - use droid.config.tools to filter |
| Orchestrator 765-line prompt? | ✅ Keep as system_prompt, use managed_agents |
| Parallel mode? | ✅ Smolagents handles this natively |
| Memory system? | ✅ Use smolagents memory + Serena memories |
| Knowledge DB integration? | ✅ Custom KnowledgeRetrieverTool (Agentic RAG) |
| Output format? | ✅ Same format as current droid-execute.sh |

## New Files Summary

```
src/klean/
├── smol/                            # NEW independent package
│   ├── __init__.py                  # Package exports
│   ├── loader.py                    # Parse agent .md files
│   ├── models.py                    # LiteLLM wrapper + role mapping
│   ├── tools.py                     # KnowledgeRetrieverTool + file tools
│   └── executor.py                  # SmolKLNExecutor main class
└── data/
    ├── agents/                      # COPIED agent definitions
    │   ├── security-auditor.md
    │   ├── code-reviewer.md
    │   ├── debugger.md
    │   ├── orchestrator.md
    │   └── ... (8 total)
    ├── commands/kln/
    │   └── agent.md                 # NEW /kln:agent command
    └── scripts/
        └── smol-kln.py              # CLI entry point
```

## Independence Checklist

| Requirement | Status |
|-------------|--------|
| No imports from `src/klean/droids/` | ✅ |
| Agent .md files are COPIED, not symlinked | ✅ |
| Install to `~/.klean/agents/` (not `~/.factory/`) | ✅ |
| New command `/kln:agent` (not modifying `/kln:droid`) | ✅ |
| Works after droid system is deleted | ✅ |

## Key Design Decisions

1. **100% Independent**: No references to droid system - can delete droids anytime
2. **Copy not reference**: Agent .md files are copied during development
3. **New command**: `/kln:agent` instead of modifying `/kln:droid`
4. **Agentic RAG**: Knowledge DB as retriever tool for iterative search
5. **Same output format**: Compatible with existing output patterns
6. **Smolagents native**: Use CodeAgent, LiteLLMModel, @tool decorator

## Deletion Plan (Future)

When ready to remove droids:
```bash
# Safe to delete - SmolKLN is independent
rm -rf src/klean/droids/
rm -rf src/klean/data/droids/
rm src/klean/data/scripts/droid-execute.sh
rm src/klean/data/commands/kln/droid.md
# SmolKLN continues working unchanged
```

---

*Created: 2024-12-22*
*Updated: 2024-12-22*
*Status: Ready for Implementation*
*Naming: SmolKLN (independent agent system)*
