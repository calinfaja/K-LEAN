#!/usr/bin/env python3
"""
K-LEAN Smart Capture - LLM-Evaluated Knowledge Capture

Evaluates external content (URLs, files) using LiteLLM to determine
if it's worth saving to the knowledge database.

This is the "SaveInfo" command - for capturing external content.
For saving insights from conversation, use /kln:learn (context-aware extraction).

Usage:
  smart-capture.py <url> [--search-context "query"]
  smart-capture.py --file <path> [--search-context "context"]

Features:
- Fetches URL content or reads file
- Sends to LiteLLM for evaluation
- Generates structured V2 schema entry
- Saves to knowledge database if valuable

Environment:
  LITELLM_URL - LiteLLM proxy URL (default: http://localhost:4000)
  LITELLM_MODEL - Model to use (default: qwen3-coder)
"""

import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

# Import shared utilities
try:
    from kb_utils import (  # noqa: F401
        PYTHON_BIN,
        debug_log,
        find_project_root,
        get_socket_path,
        is_server_running,
    )
except ImportError:
    # Fallback for standalone use
    sys.path.insert(0, str(Path(__file__).parent))
    from kb_utils import (
        PYTHON_BIN,
        find_project_root,
    )

# Allowed URL schemes for security
ALLOWED_URL_SCHEMES = {"http", "https"}

# =============================================================================
# Configuration
# =============================================================================
LITELLM_URL = os.environ.get("LITELLM_URL", "http://localhost:4000")
LITELLM_MODEL = os.environ.get("LITELLM_MODEL", "qwen3-coder")

# Evaluation prompt for LiteLLM
EVAL_PROMPT = """Analyze this content and determine if it's worth saving to a knowledge database.

Content source: {source_type}
Search context: {search_context}
Content:
```
{content}
```

If the content is valuable (provides useful information, solutions, patterns, or insights),
respond with a JSON object containing:
{{
  "save": true,
  "title": "Short descriptive title (max 100 chars)",
  "summary": "2-3 sentence summary of key information",
  "atomic_insight": "One-sentence actionable takeaway",
  "key_concepts": ["concept1", "concept2", "concept3"],
  "quality": "high|medium|low",
  "type": "web|solution|pattern|reference",
  "save_reason": "Why this is worth saving"
}}

If the content is NOT worth saving (irrelevant, too generic, error page, etc.),
respond with:
{{
  "save": false,
  "reason": "Why this is not worth saving"
}}

Respond with ONLY the JSON object, no other text."""


# =============================================================================
# Helpers
# =============================================================================
def fetch_url(url: str, max_chars: int = 15000) -> str:
    """Fetch URL content with scheme validation."""
    # Validate URL scheme to prevent SSRF attacks
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme.lower() not in ALLOWED_URL_SCHEMES:
        return f"Error: Invalid URL scheme '{parsed.scheme}'. Only http/https allowed."
    if not parsed.netloc:
        return "Error: Invalid URL - no hostname specified."

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "K-LEAN-SmartCapture/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode("utf-8", errors="ignore")
            if len(content) > max_chars:
                content = content[:max_chars] + "\n... [truncated]"
            return content
    except Exception as e:
        return f"Error fetching URL: {e}"


def read_file(path: str, max_chars: int = 15000) -> str:
    """Read file content."""
    try:
        with open(path, errors="ignore") as f:
            content = f.read()
            if len(content) > max_chars:
                content = content[:max_chars] + "\n... [truncated]"
            return content
    except Exception as e:
        return f"Error reading file: {e}"


