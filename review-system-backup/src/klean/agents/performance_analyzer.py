"""Performance Analyzer Droid - Multi-turn performance analysis with Agent SDK.

This droid performs comprehensive performance analysis through multi-turn
conversation with Claude, enabling context preservation and knowledge integration.

Multi-turn process:
1. Bottleneck identification: Identify performance bottlenecks and hot paths
2. Complexity analysis: Analyze algorithmic complexity (O notation)
3. Memory analysis: Identify memory usage patterns and leaks
4. Optimization recommendations: Recommend optimizations with expected improvements
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..droids.base import SDKDroid
from ..utils import get_model_for_task


class PerformanceAnalyzerDroid(SDKDroid):
    """Multi-turn performance analyzer using Agent SDK.

    This droid performs performance analysis in four turns:
    1. Turn 1: Identify performance bottlenecks and hot paths
    2. Turn 2: Analyze algorithmic complexity (O notation)
    3. Turn 3: Identify memory usage patterns and leaks
    4. Turn 4: Recommend optimizations with expected improvements

    The multi-turn approach enables:
    - Full context preservation across analyses
    - Deep understanding of performance characteristics
    - Natural conversational flow with Claude
    - Structured JSON output with actionable insights
    """

    def __init__(self, model: Optional[str] = None):
        """Initialize Performance Analyzer Droid.

        Args:
            model: Claude model to use. If None, auto-discovers the best
                   available model for performance analysis from LiteLLM
                   (preferably qwen3-coder) or falls back to
                   claude-opus-4-5-20251101 for native API.
        """
        # Default model selection based on available API
        if model is None:
            # Try to find qwen3-coder for performance analysis
            model = get_model_for_task("performance")

            # Fall back to native API if no LiteLLM models available
            if model is None:
                model = "claude-opus-4-5-20251101"

        super().__init__(
            name="performance-analyzer-sdk",
            description="Multi-turn performance analysis with bottleneck detection, complexity analysis, and optimization recommendations",
            model=model,
        )

    async def execute(
        self,
        path: str,
        focus: Optional[str] = None,
        depth: str = "medium",
    ) -> Dict[str, Any]:
        """Execute performance analysis.

        Args:
            path: File or directory to analyze
            focus: Specific area to focus on (e.g., "database", "loops", "I/O")
            depth: Analysis depth ("light" = quick, "medium" = normal, "deep" = thorough)

        Returns:
            Dict with:
                - output: JSON string with structured findings
                - format: "json"
                - droid: "performance-analyzer-sdk"
                - turns: number of turns (4)
                - summary: brief summary of findings
        """
        await self._initialize_client()

        try:
            # Load code to analyze
            code_content = await self._load_code(path)

            # Phase 5: Inject relevant KB context
            kb_context = await self._inject_kb_context(path)

            # Turn 1: Identify bottlenecks and hot paths (with KB context)
            turn1_result = await self._turn1_bottleneck_identification(code_content, depth, kb_context)

            # Turn 2: Analyze algorithmic complexity
            turn2_result = await self._turn2_complexity_analysis(turn1_result)

            # Turn 3: Identify memory usage patterns and leaks
            turn3_result = await self._turn3_memory_analysis(turn2_result)

            # Turn 4: Recommend optimizations with expected improvements
            turn4_result = await self._turn4_optimization_recommendations(turn3_result, focus)

            # Compile final results
            final_output = {
                "analysis_summary": {
                    "file_path": path,
                    "depth": depth,
                    "turns_completed": 4,
                    "focus_area": focus or "general",
                },
                **turn4_result,
            }

            return {
                "output": json.dumps(final_output, indent=2),
                "format": "json",
                "droid": "performance-analyzer-sdk",
                "turns": 4,
                "summary": f"Performance analysis complete: {turn4_result.get('total_bottlenecks', 0)} bottlenecks found, {len(turn4_result.get('complexity_issues', []))} complexity issues, {len(turn4_result.get('memory_issues', []))} memory issues detected.",
            }

        except Exception as e:
            return {
                "output": json.dumps({"error": str(e)}),
                "format": "json",
                "droid": "performance-analyzer-sdk",
                "turns": 0,
                "summary": f"Error during analysis: {str(e)}",
            }

    async def _load_code(self, path: str) -> str:
        """Load code from file or directory.

        Args:
            path: File or directory path

        Returns:
            Code content (or error message)

        Raises:
            FileNotFoundError: If path doesn't exist
        """
        p = Path(path)

        if p.is_file():
            try:
                return p.read_text(errors="ignore")
            except Exception as e:
                raise FileNotFoundError(f"Cannot read file {path}: {e}")

        elif p.is_dir():
            # Load Python files from directory
            code_parts = []
            file_count = 0

            for py_file in sorted(p.rglob("*.py")):
                # Skip common non-code directories
                skip_dirs = {".venv", "venv", "__pycache__", ".git", "node_modules"}
                if any(skip_dir in py_file.parts for skip_dir in skip_dirs):
                    continue

                try:
                    content = py_file.read_text(errors="ignore")
                    # Limit file size to avoid token overload
                    if len(content) < 5000:
                        code_parts.append(f"# File: {py_file.relative_to(p)}\n{content}")
                        file_count += 1

                    if file_count >= 10:  # Limit to 10 files
                        break
                except Exception:
                    continue

            if not code_parts:
                raise FileNotFoundError(f"No Python files found in {path}")

            return "\n\n---\n\n".join(code_parts)

        else:
            raise FileNotFoundError(f"Path not found: {path}")

    async def _turn1_bottleneck_identification(
        self, code: str, depth: str, kb_context: str = ""
    ) -> Dict[str, Any]:
        """Turn 1: Identify performance bottlenecks and hot paths.

        Args:
            code: Code content to analyze
            depth: Analysis depth level
            kb_context: Context from knowledge base with related performance patterns

        Returns:
            Dict with identified bottlenecks and hot paths
        """
        depth_instructions = {
            "light": "Quick scan for obvious performance bottlenecks (nested loops, inefficient patterns)",
            "medium": "Standard analysis identifying bottlenecks, hot paths, and inefficient operations",
            "deep": "Thorough analysis including subtle bottlenecks, data flow, and performance anti-patterns",
        }

        # Limit code size to avoid token overflow
        code_snippet = code[:4000] if len(code) > 4000 else code

        # Prepend KB context if available
        context_section = f"\n## Related Performance Knowledge\n{kb_context}\n\n" if kb_context else ""

        prompt = f"""Analyze this Python code for performance bottlenecks and hot paths.

