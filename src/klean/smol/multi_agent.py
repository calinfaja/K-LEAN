"""Multi-agent executor for K-LEAN.

Uses smolagents managed_agents for orchestrated multi-model reviews.
"""

import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from .context import format_context_for_prompt, gather_project_context
from .executor import add_step_awareness
from .models import create_model
from .multi_config import get_3_agent_config, get_thorough_agent_config
from .tools import get_citation_stats, get_tools_for_agent, validate_citations, validate_file_paths


class MultiAgentExecutor:
    """Execute tasks using multi-agent orchestration.

    Uses smolagents managed_agents to coordinate specialist agents
    under a manager agent.
    """

    def __init__(
        self,
        api_base: str = "http://localhost:4000",
        project_path: Path = None,
    ):
        """Initialize executor.

        Args:
            api_base: LiteLLM proxy URL
            project_path: Override project root detection
        """
        self.api_base = api_base
        self.project_context = gather_project_context(project_path)
        self.project_root = self.project_context.project_root
        self.output_dir = self._get_output_dir()

    def _get_output_dir(self) -> Path:
        """Get output directory for multi-agent results."""
        output_dir = self.project_root / ".claude" / "kln" / "multiAgent"
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            return output_dir
        except (PermissionError, OSError):
            # Fallback to system temp directory (cross-platform)
            fallback = Path(tempfile.gettempdir()) / "claude-reviews" / "multiAgent"
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback

    def _load_agent_prompt(self, agent_name: str) -> str:
        """Load system prompt for an agent from .md file.

        Returns just the agent-specific instructions.
        Code rules are injected via KLEAN_SYSTEM_PROMPT template.
        """
        prompts_dir = Path(__file__).parent.parent / "data" / "multi-agents"
        prompt_file = prompts_dir / f"{agent_name}.md"

        if prompt_file.exists():
            content = prompt_file.read_text()
            # Skip YAML frontmatter if present
            if content.startswith("---"):
                parts = content.split("---", 2)
                if len(parts) >= 3:
                    return parts[2].strip()
            return content
        return ""

    def _format_result(self, result) -> str:
        """Format agent result to clean markdown.

        smolagents CodeAgent with managed_agents returns dict like:
        {'thought': '...', 'code': '## Summary\\n...'}

        This extracts and formats the content properly.
        """
        if isinstance(result, dict):
            # Extract code (main content) if present
            if "code" in result:
                content = result["code"]
                # Handle escaped newlines from JSON serialization
                if isinstance(content, str) and "\\n" in content:
                    content = content.replace("\\n", "\n")
                return content
            # Fallback: format dict as readable markdown
            parts = []
            if "thought" in result:
                parts.append(f"## Analysis Summary\n\n{result['thought']}")
            for key, value in result.items():
                if key not in ("thought", "code"):
                    parts.append(f"## {key.title()}\n\n{value}")
            return "\n\n".join(parts) if parts else str(result)
        return str(result)

    def _save_result(
        self,
        task: str,
        variant: str,
        output: str,
        duration: float,
        agents_used: list[str],
    ) -> Path:
        """Save multi-agent result to markdown file."""
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        safe_task = "".join(c if c.isalnum() or c in "-_" else "-" for c in task)[:30]
        safe_task = safe_task.strip("-") or "review"

        filename = f"{timestamp}_multi-{variant}_{safe_task}.md"
        output_path = self.output_dir / filename

        content = f"""# Multi-Agent Review Report

**Variant:** {variant}
**Agents:** {", ".join(agents_used)}
**Task:** {task}
**Duration:** {duration:.1f}s
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

{output}
"""
        output_path.write_text(content)
        return output_path

    def execute(
        self,
        task: str,
        thorough: bool = False,
        manager_model: str = None,
    ) -> dict[str, Any]:
        """Execute multi-agent review.

        Args:
            task: Review task description
            thorough: Use 4-agent variant if True, else 3-agent
            manager_model: Override manager model

        Returns:
            Dict with output, variant, agents_used, duration_s, success
        """
        try:
            from smolagents import CodeAgent
        except ImportError:
            return {
                "output": "Error: smolagents not installed. Install with: pip install smolagents[litellm]",
                "variant": "thorough" if thorough else "3-agent",
                "agents_used": [],
                "duration_s": 0,
                "success": False,
            }

        # Get configuration
        config = get_thorough_agent_config() if thorough else get_3_agent_config()
        variant = "thorough" if thorough else "3-agent"

        # Override manager model if specified
        if manager_model:
            config["manager"].model = manager_model

        # Build project context
        project_context_str = format_context_for_prompt(self.project_context)

        # Create specialist agents
        specialists = []
        for name, agent_config in config.items():
            if name == "manager":
                continue

            try:
                model = create_model(agent_config.model, self.api_base)
                tools = get_tools_for_agent(agent_config.tools, project_path=str(self.project_root))

                # Load system prompt
                system_prompt = self._load_agent_prompt(name)

                # Safe imports beyond default (collections, datetime, itertools, math,
                # queue, random, re, stat, statistics, time, unicodedata are default)
                # Avoid: os, subprocess, sys, socket, pathlib, shutil, io
                safe_imports = [
                    "json",
                    "typing",
                    "functools",
                    "copy",
                    "string",
                    "decimal",
                    "enum",
                    "dataclasses",
                    "operator",
                    "textwrap",
                ]

                agent = CodeAgent(
                    model=model,
                    tools=tools,
                    name=agent_config.name,
                    description=agent_config.description,
                    max_steps=agent_config.max_steps,
                    planning_interval=agent_config.planning_interval,
                    additional_authorized_imports=safe_imports,
                    step_callbacks=[add_step_awareness],  # Warn on low steps
                )

                # REPLACE default system prompt (removes John Doe/Ulam examples)
                # Use KLEAN base template with agent-specific prompt as custom_instructions
                from jinja2 import Template

                from .prompts import KLEAN_SYSTEM_PROMPT

                template = Template(KLEAN_SYSTEM_PROMPT)
                rendered_prompt = template.render(
                    tools={t.name: t for t in tools},
                    managed_agents={},
                    custom_instructions=system_prompt,
                )
                agent.prompt_templates["system_prompt"] = rendered_prompt

                specialists.append(agent)
            except Exception as e:
                return {
                    "output": f"Error creating agent {name}: {e}",
                    "variant": variant,
                    "agents_used": [],
                    "duration_s": 0,
                    "success": False,
                }

        # Create manager with specialists as managed_agents
        manager_config = config["manager"]
        try:
            manager_model_obj = create_model(manager_config.model, self.api_base)
            manager_prompt = self._load_agent_prompt("manager")

            # Safe imports beyond default (manager delegates but may generate code)
            safe_imports = [
                "json",
                "typing",
                "functools",
                "copy",
                "string",
                "decimal",
                "enum",
                "dataclasses",
                "operator",
                "textwrap",
            ]

            manager = CodeAgent(
                model=manager_model_obj,
                tools=[],  # Manager only delegates
                managed_agents=specialists,
                max_steps=manager_config.max_steps,
                planning_interval=manager_config.planning_interval,
                additional_authorized_imports=safe_imports,
                step_callbacks=[add_step_awareness],  # Warn on low steps
                final_answer_checks=[
                    validate_citations,
                    validate_file_paths,
                ],  # Verify citations + paths exist
            )

            # REPLACE default system prompt for manager too
            from jinja2 import Template

            from .prompts import KLEAN_SYSTEM_PROMPT

            template = Template(KLEAN_SYSTEM_PROMPT)
            rendered_prompt = template.render(
                tools={},
                managed_agents={a.name: a for a in specialists},
                custom_instructions=manager_prompt,
            )
            manager.prompt_templates["system_prompt"] = rendered_prompt
        except Exception as e:
            return {
                "output": f"Error creating manager: {e}",
                "variant": variant,
                "agents_used": [],
                "duration_s": 0,
                "success": False,
            }

        # Build full prompt with project context
        full_prompt = f"""{project_context_str}

# Task
{task}

# Working Directory
{self.project_root}
"""

        # Execute
        start_time = time.time()
        try:
            result = manager.run(full_prompt)
            duration = time.time() - start_time
            output = self._format_result(result)

            # Get citation statistics from agent memory
            citation_stats = get_citation_stats(output, manager.memory)

            # Save result
            agents_used = [a.name for a in specialists]
            output_file = self._save_result(task, variant, output, duration, agents_used)

            return {
                "output": output,
                "variant": variant,
                "agents_used": agents_used,
                "duration_s": round(duration, 1),
                "success": True,
                "output_file": str(output_file),
                "citation_stats": citation_stats,
            }
        except Exception as e:
            duration = time.time() - start_time
            return {
                "output": f"Execution error: {e}",
                "variant": variant,
                "agents_used": [a.name for a in specialists],
                "duration_s": round(duration, 1),
                "success": False,
            }
