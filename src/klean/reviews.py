"""K-LEAN Review Operations.

Cross-platform code review functionality using LiteLLM proxy.
Replaces shell scripts: quick-review.sh, consensus-review.sh, second-opinion.sh

Features:
- Async HTTP calls using httpx for parallel model queries
- Handles both regular and thinking models (content/reasoning_content)
- Automatic <think> tag stripping for models like deepseek-r1
- Health check with automatic fallback to healthy models
"""

from __future__ import annotations

import asyncio
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import httpx

# LiteLLM proxy default
LITELLM_URL = "http://localhost:4000"


@dataclass
class ReviewResult:
    """Result from a single review."""

    model: str
    content: str
    success: bool
    error: str | None = None
    duration_ms: int = 0


@dataclass
class ConsensusResult:
    """Result from consensus review with multiple models."""

    results: list[ReviewResult] = field(default_factory=list)
    total_duration_ms: int = 0
    successful_count: int = 0
    failed_count: int = 0


# =============================================================================
# HTTP Client Helpers
# =============================================================================


async def _get_available_models(client: httpx.AsyncClient) -> list[str]:
    """Get list of available models from LiteLLM.

    Args:
        client: Async HTTP client.

    Returns:
        List of model IDs.
    """
    try:
        response = await client.get(f"{LITELLM_URL}/models", timeout=5.0)
        response.raise_for_status()
        data = response.json()
        return [m["id"] for m in data.get("data", [])]
    except Exception:
        return []


async def _check_model_health(client: httpx.AsyncClient, model: str) -> bool:
    """Check if a model is healthy by sending a test request.

    Args:
        client: Async HTTP client.
        model: Model ID to check.

    Returns:
        True if model responds successfully.
    """
    try:
        response = await client.post(
            f"{LITELLM_URL}/chat/completions",
            json={
                "model": model,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 5,
            },
            timeout=10.0,
        )
        return response.status_code == 200
    except Exception:
        return False


async def _get_healthy_models(client: httpx.AsyncClient, count: int = 5) -> list[str]:
    """Get list of healthy models.

    Args:
        client: Async HTTP client.
        count: Maximum number of models to return.

    Returns:
        List of healthy model IDs.
    """
    models = await _get_available_models(client)
    healthy = []

    # Check models in parallel
    async def check_one(model: str) -> tuple[str, bool]:
        is_healthy = await _check_model_health(client, model)
        return model, is_healthy

    results = await asyncio.gather(*[check_one(m) for m in models[: count * 2]])

    for model, is_healthy in results:
        if is_healthy and len(healthy) < count:
            healthy.append(model)

    return healthy


def _extract_content(response_json: dict) -> str:
    """Extract content from LLM response, handling thinking models.

    Args:
        response_json: Raw JSON response from LiteLLM.

    Returns:
        Extracted content string.
    """
    try:
        choices = response_json.get("choices", [])
        if not choices:
            return ""

        message = choices[0].get("message", {})

        # Try regular content first
        content = message.get("content")
        if content:
            return _strip_think_tags(content)

        # Fallback to reasoning_content for thinking models
        content = message.get("reasoning_content", "")
        return _strip_think_tags(content)
    except Exception:
        return ""


def _strip_think_tags(content: str) -> str:
    """Strip <think>...</think> tags from model output.

    Args:
        content: Raw content string.

    Returns:
        Content with think tags removed.
    """
    # Use regex with DOTALL to handle multiline
    return re.sub(r"<think>.*?</think>\s*", "", content, flags=re.DOTALL).strip()


# =============================================================================
# Review Functions
# =============================================================================


