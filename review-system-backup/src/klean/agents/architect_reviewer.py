"""Architect Reviewer Droid - Multi-turn architecture analysis with Agent SDK.

This droid performs comprehensive architecture analysis through multi-turn
conversation with Claude, enabling context preservation and knowledge integration.

Multi-turn process:
1. Component mapping: Analyze system components and dependencies
2. Pattern detection: Identify design patterns and anti-patterns
3. SOLID evaluation: Evaluate against SOLID principles
4. Recommendations: Recommend architectural improvements
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..droids.base import SDKDroid
from ..utils import get_model_for_task


class ArchitectReviewerDroid(SDKDroid):
    """Multi-turn architecture reviewer using Agent SDK.

    This droid performs architecture analysis in four turns:
    1. Turn 1: Map system components and dependencies
    2. Turn 2: Identify design patterns and anti-patterns
    3. Turn 3: Evaluate against SOLID principles
    4. Turn 4: Recommend architectural improvements

    The multi-turn approach enables:
    - Full context preservation across analyses
    - Deep understanding of system design
    - Natural conversational flow with Claude
    - Structured JSON output with actionable insights
    """

    def __init__(self, model: Optional[str] = None):
        """Initialize Architect Reviewer Droid.

        Args:
            model: Claude model to use. If None, auto-discovers the best
                   available model for architecture analysis from LiteLLM
                   (preferably deepseek-v3-thinking) or falls back to
                   claude-opus-4-5-20251101 for native API.
        """
        # Default model selection based on available API
        if model is None:
            # Try to find deepseek-v3-thinking for architecture analysis
            model = get_model_for_task("architecture")

            # Fall back to native API if no LiteLLM models available
            if model is None:
                model = "claude-opus-4-5-20251101"

        super().__init__(
            name="architect-reviewer-sdk",
            description="Multi-turn architecture analysis with pattern detection and SOLID evaluation",
            model=model,
        )

    async def execute(
        self,
        path: str,
        focus: Optional[str] = None,
        depth: str = "medium",
    ) -> Dict[str, Any]:
        """Execute architecture review.

        Args:
            path: File or directory to review
            focus: Specific area to focus on (e.g., "modularity", "coupling", "cohesion")
            depth: Analysis depth ("light" = quick, "medium" = normal, "deep" = thorough)

        Returns:
            Dict with:
                - output: JSON string with structured findings
                - format: "json"
                - droid: "architect-reviewer-sdk"
                - turns: number of turns (4)
                - summary: brief summary of findings
        """
        await self._initialize_client()

        try:
            # Load code to analyze
            code_content = await self._load_code(path)

            # Turn 1: Map components and dependencies
            turn1_result = await self._turn1_component_mapping(code_content, depth)

            # Turn 2: Identify design patterns and anti-patterns
            turn2_result = await self._turn2_pattern_detection(turn1_result)

            # Turn 3: Evaluate against SOLID principles
            turn3_result = await self._turn3_solid_evaluation(turn2_result)

            # Turn 4: Recommend architectural improvements
            turn4_result = await self._turn4_recommendations(turn3_result, focus)

            # Compile final results
            final_output = {
                "review_summary": {
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
                "droid": "architect-reviewer-sdk",
                "turns": 4,
                "summary": f"Architecture review complete: {turn4_result.get('total_components', 0)} components analyzed, {len(turn4_result.get('patterns_found', []))} patterns detected, {len(turn4_result.get('solid_violations', []))} SOLID violations found.",
            }

        except Exception as e:
            return {
                "output": json.dumps({"error": str(e)}),
                "format": "json",
                "droid": "architect-reviewer-sdk",
                "turns": 0,
                "summary": f"Error during review: {str(e)}",
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

    async def _turn1_component_mapping(
        self, code: str, depth: str
    ) -> Dict[str, Any]:
        """Turn 1: Map system components and dependencies.

        Args:
            code: Code content to analyze
            depth: Analysis depth level

        Returns:
            Dict with component mapping and dependency graph
        """
        depth_instructions = {
            "light": "Quick overview of main components and obvious dependencies",
            "medium": "Standard analysis identifying components, classes, and key relationships",
            "deep": "Thorough analysis including internal dependencies, data flow, and interaction patterns",
        }

        # Limit code size to avoid token overflow
        code_snippet = code[:4000] if len(code) > 4000 else code

        prompt = f"""Analyze this Python code and map its architecture components and dependencies.

