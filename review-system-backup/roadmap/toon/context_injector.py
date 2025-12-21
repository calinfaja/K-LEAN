#!/usr/bin/env python3
"""
Context Injector for Droids - Phase 5

Injects relevant knowledge base facts into droid analysis prompts.

Usage:
    from knowledge_context_injector import ContextInjector

    injector = ContextInjector()
    context = injector.inject_context(
        filename="src/auth/oauth2.py",
        limit=5
    )
    # Returns formatted context string with relevant facts

Strategy:
1. Guess domain from filename (security.py → "security")
2. Hybrid search KB for related facts
3. TOON compress if > 10 facts
4. Format as ready-to-inject context

Token savings: 18% when using TOON compression
"""

import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent))

# Import with fallback for hyphenated module name
try:
    from knowledge_hybrid_search import HybridSearch
except ImportError:
    # Try alternative import for hyphenated filename
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "hybrid_search",
        str(Path(__file__).parent / "knowledge-hybrid-search.py")
    )
    if spec and spec.loader:
        hybrid_search = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hybrid_search)
        HybridSearch = hybrid_search.HybridSearch
    else:
        raise ImportError("Could not load knowledge-hybrid-search module")


class ContextInjector:
    """Injects knowledge base context into droid analysis"""

    # Domain mapping from filename patterns
    DOMAIN_PATTERNS = {
        "security": ["auth", "crypto", "jwt", "oauth", "ssl", "tls", "password", "hash"],
        "performance": ["cache", "optimize", "pool", "latency", "throughput", "ble", "power"],
        "architecture": ["design", "pattern", "api", "microservice", "async", "concurrent"],
        "database": ["db", "sql", "query", "index", "transaction", "connection", "schema"],
        "testing": ["test", "mock", "unit", "integration", "fixture", "coverage"],
        "embedded": ["nrf", "stm32", "avr", "firmware", "iot", "rtos"],
    }

    def __init__(self, project_path: str = None):
        """Initialize context injector"""
        self.search = HybridSearch(project_path)

    def guess_domain(self, filename: str) -> Optional[str]:
        """Guess domain from filename"""
        name = filename.lower()

        # Direct pattern match
        for domain, patterns in self.DOMAIN_PATTERNS.items():
            if any(pattern in name for pattern in patterns):
                return domain

        # Default
        return None

    def inject_context(
        self,
        filename: str,
        limit: int = 5,
        use_toon: bool = True,
    ) -> str:
        """
        Inject knowledge base context for a file.

        Args:
            filename: File being analyzed (e.g., "src/auth/oauth2.py")
            limit: Max facts to include
            use_toon: Use TOON compression for > 10 facts

        Returns:
            Formatted context string ready for prompt injection
        """
        # Guess domain
        domain = self.guess_domain(filename)
        if not domain:
            return ""

        # Search KB for related facts
        results = self.search.search(
            query=domain,
            strategy="hybrid",
            tags=[domain],
            limit=limit * 2,  # Get more to filter
        )

        if not results:
            return ""

        # Filter and format
        facts = []
        for result in results[:limit]:
            facts.append({
                "title": result.get("title"),
                "summary": result.get("summary"),
                "tags": result.get("tags"),
                "usage_count": result.get("usage_count"),
            })

        if not facts:
            return ""

        # Format context
        if use_toon and len(facts) > 10:
            context = self._format_toon(facts, domain)
        else:
            context = self._format_json(facts, domain)

        return context

    def _format_json(self, facts: List[Dict[str, Any]], domain: str) -> str:
        """Format facts as JSON context"""
        header = f"## Related Knowledge: {domain.title()}\n\n"
        items = []
        for i, fact in enumerate(facts, 1):
            item = f"{i}. **{fact['title']}**\n"
            item += f"   {fact['summary'][:100]}...\n"
            if fact.get("usage_count", 0) > 0:
                item += f"   (Reused {fact['usage_count']}x)\n"
            items.append(item)

        return header + "\n".join(items)

    def _format_toon(self, facts: List[Dict[str, Any]], domain: str) -> str:
        """Format facts as TOON-compressed context"""
        try:
            import toon
            compressed = toon.encode(facts)
            return f"Related knowledge [{domain}]: {compressed[:200]}..."
        except ImportError:
            # Fallback to JSON if TOON not available
            return self._format_json(facts, domain)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Inject knowledge context")
    parser.add_argument("filename", help="File being analyzed")
    parser.add_argument("--limit", "-n", type=int, default=5, help="Max facts")
    parser.add_argument("--project", "-p", help="Project path")
    parser.add_argument("--no-toon", action="store_true", help="Disable TOON compression")

    args = parser.parse_args()

    try:
        injector = ContextInjector(args.project)
        context = injector.inject_context(
            filename=args.filename,
            limit=args.limit,
            use_toon=not args.no_toon,
        )

        if context:
            print(context)
        else:
            print(f"No related knowledge found for {args.filename}")

    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
