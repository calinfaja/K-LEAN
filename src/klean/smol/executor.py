"""SmolKLN executor - runs agents using Smolagents.

Primary agent execution engine for K-LEAN.
"""

from pathlib import Path
from typing import Optional, Dict, Any, List
import json
import time

from .loader import load_agent, list_available_agents, Agent
from .models import create_model, get_model_for_role
from .tools import get_default_tools, KnowledgeRetrieverTool
from .context import (
    gather_project_context,
    format_context_for_prompt,
    ProjectContext,
)
from .memory import AgentMemory


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

    def execute(
        self,
        agent_name: str,
        task: str,
        model_override: str = None,
        context: str = None,
        max_steps: int = 10,
    ) -> Dict[str, Any]:
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

        # Determine model to use
        if model_override:
            model_name = model_override
        elif agent.config.model and agent.config.model != "inherit":
            model_name = agent.config.model
        else:
            model_name = get_model_for_role(agent_name)

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
            combined_context = memory_context + "\n\n" + combined_context if combined_context else memory_context

        # Build full prompt with project context and memory
        full_prompt = self._build_prompt(agent, task, combined_context if combined_context else None)

        # Get tools for this agent - pass project path for Knowledge DB
        tools = get_default_tools(str(self.project_root))

        # Create smolagents CodeAgent
        # First create with defaults, then customize system prompt
        smol_agent = CodeAgent(
            tools=tools,
            model=model,
            max_steps=max_steps,
        )

        # Prepend agent's system prompt to the default system prompt
        if agent.system_prompt:
            default_prompt = smol_agent.prompt_templates.get("system_prompt", "")
            smol_agent.prompt_templates["system_prompt"] = (
                agent.system_prompt + "\n\n" + default_prompt
            )

        try:
            # Execute with timing
            start_time = time.time()
            result = smol_agent.run(full_prompt)
            duration = time.time() - start_time

            output = str(result)

            # Record successful result to memory
            self.memory.record(
                f"Agent {agent_name}: {output[:500]}",
                "result",
                agent=agent_name,
                model=model_name,
                duration=duration
            )

            return {
                "output": output,
                "agent": agent_name,
                "model": model_name,
                "duration_s": round(duration, 1),
                "success": True,
            }
        except Exception as e:
            error_msg = f"Execution error: {str(e)}"

            # Record error to memory
            self.memory.record(
                f"Agent {agent_name} failed: {str(e)}",
                "error",
                agent=agent_name,
                model=model_name
            )

            return {
                "output": error_msg,
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

        # Instructions
        prompt_parts.append(f"""
# Instructions
IMPORTANT: You MUST examine actual files before providing feedback.
Working directory: {self.project_root}

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

    def list_agents(self) -> List[str]:
        """List available agents."""
        return list_available_agents(self.agents_dir)

    def get_agent_info(self, agent_name: str) -> Dict[str, Any]:
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
