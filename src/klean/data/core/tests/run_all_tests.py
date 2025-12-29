#!/usr/bin/env python3
"""Run all K-LEAN tests.

Usage:
    python run_all_tests.py           # Run all tests
    python run_all_tests.py --unit    # Run only unit tests (fast)
    python run_all_tests.py --cli     # Run only CLI tests (requires LiteLLM)
"""

import argparse
import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_tests(pattern: str = "test_*.py", verbosity: int = 2):
    """Discover and run tests matching pattern."""
    loader = unittest.TestLoader()
    suite = loader.discover(
        start_dir=os.path.dirname(os.path.abspath(__file__)),
        pattern=pattern
    )

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    return result.wasSuccessful()


def main():
    parser = argparse.ArgumentParser(description="Run K-LEAN tests")
    parser.add_argument("--unit", action="store_true",
                       help="Run only unit tests (fast, no LiteLLM required)")
    parser.add_argument("--cli", action="store_true",
                       help="Run only CLI integration tests")
    parser.add_argument("-v", "--verbose", action="count", default=2,
                       help="Increase verbosity")
    args = parser.parse_args()

    print("=" * 60)
    print("K-LEAN Test Suite - httpx to litellm Migration")
    print("=" * 60)
    print()

    if args.unit:
        print("Running unit tests only...")
        print()
        patterns = ["test_llm_client.py", "test_async_completion.py"]
        success = True
        for pattern in patterns:
            print(f"\n--- {pattern} ---")
            success = run_tests(pattern, args.verbose) and success
    elif args.cli:
        print("Running CLI integration tests only...")
        print("(Requires LiteLLM proxy running on localhost:4000)")
        print()
        success = run_tests("test_cli_integration.py", args.verbose)
    else:
        print("Running all tests...")
        print()
        success = run_tests("test_*.py", args.verbose)

    print()
    print("=" * 60)
    if success:
        print("All tests passed!")
        print("=" * 60)
        return 0
    else:
        print("Some tests failed!")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
