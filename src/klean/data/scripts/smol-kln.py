#!/usr/bin/env python3
"""SmolKLN CLI - Run SmolKLN agents from command line.

Usage:
    smol-kln.py <agent> <task> [--model MODEL] [--telemetry]
    smol-kln.py --list
    smol-kln.py --help

Examples:
    smol-kln.py security-auditor "audit authentication module"
    smol-kln.py code-reviewer "review main.py" --model qwen3-coder
    smol-kln.py security-auditor "audit auth" --telemetry  # With tracing
    smol-kln.py --list
"""

import argparse
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Run SmolKLN agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s security-auditor "audit auth module"
  %(prog)s code-reviewer "review main.py" --model qwen3-coder
  %(prog)s --list
        """
    )
    parser.add_argument("agent", nargs="?", help="Agent name (e.g., security-auditor)")
    parser.add_argument("task", nargs="?", help="Task description")
    parser.add_argument("--model", "-m", help="Override model")
    parser.add_argument("--list", "-l", action="store_true", help="List available agents")
    parser.add_argument("--api-base", default="http://localhost:4000", help="LiteLLM API base URL")
    parser.add_argument("--telemetry", "-t", action="store_true",
                        help="Enable Phoenix telemetry (view at localhost:6006)")

    args = parser.parse_args()

    # Setup telemetry if requested
    if args.telemetry:
        try:
            from phoenix.otel import register
            from openinference.instrumentation.smolagents import SmolagentsInstrumentor

            register(project_name="smolkln")
            SmolagentsInstrumentor().instrument()
            print("📊 Telemetry enabled - view at http://localhost:6006")
        except ImportError:
            print("⚠️  Telemetry not installed. Run: pipx inject k-lean 'k-lean[telemetry]'")

    # Check if smolagents is installed
    try:
        from klean.smol import SmolKLNExecutor, list_available_agents
    except ImportError:
        print("Error: smolagents not installed.")
        print("Install with: pipx inject k-lean 'smolagents[litellm]' 'txtai[ann]'")
        sys.exit(1)

    # List agents
    if args.list:
        agents_dir = Path.home() / ".klean" / "agents"
        if not agents_dir.exists():
            print("No agents installed. Run: k-lean install")
            sys.exit(1)

        agents = list_available_agents(agents_dir)
        print("Available SmolKLN agents:")
        for agent in agents:
            print(f"  - {agent}")
        sys.exit(0)

    # Validate args
    if not args.agent:
        parser.print_help()
        sys.exit(1)

    if not args.task:
        print(f"Error: Task description required for agent '{args.agent}'")
        sys.exit(1)

    # Execute agent
    try:
        executor = SmolKLNExecutor(api_base=args.api_base)
        print(f"Running {args.agent}...")
        print(f"Project: {executor.project_root}")
        print("-" * 60)

        result = executor.execute(
            args.agent,
            args.task,
            model_override=args.model
        )

        if result["success"]:
            print(result["output"])
            print("-" * 60)
            print(f"✓ Completed in {result['duration_s']}s using {result['model']}")
        else:
            print(f"✗ Error: {result['output']}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
