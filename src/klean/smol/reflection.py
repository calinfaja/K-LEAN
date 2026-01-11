"""Self-correction through critique and retry.

Implements the Reflexion pattern: agents critique their own output
and retry with feedback if quality is insufficient.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable

from klean.discovery import get_model


class CritiqueVerdict(Enum):
    """Verdict from critique evaluation."""

    PASS = "pass"
    RETRY = "retry"
    FAIL = "fail"


@dataclass
class Critique:
    """Result of critiquing agent output."""

    verdict: CritiqueVerdict
    feedback: str
    issues: list[str]
    suggestions: list[str]
    confidence: float


CRITIC_PROMPT = """Evaluate this agent output:

## Task
{task}

## Output
{output}

## Criteria
1. Did the agent examine actual files (not assumptions)?
2. Are findings specific with file:line references?
3. Are recommendations actionable?
4. Is output complete and well-structured?

Respond with:
VERDICT: [PASS|RETRY|FAIL]
CONFIDENCE: [0.0-1.0]
ISSUES:
- issue 1
SUGGESTIONS:
- suggestion 1
FEEDBACK: [explanation if RETRY]
"""


class ReflectionEngine:
    """Engine for self-critique and retry.

    Uses a critic model to evaluate agent output and determine
    if retry with feedback is needed.
    """

    def __init__(
        self,
        model_factory: Callable[[str], Any],
        max_retries: int = 2,
        critic_model: str = "",  # Empty = use first available from LiteLLM
    ):
        """Initialize reflection engine.

        Args:
            model_factory: Function to create model by name
            max_retries: Maximum number of retry attempts
            critic_model: Model to use for critique (empty = first available)
        """
        self.model_factory = model_factory
        self.max_retries = max_retries
        self.critic_model = critic_model or get_model() or "auto"

    def critique(self, task: str, output: str) -> Critique:
        """Critique agent output.

        Args:
            task: Original task description
            output: Agent's output to evaluate

        Returns:
            Critique with verdict and feedback
        """
        try:
            model = self.model_factory(self.critic_model)
            prompt = CRITIC_PROMPT.format(task=task, output=output)
            response = model(prompt)
            return self._parse_critique(str(response))
        except Exception as e:
            # On error, default to PASS
            return Critique(
                verdict=CritiqueVerdict.PASS,
                feedback=f"Critique error: {e}",
                issues=[],
                suggestions=[],
                confidence=0.5,
            )

    def _parse_critique(self, response: str) -> Critique:
        """Parse critique response into structured format."""
        verdict = CritiqueVerdict.PASS
        confidence = 0.8
        issues = []
        suggestions = []
        feedback = ""
        section = None

        for line in response.strip().split("\n"):
            line = line.strip()
            if line.startswith("VERDICT:"):
                v = line.split(":", 1)[1].strip().upper()
                if "RETRY" in v:
                    verdict = CritiqueVerdict.RETRY
                elif "FAIL" in v:
                    verdict = CritiqueVerdict.FAIL
            elif line.startswith("CONFIDENCE:"):
                try:
                    confidence = float(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("ISSUES:"):
                section = "issues"
            elif line.startswith("SUGGESTIONS:"):
                section = "suggestions"
            elif line.startswith("FEEDBACK:"):
                feedback = line.split(":", 1)[1].strip()
                section = None
            elif line.startswith("- ") and section:
                if section == "issues":
                    issues.append(line[2:])
                elif section == "suggestions":
                    suggestions.append(line[2:])

        return Critique(
            verdict=verdict,
            feedback=feedback,
            issues=issues,
            suggestions=suggestions,
            confidence=confidence,
        )

    def execute_with_reflection(
        self, executor, agent_name: str, task: str, **kwargs
    ) -> dict[str, Any]:
        """Execute agent with reflection loop.

        Runs agent, critiques output, and retries with feedback if needed.

        Args:
            executor: SmolKLNExecutor instance
            agent_name: Agent to execute
            task: Task description
            **kwargs: Additional args for executor.execute()

        Returns:
            Dict with output, attempts count, and reflection status
        """
        current_task = task
        attempt = 0

        for attempt in range(self.max_retries + 1):  # noqa: B007
            # Execute agent
            result = executor.execute(agent_name, current_task, **kwargs)

            if not result["success"]:
                # Agent failed, don't retry
                break

            # Critique the output
            critique = self.critique(task, result["output"])

            if critique.verdict == CritiqueVerdict.PASS:
                # Output is good, save any suggestions as lessons
                if hasattr(executor, "memory") and executor.memory and critique.suggestions:
                    lesson = f"Task: {task[:100]}\nLearning: {'; '.join(critique.suggestions)}"
                    executor.memory.save_lesson(lesson)
                break

            if critique.verdict == CritiqueVerdict.FAIL:
                # Output is bad but not worth retrying
                result["output"] += f"\n\n[Reflection: {critique.feedback}]"
                break

            # RETRY with feedback
            issues_str = "\n".join(f"- {i}" for i in critique.issues)
            current_task = f"""{task}

## Previous Attempt Issues
{issues_str}

## Feedback
{critique.feedback}

Please address these issues and provide improved output."""

        # Add reflection metadata
        result["attempts"] = attempt + 1
        result["reflected"] = attempt > 0
        if attempt > 0:
            result["final_critique"] = {
                "verdict": critique.verdict.value,
                "confidence": critique.confidence,
                "issues": critique.issues,
            }

        return result


def create_reflection_engine(api_base: str = "http://localhost:4000") -> ReflectionEngine:
    """Create a ReflectionEngine with default model factory.

    Args:
        api_base: LiteLLM proxy URL

    Returns:
        Configured ReflectionEngine
    """
    from .models import create_model

    def model_factory(model_name: str):
        model = create_model(model_name, api_base)
        return lambda prompt: model([{"role": "user", "content": prompt}])

    return ReflectionEngine(model_factory)
