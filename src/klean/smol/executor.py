"""SmolKLN executor - runs agents using Smolagents.

Primary agent execution engine for K-LEAN.
"""

import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from klean.discovery import get_model

from .context import (
    format_context_for_prompt,
    gather_project_context,
)
from .loader import Agent, list_available_agents, load_agent
from .memory import AgentMemory
from .models import create_model
from .prompts import KLEAN_SYSTEM_PROMPT
from .tools import (
    get_citation_stats,
    get_default_tools,
    get_tools_for_agent,
    validate_citations,
    validate_file_paths,
)


def add_step_awareness(memory_step, agent) -> None:
    """Inject step awareness into observations on late steps.

    This callback warns the agent when running low on steps,
    prompting it to call final_answer() before hitting the limit.
    """
    remaining = agent.max_steps - memory_step.step_number
    if remaining <= 2:
        warning = f"\n[Step {memory_step.step_number}/{agent.max_steps}] Only {remaining} step(s) left - call final_answer() now!"
        memory_step.observations = (
            warning if memory_step.observations is None else memory_step.observations + warning
        )


class SmolKLNExecutor:
    """Execute K-LEAN agents using Smolagents.

    Primary agent execution engine for K-LEAN using smolagents + LiteLLM.
    Project-aware: Automatically detects project root, loads CLAUDE.md,
    and connects to Knowledge DB.
    """

    def __init__(
        self,
        agents_dir: Path = None,
        api_base: str = "http://localhost:4000",
        project_path: Path = None,
    ):
        """Initialize executor.

        Args:
            agents_dir: Path to agent .md files (default: ~/.klean/agents/)
            api_base: LiteLLM proxy URL
            project_path: Override project root detection (default: auto-detect)
        """
        self.agents_dir = agents_dir or (Path.home() / ".klean" / "agents")
        self.api_base = api_base

        # Gather project context (auto-detect or use provided path)
        self.project_context = gather_project_context(project_path)
        self.project_root = self.project_context.project_root

        # Initialize memory system
        self.memory = AgentMemory(self.project_context)

        # Output directory for agent results
        self.output_dir = self._get_output_dir()

    def _get_output_dir(self) -> Path:
        """Get output directory for agent results.

        Follows K-LEAN convention: <project_root>/.claude/kln/agentExecute/
        Falls back to temp directory if not writable.
        """
        output_dir = self.project_root / ".claude" / "kln" / "agentExecute"
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
            return output_dir
        except (PermissionError, OSError):
            # Fallback to system temp directory (cross-platform)
            fallback = Path(tempfile.gettempdir()) / "claude-reviews" / "agentExecute"
            fallback.mkdir(parents=True, exist_ok=True)
            return fallback

    def _format_result(self, result) -> str:
        """Format agent result to clean markdown.

        smolagents CodeAgent may return dict like:
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
        agent_name: str,
        task: str,
        model_name: str,
        output: str,
        duration: float,
        success: bool,
    ) -> Path:
        """Save agent result to markdown file.

        Returns:
            Path to the saved file.
        """
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Sanitize task for filename (max 30 chars)
        safe_task = "".join(c if c.isalnum() or c in "-_" else "-" for c in task)[:30]
        safe_task = safe_task.strip("-") or "review"

        filename = f"{timestamp}_{agent_name}_{safe_task}.md"
        output_path = self.output_dir / filename

        # Build markdown content
        status = "Success" if success else "Failed"
        content = f"""# SmolKLN Agent Report

**Agent:** {agent_name}
**Model:** {model_name}
**Task:** {task}
**Duration:** {duration:.1f}s
**Status:** {status}
**Generated:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

