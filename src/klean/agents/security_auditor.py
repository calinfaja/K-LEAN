"""Security Auditor Droid - Multi-turn security analysis with Agent SDK.

This droid performs comprehensive security analysis through multi-turn
conversation with Claude, enabling context preservation and knowledge integration.

Multi-turn process:
1. Initial scan: Analyze code for security vulnerabilities
2. Cross-reference: Map findings to OWASP Top 10 and CWE categories
3. Prioritization: Score by exploitability and remediation effort
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..droids.base import SDKDroid
from ..utils import get_model_for_task


class SecurityAuditorDroid(SDKDroid):
    """Multi-turn security auditor using Agent SDK.

    This droid performs security analysis in three turns:
    1. Turn 1: Initial vulnerability scan
    2. Turn 2: Cross-reference with OWASP/CWE standards
    3. Turn 3: Prioritize findings and recommend fixes

    The multi-turn approach enables:
    - Full context preservation across analyses
    - Knowledge integration for better categorization
    - Natural conversational flow with Claude
    - Structured JSON output
    """

    def __init__(self, model: Optional[str] = None):
        """Initialize Security Auditor Droid.

        Args:
            model: Claude model to use. If None, auto-discovers the best
                   available model for security analysis from LiteLLM or
                   falls back to claude-opus-4-5-20251101 for native API.
        """
        # Default model selection based on available API
        if model is None:
            # Try to find best model for security analysis
            model = get_model_for_task("security")

            # Fall back to native API if no LiteLLM models available
            if model is None:
                model = "claude-opus-4-5-20251101"

        super().__init__(
            name="security-auditor-sdk",
            description="Multi-turn security audit with OWASP/CWE mapping and prioritization",
            model=model,
        )

    async def execute(
        self,
        path: str,
        focus: Optional[str] = None,
        depth: str = "medium",
    ) -> Dict[str, Any]:
        """Execute security audit.

        Args:
            path: File or directory to audit
            focus: Specific area to focus on (e.g., "authentication", "injection")
            depth: Analysis depth ("light" = quick, "medium" = normal, "deep" = thorough)

        Returns:
            Dict with:
                - output: JSON string with structured findings
                - format: "json"
                - droid: "security-auditor-sdk"
                - turns: number of turns (3)
                - summary: brief summary of findings
        """
        await self._initialize_client()

        try:
            # Load code to analyze
            code_content = await self._load_code(path)

            # Phase 5: Inject relevant KB context
            kb_context = await self._inject_kb_context(path)

            # Turn 1: Initial security scan (with KB context)
            turn1_result = await self._turn1_initial_scan(code_content, depth, kb_context)

            # Turn 2: Cross-reference with OWASP/CWE
            turn2_result = await self._turn2_cross_reference(turn1_result)

            # Turn 3: Prioritization and recommendations
            turn3_result = await self._turn3_prioritize(turn2_result, focus)

            # Compile final results
            final_output = {
                "audit_summary": {
                    "file_path": path,
                    "depth": depth,
                    "turns_completed": 3,
                    "focus_area": focus or "general",
                },
                **turn3_result,
            }

            return {
                "output": json.dumps(final_output, indent=2),
                "format": "json",
                "droid": "security-auditor-sdk",
                "turns": 3,
                "summary": f"Security audit complete: {turn3_result.get('total_findings', 0)} findings analyzed across {turn3_result.get('severity_counts', {}).get('critical', 0)} critical, {turn3_result.get('severity_counts', {}).get('high', 0)} high, {turn3_result.get('severity_counts', {}).get('medium', 0)} medium severity issues.",
            }

        except Exception as e:
            return {
                "output": json.dumps({"error": str(e)}),
                "format": "json",
                "droid": "security-auditor-sdk",
                "turns": 0,
                "summary": f"Error during audit: {str(e)}",
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

    async def _turn1_initial_scan(self, code: str, depth: str, kb_context: str = "") -> Dict[str, Any]:
        """Turn 1: Analyze code for security vulnerabilities.

        Args:
            code: Code content to analyze
            depth: Analysis depth level
            kb_context: Context from knowledge base with related security patterns

        Returns:
            Dict with initial security findings
        """
        depth_instructions = {
            "light": "Quick surface-level scan for obvious vulnerabilities",
            "medium": "Standard security analysis checking common issues",
            "deep": "Thorough analysis checking for subtle vulnerabilities and patterns",
        }

        # Limit code size to avoid token overflow
        code_snippet = code[:3000] if len(code) > 3000 else code

        # Prepend KB context if available
        context_section = f"\n## Related Security Knowledge\n{kb_context}\n\n" if kb_context else ""

        prompt = f"""Analyze this Python code for security vulnerabilities.

Analysis depth: {depth_instructions.get(depth, 'medium')}

{context_section}CODE TO ANALYZE:
```python
{code_snippet}
```

For each vulnerability found, identify:
1. Vulnerability type (e.g., SQL Injection, XSS, Command Injection, etc.)
2. Location in code (line number or function name if available)
3. Severity (critical/high/medium/low)
4. Description of the issue
5. Why it's a problem