def call_litellm(prompt: str) -> dict:
    """Call LiteLLM API for evaluation."""
    try:
        data = json.dumps(
            {
                "model": LITELLM_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 1000,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            f"{LITELLM_URL}/v1/chat/completions",
            data=data,
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode())
            content = result["choices"][0]["message"]["content"]

            # Handle thinking models that wrap response
            if "<think>" in content:
                # Extract content after </think>
                parts = content.split("</think>")
                if len(parts) > 1:
                    content = parts[-1].strip()

            # Try to parse JSON from response
            # Handle markdown code blocks with bounds checking
            if "```json" in content:
                parts = content.split("```json")
                if len(parts) > 1:
                    inner = parts[1].split("```")
                    if inner:
                        content = inner[0].strip()
            elif "```" in content:
                parts = content.split("```")
                if len(parts) > 1:
                    content = parts[1].strip()

            return json.loads(content)

    except urllib.request.URLError:
        return {"save": False, "reason": "LiteLLM not available"}
    except json.JSONDecodeError:
        return {"save": False, "reason": "Invalid response from LiteLLM"}
    except Exception as e:
        return {"save": False, "reason": f"Error: {e}"}


def save_to_kb(entry: dict, project_path: Path) -> bool:
    """Save entry to knowledge database."""
    import os
    import subprocess

    # Use KB_SCRIPTS_DIR from environment or kb_utils
    from kb_utils import KB_SCRIPTS_DIR

    script = KB_SCRIPTS_DIR / "knowledge-capture.py"

    if not script.exists():
        return False

    python = str(PYTHON_BIN) if PYTHON_BIN.exists() else "python3"

    try:
        result = subprocess.run(
            [python, str(script), "--json-input", json.dumps(entry), "--json"],
            capture_output=True,
            text=True,
            cwd=str(project_path),
            env={**os.environ, "CLAUDE_PROJECT_DIR": str(project_path)},
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


# =============================================================================
# Main
# =============================================================================
def main():
    parser = argparse.ArgumentParser(
        description="Smart capture with LLM evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("url", nargs="?", help="URL to capture")
    parser.add_argument("--file", "-f", help="File path to capture")
    parser.add_argument(
        "--search-context", "-c", default="", help="Search context for relevance evaluation"
    )
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--dry-run", action="store_true", help="Evaluate but do not save")

    args = parser.parse_args()

    # Must have URL or file
    if not args.url and not args.file:
        parser.error("Either URL or --file is required")

    # Find project root
    project_root = find_project_root()
    if not project_root:
        if args.json:
            print(json.dumps({"error": "No project root found"}))
        else:
            print("Error: No project root found", file=sys.stderr)
        return 1

    # Determine source type and fetch content
    if args.url:
        source_type = "web"
        source_path = args.url
        content = fetch_url(args.url)
    else:
        source_type = "file"
        source_path = args.file
        content = read_file(args.file)

    if content.startswith("Error"):
        if args.json:
            print(json.dumps({"error": content}))
        else:
            print(f"Error: {content}", file=sys.stderr)
        return 1

    # Build evaluation prompt
    prompt = EVAL_PROMPT.format(
        source_type=source_type,
        search_context=args.search_context or "(none provided)",
        content=content[:10000],  # Further limit for prompt
    )

    # Call LiteLLM for evaluation
    if not args.json:
        print(f"Evaluating content from {source_path[:50]}...", file=sys.stderr)

    result = call_litellm(prompt)

    if not result.get("save", False):
        if args.json:
            print(json.dumps({"saved": False, "reason": result.get("reason", "Not worth saving")}))
        else:
            print(f"Not saved: {result.get('reason', 'Not worth saving')}")
        return 0

    # Build entry with V2 schema
    entry = {
        "title": result.get("title", "")[:100],
        "summary": result.get("summary", ""),
        "atomic_insight": result.get("atomic_insight", ""),
        "key_concepts": result.get("key_concepts", []),
        "quality": result.get("quality", "medium"),
        "type": result.get("type", "web"),
        "source": f"smart-{source_type}",
        "source_path": source_path,
        "tags": result.get("key_concepts", [])[:5],  # Use concepts as tags
        "found_date": datetime.now().isoformat(),
        "relevance_score": 0.85,
        "save_reason": result.get("save_reason", ""),
        "auto_captured": True,
        "search_context": args.search_context,
    }

    if args.url:
        entry["url"] = args.url

    if args.dry_run:
        if args.json:
            print(json.dumps({"would_save": True, "entry": entry}))
        else:
            print("Would save (dry run):")
            print(json.dumps(entry, indent=2))
        return 0

    # Save to knowledge DB
    saved = save_to_kb(entry, project_root)

    if args.json:
        print(
            json.dumps(
                {
                    "saved": saved,
                    "title": entry["title"],
                    "type": entry["type"],
                    "atomic_insight": entry.get("atomic_insight", ""),
                }
            )
        )
    else:
        if saved:
            print(f"Saved: {entry['title']}")
            if entry.get("atomic_insight"):
                print(f"Insight: {entry['atomic_insight']}")
        else:
            print("Error: Failed to save to knowledge DB")

    return 0 if saved else 1


if __name__ == "__main__":
    sys.exit(main())