{output}
"""
        output_path.write_text(content)
        return output_path

    def execute(
        self,
        agent_name: str,
        task: str,
        model_override: str = None,
        context: str = None,
        max_steps: int = 10,
    ) -> dict[str, Any]:
        """Execute an agent with the given task.

        Args:
            agent_name: Name of the agent (e.g., "security-auditor")
            task: Task description/prompt
            model_override: Override the agent's default model
            context: Additional context (e.g., from knowledge DB)
            max_steps: Maximum agent steps (default: 10)

        Returns:
            Dict with:
                - output: str (the analysis results)
                - agent: str (agent name)
                - model: str (model used)
                - duration_s: float
                - success: bool
                - memory_history: List[Dict] (session memory entries)
        """
        try:
            from smolagents import CodeAgent
        except ImportError:
            return {
                "output": "Error: smolagents not installed. Install with: pip install smolagents[litellm]",
                "agent": agent_name,
                "model": "none",
                "duration_s": 0,
                "success": False,
            }

        # Start memory session for this task
        self.memory.start_session(task)

        # Get memory context (prior knowledge + session history)
        memory_context = self.memory.get_augmented_context()

        # Load agent configuration
        try:
            agent = load_agent(agent_name, self.agents_dir)
        except FileNotFoundError as e:
            return {
                "output": f"Error: {e}",
                "agent": agent_name,
                "model": "none",
                "duration_s": 0,
                "success": False,
            }

        # Determine model to use (simple: override > agent config > first available)
        if model_override:
            model_name = model_override
        elif agent.config.model and agent.config.model != "inherit":
            model_name = agent.config.model
        else:
            model_name = get_model()  # First available from LiteLLM

        # Create model
        try:
            model = create_model(model_name, self.api_base)
        except Exception as e:
            return {
                "output": f"Error creating model: {e}",
                "agent": agent_name,
                "model": model_name,
                "duration_s": 0,
                "success": False,
            }

        # Combine provided context with memory context
        combined_context = context or ""
        if memory_context:
            combined_context = (
                memory_context + "\n\n" + combined_context if combined_context else memory_context
            )

        # Build full prompt with project context and memory
        full_prompt = self._build_prompt(
            agent, task, combined_context if combined_context else None
        )

        # Get tools for this agent - use agent-specific tools if defined
        if agent.config.tools:
            tools = get_tools_for_agent(agent.config.tools, str(self.project_root))
        else:
            tools = get_default_tools(str(self.project_root))

        # Create smolagents CodeAgent
        # CodeAgent is ~30% more efficient than ToolCallingAgent
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

        # Build custom instructions from agent definition
        custom_instructions = ""
        if agent.system_prompt:
            custom_instructions = agent.system_prompt

        smol_agent = CodeAgent(
            tools=tools,
            model=model,
            max_steps=max_steps,
            planning_interval=3,  # Plan every 3 steps to stay on track
            additional_authorized_imports=safe_imports,
            step_callbacks=[add_step_awareness],  # Warn on low steps
            final_answer_checks=[
                validate_citations,
                validate_file_paths,
            ],  # Verify citations + paths exist
        )

        # REPLACE default system prompt to remove John Doe/Ulam examples
        # KLEAN_SYSTEM_PROMPT uses Jinja2 placeholders for tools/managed_agents
        from jinja2 import Template

        template = Template(KLEAN_SYSTEM_PROMPT)
        rendered_prompt = template.render(
            tools={t.name: t for t in tools},
            managed_agents={},
            custom_instructions=custom_instructions,
        )
        smol_agent.prompt_templates["system_prompt"] = rendered_prompt

        try:
            # Execute with timing
            start_time = time.time()
            result = smol_agent.run(full_prompt)
            duration = time.time() - start_time

            output = self._format_result(result)

            # Get citation statistics
            citation_stats = get_citation_stats(output, smol_agent.memory)

            # Record successful result to memory
            self.memory.record(
                f"Agent {agent_name}: {output[:500]}",
                "result",
                agent=agent_name,
                model=model_name,
                duration=duration,
            )

            # Persist session memory to Knowledge DB for future agents
            persisted_count = self.memory.persist_session_to_kb(agent_name)

            # Save result to file
            output_file = self._save_result(
                agent_name, task, model_name, output, duration, success=True
            )

            return {
                "output": output,
                "agent": agent_name,
                "model": model_name,
                "duration_s": round(duration, 1),
                "success": True,
                "output_file": str(output_file),
                "memory_history": self.memory.session.get_history() if self.memory.session else [],
                "memory_persisted": persisted_count,
                "citation_stats": citation_stats,
            }
        except Exception as e:
            error_msg = f"Execution error: {str(e)}"

            # Record error to memory
            self.memory.record(
                f"Agent {agent_name} failed: {str(e)}", "error", agent=agent_name, model=model_name
            )

            # Save error result to file
            output_file = self._save_result(
                agent_name, task, model_name, error_msg, 0, success=False
            )

            return {
                "output": error_msg,
                "agent": agent_name,
                "model": model_name,
                "duration_s": 0,
                "success": False,
                "output_file": str(output_file),
                "memory_history": self.memory.session.get_history() if self.memory.session else [],
            }

    def _build_prompt(
        self,
        agent: Agent,
        task: str,
        context: str = None,
    ) -> str:
        """Build the full prompt with task and project context."""
        prompt_parts = []

        # Include project context first
        project_context_str = format_context_for_prompt(self.project_context)
        if project_context_str:
            prompt_parts.append(project_context_str)

        # Task
        prompt_parts.append(f"\n# Task\n{task}")

        # Additional context if provided
        if context:
            prompt_parts.append(f"\n# Additional Context\n{context}")

        # Instructions - minimal, let agent .md file control output format
        prompt_parts.append(f"""
# Instructions
Working directory: {self.project_root}

You MUST examine actual files before providing feedback.
Use your tools: knowledge_search, search_files, read_file to investigate.
Provide specific file:line references for findings.
""")

        return "\n".join(prompt_parts)

    def list_agents(self) -> list[str]:
        """List available agents."""
        return list_available_agents(self.agents_dir)

    def get_agent_info(self, agent_name: str) -> dict[str, Any]:
        """Get information about an agent."""
        try:
            agent = load_agent(agent_name, self.agents_dir)
            return {
                "name": agent.config.name,
                "description": agent.config.description,
                "model": agent.config.model,
                "tools": agent.config.tools,
                "source": str(agent.source_path),
            }
        except FileNotFoundError:
            return {"error": f"Agent not found: {agent_name}"}
