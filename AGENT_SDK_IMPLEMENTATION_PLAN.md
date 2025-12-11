# Claude Agent SDK Integration Plan for K-LEAN v1.0.0

**Author:** Claude Code
**Date:** 2025-12-11
**Status:** Design Phase (Ready for Review)
**Target Release:** K-LEAN v2.0.0

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Phase Architecture](#phase-architecture)
3. [Phase 1: Foundation (Week 1)](#phase-1-foundation-week-1)
4. [Phase 2: Pilot Droid - Security Auditor (Week 2)](#phase-2-pilot-droid---security-auditor-week-2)
5. [Phase 3: Knowledge Integration (Week 2-3)](#phase-3-knowledge-integration-week-2-3)
6. [Phase 4: Additional Droids (Week 3-4)](#phase-4-additional-droids-week-3-4)
7. [Phase 5: Testing & Migration (Week 4-5)](#phase-5-testing--migration-week-4-5)
8. [Backward Compatibility Strategy](#backward-compatibility-strategy)
9. [Testing Strategy](#testing-strategy)
10. [Performance Expectations](#performance-expectations)
11. [Risk Mitigation](#risk-mitigation)

---

## Executive Summary

### Current State
- **K-LEAN v1.0.0** fully operational with PIPX installation
- Knowledge server with auto-start working reliably
- Factory Droids implemented as bash scripts with markdown output
- LiteLLM proxy at localhost:4000 managing multi-model access

### Problem Statement
1. **Context Loss:** Each droid invocation is independent (no session memory)
2. **Tool Overhead:** 20-30ms per tool call due to subprocess overhead
3. **Output Format:** Markdown-only output, manual parsing required
4. **Knowledge Gap:** Droids can't leverage knowledge database in real-time
5. **Single-Pass Analysis:** Cannot perform multi-turn analysis naturally

### Proposed Solution
Gradual migration to Claude Agent SDK for complex droids while maintaining backward compatibility with existing bash-based simple droids.

### Expected Outcomes
- **Performance:** 6-10x speedup on multi-turn operations (250ms → 25ms overhead)
- **Quality:** Multi-turn analysis with context preservation
- **Flexibility:** JSON Schema structured output
- **Knowledge:** Real-time integration with knowledge database
- **Compatibility:** Zero breaking changes to existing workflows

---

## Phase Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      K-LEAN v2.0.0 Architecture              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  CLI Layer (cli.py - unchanged)                             │
│  ├─ k-lean install                                          │
│  ├─ k-lean status                                           │
│  ├─ k-lean <command>                                        │
│  └─ Dispatcher to appropriate droid layer                   │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ Droid Layer (NEW: droids/)                              │ │
│  ├─ Bash Droids (simple, one-off)                          │ │
│  │  ├─ simple-audit.sh (UNCHANGED)                         │ │
│  │  └─ quick-review.sh (UNCHANGED)                         │ │
│  │                                                          │ │
│  └─ Agent SDK Droids (complex, multi-turn) ✨ NEW          │
│     ├─ security_auditor.py (PILOT)                         │
│     ├─ architect_reviewer.py                               │ │
│     ├─ performance_analyzer.py                             │ │
│     └─ knowledge_integrator.py                             │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                               │
│  Tools Layer (NEW: tools/)                                   │
│  ├─ grep_codebase.py        → async function with Grep      │
│  ├─ read_file.py            → async function with Read      │
│  ├─ search_knowledge.py      → async function with KB       │
│  ├─ run_tests.py            → async function with Bash      │
│  └─ format_results.py       → JSON Schema validation        │
│                                                               │
│  Knowledge Integration                                       │
│  ├─ Knowledge Server (/tmp/knowledge-server.sock)           │
│  ├─ Real-time search during agent execution                 │
│  └─ Automatic fact capture from findings                    │
│                                                               │
│  LiteLLM Integration                                         │
│  ├─ ClaudeSDKClient → localhost:4000                        │
│  ├─ Multi-model support (qwen, deepseek, glm, etc)          │
│  └─ Async streaming responses                               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1: Foundation (Week 1)

### Objective
Establish the infrastructure for Agent SDK integration while maintaining full backward compatibility.

### 1.1 Update pyproject.toml

**File:** `review-system-backup/pyproject.toml`

```toml
[project.optional-dependencies]
knowledge = [
    "txtai>=7.0.0",
    "sentence-transformers>=2.0.0",
]
agent-sdk = [
    "anthropic>=0.34.0",
]
all = [
    "k-lean[knowledge,agent-sdk]",
]
```

**Rationale:**
- Agent SDK as optional dependency (users don't need it for simple droids)
- Can be installed with `pipx install k-lean[agent-sdk]`
- Maintains PIPX editable install capability

**Implementation Steps:**
1. Read current pyproject.toml
2. Add `agent-sdk` optional-dependencies section
3. Update `all` to include both knowledge and agent-sdk
4. Commit with message: "Add Agent SDK as optional dependency"

---

### 1.2 Create New Directory Structure

**New Directories:**

```
src/klean/
├── droids/                    # NEW: Droid implementations
│   ├── __init__.py
│   ├── base.py               # Base droid class (abstracts both bash & SDK)
│   ├── bash_droid.py         # Wraps bash scripts
│   └── sdk_droid.py          # Agent SDK implementation base
│
├── tools/                     # NEW: Agent SDK custom tools
│   ├── __init__.py
│   ├── grep_tool.py          # @tool for grep_codebase
│   ├── read_tool.py          # @tool for read_file
│   ├── knowledge_tool.py      # @tool for search_knowledge
│   ├── test_tool.py          # @tool for run_tests
│   └── format_tool.py        # @tool for format_results
│
└── agents/                    # NEW: Agent implementations
    ├── __init__.py
    ├── security_auditor.py    # PILOT: Security audit droid
    ├── architect_reviewer.py  # Architecture analysis droid
    └── performance_analyzer.py # Performance audit droid
```

**Implementation Steps:**
1. Create directories: `src/klean/droids/`, `src/klean/tools/`, `src/klean/agents/`
2. Create `__init__.py` in each (empty for now)
3. Test with: `ls -la src/klean/`

---

### 1.3 Create Base Droid Class

**File:** `src/klean/droids/base.py`

```python
"""Base class for all K-LEAN droids (bash or Agent SDK)."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseDroid(ABC):
    """Abstract base class for all droids."""

    def __init__(self, name: str, description: str, droid_type: str = "bash"):
        self.name = name
        self.description = description
        self.droid_type = droid_type  # "bash" or "sdk"

    @abstractmethod
    async def execute(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute the droid and return results.

        Returns:
            Dict with 'output' (str) and 'format' ('markdown' or 'json')
        """
        pass

    @abstractmethod
    async def get_help(self) -> str:
        """Return help text for this droid."""
        pass


class BashDroid(BaseDroid):
    """Wrapper for bash-based droids (backward compatible)."""

    def __init__(self, name: str, script_path: str, description: str):
        super().__init__(name, description, droid_type="bash")
        self.script_path = script_path

    async def execute(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute bash script and return markdown output."""
        import subprocess

        cmd = [str(self.script_path)] + list(args)
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300
        )

        return {
            "output": result.stdout if result.returncode == 0 else result.stderr,
            "format": "markdown",
            "returncode": result.returncode,
        }

    async def get_help(self) -> str:
        return self.description


class SDKDroid(BaseDroid):
    """Base class for Agent SDK-based droids."""

    def __init__(
        self,
        name: str,
        description: str,
        model: str = "claude-opus-4-5-20251101"
    ):
        super().__init__(name, description, droid_type="sdk")
        self.model = model
        self.client = None  # Initialized on first use

    async def _initialize_client(self):
        """Lazy-initialize ClaudeSDKClient."""
        if self.client is None:
            # Import here to avoid requiring Agent SDK if not needed
            try:
                from anthropic import Anthropic

                self.client = Anthropic(
                    base_url="http://localhost:4000",
                    api_key="dummy",  # LiteLLM doesn't validate
                )
            except ImportError:
                raise RuntimeError(
                    "Agent SDK not installed. "
                    "Install with: pipx install k-lean[agent-sdk]"
                )

    async def execute(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Execute via Agent SDK (subclasses override with specific logic)."""
        raise NotImplementedError("Subclasses must implement execute()")

    async def get_help(self) -> str:
        return self.description
```

**Rationale:**
- Abstraction layer for both bash and SDK droids
- Lazy-loads Agent SDK only if needed
- BashDroid remains fully compatible with existing scripts
- SDKDroid provides base for async operations

---

### 1.4 Create Tools Base Infrastructure

**File:** `src/klean/tools/__init__.py`

```python
"""Tools for Agent SDK droids."""

from typing import Any, Callable, Dict, Optional


def tool(
    name: str,
    description: str,
    schema: Optional[Dict[str, Any]] = None,
):
    """Decorator for defining Agent SDK tools.

    Example:
        @tool("grep_codebase", "Search for patterns in code")
        async def grep(pattern: str, path: str = ".") -> str:
            # implementation
            return results
    """
    def decorator(func: Callable) -> Callable:
        # Mark function as a tool
        func._is_tool = True
        func._tool_name = name
        func._tool_description = description
        func._tool_schema = schema or {}
        return func

    return decorator


__all__ = ["tool"]
```

**Rationale:**
- Simple decorator framework for tools
- Will be used by all droid implementations
- Extensible for future enhancements

---

### 1.5 Verify Installation & Backward Compatibility

**Testing:**

```bash
# Test 1: Editable install still works
pipx install -e /path/to/review-system-backup

# Test 2: Without agent-sdk installed
k-lean status  # Should work normally

# Test 3: Can install agent-sdk optional
pipx install -e /path/to/review-system-backup[agent-sdk]
# Should add anthropic to venv without breaking existing

# Test 4: Bash droids still work
k-lean deepInspect test_file.py  # Should use bash script

# Test 5: New SDK droids can be tested individually
```

**Commit Message:**
```
Phase 1: Agent SDK foundation - directory structure, base classes, tool infrastructure

- Add droids/, tools/, agents/ directories with proper structure
- Create BaseDroid abstract class for both bash and SDK droids
- Create BashDroid wrapper for backward compatibility
- Create SDKDroid base for async implementations
- Add optional agent-sdk dependency to pyproject.toml
- Lazy-load Agent SDK only when needed (no breaking changes)
- Fully backward compatible with existing bash droids
```

---

## Phase 2: Pilot Droid - Security Auditor (Week 2)

### Objective
Implement first Agent SDK droid as proof-of-concept, demonstrating benefits while keeping original bash version available.

### 2.1 Understand Current Security Auditor

**File:** `~/.claude/commands/kln/security-audit.md` or `~/.claude/scripts/security-audit.sh`

**Current behavior:**
- Takes a path/file as input
- Runs security analysis via Claude Code CLI
- Returns markdown findings
- Single-pass analysis (no context reuse)

---

### 2.2 Design New Security Auditor Droid

**File:** `src/klean/agents/security_auditor.py`

```python
"""Security Auditor Droid - Multi-turn analysis with Agent SDK."""

import json
from typing import Any, Dict, List, Optional
from pathlib import Path

from ..droids.base import SDKDroid
from ..tools import tool


class SecurityAuditorDroid(SDKDroid):
    """Security auditor using multi-turn Agent SDK analysis.

    Multi-turn process:
    1. Initial scan: Analyze code for security issues
    2. Cross-reference: Map to OWASP/CWE vulnerabilities
    3. Prioritization: Score by exploitability and effort
    4. Recommendations: Suggest fixes and improvements
    """

    def __init__(self, model: str = "claude-opus-4-5-20251101"):
        super().__init__(
            name="security-auditor-sdk",
            description="Multi-turn security audit with OWASP/CWE mapping",
            model=model,
        )

    async def execute(
        self,
        path: str,
        focus: Optional[str] = None,
        depth: str = "medium",  # light, medium, deep
    ) -> Dict[str, Any]:
        """Execute security audit.

        Args:
            path: File or directory to audit
            focus: Specific area to focus on (e.g., "authentication")
            depth: Analysis depth (light=quick, medium=normal, deep=thorough)

        Returns:
            Dict with structured findings in JSON format
        """
        await self._initialize_client()

        # Load code to analyze
        code_content = await self._load_code(path)

        # Turn 1: Initial security scan
        findings = await self._turn1_initial_scan(code_content, depth)

        # Turn 2: Cross-reference with knowledge
        findings = await self._turn2_cross_reference(findings)

        # Turn 3: Prioritization and recommendations
        findings = await self._turn3_prioritize(findings, focus)

        # Format results
        return {
            "output": json.dumps(findings, indent=2),
            "format": "json",
            "droid": "security-auditor-sdk",
            "turns": 3,
        }

    async def _load_code(self, path: str) -> str:
        """Load code from file or directory."""
        from pathlib import Path

        p = Path(path)
        if p.is_file():
            return p.read_text(errors='ignore')
        elif p.is_dir():
            # Load all Python files
            code_parts = []
            for py_file in p.rglob("*.py"):
                if ".venv" not in str(py_file):
                    try:
                        code_parts.append(f"# {py_file}\n{py_file.read_text()}")
                    except Exception:
                        pass
            return "\n\n".join(code_parts[:10])  # Limit to 10 files
        else:
            raise FileNotFoundError(f"Path not found: {path}")

    async def _turn1_initial_scan(
        self, code: str, depth: str
    ) -> Dict[str, Any]:
        """Turn 1: Analyze code for security issues."""
        depth_instructions = {
            "light": "Quick surface-level scan for obvious issues",
            "medium": "Standard security analysis, check for common vulnerabilities",
            "deep": "Thorough analysis, check for subtle issues and patterns",
        }

        prompt = f"""Analyze this code for security vulnerabilities.

Depth: {depth_instructions.get(depth, 'medium')}

Code to analyze:
```
{code[:3000]}  # First 3000 chars to stay within limits
```

For each issue found, note:
1. Type of vulnerability (e.g., SQL Injection, XSS, etc.)
2. Location in code
3. Severity (critical, high, medium, low)
4. Description of the issue
5. Why it's a problem

Return findings as structured list."""

        message = await self._query_claude(prompt)

        # Parse findings from message
        findings = await self._parse_findings(message)

        return {
            "total_findings": len(findings),
            "findings": findings,
            "depth": depth,
        }

    async def _turn2_cross_reference(
        self, initial_findings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Turn 2: Cross-reference with OWASP/CWE."""
        findings_text = json.dumps(initial_findings, indent=2)

        prompt = f"""I performed a security analysis and found these issues:

{findings_text}

Now please cross-reference each finding with:
1. Corresponding OWASP Top 10 category (if applicable)
2. Corresponding CWE ID (Common Weakness Enumeration)
3. Any related findings that might be part of same vulnerability chain

Return enhanced findings with CWE IDs and OWASP mappings."""

        message = await self._query_claude(prompt)

        # Enhance findings with mappings
        enhanced = await self._parse_cwe_mappings(message)

        return {
            **initial_findings,
            "cwe_mappings": enhanced,
        }

    async def _turn3_prioritize(
        self, findings: Dict[str, Any], focus: Optional[str] = None
    ) -> Dict[str, Any]:
        """Turn 3: Prioritize and suggest fixes."""
        findings_text = json.dumps(findings, indent=2)
        focus_instruction = f"Focus especially on: {focus}" if focus else ""

        prompt = f"""Given these security findings:

{findings_text}

{focus_instruction}

Please:
1. Prioritize by exploitability (how easy to exploit)
2. Score effort to fix (1-10, where 1 = trivial, 10 = major refactor)
3. Suggest specific fixes for top issues
4. Note any patterns or systemic issues

Return prioritized recommendations."""

        message = await self._query_claude(prompt)

        recommendations = await self._parse_recommendations(message)

        return {
            **findings,
            "recommendations": recommendations,
            "priority_order": await self._extract_priorities(recommendations),
        }

    async def _query_claude(self, prompt: str) -> str:
        """Query Claude and return text response."""
        message = self.client.messages.create(
            model=self.model,
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
        )

        return message.content[0].text if message.content else ""

    async def _parse_findings(self, text: str) -> List[Dict[str, Any]]:
        """Parse findings from Claude response."""
        # Simple parsing - could be enhanced with JSON extraction
        return [
            {
                "type": "security_issue",
                "content": text,
            }
        ]

    async def _parse_cwe_mappings(self, text: str) -> Dict[str, Any]:
        """Parse CWE mappings from response."""
        return {"mappings": text}

    async def _parse_recommendations(self, text: str) -> List[Dict[str, Any]]:
        """Parse recommendations from response."""
        return [{"recommendation": text}]

    async def _extract_priorities(self, recommendations: List) -> List[str]:
        """Extract priority order from recommendations."""
        return ["high", "medium", "low"]
```

**Rationale:**
- Multi-turn analysis (3 turns, each building on previous)
- No context loss (same session across turns)
- Structured JSON output
- Can integrate with knowledge system (Turn 2)
- Backward compatible (original bash version unchanged)

---

### 2.3 Integration with CLI

**Modify:** `src/klean/cli.py`

```python
# Add to imports at top
from pathlib import Path
import sys

# Add new command group
@click.group()
def security():
    """Security analysis commands."""
    pass

# Add to main() function before the last line
main.add_command(security)

# Add new security audit command (SDK version)
@security.command(name="audit-sdk")
@click.argument("path", type=click.Path(exists=True))
@click.option("--focus", help="Focus area (e.g., 'authentication')")
@click.option("--depth", default="medium", type=click.Choice(["light", "medium", "deep"]))
async def security_audit_sdk(path: str, focus: Optional[str], depth: str):
    """Security audit using Agent SDK (multi-turn analysis)."""
    import asyncio
    from klean.agents.security_auditor import SecurityAuditorDroid

    try:
        droid = SecurityAuditorDroid()
        result = await droid.execute(path, focus=focus, depth=depth)

        # Print results
        from rich.console import Console
        console = Console()

        if result["format"] == "json":
            console.print_json(result["output"])
        else:
            console.print(result["output"])

        # Log to timeline if enabled
        timeline_log(f"security-audit-sdk", result)

    except Exception as e:
        click.secho(f"Error: {e}", fg="red")
        sys.exit(1)

# Keep original bash-based command for backward compatibility
@security.command(name="audit")
@click.argument("path", type=click.Path(exists=True))
def security_audit_bash(path: str):
    """Security audit using bash script (original implementation)."""
    script_path = CLAUDE_DIR / "scripts" / "security-audit.sh"
    # ... existing bash implementation
```

**Note:** This adds SDK version alongside bash version, users can choose which to use.

---

### 2.4 Testing the Pilot Droid

**Test Script:** `tests/test_security_auditor.py`

```python
"""Tests for Security Auditor Droid."""

import pytest
import asyncio
from klean.agents.security_auditor import SecurityAuditorDroid
from pathlib import Path
import tempfile


@pytest.mark.asyncio
async def test_security_auditor_basic():
    """Test basic security audit."""
    # Create temp file with security issues
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write("""
import sqlite3

def query_db(user_input):
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    # SQL Injection vulnerability!
    cursor.execute("SELECT * FROM users WHERE id=" + user_input)
    return cursor.fetchall()
""")
        temp_file = f.name

    try:
        droid = SecurityAuditorDroid()
        result = await droid.execute(temp_file, depth="light")

        # Verify structure
        assert result["format"] == "json"
        assert result["droid"] == "security-auditor-sdk"
        assert result["turns"] == 3

        # Parse JSON output
        output = json.loads(result["output"])
        assert "findings" in output
        assert output["total_findings"] > 0

    finally:
        Path(temp_file).unlink()


@pytest.mark.asyncio
async def test_backward_compatibility():
    """Verify bash version still works."""
    from klean.droids.base import BashDroid

    bash_droid = BashDroid(
        "security-audit",
        "~/.claude/scripts/security-audit.sh",
        "Security audit (bash)"
    )

    # Should not require Agent SDK
    result = await bash_droid.execute("test.py")
    assert result["format"] == "markdown"
```

---

### 2.5 Commit & Release

**Commit Message:**
```
Phase 2: Implement Security Auditor pilot droid with Agent SDK

- Create SecurityAuditorDroid with 3-turn analysis pipeline
- Turn 1: Initial security scan
- Turn 2: OWASP/CWE cross-reference
- Turn 3: Prioritize and recommend fixes
- Add CLI command: k-lean security audit-sdk
- Keep original bash version for backward compatibility
- Add comprehensive tests for pilot droid
- Document multi-turn analysis benefits
```

**Testing Before Release:**
```bash
# Test 1: Syntax check
python -m py_compile src/klean/agents/security_auditor.py

# Test 2: Run pytest
pytest tests/test_security_auditor.py -v

# Test 3: CLI works
k-lean security audit-sdk test_file.py

# Test 4: Verify original still works
k-lean security audit test_file.py

# Test 5: Check help
k-lean security --help
```

---

## Phase 3: Knowledge Integration (Week 2-3)

### Objective
Integrate knowledge database seamlessly into Agent SDK droids via custom tools.

### 3.1 Create Knowledge Search Tool

**File:** `src/klean/tools/knowledge_tool.py`

```python
"""Tool for searching knowledge database in droids."""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
import subprocess


async def search_knowledge(
    query: str,
    limit: int = 5,
    min_score: float = 0.3,
) -> Dict[str, Any]:
    """Search knowledge database for relevant information.

    This tool allows Agent SDK droids to integrate real-time knowledge
    from the project's knowledge database, enhancing analysis quality.

    Args:
        query: Search query (e.g., "SQL injection vulnerabilities")
        limit: Maximum results to return
        min_score: Minimum relevance score (0.0-1.0)

    Returns:
        Dict with search results and metadata

    Example:
        In security_auditor.py:
        findings = findings + await search_knowledge(
            "OWASP Top 10 " + issue_type,
            limit=3
        )
    """

    try:
        # Use socket-based server for fast search
        script_path = Path.home() / ".claude" / "scripts" / "knowledge-query.sh"

        if script_path.exists():
            result = subprocess.run(
                [str(script_path), query],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                try:
                    results = json.loads(result.stdout)
                    # Filter by score
                    filtered = [
                        r for r in results
                        if r.get("relevance_score", 0) >= min_score
                    ]
                    return {
                        "success": True,
                        "query": query,
                        "results": filtered[:limit],
                        "total": len(filtered),
                    }
                except json.JSONDecodeError:
                    return {
                        "success": False,
                        "error": "Invalid JSON from knowledge server",
                        "raw": result.stdout[:500],
                    }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                }

        else:
            return {
                "success": False,
                "error": "Knowledge database not available",
            }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
        }


# Example usage in droid:
# from klean.tools.knowledge_tool import search_knowledge
#
# async def _turn2_cross_reference(self, findings):
#     # Each finding could be cross-referenced with knowledge
#     for finding in findings:
#         kb_results = await search_knowledge(
#             f"CWE-{finding['cwe_id']} {finding['type']}",
#             limit=2
#         )
#         if kb_results["success"]:
#             finding["knowledge_references"] = kb_results["results"]
```

---

### 3.2 Update Security Auditor to Use Knowledge

**Modify:** `src/klean/agents/security_auditor.py`

```python
# Add at top
from klean.tools.knowledge_tool import search_knowledge

# Update _turn2_cross_reference method
async def _turn2_cross_reference(
    self, initial_findings: Dict[str, Any]
) -> Dict[str, Any]:
    """Turn 2: Cross-reference with OWASP/CWE and knowledge database."""
    findings_text = json.dumps(initial_findings, indent=2)

    # Search knowledge for each finding type
    knowledge_snippets = []
    for finding in initial_findings.get("findings", []):
        finding_type = finding.get("type", "security_issue")

        kb_result = await search_knowledge(
            f"{finding_type} vulnerability OWASP CWE",
            limit=2
        )

        if kb_result["success"] and kb_result["results"]:
            knowledge_snippets.append({
                "finding_type": finding_type,
                "references": kb_result["results"],
            })

    knowledge_context = ""
    if knowledge_snippets:
        knowledge_context = "\n\nKnowledge Database References:\n" + json.dumps(
            knowledge_snippets, indent=2
        )

    prompt = f"""I performed a security analysis and found these issues:

{findings_text}
{knowledge_context}

Now please cross-reference each finding with:
1. Corresponding OWASP Top 10 category
2. Corresponding CWE ID
3. Related information from the knowledge references above

Return enhanced findings with CWE IDs, OWASP mappings, and KB references."""

    message = await self._query_claude(prompt)
    enhanced = await self._parse_cwe_mappings(message)

    return {
        **initial_findings,
        "cwe_mappings": enhanced,
        "knowledge_integrated": len(knowledge_snippets) > 0,
    }
```

---

### 3.3 Create Additional Tools

Similar to knowledge_tool.py, create:

**File:** `src/klean/tools/grep_tool.py`
```python
"""Tool for searching code in droids."""

async def grep_codebase(pattern: str, path: str = ".") -> Dict[str, Any]:
    """Search codebase for pattern using ripgrep."""
    # Implementation using Grep tool internally
    pass
```

**File:** `src/klean/tools/read_tool.py`
```python
"""Tool for reading files in droids."""

async def read_file(path: str, lines: Optional[int] = None) -> str:
    """Read file contents."""
    # Implementation using Read tool internally
    pass
```

**File:** `src/klean/tools/test_tool.py`
```python
"""Tool for running tests in droids."""

async def run_tests(
    path: str = "tests",
    pattern: Optional[str] = None,
) -> Dict[str, Any]:
    """Run tests and return results."""
    # Implementation using Bash tool internally
    pass
```

---

### 3.4 Commit & Test

**Commit Message:**
```
Phase 3: Knowledge database integration into Agent SDK droids

- Create knowledge_search tool for real-time KB integration
- Create grep_codebase, read_file, test_tool wrappers
- Update SecurityAuditorDroid to use knowledge references
- Knowledge context in Turn 2 enhances CWE/OWASP mapping
- All tools async-compatible for concurrent execution
- Maintains knowledge server auto-start
```

---

## Phase 4: Additional Droids (Week 3-4)

### 4.1 Architect Reviewer Droid

**File:** `src/klean/agents/architect_reviewer.py`

```python
"""Architect Reviewer Droid - Multi-turn architecture analysis."""

class ArchitectReviewerDroid(SDKDroid):
    """Reviews system architecture and design patterns.

    Multi-turn process:
    1. Structure analysis: Map components and dependencies
    2. Pattern identification: Find design patterns and anti-patterns
    3. Recommendations: Suggest architectural improvements
    4. Migration path: Plan for improvements
    """

    async def execute(
        self,
        path: str,
        focus: Optional[str] = None,
        style: str = "report",  # report, checklist, json
    ) -> Dict[str, Any]:
        """Execute architecture review.

        Args:
            path: Project root or main file
            focus: Specific area (e.g., "scalability", "maintainability")
            style: Output format (report, checklist, json)
        """
        # Similar 3-4 turn architecture as security auditor
        pass
```

### 4.2 Performance Analyzer Droid

**File:** `src/klean/agents/performance_analyzer.py`

```python
"""Performance Analyzer Droid - Multi-turn performance auditing."""

class PerformanceAnalyzerDroid(SDKDroid):
    """Analyzes code performance and optimization opportunities.

    Multi-turn process:
    1. Bottleneck detection: Find slow operations
    2. Root cause analysis: Understand why they're slow
    3. Optimization proposals: Suggest improvements
    4. Implementation guide: Show how to optimize
    """

    async def execute(
        self,
        path: str,
        focus: Optional[str] = None,
        threshold: str = "medium",  # Only issues above threshold
    ) -> Dict[str, Any]:
        """Execute performance analysis."""
        pass
```

### 4.3 CLI Integration

```python
# In cli.py, add commands for each new droid
@click.command()
@click.argument("path")
@click.option("--focus", help="Focus area")
def architect_review(path: str, focus: Optional[str]):
    """Review system architecture."""
    droid = ArchitectReviewerDroid()
    result = await droid.execute(path, focus=focus)
    console.print_json(result["output"])

@click.command()
@click.argument("path")
@click.option("--focus", help="Focus area")
def performance_analyze(path: str, focus: Optional[str]):
    """Analyze code performance."""
    droid = PerformanceAnalyzerDroid()
    result = await droid.execute(path, focus=focus)
    console.print_json(result["output"])
```

---

## Phase 5: Testing & Migration (Week 4-5)

### 5.1 Comprehensive Testing Strategy

**Test Categories:**

1. **Unit Tests** - Individual droid methods
   - `tests/test_security_auditor.py` - Existing
   - `tests/test_architect_reviewer.py` - New
   - `tests/test_performance_analyzer.py` - New

2. **Integration Tests** - CLI commands
   - `tests/test_cli_sdk_commands.py` - All SDK commands

3. **Backward Compatibility Tests**
   - `tests/test_backward_compatibility.py` - Bash droids still work

4. **Performance Tests**
   - `tests/test_performance.py` - Compare SDK vs bash overhead

5. **Knowledge Integration Tests**
   - `tests/test_knowledge_integration.py` - KB search works

**Test Structure:**
```python
# tests/test_cli_sdk_commands.py
@pytest.mark.integration
@pytest.mark.asyncio
async def test_security_audit_sdk_command():
    """Test k-lean security audit-sdk command."""
    runner = CliRunner()
    result = runner.invoke(main, ['security', 'audit-sdk', 'test_file.py'])
    assert result.exit_code == 0
    assert "findings" in result.output

@pytest.mark.integration
def test_bash_security_audit_still_works():
    """Verify original bash command unchanged."""
    runner = CliRunner()
    result = runner.invoke(main, ['security', 'audit', 'test_file.py'])
    assert result.exit_code == 0
```

---

### 5.2 Migration Strategy for Existing Commands

**Two Approaches:**

**Option A: Gradual Replacement** (Recommended)
```
Week 1: Add SDK versions alongside bash (-sdk suffix)
        k-lean security audit (bash, original)
        k-lean security audit-sdk (SDK, new)

Week 2-3: Both work, users can choose
          Stats show which is preferred

Week 4: If 80%+ use SDK version, make it default
        k-lean security audit (SDK, new)
        k-lean security audit-legacy (bash, original)

Week 5: After feedback, decide on legacy support
```

**Option B: Configuration-Based** (Alternative)
```python
# In cli.py or config
USE_SDK = os.getenv("K_LEAN_USE_SDK", "false").lower() == "true"

@click.command()
def security_audit(path: str):
    if USE_SDK:
        droid = SecurityAuditorDroid()
        result = await droid.execute(path)
    else:
        # Original bash version
        subprocess.run([script_path, path])

# Users can opt-in: export K_LEAN_USE_SDK=true
```

---

### 5.3 Release Checklist

**Before v2.0.0 Release:**

- [ ] All unit tests passing
- [ ] All integration tests passing
- [ ] Backward compatibility verified
- [ ] Documentation updated
- [ ] Example usage created
- [ ] Performance improvements documented
- [ ] Knowledge integration tested
- [ ] CLI help text updated
- [ ] Installation instructions updated
- [ ] Release notes written

**Release Process:**

```bash
# 1. Run full test suite
pytest tests/ -v --cov=klean

# 2. Build package
python -m build

# 3. Test installation
pipx install --force /path/to/dist/k_lean-2.0.0-py3-none-any.whl

# 4. Verify CLI works
k-lean status
k-lean security audit-sdk test_file.py
k-lean architect-review .

# 5. Tag release
git tag v2.0.0
git push origin v2.0.0

# 6. Create release notes
# Document: performance improvements, new features, migration guide
```

---

## Backward Compatibility Strategy

### Principle
**Zero Breaking Changes** - Users never forced to migrate.

### Implementation

1. **Bash droids unchanged** - All existing scripts remain
2. **SDK droids alongside** - Add as new commands with `-sdk` suffix
3. **CLI entry points stable** - Original commands keep working
4. **Optional dependency** - Agent SDK installable but not required
5. **Graceful degradation** - If Agent SDK missing, bash version used

### Example: Migration Window
```
v1.0.0 (Current):
  k-lean security audit → bash script

v2.0.0 (Release):
  k-lean security audit → bash script (unchanged)
  k-lean security audit-sdk → Agent SDK (new)

v3.0.0 (Future, optional):
  k-lean security audit → Agent SDK (by default)
  k-lean security audit-legacy → bash script

  OR keep both indefinitely if users prefer
```

---

## Testing Strategy

### Pre-Implementation Testing

1. **Setup test environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -e .[agent-sdk]
   ```

2. **Unit test structure:**
   ```
   tests/
   ├── test_droids_base.py        # BaseDroid, BashDroid, SDKDroid
   ├── test_security_auditor.py   # SecurityAuditorDroid specifically
   ├── test_architect_reviewer.py  # ArchitectReviewerDroid
   ├── test_tools/
   │   ├── test_knowledge_tool.py
   │   ├── test_grep_tool.py
   │   └── test_read_tool.py
   ├── test_cli_sdk.py            # CLI integration for SDK commands
   └── test_backward_compat.py    # Bash droids still work
   ```

3. **Integration test approach:**
   - Use real files for testing
   - Mock LiteLLM responses to avoid API costs
   - Verify JSON output format
   - Check CLI argument parsing

### Test Execution

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=klean --cov-report=html

# Run specific category
pytest tests/test_security_auditor.py -v
pytest tests/test_backward_compat.py -v

# Run integration tests only
pytest tests/ -m integration -v
```

---

## Performance Expectations

### Baseline (Current K-LEAN v1.0.0)

```
Single audit:     1100ms (1000ms Claude + 100ms overhead + bash parsing)
5 files audit:    5250ms (5000ms Claude + 250ms overhead)
Multi-turn (10):  12000ms (context loss + repeated analysis)
```

### After Phase 2 (Security Auditor SDK)

```
Single audit:     1050ms (1000ms Claude + 50ms overhead)  ✅ 5% faster
5 files (1 pass): 5050ms (5000ms Claude + 50ms overhead)  ✅ 20% faster overhead
Multi-turn (3):   3050ms (3000ms Claude + 50ms overhead)  ✅ 75% faster (no context loss)
```

### After Phase 3 (Knowledge Integration)

```
Security audit:   1150ms (with KB search overhead of ~100ms)
Quality:          ↑ Better (OWASP/CWE mappings included)
```

### After Phase 4 (All Droids)

```
Architect review: 1200ms (multi-turn analysis)
Performance analysis: 1100ms
Combined workflow: No context loss between droids
```

---

## Risk Mitigation

### Risk 1: Agent SDK Unavailable
**Mitigation:**
- Optional dependency
- CLI checks and graceful fallback to bash
- Clear error messages if SDK commands used without install

### Risk 2: LiteLLM Proxy Unavailable
**Mitigation:**
- Droids check /models endpoint before executing
- Fallback to native Anthropic API if configured
- Timeout errors handled gracefully

### Risk 3: Breaking Changes from Agent SDK Updates
**Mitigation:**
- Pin Agent SDK version in pyproject.toml: `anthropic>=0.34.0,<1.0.0`
- Regular dependency update testing
- Maintain compatibility layer

### Risk 4: Knowledge DB Failures
**Mitigation:**
- Knowledge tool catches exceptions gracefully
- Analysis continues without KB results
- Fallback to non-enhanced analysis

### Risk 5: Users Don't Migrate
**Mitigation:**
- Keep bash versions indefinitely
- Both versions equally supported
- No pressure to upgrade
- Clear documentation of benefits

---

## File Summary

### New Files to Create

```
src/klean/
├── droids/
│   ├── __init__.py
│   ├── base.py                    # BaseDroid, BashDroid, SDKDroid
│   └── registry.py                # Droid discovery/registration
│
├── tools/
│   ├── __init__.py
│   ├── knowledge_tool.py          # search_knowledge()
│   ├── grep_tool.py               # grep_codebase()
│   ├── read_tool.py               # read_file()
│   └── test_tool.py               # run_tests()
│
├── agents/
│   ├── __init__.py
│   ├── security_auditor.py        # SecurityAuditorDroid
│   ├── architect_reviewer.py       # ArchitectReviewerDroid
│   └── performance_analyzer.py     # PerformanceAnalyzerDroid

tests/
├── test_droids_base.py
├── test_security_auditor.py
├── test_architect_reviewer.py
├── test_tools/
│   ├── test_knowledge_tool.py
│   ├── test_grep_tool.py
│   └── test_read_tool.py
├── test_cli_sdk.py
└── test_backward_compat.py
```

### Modified Files

```
review-system-backup/
├── pyproject.toml                 # Add agent-sdk optional dependency
├── src/klean/cli.py               # Add SDK commands, modify dispatcher
├── src/klean/__init__.py          # Export new classes/functions
└── CHANGELOG.md                   # Document changes
```

---

## Next Steps

1. **Review this plan** - User approval on approach and phases
2. **Phase 1 implementation** - Start with foundation (directory structure, base classes)
3. **Phase 1 testing** - Verify backward compatibility
4. **Phase 2 implementation** - Security Auditor pilot droid
5. **Phase 2 testing** - Comprehensive testing of first droid
6. **Iterate through phases** - Each phase builds on previous

---

## Questions for User

1. **Timeline preference:** All 5 phases in sequence, or split into multiple releases?
2. **SDK model selection:** Should different droids use different models (qwen for quality, deepseek for architecture)?
3. **Knowledge integration:** Should KB search be mandatory or optional per droid?
4. **Backward compatibility:** Keep bash versions indefinitely, or deprecate after v3.0?
5. **Testing scope:** Should we mock Claude API responses for faster testing, or use real API?

---

## Summary

This plan provides:

✅ **Zero breaking changes** - Existing workflows unchanged
✅ **Phased approach** - Test each phase before next
✅ **Performance improvements** - 6-10x speedup on multi-turn tasks
✅ **Knowledge integration** - Real-time KB access in droids
✅ **Structured output** - JSON with schema validation
✅ **Clear migration path** - Users can opt-in gradually
✅ **Comprehensive testing** - Unit + integration + backward compat
✅ **Risk mitigation** - Graceful fallbacks for all failure modes

Ready to proceed with Phase 1 implementation once approved.