Analysis depth: {depth_instructions.get(depth, 'medium')}

CODE TO ANALYZE:
```python
{code_snippet}
```

For this codebase, identify:
1. Main components/modules (classes, functions, modules)
2. Dependencies between components (imports, calls, data flow)
3. Entry points and interfaces
4. Data structures and models
5. External dependencies

Return as a JSON object with these fields:
- components: array of {{name, type, purpose, complexity_score}}
- dependencies: array of {{from, to, dependency_type, is_circular}}
- entry_points: array of entry points
- external_deps: array of external packages used
- total_components: integer count"""

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

                mapping_data = json.loads(json_str)
                components = mapping_data.get("components", [])
                dependencies = mapping_data.get("dependencies", [])
            except (json.JSONDecodeError, IndexError):
                # Fallback: treat entire response as text analysis
                components = [
                    {
                        "name": "analysis",
                        "type": "text",
                        "purpose": response_text,
                        "complexity_score": 5,
                    }
                ]
                dependencies = []

            return {
                "total_components": len(components),
                "components": components,
                "dependencies": dependencies,
                "entry_points": mapping_data.get("entry_points", []),
                "external_deps": mapping_data.get("external_deps", []),
                "depth": depth,
            }

        except Exception as e:
            return {
                "total_components": 0,
                "components": [],
                "dependencies": [],
                "entry_points": [],
                "external_deps": [],
                "depth": depth,
                "error": str(e),
            }

    async def _turn2_pattern_detection(
        self, turn1_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Turn 2: Identify design patterns and anti-patterns.

        Args:
            turn1_data: Results from Turn 1

        Returns:
            Dict with identified patterns and anti-patterns
        """
        components = turn1_data.get("components", [])

        if not components:
            return {
                **turn1_data,
                "patterns_found": [],
                "anti_patterns": [],
            }

        components_text = json.dumps(components, indent=2)

        prompt = f"""Based on this component mapping:

{components_text}

Identify:
1. Design patterns used (e.g., Singleton, Factory, Observer, Strategy, etc.)
2. Anti-patterns present (e.g., God Object, Spaghetti Code, Tight Coupling, etc.)
3. For each pattern/anti-pattern:
   - Name and category
   - Where it appears (component names)
   - Whether it's appropriate for the context
   - Impact on maintainability

Return as JSON with:
- patterns_found: array of {{name, category, location, is_appropriate, benefits}}
- anti_patterns: array of {{name, category, location, severity, impact_on_maintainability}}"""

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

                patterns_data = json.loads(json_str)
                patterns_found = patterns_data.get("patterns_found", [])
                anti_patterns = patterns_data.get("anti_patterns", [])
            except (json.JSONDecodeError, IndexError, ValueError):
                patterns_found = []
                anti_patterns = []

            return {
                **turn1_data,
                "patterns_found": patterns_found,
                "anti_patterns": anti_patterns,
            }

        except Exception as e:
            return {
                **turn1_data,
                "patterns_found": [],
                "anti_patterns": [],
                "error": str(e),
            }

    async def _turn3_solid_evaluation(
        self, turn2_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Turn 3: Evaluate against SOLID principles.

        Args:
            turn2_data: Results from Turn 2

        Returns:
            Dict with SOLID principle evaluation
        """
        components = turn2_data.get("components", [])

        if not components:
            return {
                **turn2_data,
                "solid_violations": [],
                "solid_scores": {},
            }

        components_text = json.dumps(components, indent=2)
        anti_patterns = turn2_data.get("anti_patterns", [])
        anti_patterns_text = json.dumps(anti_patterns, indent=2) if anti_patterns else "None"

        prompt = f"""Evaluate this architecture against SOLID principles:

COMPONENTS:
{components_text}

ANTI-PATTERNS DETECTED:
{anti_patterns_text}

For each SOLID principle, analyze:
1. Single Responsibility Principle (SRP): Each class should have one reason to change
2. Open/Closed Principle (OCP): Open for extension, closed for modification
3. Liskov Substitution Principle (LSP): Derived classes must be substitutable for base classes
4. Interface Segregation Principle (ISP): No client should depend on methods it doesn't use
5. Dependency Inversion Principle (DIP): Depend on abstractions, not concretions

Return as JSON with:
- solid_violations: array of {{principle, component, description, severity}}
- solid_scores: object with {{srp, ocp, lsp, isp, dip}} each scored 0-10 (10 = perfect adherence)
- overall_solid_score: average of all principle scores"""

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

                solid_data = json.loads(json_str)
                solid_violations = solid_data.get("solid_violations", [])
                solid_scores = solid_data.get("solid_scores", {})
                overall_score = solid_data.get("overall_solid_score", 5.0)
            except (json.JSONDecodeError, IndexError, ValueError):
                solid_violations = []
                solid_scores = {}
                overall_score = 5.0

            return {
                **turn2_data,
                "solid_violations": solid_violations,
                "solid_scores": solid_scores,
                "overall_solid_score": overall_score,
            }

        except Exception as e:
            return {
                **turn2_data,
                "solid_violations": [],
                "solid_scores": {},
                "overall_solid_score": 5.0,
                "error": str(e),
            }

    async def _turn4_recommendations(
        self, turn3_data: Dict[str, Any], focus: Optional[str] = None
    ) -> Dict[str, Any]:
        """Turn 4: Recommend architectural improvements.

        Args:
            turn3_data: Results from Turn 3
            focus: Optional area to focus on

        Returns:
            Dict with prioritized recommendations
        """
        anti_patterns = turn3_data.get("anti_patterns", [])
        solid_violations = turn3_data.get("solid_violations", [])

        if not anti_patterns and not solid_violations:
            return {
                **turn3_data,
                "recommendations": [],
                "priority_actions": [],
                "refactoring_complexity": "none",
            }

        issues_text = json.dumps(
            {
                "anti_patterns": anti_patterns,
                "solid_violations": solid_violations,
            },
            indent=2,
        )
        focus_instruction = f"\nFocus especially on: {focus}" if focus else ""

        prompt = f"""Given these architecture issues:

{issues_text}

Please provide:
1. Specific refactoring recommendations (prioritized by impact)
2. For top 5 issues, suggest concrete steps to resolve
3. Estimate refactoring complexity for each (trivial/moderate/major)
4. Identify any systemic issues requiring broader changes
5. Suggest architectural patterns that would help

{focus_instruction}

Return JSON with:
- recommendations: array of {{issue, recommendation, priority_score (1-10), complexity, estimated_effort_days}}
- priority_actions: top 3-5 actions to take first
- refactoring_complexity: overall assessment (trivial/moderate/major/extensive)
- suggested_patterns: patterns that would help
- systemic_issues: broader problems requiring architectural changes"""

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
                priority_actions = recommendations_data.get("priority_actions", [])
                refactoring_complexity = recommendations_data.get(
                    "refactoring_complexity", "moderate"
                )
                suggested_patterns = recommendations_data.get("suggested_patterns", [])
                systemic_issues = recommendations_data.get("systemic_issues", [])
            except (json.JSONDecodeError, IndexError, ValueError):
                recommendations = []
                priority_actions = []
                refactoring_complexity = "unknown"
                suggested_patterns = []
                systemic_issues = []

            return {
                **turn3_data,
                "recommendations": recommendations,
                "priority_actions": priority_actions,
                "refactoring_complexity": refactoring_complexity,
                "suggested_patterns": suggested_patterns,
                "systemic_issues": systemic_issues,
            }

        except Exception as e:
            return {
                **turn3_data,
                "recommendations": [],
                "priority_actions": [],
                "refactoring_complexity": "unknown",
                "suggested_patterns": [],
                "systemic_issues": [],
                "error": str(e),
            }
