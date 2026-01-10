#!/usr/bin/env python3
"""
K-LEAN v3 Core Module
Multi-model code review system with Claude Agent SDK integration
"""

import asyncio
import json
import os
import re
import sys
import time
import urllib.request
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Optional

# LiteLLM for LLM calls (replaces httpx for better telemetry)
import litellm
import yaml

# Claude Agent SDK
try:
    from claude_agent_sdk import ClaudeSDKClient, query  # noqa: F401

    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False

# Suppress Pydantic serialization warnings from LiteLLM
# These occur when response fields don't match Pydantic models exactly
warnings.filterwarnings("ignore", message="Pydantic serializer warnings", category=UserWarning)

# ------------------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------------------

CONFIG_PATH = Path.home() / ".claude" / "kln" / "config.yaml"
CACHE_DIR = Path.home() / ".claude" / "kln" / "cache"
PROMPTS_DIR = Path.home() / ".claude" / "kln" / "prompts"


def load_config() -> dict:
    """Load K-LEAN configuration"""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return yaml.safe_load(f)
    return {
        "litellm": {"endpoint": "http://localhost:4000", "timeout": 120},
        "models": {"default_single": "auto", "default_multi": 3},
        "routing": {},
        "cache": {"latency_file": str(CACHE_DIR / "latency.json"), "max_age_hours": 24},
    }


CONFIG = load_config()

# ------------------------------------------------------------------------------
# LLM Client (litellm-based, replaces httpx)
# ------------------------------------------------------------------------------