async def quick_review(
    model: str,
    focus: str,
    context: str,
    system_prompt: str = "Concise code reviewer.",
    timeout: float = 60.0,
) -> ReviewResult:
    """Perform a quick review with a single model.

    Args:
        model: Model ID to use.
        focus: Review focus area.
        context: Code context (diff, code snippet, etc.).
        system_prompt: System prompt for the model.
        timeout: Request timeout in seconds.

    Returns:
        ReviewResult with model response.
    """
    start_time = datetime.now()

    prompt = f"""Review this code for: {focus}

CODE:
{context}

Provide: Grade (A-F), Risk, Issues, Verdict (APPROVE/REQUEST_CHANGES)"""

    async with httpx.AsyncClient() as client:
        # Check model health first
        if not await _check_model_health(client, model):
            # Try to find a healthy fallback
            healthy = await _get_healthy_models(client, count=1)
            if healthy:
                model = healthy[0]
            else:
                return ReviewResult(
                    model=model,
                    content="",
                    success=False,
                    error="No healthy models available",
                    duration_ms=0,
                )

        try:
            response = await client.post(
                f"{LITELLM_URL}/chat/completions",
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.3,
                    "max_tokens": 10000,
                },
                timeout=timeout,
            )
            response.raise_for_status()
            content = _extract_content(response.json())

            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            return ReviewResult(
                model=model,
                content=content,
                success=bool(content),
                error=None if content else "Empty response",
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
            return ReviewResult(
                model=model,
                content="",
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )


async def consensus_review(
    focus: str,
    context: str,
    model_count: int = 5,
    system_prompt: str = "Concise code reviewer.",
    timeout: float = 120.0,
) -> ConsensusResult:
    """Perform parallel review with multiple models.

    Args:
        focus: Review focus area.
        context: Code context (diff, code snippet, etc.).
        model_count: Number of models to use.
        system_prompt: System prompt for all models.
        timeout: Request timeout per model.

    Returns:
        ConsensusResult with all model responses.
    """
    start_time = datetime.now()

    prompt = f"""Review this code for: {focus}

CODE:
{context}

Provide: Grade (A-F), Risk, Top 3 Issues, Verdict"""

    async with httpx.AsyncClient() as client:
        # Get healthy models
        healthy_models = await _get_healthy_models(client, count=model_count)

        if not healthy_models:
            return ConsensusResult(
                results=[
                    ReviewResult(
                        model="none",
                        content="",
                        success=False,
                        error="No healthy models available",
                    )
                ],
                total_duration_ms=0,
                successful_count=0,
                failed_count=1,
            )

        # Query all models in parallel
        async def query_model(model: str) -> ReviewResult:
            model_start = datetime.now()
            try:
                response = await client.post(
                    f"{LITELLM_URL}/chat/completions",
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": prompt},
                        ],
                        "temperature": 0.3,
                        "max_tokens": 10000,
                    },
                    timeout=timeout,
                )
                response.raise_for_status()
                content = _extract_content(response.json())
                duration_ms = int((datetime.now() - model_start).total_seconds() * 1000)

                return ReviewResult(
                    model=model,
                    content=content,
                    success=bool(content),
                    error=None if content else "Empty response",
                    duration_ms=duration_ms,
                )
            except Exception as e:
                duration_ms = int((datetime.now() - model_start).total_seconds() * 1000)
                return ReviewResult(
                    model=model,
                    content="",
                    success=False,
                    error=str(e),
                    duration_ms=duration_ms,
                )

        results = await asyncio.gather(*[query_model(m) for m in healthy_models])
        total_duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        return ConsensusResult(
            results=list(results),
            total_duration_ms=total_duration_ms,
            successful_count=sum(1 for r in results if r.success),
            failed_count=sum(1 for r in results if not r.success),
        )


