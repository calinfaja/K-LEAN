"""Multi-agent orchestrator for complex tasks.

Coordinates multiple agents for tasks that require planning,
parallel execution, and result synthesis.
"""

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class TaskStatus(Enum):
    """Status of a subtask."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class SubTask:
    """A single subtask in a plan."""

    id: str
    description: str
    agent: str
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[dict] = None


@dataclass
class TaskPlan:
    """Plan for executing a complex task."""

    goal: str
    subtasks: list[SubTask] = field(default_factory=list)
    parallel_groups: list[list[str]] = field(default_factory=list)


PLANNER_PROMPT = """Create an execution plan for this task.

## Task
{task}

## Available Agents
{agents}

## Agent Descriptions
{agent_info}

Respond with JSON:
{{
  "subtasks": [
    {{"id": "1", "description": "specific task", "agent": "agent-name", "dependencies": []}}
  ],
  "parallel_groups": [["1"], ["2", "3"]]
}}

Rules:
1. Use specific, actionable descriptions
2. Match agent to its specialty
3. Group independent tasks for parallel execution
4. List dependencies (subtask IDs that must complete first)
5. Keep it minimal - don't over-engineer
"""


class SmolKLNOrchestrator:
    """Orchestrator for multi-agent task execution.

    Coordinates multiple agents by:
    1. Planning - Breaking task into subtasks
    2. Scheduling - Executing with dependency awareness
    3. Synthesizing - Combining results
    """

    def __init__(self, executor, max_parallel: int = 3, planner_model: str = None):
        """Initialize orchestrator.

        Args:
            executor: SmolKLNExecutor instance
            max_parallel: Max concurrent agents
            planner_model: Model for planning (default: use executor default)
        """
        self.executor = executor
        self.max_parallel = max_parallel
        self.planner_model = planner_model

    def execute(
        self, task: str, agents: list[str] = None, synthesize: bool = True
    ) -> dict[str, Any]:
        """Execute a complex task with multiple agents.

        Args:
            task: Task description
            agents: Specific agents to use (default: all available)
            synthesize: Whether to synthesize results (default: True)

        Returns:
            Dict with output, plan, per-agent results, and success status
        """
        # 1. Create plan
        plan = self._create_plan(task, agents)

        if not plan.subtasks:
            return {
                "output": "Failed to create execution plan",
                "plan": None,
                "results": {},
                "success": False,
            }

        # 2. Execute with dependencies
        results = self._execute_plan(plan)

        # 3. Synthesize output
        if synthesize:
            final = self._synthesize(task, results)
        else:
            final = self._format_results(results)

        return {
            "output": final,
            "plan": {
                "goal": plan.goal,
                "subtasks": [
                    {"id": st.id, "description": st.description, "agent": st.agent}
                    for st in plan.subtasks
                ],
                "parallel_groups": plan.parallel_groups,
            },
            "results": dict(results.items()),
            "success": all(r.get("success", False) for r in results.values()),
        }

    def _create_plan(self, task: str, agents: list[str] = None) -> TaskPlan:
        """Create execution plan using planner agent."""
        available = agents or self.executor.list_agents()

        # Get agent descriptions
        agent_info = []
        for name in available:
            info = self.executor.get_agent_info(name)
            if not info.get("error"):
                desc = info.get("description", "No description")
                agent_info.append(f"- {name}: {desc}")

        prompt = PLANNER_PROMPT.format(
            task=task,
            agents=", ".join(available),
            agent_info="\n".join(agent_info) if agent_info else "No descriptions available",
        )

        # Use code-reviewer or first available agent for planning
        planner_agent = "code-reviewer" if "code-reviewer" in available else available[0]

        result = self.executor.execute(
            planner_agent, prompt, model_override=self.planner_model, max_steps=5
        )

        return self._parse_plan(result["output"], task)

    def _parse_plan(self, output: str, task: str) -> TaskPlan:
        """Parse planner output into TaskPlan."""
        # Find JSON in output
        match = re.search(r"\{[\s\S]*\}", output)
        if match:
            try:
                data = json.loads(match.group())
                subtasks = []
                for st in data.get("subtasks", []):
                    subtasks.append(
                        SubTask(
                            id=str(st.get("id", len(subtasks) + 1)),
                            description=st.get("description", ""),
                            agent=st.get("agent", "code-reviewer"),
                            dependencies=st.get("dependencies", []),
                        )
                    )

                if subtasks:
                    return TaskPlan(
                        goal=task,
                        subtasks=subtasks,
                        parallel_groups=data.get("parallel_groups", [[st.id for st in subtasks]]),
                    )
            except json.JSONDecodeError:
                pass

        # Fallback: single task plan
        return TaskPlan(
            goal=task, subtasks=[SubTask("1", task, "code-reviewer", [])], parallel_groups=[["1"]]
        )

    def _execute_plan(self, plan: TaskPlan) -> dict[str, dict]:
        """Execute plan with dependency-aware scheduling."""
        results = {}

        for group in plan.parallel_groups:
            # Get subtasks for this group
            tasks = [st for st in plan.subtasks if st.id in group]

            # Check dependencies are satisfied
            tasks = [
                st
                for st in tasks
                if all(
                    dep in results and results[dep].get("success", False) for dep in st.dependencies
                )
            ]

            if not tasks:
                continue

            # Execute in parallel
            with ThreadPoolExecutor(max_workers=self.max_parallel) as pool:
                futures = {pool.submit(self._execute_subtask, st, results): st for st in tasks}

                for future in as_completed(futures, timeout=300):
                    subtask = futures[future]
                    try:
                        result = future.result(timeout=120)
                        results[subtask.id] = result
                        subtask.status = (
                            TaskStatus.COMPLETED if result.get("success") else TaskStatus.FAILED
                        )
                        subtask.result = result
                    except Exception as e:
                        results[subtask.id] = {
                            "success": False,
                            "output": f"Execution error: {str(e)}",
                            "agent": subtask.agent,
                        }
                        subtask.status = TaskStatus.FAILED

        return results

    def _execute_subtask(self, subtask: SubTask, prior_results: dict) -> dict:
        """Execute a single subtask with context from dependencies."""
        subtask.status = TaskStatus.RUNNING

        # Build context from dependencies
        context = ""
        for dep_id in subtask.dependencies:
            if dep_id in prior_results:
                dep_output = prior_results[dep_id].get("output", "")
                # Truncate to avoid context overflow
                context += f"\n## From task {dep_id}:\n{dep_output[:800]}"

        return self.executor.execute(
            subtask.agent, subtask.description, context=context.strip() or None
        )

    def _synthesize(self, task: str, results: dict) -> str:
        """Synthesize results from multiple agents into cohesive output."""
        if len(results) == 1:
            # Single result, no synthesis needed
            return list(results.values())[0].get("output", "")

        # Format results for synthesis
        formatted = []
        for tid, r in results.items():
            output = r.get("output", "")
            agent = r.get("agent", "unknown")
            # Truncate long outputs
            if len(output) > 600:
                output = output[:600] + "..."
            formatted.append(f"### Task {tid} ({agent})\n{output}")

        synthesis_prompt = f"""Synthesize these agent results into a cohesive response.

