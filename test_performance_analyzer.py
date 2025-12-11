#!/usr/bin/env python3
"""Test script for PerformanceAnalyzerDroid.

This script tests the PerformanceAnalyzerDroid implementation with sample code
that has known performance issues.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the review-system-backup src to path
sys.path.insert(0, str(Path(__file__).parent / "review-system-backup" / "src"))

from klean.agents.performance_analyzer import PerformanceAnalyzerDroid


# Sample code with performance issues for testing
SAMPLE_CODE = '''
def find_duplicates(data):
    """Find duplicates in a list - inefficient O(n²) implementation."""
    duplicates = []
    for i in range(len(data)):
        for j in range(i + 1, len(data)):
            if data[i] == data[j] and data[i] not in duplicates:
                duplicates.append(data[i])
    return duplicates


def process_users(user_ids):
    """Process users - N+1 query problem."""
    results = []
    for user_id in user_ids:
        # Simulated database query for each user
        user = database.query(f"SELECT * FROM users WHERE id = {user_id}")
        results.append(user)
    return results


def calculate_stats(numbers):
    """Calculate statistics - repeated calculations."""
    total = sum(numbers)
    count = len(numbers)

    # Inefficient: recalculating mean multiple times
    mean = sum(numbers) / len(numbers)
    variance = sum((x - sum(numbers) / len(numbers)) ** 2 for x in numbers) / len(numbers)
    std_dev = (sum((x - sum(numbers) / len(numbers)) ** 2 for x in numbers) / len(numbers)) ** 0.5

    return {"mean": mean, "variance": variance, "std_dev": std_dev}


class DataCache:
    """Cache without cleanup - potential memory leak."""
    def __init__(self):
        self.cache = {}
        self.history = []

    def add(self, key, value):
        self.cache[key] = value
        self.history.append((key, value))  # Growing unbounded

    def get(self, key):
        return self.cache.get(key)


def load_large_file(filepath):
    """Load entire file into memory - memory inefficient."""
    with open(filepath, 'r') as f:
        # Loads entire file at once
        data = f.read()
        lines = data.split('\\n')
        return [line.strip() for line in lines]
'''


async def test_performance_analyzer():
    """Test the PerformanceAnalyzerDroid."""
    print("=" * 70)
    print("Testing PerformanceAnalyzerDroid")
    print("=" * 70)

    # Create a temporary test file
    test_file = Path("/tmp/test_performance_code.py")
    test_file.write_text(SAMPLE_CODE)

    try:
        # Initialize the droid
        print("\n1. Initializing PerformanceAnalyzerDroid...")
        droid = PerformanceAnalyzerDroid()
        print(f"   ✓ Droid initialized: {droid.name}")
        print(f"   ✓ Model: {droid.model}")
        print(f"   ✓ Description: {droid.description}")

        # Execute analysis
        print("\n2. Executing performance analysis...")
        print(f"   Analyzing: {test_file}")
        print("   Depth: medium")

        result = await droid.execute(
            path=str(test_file),
            depth="medium",
            focus="algorithmic complexity"
        )

        print("\n3. Analysis Results:")
        print(f"   ✓ Format: {result['format']}")
        print(f"   ✓ Droid: {result['droid']}")
        print(f"   ✓ Turns completed: {result['turns']}")
        print(f"   ✓ Summary: {result['summary']}")

        # Parse and display structured output
        print("\n4. Detailed Findings:")
        output_data = json.loads(result['output'])

        # Display analysis summary
        summary = output_data.get('analysis_summary', {})
        print(f"\n   Analysis Summary:")
        print(f"   - File: {summary.get('file_path')}")
        print(f"   - Depth: {summary.get('depth')}")
        print(f"   - Turns: {summary.get('turns_completed')}")
        print(f"   - Focus: {summary.get('focus_area')}")

        # Display bottlenecks
        bottlenecks = output_data.get('bottlenecks', [])
        print(f"\n   Bottlenecks Found ({len(bottlenecks)}):")
        for i, bottleneck in enumerate(bottlenecks[:3], 1):
            print(f"   {i}. {bottleneck.get('name', 'Unknown')}")
            print(f"      Location: {bottleneck.get('location', 'Unknown')}")
            print(f"      Type: {bottleneck.get('type', 'Unknown')}")
            print(f"      Severity: {bottleneck.get('severity_score', 0)}/10")

        # Display complexity issues
        complexity_issues = output_data.get('complexity_issues', [])
        print(f"\n   Complexity Issues ({len(complexity_issues)}):")
        for i, issue in enumerate(complexity_issues[:3], 1):
            print(f"   {i}. {issue.get('component', 'Unknown')}")
            print(f"      Current: {issue.get('current_time_complexity', 'Unknown')}")
            print(f"      Optimal: {issue.get('optimal_time_complexity', 'Unknown')}")

        # Display memory issues
        memory_issues = output_data.get('memory_issues', [])
        print(f"\n   Memory Issues ({len(memory_issues)}):")
        for i, issue in enumerate(memory_issues[:3], 1):
            print(f"   {i}. {issue.get('issue_type', 'Unknown')}")
            print(f"      Location: {issue.get('location', 'Unknown')}")
            print(f"      Severity: {issue.get('severity', 'Unknown')}")

        # Display top recommendations
        recommendations = output_data.get('recommendations', [])
        print(f"\n   Top Recommendations ({len(recommendations)}):")
        for i, rec in enumerate(recommendations[:3], 1):
            print(f"   {i}. Priority {rec.get('priority_score', 0)}/10")
            print(f"      Issue: {rec.get('issue', 'Unknown')}")
            print(f"      Expected: {rec.get('expected_improvement', 'Unknown')}")
            print(f"      Complexity: {rec.get('complexity', 'Unknown')}")

        # Display overall scores
        print(f"\n   Overall Scores:")
        print(f"   - Performance: {output_data.get('overall_performance_score', 'N/A')}/10")
        print(f"   - Memory: {output_data.get('memory_score', 'N/A')}/10")
        print(f"   - Worst Complexity: {output_data.get('worst_complexity', 'Unknown')}")

        # Display quick wins
        quick_wins = output_data.get('quick_wins', [])
        if quick_wins:
            print(f"\n   Quick Wins ({len(quick_wins)}):")
            for i, win in enumerate(quick_wins[:3], 1):
                print(f"   {i}. {win}")

        print("\n" + "=" * 70)
        print("✓ Test completed successfully!")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()


async def test_directory_analysis():
    """Test analyzing a directory."""
    print("\n" + "=" * 70)
    print("Testing Directory Analysis")
    print("=" * 70)

    # Use the agents directory itself as test target
    test_dir = Path(__file__).parent / "review-system-backup" / "src" / "klean" / "agents"

    if not test_dir.exists():
        print("✗ Test directory not found, skipping directory test")
        return True

    try:
        print(f"\n1. Analyzing directory: {test_dir}")

        droid = PerformanceAnalyzerDroid()
        result = await droid.execute(
            path=str(test_dir),
            depth="light",
        )

        print(f"\n2. Results:")
        print(f"   ✓ Analysis completed")
        print(f"   ✓ Summary: {result['summary']}")

        output_data = json.loads(result['output'])
        print(f"   ✓ Files analyzed: {output_data.get('analysis_summary', {}).get('file_path')}")
        print(f"   ✓ Bottlenecks: {output_data.get('total_bottlenecks', 0)}")

        print("\n" + "=" * 70)
        print("✓ Directory test completed successfully!")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n✗ Directory test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("PerformanceAnalyzerDroid Test Suite")
    print("=" * 70)

    results = []

    # Test 1: Basic functionality
    results.append(await test_performance_analyzer())

    # Test 2: Directory analysis
    results.append(await test_directory_analysis())

    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    print(f"Total tests: {len(results)}")
    print(f"Passed: {sum(results)}")
    print(f"Failed: {len(results) - sum(results)}")

    if all(results):
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
