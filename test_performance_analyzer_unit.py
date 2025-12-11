#!/usr/bin/env python3
"""Unit tests for PerformanceAnalyzerDroid.

This script tests the PerformanceAnalyzerDroid implementation without requiring
the Anthropic API or LiteLLM proxy.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

# Add the review-system-backup src to path
sys.path.insert(0, str(Path(__file__).parent / "review-system-backup" / "src"))

from klean.agents.performance_analyzer import PerformanceAnalyzerDroid


def test_initialization():
    """Test droid initialization."""
    print("Test 1: Initialization")
    print("-" * 50)

    # Test with auto model selection
    droid = PerformanceAnalyzerDroid()
    print(f"✓ Default initialization")
    print(f"  - Name: {droid.name}")
    print(f"  - Type: {droid.droid_type}")
    print(f"  - Description: {droid.description}")
    print(f"  - Model: {droid.model}")

    assert droid.name == "performance-analyzer-sdk"
    assert droid.droid_type == "sdk"
    assert "performance" in droid.description.lower()
    print("✓ All initialization checks passed\n")

    # Test with specific model
    droid2 = PerformanceAnalyzerDroid(model="claude-opus-4-5-20251101")
    assert droid2.model == "claude-opus-4-5-20251101"
    print(f"✓ Custom model initialization: {droid2.model}\n")

    return True


def test_load_code_from_file():
    """Test loading code from a file."""
    print("Test 2: Load Code from File")
    print("-" * 50)

    import asyncio

    async def run_test():
        droid = PerformanceAnalyzerDroid()

        # Create a temporary test file
        test_file = Path("/tmp/test_perf_code.py")
        test_content = "def test():\n    return 42"
        test_file.write_text(test_content)

        try:
            # Test loading
            code = await droid._load_code(str(test_file))
            assert code == test_content
            print(f"✓ File loaded successfully")
            print(f"  - Length: {len(code)} chars")
            return True
        finally:
            test_file.unlink()

    result = asyncio.run(run_test())
    print("✓ File loading test passed\n")
    return result


def test_load_code_from_directory():
    """Test loading code from a directory."""
    print("Test 3: Load Code from Directory")
    print("-" * 50)

    import asyncio
    import tempfile
    import os

    async def run_test():
        droid = PerformanceAnalyzerDroid()

        # Create temporary directory with Python files
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files
            (Path(tmpdir) / "file1.py").write_text("def func1(): pass")
            (Path(tmpdir) / "file2.py").write_text("def func2(): pass")

            # Create subdirectory (should be included)
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            (subdir / "file3.py").write_text("def func3(): pass")

            # Load code
            code = await droid._load_code(tmpdir)

            assert "func1" in code
            assert "func2" in code
            assert "func3" in code
            print(f"✓ Directory loaded successfully")
            print(f"  - Length: {len(code)} chars")
            print(f"  - Contains 3 files")
            return True

    result = asyncio.run(run_test())
    print("✓ Directory loading test passed\n")
    return result


def test_load_code_errors():
    """Test error handling in code loading."""
    print("Test 4: Load Code Error Handling")
    print("-" * 50)

    import asyncio

    async def run_test():
        droid = PerformanceAnalyzerDroid()

        # Test non-existent path
        try:
            await droid._load_code("/nonexistent/path")
            print("✗ Should have raised FileNotFoundError")
            return False
        except FileNotFoundError as e:
            print(f"✓ FileNotFoundError raised correctly")
            print(f"  - Message: {str(e)[:60]}...")

        # Test empty directory
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            try:
                await droid._load_code(tmpdir)
                print("✗ Should have raised FileNotFoundError for empty dir")
                return False
            except FileNotFoundError as e:
                print(f"✓ FileNotFoundError raised for empty directory")
                print(f"  - Message: {str(e)[:60]}...")

        return True

    result = asyncio.run(run_test())
    print("✓ Error handling test passed\n")
    return result


def test_json_parsing():
    """Test JSON parsing from various response formats."""
    print("Test 5: JSON Response Parsing")
    print("-" * 50)

    import json
    import asyncio

    async def run_test():
        droid = PerformanceAnalyzerDroid()

        # Mock the client
        mock_client = MagicMock()
        droid.client = mock_client

        # Test 1: JSON wrapped in markdown code block
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = '```json\n{"bottlenecks": [], "total_bottlenecks": 0}\n```'
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response

        # Create test file
        test_file = Path("/tmp/test_json.py")
        test_file.write_text("def test(): pass")

        try:
            result = await droid._turn1_bottleneck_identification("def test(): pass", "medium")

            assert "total_bottlenecks" in result
            assert result["total_bottlenecks"] == 0
            print(f"✓ Parsed JSON from markdown code block")

            # Test 2: Plain JSON
            mock_content.text = '{"bottlenecks": [{"name": "test"}], "total_bottlenecks": 1}'
            result = await droid._turn1_bottleneck_identification("def test(): pass", "medium")

            assert result["total_bottlenecks"] == 1
            print(f"✓ Parsed plain JSON")

            return True

        finally:
            if test_file.exists():
                test_file.unlink()

    result = asyncio.run(run_test())
    print("✓ JSON parsing test passed\n")
    return result


def test_turn_data_flow():
    """Test data flow between turns."""
    print("Test 6: Turn Data Flow")
    print("-" * 50)

    import asyncio

    async def run_test():
        droid = PerformanceAnalyzerDroid()

        # Mock the client
        mock_client = MagicMock()
        droid.client = mock_client

        # Mock Turn 1 response
        mock_response = MagicMock()
        mock_content = MagicMock()
        mock_content.text = '''```json
{
    "bottlenecks": [
        {"name": "nested_loop", "location": "line 10", "type": "algorithmic", "severity_score": 8, "description": "O(n²) nested loop"}
    ],
    "hot_paths": [{"path_description": "main loop", "estimated_frequency": "high", "impact_score": 7}],
    "inefficient_operations": [],
    "total_bottlenecks": 1,
    "overall_performance_score": 6.0
}
```'''
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response

        # Test Turn 1
        turn1_result = await droid._turn1_bottleneck_identification("def test(): pass", "medium")
        print(f"✓ Turn 1 completed")
        print(f"  - Bottlenecks: {turn1_result['total_bottlenecks']}")
        print(f"  - Performance score: {turn1_result['overall_performance_score']}")

        # Mock Turn 2 response
        mock_content.text = '''```json
{
    "complexity_issues": [
        {"component": "nested_loop", "current_time_complexity": "O(n²)", "optimal_time_complexity": "O(n)", "current_space_complexity": "O(1)", "optimal_space_complexity": "O(n)", "improvement_potential": "high"}
    ],
    "time_complexity": {"nested_loop": "O(n²)"},
    "space_complexity": {"nested_loop": "O(1)"},
    "worst_complexity": "O(n²)",
    "improvement_opportunities": 1
}
```'''

        # Test Turn 2
        turn2_result = await droid._turn2_complexity_analysis(turn1_result)
        print(f"✓ Turn 2 completed")
        print(f"  - Complexity issues: {len(turn2_result['complexity_issues'])}")
        print(f"  - Worst complexity: {turn2_result['worst_complexity']}")

        # Verify data flows through
        assert "total_bottlenecks" in turn2_result  # From turn 1
        assert "complexity_issues" in turn2_result  # From turn 2
        print(f"✓ Data preserved from Turn 1 to Turn 2")

        # Mock Turn 3 response
        mock_content.text = '''```json
{
    "memory_issues": [
        {"issue_type": "memory_leak", "location": "cache", "description": "Unbounded cache growth", "severity": "high", "estimated_memory_waste": "100MB+"}
    ],
    "memory_leak_risks": ["unbounded_cache"],
    "memory_optimization_opportunities": ["implement_lru_cache"],
    "memory_score": 4.0,
    "peak_memory_concerns": ["cache_growth"]
}
```'''

        # Test Turn 3
        turn3_result = await droid._turn3_memory_analysis(turn2_result)
        print(f"✓ Turn 3 completed")
        print(f"  - Memory issues: {len(turn3_result['memory_issues'])}")
        print(f"  - Memory score: {turn3_result['memory_score']}")

        # Verify cumulative data
        assert "total_bottlenecks" in turn3_result  # From turn 1
        assert "complexity_issues" in turn3_result  # From turn 2
        assert "memory_issues" in turn3_result  # From turn 3
        print(f"✓ Data preserved through all turns")

        return True

    result = asyncio.run(run_test())
    print("✓ Turn data flow test passed\n")
    return result


def test_error_handling():
    """Test error handling in each turn."""
    print("Test 7: Error Handling")
    print("-" * 50)

    import asyncio

    async def run_test():
        droid = PerformanceAnalyzerDroid()

        # Mock the client to raise an exception
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = Exception("API Error")
        droid.client = mock_client

        # Test Turn 1 error handling
        result = await droid._turn1_bottleneck_identification("def test(): pass", "medium")
        assert "error" in result
        assert result["total_bottlenecks"] == 0
        print(f"✓ Turn 1 error handled gracefully")

        # Test Turn 2 error handling (provide data so it tries to call API)
        turn1_data = {
            "bottlenecks": [{"name": "test", "location": "line 1"}],
            "hot_paths": [{"path_description": "test"}]
        }
        result = await droid._turn2_complexity_analysis(turn1_data)
        assert "error" in result
        print(f"✓ Turn 2 error handled gracefully")

        # Test Turn 3 error handling (provide data so it tries to call API)
        turn2_data = {
            "bottlenecks": [{"name": "test"}],
            "space_complexity": {"test": "O(n)"}
        }
        result = await droid._turn3_memory_analysis(turn2_data)
        assert "error" in result
        print(f"✓ Turn 3 error handled gracefully")

        # Test Turn 4 error handling (provide data so it tries to call API)
        turn3_data = {
            "bottlenecks": [{"name": "test"}],
            "complexity_issues": [{"component": "test"}],
            "memory_issues": [{"issue_type": "leak"}]
        }
        result = await droid._turn4_optimization_recommendations(turn3_data)
        assert "error" in result
        print(f"✓ Turn 4 error handled gracefully")

        return True

    result = asyncio.run(run_test())
    print("✓ Error handling test passed\n")
    return result


def main():
    """Run all unit tests."""
    print("\n" + "=" * 70)
    print("PerformanceAnalyzerDroid Unit Test Suite")
    print("=" * 70)
    print()

    tests = [
        test_initialization,
        test_load_code_from_file,
        test_load_code_from_directory,
        test_load_code_errors,
        test_json_parsing,
        test_turn_data_flow,
        test_error_handling,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    # Summary
    print("=" * 70)
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
    sys.exit(main())