async def second_opinion(
    focus: str,
    context: str,
    primary_model: str = "deepseek-r1",
    fallback_models: list[str] | None = None,
    system_prompt: str = "Concise code reviewer.",
    timeout: float = 60.0,
) -> ReviewResult:
    """Get a second opinion with fallback to other models.

    Tries primary model first, falls back to others if unhealthy.

    Args:
        focus: Review focus area.
        context: Code context.
        primary_model: Preferred model to try first.
        fallback_models: List of fallback models to try.
        system_prompt: System prompt for the model.
        timeout: Request timeout.

    Returns:
        ReviewResult from first successful model.
    """
    if fallback_models is None:
        fallback_models = ["qwen3-coder", "kimi-k2", "glm-4.6-thinking"]

    models_to_try = [primary_model] + fallback_models

    async with httpx.AsyncClient() as client:
        for model in models_to_try:
            if await _check_model_health(client, model):
                result = await quick_review(
                    model=model,
                    focus=focus,
                    context=context,
                    system_prompt=system_prompt,
                    timeout=timeout,
                )
                if result.success:
                    return result

        # All models failed
        return ReviewResult(
            model="none",
            content="",
            success=False,
            error="All models unavailable",
            duration_ms=0,
        )


# =============================================================================
# Context Helpers
# =============================================================================


def get_git_diff(work_dir: Path | None = None, max_lines: int = 300) -> str:
    """Get git diff for review context.

    Args:
        work_dir: Working directory (defaults to cwd).
        max_lines: Maximum lines to include.

    Returns:
        Git diff string or fallback message.
    """
    cwd = str(work_dir) if work_dir else None

    # Try HEAD~1..HEAD first
    try:
        result = subprocess.run(
            ["git", "diff", "HEAD~1..HEAD"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split("\n")
            return "\n".join(lines[:max_lines])
    except Exception:
        pass

    # Fallback to unstaged diff
    try:
        result = subprocess.run(
            ["git", "diff"],
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split("\n")
            return "\n".join(lines[:max_lines])
    except Exception:
        pass

    return "No git changes found."


def format_review_markdown(
    result: ReviewResult | ConsensusResult,
    focus: str,
    work_dir: Path | None = None,
) -> str:
    """Format review result as markdown.

    Args:
        result: Review result to format.
        focus: Review focus area.
        work_dir: Working directory for header.

    Returns:
        Formatted markdown string.
    """
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    directory = str(work_dir) if work_dir else "."

    if isinstance(result, ReviewResult):
        return f"""# Quick Review: {focus}

**Model:** {result.model}
**Date:** {now}
**Directory:** {directory}
**Duration:** {result.duration_ms}ms

---

{result.content}
"""

    # ConsensusResult
    models = ", ".join(r.model for r in result.results if r.success)
    sections = []

    for r in result.results:
        if r.success:
            sections.append(f"## {r.model}\n\n{r.content}")

    return f"""# Consensus Review: {focus}

**Date:** {now}
**Directory:** {directory}
**Models:** {models}
**Duration:** {result.total_duration_ms}ms
**Success:** {result.successful_count}/{result.successful_count + result.failed_count}

---

{chr(10).join(sections)}
"""


# =============================================================================
# Sync Wrappers for CLI
# =============================================================================


def run_quick_review(
    model: str,
    focus: str,
    context: str,
    system_prompt: str = "Concise code reviewer.",
) -> ReviewResult:
    """Synchronous wrapper for quick_review.

    Args:
        model: Model ID to use.
        focus: Review focus area.
        context: Code context.
        system_prompt: System prompt.

    Returns:
        ReviewResult.
    """
    return asyncio.run(quick_review(model, focus, context, system_prompt))


def run_consensus_review(
    focus: str,
    context: str,
    model_count: int = 5,
    system_prompt: str = "Concise code reviewer.",
) -> ConsensusResult:
    """Synchronous wrapper for consensus_review.

    Args:
        focus: Review focus area.
        context: Code context.
        model_count: Number of models.
        system_prompt: System prompt.

    Returns:
        ConsensusResult.
    """
    return asyncio.run(consensus_review(focus, context, model_count, system_prompt))


def run_second_opinion(
    focus: str,
    context: str,
    primary_model: str = "deepseek-r1",
) -> ReviewResult:
    """Synchronous wrapper for second_opinion.

    Args:
        focus: Review focus area.
        context: Code context.
        primary_model: Preferred model.

    Returns:
        ReviewResult.
    """
    return asyncio.run(second_opinion(focus, context, primary_model))