class LLMClient:
    """Unified LLM client using litellm for full telemetry support.

    Replaces direct httpx calls with litellm.completion/acompletion.
    Benefits:
    - Full Phoenix telemetry (prompts, responses, tokens, reasoning)
    - Automatic reasoning_content extraction for thinking models
    - Consistent error handling across providers
    """

    def __init__(self, endpoint: str = None):
        self.endpoint = endpoint or CONFIG["litellm"]["endpoint"]
        self.timeout = CONFIG["litellm"].get("timeout", 120)
        self._configure_litellm()

    def _configure_litellm(self):
        """Configure litellm to use our LiteLLM proxy."""
        litellm.api_base = self.endpoint
        litellm.drop_params = True  # Handle model differences gracefully

    def _proxy_model(self, model: str) -> str:
        """Add openai/ prefix for proxy routing.

        LiteLLM library needs this prefix to route to custom endpoints.
        """
        if model.startswith("openai/"):
            return model
        return f"openai/{model}"

    def discover_models(self) -> list:
        """Discover available models from LiteLLM proxy."""
        try:
            req = urllib.request.Request(
                f"{self.endpoint}/models", headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            return [m["id"] for m in data.get("data", [])]
        except Exception as e:
            print(f"Model discovery failed: {e}", file=sys.stderr)
            return []

    def enable_telemetry(self, project_name: str):
        """Enable Phoenix telemetry for full traces."""
        os.environ["PHOENIX_PROJECT_NAME"] = project_name
        os.environ.setdefault("PHOENIX_COLLECTOR_HTTP_ENDPOINT", "http://localhost:6006")
        litellm.callbacks = ["arize_phoenix"]
        print(f"Telemetry enabled - project: {project_name}")
        print("View at http://localhost:6006")

    def completion(self, model: str, messages: list, **kwargs) -> dict:
        """Sync LLM completion with full response extraction."""
        proxy_model = self._proxy_model(model)

        response = litellm.completion(
            model=proxy_model,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", 4000),
            temperature=kwargs.get("temperature", 0.7),
            timeout=kwargs.get("timeout", self.timeout),
            api_key="not-needed",  # Proxy handles auth
        )

        message = response.choices[0].message
        return {
            "content": message.content or "",
            "reasoning_content": getattr(message, "reasoning_content", None),
            "thinking_blocks": getattr(message, "thinking_blocks", None),
            "usage": dict(response.usage) if response.usage else {},
            "model": response.model,
        }

    async def acompletion(self, model: str, messages: list, **kwargs) -> dict:
        """Async LLM completion for parallel calls."""
        proxy_model = self._proxy_model(model)

        response = await litellm.acompletion(
            model=proxy_model,
            messages=messages,
            max_tokens=kwargs.get("max_tokens", 4000),
            temperature=kwargs.get("temperature", 0.7),
            timeout=kwargs.get("timeout", self.timeout),
            api_key="not-needed",
        )

        message = response.choices[0].message
        return {
            "content": message.content or "",
            "reasoning_content": getattr(message, "reasoning_content", None),
            "thinking_blocks": getattr(message, "thinking_blocks", None),
            "usage": dict(response.usage) if response.usage else {},
            "model": response.model,
        }


# ------------------------------------------------------------------------------
# Model Discovery & Resolution
# ------------------------------------------------------------------------------


@dataclass
class ModelInfo:
    """Model information from discovery"""

    id: str
    latency_ms: Optional[float] = None
    available: bool = True
    last_tested: Optional[datetime] = None


class ModelResolver:
    """Dynamic model discovery and selection"""

    def __init__(self):
        self.endpoint = CONFIG["litellm"]["endpoint"]
        self.cache_file = Path(
            os.path.expanduser(CONFIG["cache"].get("latency_file", str(CACHE_DIR / "latency.json")))
        )
        self.cache_max_age = timedelta(hours=CONFIG["cache"].get("max_age_hours", 24))
        self._models: dict[str, ModelInfo] = {}
        self._llm_client = LLMClient(self.endpoint)
        self._load_cache()

    def _load_cache(self):
        """Load latency cache from disk"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    data = json.load(f)
                for model_id, info in data.get("models", {}).items():
                    self._models[model_id] = ModelInfo(
                        id=model_id,
                        latency_ms=info.get("latency_ms"),
                        available=info.get("available", True),
                        last_tested=datetime.fromisoformat(info["last_tested"])
                        if info.get("last_tested")
                        else None,
                    )
            except Exception:
                pass

    def _save_cache(self):
        """Save latency cache to disk"""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "updated": datetime.now().isoformat(),
            "models": {
                m.id: {
                    "latency_ms": m.latency_ms,
                    "available": m.available,
                    "last_tested": m.last_tested.isoformat() if m.last_tested else None,
                }
                for m in self._models.values()
            },
        }
        with open(self.cache_file, "w") as f:
            json.dump(data, f, indent=2)

    def discover_models(self) -> list[str]:
        """Discover available models from LiteLLM"""
        try:
            models = self._llm_client.discover_models()

            # Update cache with discovered models
            for model_id in models:
                if model_id not in self._models:
                    self._models[model_id] = ModelInfo(id=model_id)
                self._models[model_id].available = True

            return models
        except Exception as e:
            print(f"Warning: Could not discover models: {e}", file=sys.stderr)
            return list(self._models.keys())

    def test_latency(self, model_id: str) -> Optional[float]:
        """Test model latency with a simple query"""
        try:
            start = time.time()
            self._llm_client.completion(
                model_id, [{"role": "user", "content": "Hi"}], max_tokens=5, timeout=30
            )
            latency = (time.time() - start) * 1000

            # Update cache
            if model_id not in self._models:
                self._models[model_id] = ModelInfo(id=model_id)
            self._models[model_id].latency_ms = latency
            self._models[model_id].last_tested = datetime.now()
            self._save_cache()

            return latency
        except Exception:
            return None

    def get_fastest(self, count: int = 1, exclude: list[str] = None) -> list[str]:
        """Get fastest models by cached latency"""
        exclude = exclude or []
        available = [
            m for m in self._models.values() if m.available and m.latency_ms and m.id not in exclude
        ]
        sorted_models = sorted(available, key=lambda m: m.latency_ms or float("inf"))
        return [m.id for m in sorted_models[:count]]

    def select_models(
        self,
        count: int = 1,
        task: str = "",
        prefer_fastest: bool = True,
        ensure_diversity: bool = True,
    ) -> list[str]:
        """Smart model selection based on task and latency"""
        available = self.discover_models()
        if not available:
            return []

        # Apply routing boosts based on task keywords
        routing = CONFIG.get("routing", {})
        boosted = set()
        task_lower = task.lower()
        for keyword, models in routing.items():
            if keyword in task_lower:
                boosted.update(models)

        # Score models
        scores = {}
        for model_id in available:
            score = 0
            info = self._models.get(model_id)

            # Latency score (lower is better)
            if prefer_fastest and info and info.latency_ms:
                score -= info.latency_ms / 1000  # Normalize to seconds

            # Boost score for routing matches
            if model_id in boosted:
                score += 10

            # Diversity: prefer thinking models for some slots
            if ensure_diversity and count > 1:
                if "thinking" in model_id:
                    score += 2

            scores[model_id] = score

        # Sort and select
        sorted_models = sorted(available, key=lambda m: scores.get(m, 0), reverse=True)

        # Ensure diversity if requested
        if ensure_diversity and count > 1:
            selected = []
            thinking_count = 0
            for model_id in sorted_models:
                is_thinking = "thinking" in model_id
                # Limit thinking models to half
                if is_thinking and thinking_count >= count // 2:
                    continue
                selected.append(model_id)
                if is_thinking:
                    thinking_count += 1
                if len(selected) >= count:
                    break
            return selected

        return sorted_models[:count]


# ------------------------------------------------------------------------------
# Review Execution
# ------------------------------------------------------------------------------


class ReviewEngine:
    """Execute reviews via LiteLLM or Claude SDK"""

    def __init__(self):
        self.resolver = ModelResolver()
        self.endpoint = CONFIG["litellm"]["endpoint"]
        self.timeout = CONFIG["litellm"].get("timeout", 120)
        self._available_models = None
        self._llm_client = LLMClient(self.endpoint)

    def get_available_models(self) -> list[str]:
        """Get available models from LiteLLM (cached)"""
        if self._available_models is None:
            self._available_models = self.resolver.discover_models()
        return self._available_models

    def resolve_model_name(self, model: str) -> str:
        """Resolve model name using auto-discovery - match by substring"""
        if not model:
            return self._get_default_model()

        model_lower = model.lower()
        available = self.get_available_models()

        # Exact match first
        for m in available:
            if m.lower() == model_lower:
                return m

        # Substring match (e.g., "deepseek" matches "deepseek-v3-thinking")
        matches = [m for m in available if model_lower in m.lower()]
        if len(matches) == 1:
            return matches[0]
        elif len(matches) > 1:
            # Prefer thinking models for reasoning tasks
            thinking = [m for m in matches if "thinking" in m.lower()]
            if thinking:
                return thinking[0]
            return matches[0]

        # No match - return as-is (let LiteLLM handle the error)
        return model

    def _get_default_model(self) -> str:
        """Get default model - prefer deepseek-v3-thinking for reasoning"""
        available = self.get_available_models()
        # Prefer deepseek-v3-thinking for rethink tasks
        for m in available:
            if "deepseek-v3-thinking" in m.lower():
                return m
        # Fallback to first available
        return available[0] if available else "deepseek-v3-thinking"

    def _load_prompt(self, focus: str, context: str = "", output_format: str = "text") -> str:
        """Load and fill review prompt template with format selection"""
        prompt_file = PROMPTS_DIR / "review.md"
        if prompt_file.exists():
            template = prompt_file.read_text()
        else:
            template = (
                "Review the code with focus on: {{FOCUS}}\n\n{{OUTPUT_FORMAT}}\n\n{{CONTEXT}}"
            )

        # Load format template
        format_file = PROMPTS_DIR / f"format-{output_format}.md"
        if format_file.exists():
            format_template = format_file.read_text()
        else:
            format_template = "Respond with GRADE, RISK, and findings."

        return (
            template.replace("{{FOCUS}}", focus)
            .replace("{{OUTPUT_FORMAT}}", format_template)
            .replace("{{CONTEXT}}", context)
        )

    def quick_review(self, focus: str, context: str = "", model: str = "auto") -> dict:
        """Quick review via LiteLLM API (single model)"""

        # Resolve model
        if model == "auto":
            models = self.resolver.select_models(count=1, task=focus, prefer_fastest=True)
            model = models[0] if models else "qwen3-coder"

        prompt = self._load_prompt(focus, context)

        try:
            start = time.time()
            result = self._llm_client.completion(
                model, [{"role": "user", "content": prompt}], max_tokens=4000, timeout=self.timeout
            )
            latency = (time.time() - start) * 1000

            # Extract response (handle thinking models)
            content = result["content"] or result.get("reasoning_content") or ""

            return {
                "success": True,
                "model": model,
                "latency_ms": latency,
                "content": content,
                "reasoning_content": result.get("reasoning_content"),
                "usage": result.get("usage", {}),
            }
        except Exception as e:
            return {"success": False, "model": model, "error": str(e)}

    async def multi_review(
        self,
        focus: str,
        context: str = "",
        model_count: int = 3,
        models: list[str] = None,
        output_format: str = "json",
    ) -> dict:
        """Multi-model review with parallel execution"""

        # Resolve models
        if not models:
            models = self.resolver.select_models(
                count=model_count, task=focus, ensure_diversity=True
            )

        # Use JSON format for multi-model to enable proper consensus
        prompt = self._load_prompt(focus, context, output_format=output_format)

        async def run_single(model: str) -> dict:
            """Run single model review async"""
            try:
                start = time.time()
                result = await self._llm_client.acompletion(
                    model,
                    [{"role": "user", "content": prompt}],
                    max_tokens=4000,
                    timeout=self.timeout,
                )
                latency = (time.time() - start) * 1000

                # Extract response
                content = result["content"] or result.get("reasoning_content") or ""

                return {
                    "success": True,
                    "model": model,
                    "latency_ms": latency,
                    "content": content,
                    "reasoning_content": result.get("reasoning_content"),
                }
            except Exception as e:
                return {"success": False, "model": model, "error": str(e)}

        # Run all models in parallel
        start_total = time.time()
        results = await asyncio.gather(*[run_single(m) for m in models])
        total_time = (time.time() - start_total) * 1000

        # Aggregate results
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        # Find consensus issues (mentioned by 2+ models)
        all_issues = []
        for r in successful:
            # Simple extraction of issues (could be smarter)
            content = r.get("content", "")
            if "CRITICAL" in content:
                all_issues.append(("critical", r["model"], content))

        return {
            "success": len(successful) > 0,
            "models_used": [r["model"] for r in successful],
            "models_failed": [r["model"] for r in failed],
            "total_time_ms": total_time,
            "individual_results": results,
            "consensus": self._find_consensus(successful),
        }

    def _parse_json_review(self, content: str) -> Optional[dict[str, Any]]:
        """Extract and parse JSON from model response"""
        # Try direct JSON parse first
        try:
            return json.loads(content.strip())
        except json.JSONDecodeError:
            pass

        # Try to find JSON block in markdown
        json_match = re.search(r"```json?\s*([\s\S]*?)\s*```", content)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # Try to find raw JSON object
        brace_match = re.search(r"\{[\s\S]*\}", content)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        return None

    def _extract_text_review(self, content: str) -> dict[str, Any]:
        """Fallback: extract review data from text format"""
        result = {"grade": None, "risk": None, "findings": [], "summary": ""}

        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("GRADE:"):
                result["grade"] = line.split(":")[1].strip().split()[0]
            elif line.startswith("RISK:"):
                result["risk"] = line.split(":")[1].strip().split()[0]

        # Extract critical issues section
        if "CRITICAL ISSUES:" in content or "CRITICAL:" in content:
            result["has_critical"] = True

        return result

    def _find_consensus(self, results: list[dict]) -> dict[str, Any]:
        """Find consensus across multiple model reviews with JSON support"""
        parsed_results = []
        grades = []
        risks = []
        all_findings = []

        for r in results:
            content = r.get("content", "")
            model = r.get("model", "unknown")

            # Try JSON first, fallback to text
            parsed = self._parse_json_review(content)
            if parsed:
                parsed["_model"] = model
                parsed["_format"] = "json"
                parsed_results.append(parsed)

                if parsed.get("grade"):
                    grades.append(parsed["grade"])
                if parsed.get("risk"):
                    risks.append(parsed["risk"])

                # Collect findings with model attribution
                for finding in parsed.get("findings", []):
                    finding["_model"] = model
                    all_findings.append(finding)
            else:
                # Fallback to text extraction
                parsed = self._extract_text_review(content)
                parsed["_model"] = model
                parsed["_format"] = "text"
                parsed_results.append(parsed)

                if parsed.get("grade"):
                    grades.append(parsed["grade"])
                if parsed.get("risk"):
                    risks.append(parsed["risk"])

        # Calculate grade consensus
        grade_counts = {}
        for g in grades:
            grade_counts[g] = grade_counts.get(g, 0) + 1
        consensus_grade = max(grade_counts, key=grade_counts.get) if grade_counts else None

        # Calculate risk consensus
        risk_counts = {}
        for r in risks:
            risk_counts[r] = risk_counts.get(r, 0) + 1
        consensus_risk = max(risk_counts, key=risk_counts.get) if risk_counts else None

        # Group findings by location similarity
        finding_groups = self._group_similar_findings(all_findings)

        # Classify by confidence
        total_models = len(results)
        high_confidence = []  # All models agree
        medium_confidence = []  # 2+ models agree
        low_confidence = []  # Only 1 model found

        for group in finding_groups:
            models_found = len({f.get("_model") for f in group["findings"]})
            representative = group["findings"][0]  # Use first as representative

            if models_found == total_models:
                high_confidence.append(
                    {
                        "issue": representative.get("issue", ""),
                        "location": representative.get("location", ""),
                        "severity": representative.get("severity", ""),
                        "models": [f.get("_model") for f in group["findings"]],
                    }
                )
            elif models_found >= 2:
                medium_confidence.append(
                    {
                        "issue": representative.get("issue", ""),
                        "location": representative.get("location", ""),
                        "severity": representative.get("severity", ""),
                        "models": [f.get("_model") for f in group["findings"]],
                    }
                )
            else:
                low_confidence.append(
                    {
                        "issue": representative.get("issue", ""),
                        "location": representative.get("location", ""),
                        "severity": representative.get("severity", ""),
                        "models": [f.get("_model") for f in group["findings"]],
                    }
                )

        return {
            "grades": grades,
            "risks": risks,
            "consensus_grade": consensus_grade,
            "consensus_risk": consensus_risk,
            "grade_agreement": len(set(grades)) == 1 if grades else False,
            "risk_agreement": len(set(risks)) == 1 if risks else False,
            "high_confidence": high_confidence,
            "medium_confidence": medium_confidence,
            "low_confidence": low_confidence,
            "total_findings": len(all_findings),
            "parsed_results": parsed_results,
        }

    def _group_similar_findings(self, findings: list[dict]) -> list[dict]:
        """Group findings by location and issue similarity"""
        groups = []

        for finding in findings:
            location = finding.get("location", "").lower()
            issue = finding.get("issue", "").lower()

            # Try to find existing group
            matched = False
            for group in groups:
                ref_location = group["location"].lower()
                ref_issue = group["issue"].lower()

                # Match by same file:line OR high text similarity
                if location and ref_location:
                    # Same location
                    if location == ref_location:
                        group["findings"].append(finding)
                        matched = True
                        break
                    # Same file, similar issue text
                    if location.split(":")[0] == ref_location.split(":")[0]:
                        # Simple word overlap check
                        words1 = set(issue.split())
                        words2 = set(ref_issue.split())
                        overlap = len(words1 & words2) / max(len(words1 | words2), 1)
                        if overlap > 0.5:
                            group["findings"].append(finding)
                            matched = True
                            break

            if not matched:
                groups.append(
                    {
                        "location": finding.get("location", ""),
                        "issue": finding.get("issue", ""),
                        "findings": [finding],
                    }
                )

        return groups

    # --------------------------------------------------------------------------
    # Rethink - Fresh Perspective on Stuck Debugging
    # --------------------------------------------------------------------------

    def _load_rethink_prompt(self) -> str:
        """Load the rethink/contrarian system prompt"""
        prompt_file = PROMPTS_DIR / "rethink.md"
        if prompt_file.exists():
            return prompt_file.read_text()
        # Fallback minimal prompt
        return """You are a contrarian debugging expert. Suggest 3-5 approaches the developer
probably DISMISSED or DIDN'T CONSIDER. For each: explain why untried, why it might work,
and give a concrete first step. NEVER suggest things already tried."""

    def rethink_single(self, context: str, model: str = "") -> dict:
        """Get fresh perspective from a single model"""
        model = self.resolve_model_name(model)
        system_prompt = self._load_rethink_prompt()

        try:
            start = time.time()
            result = self._llm_client.completion(
                model,
                [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context},
                ],
                max_tokens=4000,
                temperature=0.7,  # Higher temp for more creative ideas
                timeout=self.timeout,
            )
            latency = (time.time() - start) * 1000

            # Extract response (handle thinking models)
            content = result["content"] or result.get("reasoning_content") or ""

            return {
                "success": True,
                "model": model,
                "latency_ms": latency,
                "content": content,
                "reasoning_content": result.get("reasoning_content"),
                "ideas": self._parse_rethink_ideas(content),
            }
        except Exception as e:
            return {"success": False, "model": model, "error": str(e)}

    async def rethink_multi(
        self, context: str, model_count: int = 5, models: list[str] = None
    ) -> dict:
        """Get fresh perspectives from multiple models in parallel"""

        # Resolve models
        if models:
            models = [self.resolve_model_name(m) for m in models]
        else:
            # Auto-select diverse models
            available = self.resolver.discover_models()
            if len(available) >= model_count:
                # Prefer diversity - mix of thinking and fast models
                import random

                random.shuffle(available)
                models = available[:model_count]
            else:
                models = available

        system_prompt = self._load_rethink_prompt()

        async def run_single(model: str) -> dict:
            """Run single model rethink async"""
            try:
                start = time.time()
                result = await self._llm_client.acompletion(
                    model,
                    [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": context},
                    ],
                    max_tokens=4000,
                    temperature=0.7,
                    timeout=self.timeout,
                )
                latency = (time.time() - start) * 1000

                content = result["content"] or result.get("reasoning_content") or ""

                return {
                    "success": True,
                    "model": model,
                    "latency_ms": latency,
                    "content": content,
                    "reasoning_content": result.get("reasoning_content"),
                    "ideas": self._parse_rethink_ideas(content),
                }
            except Exception as e:
                return {"success": False, "model": model, "error": str(e)}

        # Run all models in parallel
        start_total = time.time()
        results = await asyncio.gather(*[run_single(m) for m in models])
        total_time = (time.time() - start_total) * 1000

        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        # Aggregate and rank ideas
        all_ideas = []
        for r in successful:
            for idea in r.get("ideas", []):
                idea["_model"] = r["model"]
                all_ideas.append(idea)

        # Dedupe and rank
        ranked_ideas = self._rank_rethink_ideas(all_ideas)

        return {
            "success": len(successful) > 0,
            "models_used": [r["model"] for r in successful],
            "models_failed": [r["model"] for r in failed],
            "total_time_ms": total_time,
            "individual_results": results,
            "all_ideas": all_ideas,
            "ranked_ideas": ranked_ideas,
        }

    def _parse_rethink_ideas(self, content: str) -> list[dict]:
        """Parse ideas from model response"""
        ideas = []

        # Look for numbered or headed sections
        # Pattern: ### Approach N: or **Approach N**: or just numbered
        sections = re.split(
            r"(?:###\s*Approach\s*\d+[:\s]|(?:\*\*)?Approach\s*\d+[:\s*]|\n\d+\.\s+(?=\*\*|[A-Z]))",
            content,
        )

        for i, section in enumerate(sections[1:], 1):  # Skip first empty section
            idea = {"id": i, "raw": section.strip()}

            # Extract "Why Untried"
            untried_match = re.search(
                r"\*\*Why\s+(?:Untried|You\s+Probably|Not\s+Tried)[:\*]*\s*([^\n*]+(?:\n(?!\*\*)[^\n]+)*)",
                section,
                re.I,
            )
            if untried_match:
                idea["why_untried"] = untried_match.group(1).strip()

            # Extract "Why It Might Work"
            work_match = re.search(
                r"\*\*Why\s+(?:It\s+)?Might\s+Work[:\*]*\s*([^\n*]+(?:\n(?!\*\*)[^\n]+)*)",
                section,
                re.I,
            )
            if work_match:
                idea["why_might_work"] = work_match.group(1).strip()

            # Extract "First Step"
            step_match = re.search(
                r"\*\*First\s+Step[:\*]*\s*([^\n*]+(?:\n(?!\*\*)[^\n]+)*)", section, re.I
            )
            if step_match:
                idea["first_step"] = step_match.group(1).strip()

            # Extract approach title (first line or bold text)
            title_match = re.search(r"^[:\s]*\**([^\n*]+)", section)
            if title_match:
                idea["approach"] = title_match.group(1).strip()

            if idea.get("approach") or idea.get("first_step"):
                ideas.append(idea)

        return ideas

    def _rank_rethink_ideas(self, ideas: list[dict]) -> list[dict]:
        """Rank ideas by novelty and actionability, dedupe similar ones"""
        if not ideas:
            return []

        # Score each idea
        for idea in ideas:
            score = 0

            # Actionability: Has concrete first step
            if idea.get("first_step"):
                step = idea["first_step"].lower()
                # Bonus for specific commands/actions
                if any(
                    x in step
                    for x in ["run", "check", "look", "grep", "cat", "echo", "print", "log"]
                ):
                    score += 3
                else:
                    score += 1

            # Novelty indicators
            if idea.get("why_untried"):
                score += 2
            if idea.get("why_might_work"):
                score += 2

            # Penalize vague suggestions
            approach = (idea.get("approach") or "").lower()
            if any(x in approach for x in ["check logs", "add logging", "debug more", "try again"]):
                score -= 2

            idea["_score"] = score

        # Dedupe by approach similarity
        seen_approaches = set()
        unique_ideas = []
        for idea in sorted(ideas, key=lambda x: x.get("_score", 0), reverse=True):
            approach = (idea.get("approach") or idea.get("first_step") or "").lower()
            # Simple word-based dedup
            words = set(approach.split()[:5])  # First 5 words
            words_key = frozenset(words)

            # Check for overlap with seen
            is_dupe = False
            for seen in seen_approaches:
                overlap = len(words & seen) / max(len(words | seen), 1)
                if overlap > 0.6:
                    is_dupe = True
                    break

            if not is_dupe:
                seen_approaches.add(words_key)
                unique_ideas.append(idea)

        return unique_ideas[:10]  # Top 10 unique ideas


# ------------------------------------------------------------------------------
# Deep Review with Claude SDK
# ------------------------------------------------------------------------------


async def deep_review_sdk(focus: str, cwd: str = None) -> dict:
    """Deep review using Claude Agent SDK with full tools"""
    if not SDK_AVAILABLE:
        return {"success": False, "error": "Claude Agent SDK not available"}

    cwd = cwd or os.getcwd()

    prompt = f"""Perform a thorough code review with focus on: {focus}

Use the available tools to:
1. Read relevant source files
2. Search for patterns and potential issues
3. Check for related code and dependencies

Provide a comprehensive review with:
- GRADE (A-F)
- RISK level (LOW/MEDIUM/HIGH/CRITICAL)
- Critical issues found
- Warnings
- Suggestions for improvement
"""

    try:
        # Use SDK query with tools
        result = await query(
            prompt=prompt,
            options={
                "cwd": cwd,
                "allowed_tools": ["Read", "Grep", "Glob", "Bash"],
                "max_turns": 20,
            },
        )

        return {"success": True, "method": "sdk", "result": result}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ------------------------------------------------------------------------------
# CLI Entry Points
# ------------------------------------------------------------------------------


def cli_quick(args):
    """CLI entry for quick review"""
    import argparse
    import select

    parser = argparse.ArgumentParser(description="Quick code review")
    parser.add_argument("focus", nargs="*", help="Review focus")
    parser.add_argument("-m", "--model", default="auto", help="Model to use")
    parser.add_argument("-o", "--output", choices=["text", "json", "markdown"], default="text")
    parser.add_argument("-c", "--context-file", help="File containing code to review")
    parser.add_argument("--telemetry", action="store_true", help="Enable Phoenix telemetry")
    parsed = parser.parse_args(args)

    focus = " ".join(parsed.focus) or "general code review"

    # Get context from file or stdin
    context = ""
    if parsed.context_file:
        try:
            with open(parsed.context_file) as f:
                context = f.read()
        except Exception as e:
            print(f"Error reading context file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Read from stdin if available
        if select.select([sys.stdin], [], [], 0.0)[0]:
            context = sys.stdin.read()

    engine = ReviewEngine()

    # Setup telemetry if requested (uses litellm.callbacks for full traces)
    if parsed.telemetry:
        engine._llm_client.enable_telemetry("kln-quick")

    result = engine.quick_review(focus, context=context, model=parsed.model)

    if parsed.output == "json":
        print(json.dumps(result, indent=2))
    else:
        if result["success"]:
            print(f"Model: {result['model']} ({result['latency_ms']:.0f}ms)\n")
            print(result["content"])
        else:
            print(f"Error: {result.get('error')}")


def cli_multi(args):
    """CLI entry for multi-model review"""
    import argparse
    import select

    parser = argparse.ArgumentParser(description="Multi-model review")
    parser.add_argument("focus", nargs="*", help="Review focus")
    parser.add_argument(
        "-n", "--models", default="3", help="Number of models OR comma-separated list"
    )
    parser.add_argument(
        "-m", "--model", action="append", help="Specific models (deprecated, use --models)"
    )
    parser.add_argument("-o", "--output", choices=["text", "json", "markdown"], default="text")
    parser.add_argument("-c", "--context-file", help="File containing code to review")
    parser.add_argument("--telemetry", action="store_true", help="Enable Phoenix telemetry")
    parsed = parser.parse_args(args)

    focus = " ".join(parsed.focus) or "general code review"

    # Get context from file or stdin
    context = ""
    if parsed.context_file:
        try:
            with open(parsed.context_file) as f:
                context = f.read()
        except Exception as e:
            print(f"Error reading context file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Read from stdin if available
        if select.select([sys.stdin], [], [], 0.0)[0]:
            context = sys.stdin.read()

    engine = ReviewEngine()

    # Setup telemetry if requested (uses litellm.callbacks for full traces)
    if parsed.telemetry:
        engine._llm_client.enable_telemetry("kln-multi")

    # Parse --models: integer OR comma-separated list
    model_count = 3
    specific_models = parsed.model or []

    if parsed.models:
        if "," in parsed.models:
            # Comma-separated list of models
            specific_models = [m.strip() for m in parsed.models.split(",")]
            model_count = len(specific_models)
        else:
            try:
                model_count = int(parsed.models)
            except ValueError:
                # Single model name
                specific_models = [parsed.models]
                model_count = 1

    result = asyncio.run(
        engine.multi_review(
            focus,
            context=context,
            model_count=model_count,
            models=specific_models if specific_models else None,
        )
    )

    if parsed.output == "json":
        print(json.dumps(result, indent=2))
    else:
        # Header
        print(f"\n{'=' * 60}")
        print(f"MULTI-MODEL REVIEW ({len(result['models_used'])} models)")
        print(f"{'=' * 60}")
        print(f"Focus: {focus}")
        print(f"Models: {', '.join(result['models_used'])}")
        print(f"Total time: {result['total_time_ms']:.0f}ms")

        # Consensus summary
        consensus = result.get("consensus", {})
        print(f"\n{'=' * 60}")
        print("CONSENSUS ANALYSIS")
        print(f"{'=' * 60}")

        # Grade consensus
        grades = consensus.get("grades", [])
        consensus_grade = consensus.get("consensus_grade", "N/A")
        grade_agree = (
            "unanimous"
            if consensus.get("grade_agreement")
            else f"{grades.count(consensus_grade)}/{len(grades)}"
        )
        print(f"\nGrade: {consensus_grade} ({grade_agree})")
        if grades:
            print(f"  Individual: {', '.join(grades)}")

        # Risk consensus
        risks = consensus.get("risks", [])
        consensus_risk = consensus.get("consensus_risk", "N/A")
        risk_agree = (
            "unanimous"
            if consensus.get("risk_agreement")
            else f"{risks.count(consensus_risk)}/{len(risks)}"
        )
        print(f"\nRisk: {consensus_risk} ({risk_agree})")
        if risks:
            print(f"  Individual: {', '.join(risks)}")

        # High confidence findings
        high_conf = consensus.get("high_confidence", [])
        if high_conf:
            print(f"\nHIGH CONFIDENCE (all {len(result['models_used'])} models agree):")
            for f in high_conf:
                print(
                    f"  [{f.get('severity', '?')}] {f.get('location', '?')}: {f.get('issue', '')[:60]}"
                )

        # Medium confidence findings
        med_conf = consensus.get("medium_confidence", [])
        if med_conf:
            print("\nMEDIUM CONFIDENCE (2+ models agree):")
            for f in med_conf:
                models = ", ".join(f.get("models", []))
                print(
                    f"  [{f.get('severity', '?')}] {f.get('location', '?')}: {f.get('issue', '')[:60]}"
                )
                print(f"    Found by: {models}")

        # Low confidence findings
        low_conf = consensus.get("low_confidence", [])
        if low_conf:
            print("\nLOW CONFIDENCE (single model - investigate):")
            for f in low_conf[:5]:  # Limit to 5
                models = ", ".join(f.get("models", []))
                print(
                    f"  [{f.get('severity', '?')}] {f.get('location', '?')}: {f.get('issue', '')[:60]}"
                )
                print(f"    Found by: {models}")
            if len(low_conf) > 5:
                print(f"  ... and {len(low_conf) - 5} more")

        # Individual reviews (collapsed)
        print(f"\n{'=' * 60}")
        print("INDIVIDUAL REVIEWS (use -o json for full details)")
        print(f"{'=' * 60}")
        for r in result["individual_results"]:
            if r["success"]:
                latency = r.get("latency_ms", 0)
                # Try to get grade from parsed result
                parsed = engine._parse_json_review(r.get("content", ""))
                grade = parsed.get("grade", "?") if parsed else "?"
                risk = parsed.get("risk", "?") if parsed else "?"
                findings_count = len(parsed.get("findings", [])) if parsed else "?"
                print(
                    f"  {r['model']:30} Grade:{grade} Risk:{risk} Findings:{findings_count} ({latency:.0f}ms)"
                )


def cli_rethink(args):
    """CLI entry for rethink - fresh perspective on stuck debugging"""
    import argparse

    parser = argparse.ArgumentParser(description="Get fresh debugging perspectives")
    parser.add_argument("focus", nargs="*", help="Optional focus/hint about the problem")
    parser.add_argument(
        "-n", "--models", default="5", help="Number of models OR specific model name"
    )
    parser.add_argument("-c", "--context-file", help="File containing debugging context")
    parser.add_argument("-o", "--output", choices=["text", "json"], default="text")
    parser.add_argument("--telemetry", action="store_true", help="Enable Phoenix telemetry")
    parsed = parser.parse_args(args)

    engine = ReviewEngine()

    # Setup telemetry if requested (uses litellm.callbacks for full traces)
    if parsed.telemetry:
        engine._llm_client.enable_telemetry("kln-rethink")

    # Get context from file or stdin
    context = ""
    if parsed.context_file:
        try:
            with open(parsed.context_file) as f:
                context = f.read()
        except Exception as e:
            print(f"Error reading context file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Read from stdin if available
        import select

        if select.select([sys.stdin], [], [], 0.0)[0]:
            context = sys.stdin.read()

    if not context:
        print("Error: No debugging context provided.", file=sys.stderr)
        print("Use --context-file or pipe context via stdin", file=sys.stderr)
        sys.exit(1)

    # Add focus to context if provided
    if parsed.focus:
        context += f"\n\nUser's Focus: {' '.join(parsed.focus)}"

    # Determine single vs multi model
    try:
        model_count = int(parsed.models)
        is_multi = True
    except ValueError:
        # It's a model name
        model_name = parsed.models
        is_multi = False

    if is_multi:
        result = asyncio.run(engine.rethink_multi(context, model_count=model_count))
    else:
        result = engine.rethink_single(context, model=model_name)

    if parsed.output == "json":
        print(json.dumps(result, indent=2))
    else:
        if is_multi:
            _print_rethink_multi_results(result)
        else:
            _print_rethink_single_results(result)


def _print_rethink_single_results(result):
    """Print results from single model rethink"""
    if not result["success"]:
        print(f"Error: {result.get('error')}", file=sys.stderr)
        return

    print(f"\n{'=' * 65}")
    print(f"FRESH PERSPECTIVES from {result['model']}")
    print(f"{'=' * 65}")
    print(f"Response time: {result['latency_ms']:.0f}ms\n")

    # Print raw content if no structured ideas parsed
    ideas = result.get("ideas", [])
    if not ideas:
        print(result.get("content", "No ideas generated"))
        return

    for i, idea in enumerate(ideas, 1):
        print(f"\n{'─' * 65}")
        print(f"IDEA #{i}: {idea.get('approach', 'Untitled')}")
        print(f"{'─' * 65}")

        if idea.get("why_untried"):
            print("\n**Why You Probably Didn't Try This**:")
            print(f"  {idea['why_untried']}")

        if idea.get("why_might_work"):
            print("\n**Why It Might Work**:")
            print(f"  {idea['why_might_work']}")

        if idea.get("first_step"):
            print("\n**First Step**:")
            print(f"  {idea['first_step']}")

    print(f"\n{'=' * 65}")


def _print_rethink_multi_results(result):
    """Print results from multi-model rethink"""
    if not result["success"]:
        print("Error: All models failed", file=sys.stderr)
        for r in result.get("individual_results", []):
            if not r.get("success"):
                print(f"  {r['model']}: {r.get('error')}", file=sys.stderr)
        return

    print(f"\n{'=' * 65}")
    print(f"FRESH PERSPECTIVES from {len(result['models_used'])} MODELS")
    print(f"{'=' * 65}")
    print(f"Models: {', '.join(result['models_used'])}")
    print(f"Total time: {result['total_time_ms']:.0f}ms")

    if result.get("models_failed"):
        print(f"Failed: {', '.join(result['models_failed'])}")

    # Print ranked ideas
    ranked = result.get("ranked_ideas", [])
    if ranked:
        print(f"\n{'=' * 65}")
        print("TOP RANKED IDEAS (by novelty + actionability)")
        print(f"{'=' * 65}")

        for i, idea in enumerate(ranked[:7], 1):  # Top 7
            print(f"\n{'─' * 65}")
            print(f"#{i} [{idea.get('_model', '?')}]: {idea.get('approach', 'Untitled')}")
            print(f"{'─' * 65}")

            if idea.get("why_untried"):
                print(f"  Why untried: {idea['why_untried'][:100]}...")

            if idea.get("first_step"):
                print(f"  First step: {idea['first_step']}")

    # Individual model summaries
    print(f"\n{'=' * 65}")
    print("PER-MODEL SUMMARY")
    print(f"{'=' * 65}")
    for r in result.get("individual_results", []):
        if r.get("success"):
            ideas_count = len(r.get("ideas", []))
            print(f"  {r['model']:30} {ideas_count} ideas ({r['latency_ms']:.0f}ms)")
        else:
            print(f"  {r['model']:30} FAILED: {r.get('error', '?')[:30]}")

    print(f"\n{'=' * 65}")


def cli_status(args):
    """CLI entry for status/models"""
    resolver = ModelResolver()
    models = resolver.discover_models()

    print(f"Available Models ({len(models)}):\n")
    for model_id in sorted(models):
        info = resolver._models.get(model_id)
        latency = f"{info.latency_ms:.0f}ms" if info and info.latency_ms else "untested"
        print(f"  {model_id:30} {latency}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: klean_core.py <quick|multi|rethink|status> [args]")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "quick":
        cli_quick(sys.argv[2:])
    elif cmd == "multi":
        cli_multi(sys.argv[2:])
    elif cmd == "rethink":
        cli_rethink(sys.argv[2:])
    elif cmd == "status":
        cli_status(sys.argv[2:])
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
