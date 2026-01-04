"""SmolKLN CLI - Run SmolKLN agents from command line.

Usage:
    kln-smol <agent> <task> [--model MODEL] [--telemetry]
    kln-smol --list
    kln-smol --help

Examples:
    kln-smol security-auditor "audit authentication module"
    kln-smol code-reviewer "review main.py" --model qwen3-coder
    kln-smol security-auditor "audit auth" --telemetry  # With tracing
    kln-smol --list
"""

import argparse
import sys
from pathlib import Path


def main():
    """SmolKLN CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run SmolKLN agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s security-auditor "audit auth module"
  %(prog)s code-reviewer "review main.py" --model qwen3-coder
  %(prog)s --list
        """,
    )
    parser.add_argument("agent", nargs="?", help="Agent name (e.g., security-auditor)")
    parser.add_argument("task", nargs="?", help="Task description")
    parser.add_argument("--model", "-m", help="Override model")
    parser.add_argument("--list", "-l", action="store_true", help="List available agents")
    parser.add_argument("--api-base", default="http://localhost:4000", help="LiteLLM API base URL")
    parser.add_argument(
        "--telemetry",
        "-t",
        action="store_true",
        help="Enable Phoenix telemetry (view at localhost:6006)",
    )

    args = parser.parse_args()

    # Setup telemetry if requested
    if args.telemetry:
        try:
            from openinference.instrumentation.smolagents import SmolagentsInstrumentor
            from phoenix.otel import register

            # Production-ready: batch=True uses BatchSpanProcessor (async, non-blocking)
            # vs default SimpleSpanProcessor (sync, blocking)
            register(
                project_name="smolkln",
                batch=True,
                verbose=False,  # Suppress detailed config output
            )
            SmolagentsInstrumentor().instrument()
            print("Telemetry enabled - view at http://localhost:6006")
        except ImportError:
            print("Warning: Telemetry not installed. Run: pipx inject kln-ai 'kln-ai[telemetry]'")

    # Check if smolagents is installed
    try:
        from klean.smol import SmolKLNExecutor, list_available_agents
    except ImportError:
        print("Error: smolagents not installed.")
        print("Install with: pipx inject kln-ai 'smolagents[litellm]'")
        sys.exit(1)

    # List agents
    if args.list:
        agents_dir = Path.home() / ".klean" / "agents"
        if not agents_dir.exists():
            print("No agents installed. Run: kln install")
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

        result = executor.execute(args.agent, args.task, model_override=args.model)

        if result["success"]:
            print(result["output"])
            print("-" * 60)
            print(f"Completed in {result['duration_s']}s using {result['model']}")
            if result.get("output_file"):
                print(f"Saved to: {result['output_file']}")
            if result.get("memory_persisted", 0) > 0:
                print(f"Persisted {result['memory_persisted']} learnings to Knowledge DB")
        else:
            print(f"Error: {result['output']}")
            if result.get("output_file"):
                print(f"Error log: {result['output_file']}")
            sys.exit(1)

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