Analysis depth: {depth_instructions.get(depth, 'medium')}

{context_section}CODE TO ANALYZE:
```python
{code_snippet}
```

For this codebase, identify:
1. Performance bottlenecks (e.g., nested loops, inefficient algorithms, blocking I/O)
2. Hot paths (frequently executed code paths that impact performance)
3. Inefficient operations (e.g., repeated calculations, unnecessary object creation)
4. Database query inefficiencies (N+1 queries, missing indexes)
5. I/O bottlenecks (file operations, network calls)

Return as a JSON object with these fields:
- bottlenecks: array of {{name, location, type, severity_score (1-10), description}}
- hot_paths: array of {{path_description, estimated_frequency, impact_score (1-10)}}
- inefficient_operations: array of {{operation, location, waste_type, impact}}
- total_bottlenecks: integer count
- overall_performance_score: 0-10 (10 = optimal, 0 = severe issues)"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text if message.content else ""

            # Parse JSON from response
            try:
                # Extract JSON if wrapped in markdown
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0].strip()
                else:
                    json_str = response_text

                bottleneck_data = json.loads(json_str)
                bottlenecks = bottleneck_data.get("bottlenecks", [])
                hot_paths = bottleneck_data.get("hot_paths", [])
                inefficient_ops = bottleneck_data.get("inefficient_operations", [])
            except (json.JSONDecodeError, IndexError):
                # Fallback: treat entire response as text analysis
                bottlenecks = [
                    {
                        "name": "analysis",
                        "location": "unknown",
                        "type": "text",
                        "severity_score": 5,
                        "description": response_text,
                    }
                ]
                hot_paths = []
                inefficient_ops = []

            return {
                "total_bottlenecks": len(bottlenecks),
                "bottlenecks": bottlenecks,
                "hot_paths": hot_paths,
                "inefficient_operations": inefficient_ops,
                "overall_performance_score": bottleneck_data.get("overall_performance_score", 5.0),
                "depth": depth,
            }

        except Exception as e:
            return {
                "total_bottlenecks": 0,
                "bottlenecks": [],
                "hot_paths": [],
                "inefficient_operations": [],
                "overall_performance_score": 5.0,
                "depth": depth,
                "error": str(e),
            }

    async def _turn2_complexity_analysis(
        self, turn1_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Turn 2: Analyze algorithmic complexity (O notation).

        Args:
            turn1_data: Results from Turn 1

        Returns:
            Dict with complexity analysis for identified bottlenecks
        """
        bottlenecks = turn1_data.get("bottlenecks", [])
        hot_paths = turn1_data.get("hot_paths", [])

        if not bottlenecks and not hot_paths:
            return {
                **turn1_data,
                "complexity_issues": [],
                "time_complexity": {},
                "space_complexity": {},
            }

        bottlenecks_text = json.dumps(bottlenecks, indent=2)
        hot_paths_text = json.dumps(hot_paths, indent=2)

        prompt = f"""Based on these performance bottlenecks and hot paths:

BOTTLENECKS:
{bottlenecks_text}

HOT PATHS:
{hot_paths_text}

Analyze algorithmic complexity:
1. Determine time complexity (Big-O notation) for each bottleneck and hot path
2. Determine space complexity (memory usage patterns)
3. Identify suboptimal complexity (e.g., O(n²) where O(n) is possible)
4. Flag exponential or factorial complexity patterns
5. Identify opportunities for caching, memoization, or algorithmic improvements

Return as JSON with:
- complexity_issues: array of {{component, current_time_complexity, optimal_time_complexity, current_space_complexity, optimal_space_complexity, improvement_potential}}
- time_complexity: object mapping components to their Big-O time complexity
- space_complexity: object mapping components to their Big-O space complexity
- worst_complexity: the worst time complexity found (e.g., "O(n³)")
- improvement_opportunities: count of how many can be improved"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text if message.content else ""

            try:
                # Extract JSON
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0].strip()
                else:
                    json_str = response_text

                complexity_data = json.loads(json_str)
                complexity_issues = complexity_data.get("complexity_issues", [])
                time_complexity = complexity_data.get("time_complexity", {})
                space_complexity = complexity_data.get("space_complexity", {})
                worst_complexity = complexity_data.get("worst_complexity", "O(1)")
                improvement_opportunities = complexity_data.get("improvement_opportunities", 0)
            except (json.JSONDecodeError, IndexError, ValueError):
                complexity_issues = []
                time_complexity = {}
                space_complexity = {}
                worst_complexity = "unknown"
                improvement_opportunities = 0

            return {
                **turn1_data,
                "complexity_issues": complexity_issues,
                "time_complexity": time_complexity,
                "space_complexity": space_complexity,
                "worst_complexity": worst_complexity,
                "improvement_opportunities": improvement_opportunities,
            }

        except Exception as e:
            return {
                **turn1_data,
                "complexity_issues": [],
                "time_complexity": {},
                "space_complexity": {},
                "worst_complexity": "unknown",
                "improvement_opportunities": 0,
                "error": str(e),
            }

    async def _turn3_memory_analysis(
        self, turn2_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Turn 3: Identify memory usage patterns and leaks.

        Args:
            turn2_data: Results from Turn 2

        Returns:
            Dict with memory analysis findings
        """
        bottlenecks = turn2_data.get("bottlenecks", [])
        space_complexity = turn2_data.get("space_complexity", {})

        if not bottlenecks and not space_complexity:
            return {
                **turn2_data,
                "memory_issues": [],
                "memory_score": 10.0,
            }

        context_text = json.dumps(
            {
                "bottlenecks": bottlenecks,
                "space_complexity": space_complexity,
            },
            indent=2,
        )

        prompt = f"""Based on this performance analysis:

{context_text}

Analyze memory usage patterns:
1. Identify potential memory leaks (unclosed resources, circular references, growing caches)
2. Detect excessive memory usage (large data structures, memory duplication)
3. Find memory allocation patterns that could be optimized
4. Identify opportunities for object reuse or pooling
5. Flag long-lived objects that should be short-lived

Return as JSON with:
- memory_issues: array of {{issue_type, location, description, severity (critical/high/medium/low), estimated_memory_waste}}
- memory_leak_risks: array of potential memory leak sources
- memory_optimization_opportunities: array of ways to reduce memory usage
- memory_score: 0-10 (10 = optimal memory usage, 0 = severe issues)
- peak_memory_concerns: areas that may cause memory spikes"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text if message.content else ""

            try:
                # Extract JSON
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0].strip()
                else:
                    json_str = response_text

                memory_data = json.loads(json_str)
                memory_issues = memory_data.get("memory_issues", [])
                memory_leak_risks = memory_data.get("memory_leak_risks", [])
                memory_optimizations = memory_data.get("memory_optimization_opportunities", [])
                memory_score = memory_data.get("memory_score", 5.0)
                peak_concerns = memory_data.get("peak_memory_concerns", [])
            except (json.JSONDecodeError, IndexError, ValueError):
                memory_issues = []
                memory_leak_risks = []
                memory_optimizations = []
                memory_score = 5.0
                peak_concerns = []

            return {
                **turn2_data,
                "memory_issues": memory_issues,
                "memory_leak_risks": memory_leak_risks,
                "memory_optimization_opportunities": memory_optimizations,
                "memory_score": memory_score,
                "peak_memory_concerns": peak_concerns,
            }

        except Exception as e:
            return {
                **turn2_data,
                "memory_issues": [],
                "memory_leak_risks": [],
                "memory_optimization_opportunities": [],
                "memory_score": 5.0,
                "peak_memory_concerns": [],
                "error": str(e),
            }

    async def _turn4_optimization_recommendations(
        self, turn3_data: Dict[str, Any], focus: Optional[str] = None
    ) -> Dict[str, Any]:
        """Turn 4: Recommend optimizations with expected improvements.

        Args:
            turn3_data: Results from Turn 3
            focus: Optional area to focus on

        Returns:
            Dict with prioritized optimization recommendations
        """
        bottlenecks = turn3_data.get("bottlenecks", [])
        complexity_issues = turn3_data.get("complexity_issues", [])
        memory_issues = turn3_data.get("memory_issues", [])

        if not bottlenecks and not complexity_issues and not memory_issues:
            return {
                **turn3_data,
                "recommendations": [],
                "priority_optimizations": [],
                "optimization_complexity": "none",
                "expected_improvements": {},
            }

        issues_text = json.dumps(
            {
                "bottlenecks": bottlenecks,
                "complexity_issues": complexity_issues,
                "memory_issues": memory_issues,
            },
            indent=2,
        )
        focus_instruction = f"\nFocus especially on: {focus}" if focus else ""

        prompt = f"""Given these performance issues:

{issues_text}

Please provide:
1. Specific optimization recommendations (prioritized by impact)
2. For top 5 issues, provide concrete implementation strategies
3. Estimate expected performance improvement (e.g., "50% faster", "70% less memory")
4. Estimate implementation complexity (trivial/moderate/complex/extensive)
5. Identify any trade-offs (e.g., speed vs memory, complexity vs performance)
6. Suggest profiling areas for validation

{focus_instruction}

Return JSON with:
- recommendations: array of {{issue, recommendation, priority_score (1-10), complexity, expected_improvement, trade_offs, implementation_notes}}
- priority_optimizations: top 3-5 optimizations to implement first
- optimization_complexity: overall assessment (trivial/moderate/complex/extensive)
- expected_improvements: object with {{time_improvement_percent, memory_improvement_percent, overall_impact}}
- profiling_recommendations: areas to profile for validation
- quick_wins: optimizations that are easy to implement with high impact"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=3000,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text if message.content else ""

            try:
                # Extract JSON
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0].strip()
                else:
                    json_str = response_text

                recommendations_data = json.loads(json_str)
                recommendations = recommendations_data.get("recommendations", [])
                priority_optimizations = recommendations_data.get("priority_optimizations", [])
                optimization_complexity = recommendations_data.get("optimization_complexity", "moderate")
                expected_improvements = recommendations_data.get("expected_improvements", {})
                profiling_recommendations = recommendations_data.get("profiling_recommendations", [])
                quick_wins = recommendations_data.get("quick_wins", [])
            except (json.JSONDecodeError, IndexError, ValueError):
                recommendations = []
                priority_optimizations = []
                optimization_complexity = "unknown"
                expected_improvements = {}
                profiling_recommendations = []
                quick_wins = []

            return {
                **turn3_data,
                "recommendations": recommendations,
                "priority_optimizations": priority_optimizations,
                "optimization_complexity": optimization_complexity,
                "expected_improvements": expected_improvements,
                "profiling_recommendations": profiling_recommendations,
                "quick_wins": quick_wins,
            }

        except Exception as e:
            return {
                **turn3_data,
                "recommendations": [],
                "priority_optimizations": [],
                "optimization_complexity": "unknown",
                "expected_improvements": {},
                "profiling_recommendations": [],
                "quick_wins": [],
                "error": str(e),
            }

    async def _inject_kb_context(self, path: str) -> str:
        """Inject relevant KB context for performance analysis.

        Args:
            path: File being analyzed

        Returns:
            Formatted context string or empty string if no context available
        """
        try:
            # Try to import and use context injector
            import sys
            from pathlib import Path as PathlibPath

            scripts_dir = PathlibPath.home() / ".claude" / "scripts"
            if not scripts_dir.exists():
                return ""

            # Try dynamic import of knowledge-context-injector.py
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    "context_injector",
                    str(scripts_dir / "knowledge-context-injector.py")
                )
                if spec and spec.loader:
                    context_injector_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(context_injector_module)
                    ContextInjector = context_injector_module.ContextInjector

                    # Get context
                    injector = ContextInjector()
                    context = injector.inject_context(path, limit=5)
                    return context
            except Exception:
                # Fallback: direct script call
                pass

            # Try calling the script directly
            import subprocess
            result = subprocess.run(
                [sys.executable, str(scripts_dir / "knowledge-context-injector.py"), path, "--limit", "5"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()

        except Exception:
            # Silently fail - KB context is optional enhancement
            pass

        return ""