## Original Task
{task}

## Agent Results
{chr(10).join(formatted)}

## Instructions
1. Identify key findings from each agent
2. Resolve any conflicts
3. Provide unified summary with actionable recommendations
4. Use severity levels: CRITICAL | WARNING | INFO
"""

        result = self.executor.execute("code-reviewer", synthesis_prompt, max_steps=5)

        return result["output"]

    def _format_results(self, results: dict) -> str:
        """Format results without synthesis."""
        parts = []
        for tid, r in results.items():
            agent = r.get("agent", "unknown")
            output = r.get("output", "No output")
            success = "[OK]" if r.get("success") else "[ERROR]"
            parts.append(f"## Task {tid} ({agent}) {success}\n{output}")

        return "\n\n".join(parts)


def quick_orchestrate(
    task: str, agents: list[str] = None, api_base: str = "http://localhost:4000"
) -> dict[str, Any]:
    """Quick helper to run orchestrated task.

    Args:
        task: Task description
        agents: Specific agents to use
        api_base: LiteLLM proxy URL

    Returns:
        Orchestrator result
    """
    from .executor import SmolKLNExecutor

    executor = SmolKLNExecutor(api_base=api_base)
    orchestrator = SmolKLNOrchestrator(executor)
    return orchestrator.execute(task, agents)