Return as a JSON object with a "findings" array containing each vulnerability as an object with fields: type, location, severity, description, why_problem"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text if message.content else ""

            # Parse JSON from response (Claude should return JSON)
            try:
                # Extract JSON if wrapped in markdown
                if "```json" in response_text:
                    json_str = response_text.split("```json")[1].split("```")[0].strip()
                elif "```" in response_text:
                    json_str = response_text.split("```")[1].split("```")[0].strip()
                else:
                    json_str = response_text

                findings_data = json.loads(json_str)
                findings = findings_data.get("findings", [])
            except (json.JSONDecodeError, IndexError):
                # Fallback: treat entire response as findings
                findings = [
                    {
                        "type": "security_issue",
                        "location": "unknown",
                        "severity": "medium",
                        "description": response_text,
                        "why_problem": "Analysis returned non-structured data",
                    }
                ]

            return {
                "total_findings": len(findings),
                "findings": findings,
                "depth": depth,
            }

        except Exception as e:
            return {
                "total_findings": 0,
                "findings": [],
                "depth": depth,
                "error": str(e),
            }

    async def _turn2_cross_reference(
        self, turn1_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Turn 2: Cross-reference findings with OWASP/CWE standards.

        Args:
            turn1_data: Results from Turn 1

        Returns:
            Dict with enhanced findings including CWE/OWASP mappings
        """
        findings = turn1_data.get("findings", [])

        if not findings:
            return {
                **turn1_data,
                "cwe_mappings": [],
                "owasp_mappings": [],
            }

        findings_text = json.dumps(findings, indent=2)

        prompt = f"""I performed a security analysis and found these vulnerabilities:

{findings_text}

For each vulnerability, please:
1. Map to corresponding CWE (Common Weakness Enumeration) ID if applicable
2. Map to OWASP Top 10 category if applicable
3. Provide a CWE URL for reference
4. Note if this is part of a vulnerability chain with other findings

Return as JSON with fields: cwe_id, cwe_url, owasp_category, in_chain_with"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
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

                mappings_data = json.loads(json_str)
                # Handle both dict and list response formats
                if isinstance(mappings_data, dict):
                    mappings = mappings_data.get("mappings", [])
                elif isinstance(mappings_data, list):
                    mappings = mappings_data
                else:
                    mappings = []
            except (json.JSONDecodeError, IndexError, ValueError):
                mappings = []

            return {
                **turn1_data,
                "cwe_mappings": mappings,
                "owasp_mappings": [m.get("owasp_category") for m in mappings if "owasp_category" in m],
            }

        except Exception as e:
            return {
                **turn1_data,
                "cwe_mappings": [],
                "owasp_mappings": [],
                "error": str(e),
            }

    async def _turn3_prioritize(
        self, turn2_data: Dict[str, Any], focus: Optional[str] = None
    ) -> Dict[str, Any]:
        """Turn 3: Prioritize findings and recommend fixes.

        Args:
            turn2_data: Results from Turn 2
            focus: Optional area to focus on

        Returns:
            Dict with prioritized findings and recommendations
        """
        findings = turn2_data.get("findings", [])

        if not findings:
            return {
                **turn2_data,
                "recommendations": [],
                "priority_scores": [],
                "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
            }

        findings_text = json.dumps(findings, indent=2)
        focus_instruction = f"\nFocus especially on: {focus}" if focus else ""

        prompt = f"""Given these security findings:

{findings_text}

Please:
1. Score each finding by exploitability (1-10, where 10 is trivial to exploit)
2. Score effort to fix (1-10, where 1 is trivial fix, 10 is major refactor)
3. Calculate priority = exploitability + (10 - effort) to prioritize
4. For top 3 findings, suggest specific code fixes
5. Identify any systemic issues or patterns

{focus_instruction}

Return JSON with: exploitability_score, effort_score, priority_score, suggested_fix, is_systemic_issue"""

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
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
                # Handle both dict and list response formats
                if isinstance(recommendations_data, dict):
                    recommendations = recommendations_data.get("recommendations", [])
                elif isinstance(recommendations_data, list):
                    recommendations = recommendations_data
                else:
                    recommendations = []
            except (json.JSONDecodeError, IndexError, ValueError):
                recommendations = []

            # Calculate severity counts
            severity_counts = {
                "critical": sum(1 for f in findings if f.get("severity") == "critical"),
                "high": sum(1 for f in findings if f.get("severity") == "high"),
                "medium": sum(1 for f in findings if f.get("severity") == "medium"),
                "low": sum(1 for f in findings if f.get("severity") == "low"),
            }

            return {
                **turn2_data,
                "recommendations": recommendations,
                "priority_scores": [r.get("priority_score", 0) for r in recommendations],
                "severity_counts": severity_counts,
                "total_findings": len(findings),
            }

        except Exception as e:
            return {
                **turn2_data,
                "recommendations": [],
                "priority_scores": [],
                "severity_counts": {"critical": 0, "high": 0, "medium": 0, "low": 0},
                "error": str(e),
            }

    async def _inject_kb_context(self, path: str) -> str:
        """Inject relevant KB context for security analysis.

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
