#!/usr/bin/env python3
"""Comprehensive performance and component tests for K-LEAN v4.0.0.

This script tests:
1. Performance - Model discovery functions
2. Component instantiation - All three droids
3. Tool availability - All four tools
4. Base class tests - Abstract and concrete classes
5. Model discovery - Available models and selection
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "review-system-backup" / "src"))

# Import required modules
from klean.utils.model_discovery import (
    get_available_models,
    get_model_for_task,
    get_model_info,
    is_litellm_available,
)
from klean.droids.base import BaseDroid, BashDroid, SDKDroid
from klean.agents.security_auditor import SecurityAuditorDroid
from klean.agents.architect_reviewer import ArchitectReviewerDroid
from klean.agents.performance_analyzer import PerformanceAnalyzerDroid
from klean.tools import grep_codebase, read_file, search_knowledge, run_tests


def print_header(text):
    """Print section header."""
    print(f"\n{'=' * 80}")
    print(f"  {text}")
    print(f"{'=' * 80}\n")


def print_result(test_name, passed, details=""):
    """Print test result with emoji."""
    status = "✅" if passed else "❌"
    print(f"{status} {test_name}")
    if details:
        print(f"   {details}")


def time_function(func, *args, **kwargs):
    """Time function execution and return (result, time_ms)."""
    start = time.perf_counter()
    result = func(*args, **kwargs)
    elapsed_ms = (time.perf_counter() - start) * 1000
    return result, elapsed_ms


# Test results tracker
test_results = {
    "passed": 0,
    "failed": 0,
    "warnings": [],
    "errors": [],
}


def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("K-LEAN v4.0.0 - COMPREHENSIVE PERFORMANCE & COMPONENT TEST SUITE")
    print("=" * 80)

    # ========================================================================
    # 1. PERFORMANCE TESTS - Model Discovery
    # ========================================================================
    print_header("1. PERFORMANCE TESTS - Model Discovery")

    # Test 1.1: get_model_info() response time
    result, elapsed = time_function(get_model_info)
    target_ms = 100
    passed = elapsed < target_ms
    test_results["passed" if passed else "failed"] += 1
    print_result(
        "get_model_info() response time",
        passed,
        f"{elapsed:.2f}ms (target: <{target_ms}ms)",
    )
    if not passed:
        test_results["warnings"].append(
            f"get_model_info() took {elapsed:.2f}ms (target: <{target_ms}ms)"
        )

    # Test 1.2: get_model_for_task("security") response time
    result, elapsed = time_function(get_model_for_task, "security")
    passed = elapsed < target_ms
    test_results["passed" if passed else "failed"] += 1
    print_result(
        'get_model_for_task("security") response time',
        passed,
        f"{elapsed:.2f}ms, model: {result}",
    )
    if not passed:
        test_results["warnings"].append(
            f"get_model_for_task('security') took {elapsed:.2f}ms"
        )

    # Test 1.3: get_model_for_task("architecture") response time
    result, elapsed = time_function(get_model_for_task, "architecture")
    passed = elapsed < target_ms
    test_results["passed" if passed else "failed"] += 1
    print_result(
        'get_model_for_task("architecture") response time',
        passed,
        f"{elapsed:.2f}ms, model: {result}",
    )
    if not passed:
        test_results["warnings"].append(
            f"get_model_for_task('architecture') took {elapsed:.2f}ms"
        )

    # Test 1.4: is_litellm_available() response time
    result, elapsed = time_function(is_litellm_available)
    passed = elapsed < target_ms
    test_results["passed" if passed else "failed"] += 1
    print_result(
        "is_litellm_available() response time",
        passed,
        f"{elapsed:.2f}ms, available: {result}",
    )
    if not passed:
        test_results["warnings"].append(
            f"is_litellm_available() took {elapsed:.2f}ms"
        )

    # ========================================================================
    # 2. COMPONENT INSTANTIATION TESTS
    # ========================================================================
    print_header("2. COMPONENT INSTANTIATION TESTS")

    # Test 2.1: SecurityAuditorDroid instantiation
    try:
        security_droid = SecurityAuditorDroid()
        passed = True
        details = f"Name: {security_droid.name}, Model: {security_droid.model}"
        test_results["passed"] += 1

        # Verify attributes
        assert hasattr(security_droid, "name"), "Missing 'name' attribute"
        assert hasattr(security_droid, "model"), "Missing 'model' attribute"
        assert hasattr(security_droid, "description"), "Missing 'description' attribute"
        assert security_droid.name == "security-auditor-sdk", f"Wrong name: {security_droid.name}"

    except Exception as e:
        passed = False
        details = f"Error: {e}"
        test_results["failed"] += 1
        test_results["errors"].append(f"SecurityAuditorDroid instantiation failed: {e}")

    print_result("SecurityAuditorDroid instantiation", passed, details)

    # Test 2.2: ArchitectReviewerDroid instantiation
    try:
        architect_droid = ArchitectReviewerDroid()
        passed = True
        details = f"Name: {architect_droid.name}, Model: {architect_droid.model}"
        test_results["passed"] += 1

        # Verify attributes
        assert hasattr(architect_droid, "name"), "Missing 'name' attribute"
        assert hasattr(architect_droid, "model"), "Missing 'model' attribute"
        assert hasattr(architect_droid, "description"), "Missing 'description' attribute"
        assert architect_droid.name == "architect-reviewer-sdk", f"Wrong name: {architect_droid.name}"

    except Exception as e:
        passed = False
        details = f"Error: {e}"
        test_results["failed"] += 1
        test_results["errors"].append(f"ArchitectReviewerDroid instantiation failed: {e}")

    print_result("ArchitectReviewerDroid instantiation", passed, details)

    # Test 2.3: PerformanceAnalyzerDroid instantiation
    try:
        performance_droid = PerformanceAnalyzerDroid()
        passed = True
        details = f"Name: {performance_droid.name}, Model: {performance_droid.model}"
        test_results["passed"] += 1

        # Verify attributes
        assert hasattr(performance_droid, "name"), "Missing 'name' attribute"
        assert hasattr(performance_droid, "model"), "Missing 'model' attribute"
        assert hasattr(performance_droid, "description"), "Missing 'description' attribute"
        assert performance_droid.name == "performance-analyzer-sdk", f"Wrong name: {performance_droid.name}"

    except Exception as e:
        passed = False
        details = f"Error: {e}"
        test_results["failed"] += 1
        test_results["errors"].append(f"PerformanceAnalyzerDroid instantiation failed: {e}")

    print_result("PerformanceAnalyzerDroid instantiation", passed, details)

    # ========================================================================
    # 3. TOOL AVAILABILITY TESTS
    # ========================================================================
    print_header("3. TOOL AVAILABILITY TESTS")

    # Test 3.1: grep_codebase tool
    try:
        assert callable(grep_codebase), "grep_codebase is not callable"
        assert hasattr(grep_codebase, "_is_tool"), "Missing _is_tool attribute"
        assert grep_codebase._is_tool == True, "_is_tool is not True"
        assert hasattr(grep_codebase, "_tool_name"), "Missing _tool_name attribute"
        assert grep_codebase._tool_name == "grep_codebase", f"Wrong tool name: {grep_codebase._tool_name}"
        assert hasattr(grep_codebase, "_tool_description"), "Missing _tool_description attribute"

        passed = True
        details = f"Name: {grep_codebase._tool_name}, Desc: {grep_codebase._tool_description}"
        test_results["passed"] += 1
    except Exception as e:
        passed = False
        details = f"Error: {e}"
        test_results["failed"] += 1
        test_results["errors"].append(f"grep_codebase tool check failed: {e}")

    print_result("grep_codebase tool availability", passed, details)

    # Test 3.2: read_file tool
    try:
        assert callable(read_file), "read_file is not callable"
        assert hasattr(read_file, "_is_tool"), "Missing _is_tool attribute"
        assert read_file._is_tool == True, "_is_tool is not True"
        assert hasattr(read_file, "_tool_name"), "Missing _tool_name attribute"
        assert read_file._tool_name == "read_file", f"Wrong tool name: {read_file._tool_name}"
        assert hasattr(read_file, "_tool_description"), "Missing _tool_description attribute"

        passed = True
        details = f"Name: {read_file._tool_name}, Desc: {read_file._tool_description}"
        test_results["passed"] += 1
    except Exception as e:
        passed = False
        details = f"Error: {e}"
        test_results["failed"] += 1
        test_results["errors"].append(f"read_file tool check failed: {e}")

    print_result("read_file tool availability", passed, details)

    # Test 3.3: search_knowledge tool
    try:
        assert callable(search_knowledge), "search_knowledge is not callable"
        assert hasattr(search_knowledge, "_is_tool"), "Missing _is_tool attribute"
        assert search_knowledge._is_tool == True, "_is_tool is not True"
        assert hasattr(search_knowledge, "_tool_name"), "Missing _tool_name attribute"
        assert search_knowledge._tool_name == "search_knowledge", f"Wrong tool name: {search_knowledge._tool_name}"
        assert hasattr(search_knowledge, "_tool_description"), "Missing _tool_description attribute"

        passed = True
        details = f"Name: {search_knowledge._tool_name}, Desc: {search_knowledge._tool_description}"
        test_results["passed"] += 1
    except Exception as e:
        passed = False
        details = f"Error: {e}"
        test_results["failed"] += 1
        test_results["errors"].append(f"search_knowledge tool check failed: {e}")

    print_result("search_knowledge tool availability", passed, details)

    # Test 3.4: run_tests tool
    try:
        assert callable(run_tests), "run_tests is not callable"
        assert hasattr(run_tests, "_is_tool"), "Missing _is_tool attribute"
        assert run_tests._is_tool == True, "_is_tool is not True"
        assert hasattr(run_tests, "_tool_name"), "Missing _tool_name attribute"
        assert run_tests._tool_name == "run_tests", f"Wrong tool name: {run_tests._tool_name}"
        assert hasattr(run_tests, "_tool_description"), "Missing _tool_description attribute"

        passed = True
        details = f"Name: {run_tests._tool_name}, Desc: {run_tests._tool_description}"
        test_results["passed"] += 1
    except Exception as e:
        passed = False
        details = f"Error: {e}"
        test_results["failed"] += 1
        test_results["errors"].append(f"run_tests tool check failed: {e}")

    print_result("run_tests tool availability", passed, details)

    # ========================================================================
    # 4. BASE CLASS TESTS
    # ========================================================================
    print_header("4. BASE CLASS TESTS")

    # Test 4.1: BaseDroid is abstract
    try:
        # Try to instantiate BaseDroid directly (should fail)
        try:
            base = BaseDroid("test", "test description")
            # If we get here, it's not properly abstract
            passed = False
            details = "BaseDroid can be instantiated directly (should be abstract)"
            test_results["failed"] += 1
        except TypeError as e:
            # Expected - cannot instantiate abstract class
            passed = True
            details = "BaseDroid is properly abstract"
            test_results["passed"] += 1
    except Exception as e:
        passed = False
        details = f"Unexpected error: {e}"
        test_results["failed"] += 1
        test_results["errors"].append(f"BaseDroid abstract check failed: {e}")

    print_result("BaseDroid is abstract", passed, details)

    # Test 4.2: BashDroid can be instantiated
    try:
        bash_droid = BashDroid(
            name="test-bash",
            script_path="/bin/echo",
            description="Test bash droid"
        )
        assert hasattr(bash_droid, "name"), "Missing 'name' attribute"
        assert hasattr(bash_droid, "script_path"), "Missing 'script_path' attribute"
        assert hasattr(bash_droid, "description"), "Missing 'description' attribute"
        assert bash_droid.droid_type == "bash", f"Wrong droid_type: {bash_droid.droid_type}"

        passed = True
        details = f"Name: {bash_droid.name}, Type: {bash_droid.droid_type}"
        test_results["passed"] += 1
    except Exception as e:
        passed = False
        details = f"Error: {e}"
        test_results["failed"] += 1
        test_results["errors"].append(f"BashDroid instantiation failed: {e}")

    print_result("BashDroid instantiation", passed, details)

    # Test 4.3: SDKDroid can be subclassed
    try:
        # Create a simple subclass
        class TestSDKDroid(SDKDroid):
            def __init__(self):
                super().__init__(
                    name="test-sdk",
                    description="Test SDK droid",
                    model="claude-opus-4-5-20251101"
                )

            async def execute(self, *args, **kwargs):
                return {"output": "test", "format": "json", "droid": self.name}

        test_sdk_droid = TestSDKDroid()
        assert hasattr(test_sdk_droid, "name"), "Missing 'name' attribute"
        assert hasattr(test_sdk_droid, "model"), "Missing 'model' attribute"
        assert hasattr(test_sdk_droid, "description"), "Missing 'description' attribute"
        assert test_sdk_droid.droid_type == "sdk", f"Wrong droid_type: {test_sdk_droid.droid_type}"

        passed = True
        details = f"Name: {test_sdk_droid.name}, Type: {test_sdk_droid.droid_type}"
        test_results["passed"] += 1
    except Exception as e:
        passed = False
        details = f"Error: {e}"
        test_results["failed"] += 1
        test_results["errors"].append(f"SDKDroid subclassing failed: {e}")

    print_result("SDKDroid subclassing", passed, details)

    # ========================================================================
    # 5. MODEL DISCOVERY TESTS
    # ========================================================================
    print_header("5. MODEL DISCOVERY TESTS")

    # Test 5.1: Count available models
    try:
        models = get_available_models()
        model_count = len(models)
        passed = True
        details = f"Found {model_count} models: {', '.join(models) if models else 'None (LiteLLM not running)'}"
        test_results["passed"] += 1

        if model_count == 0:
            test_results["warnings"].append("No LiteLLM models available (server may not be running)")
    except Exception as e:
        passed = False
        details = f"Error: {e}"
        test_results["failed"] += 1
        test_results["errors"].append(f"get_available_models() failed: {e}")

    print_result("Count available models", passed, details)

    # Test 5.2: Verify model attributes
    try:
        info = get_model_info()
        assert "available" in info, "Missing 'available' key"
        assert "models" in info, "Missing 'models' key"
        assert "recommended" in info, "Missing 'recommended' key"
        assert isinstance(info["available"], bool), "'available' is not bool"
        assert isinstance(info["models"], list), "'models' is not list"
        assert isinstance(info["recommended"], dict), "'recommended' is not dict"

        passed = True
        details = f"Available: {info['available']}, Models: {len(info['models'])}, Recommendations: {len(info['recommended'])}"
        test_results["passed"] += 1
    except Exception as e:
        passed = False
        details = f"Error: {e}"
        test_results["failed"] += 1
        test_results["errors"].append(f"Model info attributes check failed: {e}")

    print_result("Verify model info attributes", passed, details)

    # Test 5.3: Model selection for each task type
    task_types = ["code_quality", "architecture", "security", "performance"]
    for task_type in task_types:
        try:
            model = get_model_for_task(task_type)
            # Model can be None if LiteLLM is not running
            passed = True
            details = f"Selected: {model if model else 'None (LiteLLM not available)'}"
            test_results["passed"] += 1
        except Exception as e:
            passed = False
            details = f"Error: {e}"
            test_results["failed"] += 1
            test_results["errors"].append(f"get_model_for_task('{task_type}') failed: {e}")

        print_result(f'Model selection for "{task_type}"', passed, details)

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================
    print_header("TEST SUMMARY")

    total_tests = test_results["passed"] + test_results["failed"]
    pass_rate = (test_results["passed"] / total_tests * 100) if total_tests > 0 else 0

    print(f"Total Tests: {total_tests}")
    print(f"Passed: {test_results['passed']} ✅")
    print(f"Failed: {test_results['failed']} ❌")
    print(f"Pass Rate: {pass_rate:.1f}%")

    if test_results["warnings"]:
        print(f"\n⚠️  Warnings ({len(test_results['warnings'])}):")
        for warning in test_results["warnings"]:
            print(f"  - {warning}")

    if test_results["errors"]:
        print(f"\n❌ Errors ({len(test_results['errors'])}):")
        for error in test_results["errors"]:
            print(f"  - {error}")

    # Overall health status
    print("\n" + "=" * 80)
    if test_results["failed"] == 0:
        print("OVERALL STATUS: ✅ HEALTHY")
        print("All components passed verification.")
    else:
        print("OVERALL STATUS: ⚠️  ISSUES FOUND")
        print(f"Found {test_results['failed']} failing tests. Review errors above.")
    print("=" * 80 + "\n")

    # Return exit code
    return 0 if test_results["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
