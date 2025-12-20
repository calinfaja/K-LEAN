#!/usr/bin/env python3
"""
Direct K-LEAN Knowledge Database Stress Tests
Uses socket protocol directly for accurate performance measurement.
"""

import json
import time
import os
import sys
import socket
import psutil
import hashlib
from datetime import datetime
from statistics import mean, median, stdev
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import threading

# Configuration
PROJECT_DIR = "/home/calin/claudeAgentic"

def get_project_hash(project_path):
    """Get socket hash for project."""
    path_str = str(Path(project_path).resolve())
    return hashlib.md5(path_str.encode()).hexdigest()[:8]

KB_SOCKET_PATH = f"/tmp/kb-{get_project_hash(PROJECT_DIR)}.sock"

class StressTestResults:
    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()

    def add_test(self, name, iterations, success_count, timings, extra_data=None):
        success_rate = (success_count / iterations * 100) if iterations > 0 else 0

        if not timings:
            timings = [0]

        result = {
            "test_name": name,
            "iterations": iterations,
            "successful": success_count,
            "failed": iterations - success_count,
            "success_rate_percent": round(success_rate, 2),
            "timing_statistics": {
                "min_ms": round(min(timings) * 1000, 2),
                "max_ms": round(max(timings) * 1000, 2),
                "avg_ms": round(mean(timings) * 1000, 2),
                "median_ms": round(median(timings) * 1000, 2),
                "stdev_ms": round(stdev(timings) * 1000, 2) if len(timings) > 1 else 0,
                "total_seconds": round(sum(timings), 2),
                "p95_ms": round(sorted(timings)[int(len(timings) * 0.95)] * 1000, 2) if len(timings) > 1 else 0,
                "p99_ms": round(sorted(timings)[int(len(timings) * 0.99)] * 1000, 2) if len(timings) > 1 else 0,
            }
        }

        if extra_data:
            result.update(extra_data)

        self.results[name] = result

    def to_json(self):
        return json.dumps({
            "test_suite": "K-LEAN Knowledge Database Direct Stress Tests",
            "timestamp": self.start_time.isoformat(),
            "duration_seconds": round((datetime.now() - self.start_time).total_seconds(), 2),
            "project_directory": PROJECT_DIR,
            "socket_path": KB_SOCKET_PATH,
            "tests": self.results,
            "summary": {
                "total_tests": len(self.results),
                "all_passed": all(r["success_rate_percent"] >= 95 for r in self.results.values()),
                "total_operations": sum(r["iterations"] for r in self.results.values()),
                "total_successes": sum(r["successful"] for r in self.results.values()),
                "overall_success_rate": round(
                    sum(r["successful"] for r in self.results.values()) /
                    sum(r["iterations"] for r in self.results.values()) * 100, 2
                ) if sum(r["iterations"] for r in self.results.values()) > 0 else 0
            }
        }, indent=2)


def socket_query(query_text, timeout=5):
    """Execute a query via direct socket connection."""
    try:
        start = time.time()

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(KB_SOCKET_PATH)

        request = json.dumps({"cmd": "search", "query": query_text}) + "\n"
        sock.sendall(request.encode())

        # Read response
        response_data = b""
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            response_data += chunk
            if b'\n' in chunk:
                break

        sock.close()
        elapsed = time.time() - start

        if response_data:
            try:
                response = json.loads(response_data.decode())
                return True, elapsed, response
            except:
                return True, elapsed, response_data
        return False, elapsed, "Empty response"

    except socket.timeout:
        return False, timeout, "Timeout"
    except Exception as e:
        elapsed = time.time() - start if 'start' in locals() else 0
        return False, elapsed, str(e)


def socket_ping(timeout=2):
    """Quick ping to server."""
    try:
        start = time.time()

        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect(KB_SOCKET_PATH)

        request = json.dumps({"cmd": "status"}) + "\n"
        sock.sendall(request.encode())

        response_data = sock.recv(4096)
        sock.close()

        elapsed = time.time() - start
        return True, elapsed, response_data

    except Exception as e:
        elapsed = time.time() - start if 'start' in locals() else 0
        return False, elapsed, str(e)


def get_memory_usage():
    """Get current process memory in MB."""
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / 1024 / 1024


def get_server_memory():
    """Get server process memory in MB."""
    try:
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            cmdline = proc.info.get('cmdline', [])
            if cmdline and 'knowledge-server.py' in ' '.join(cmdline):
                if PROJECT_DIR in ' '.join(cmdline):
                    return proc.memory_info().rss / 1024 / 1024
    except:
        pass
    return None


def test_concurrent_queries(results, num_concurrent=10):
    """Test 1: Concurrent Queries."""
    print(f"\n[TEST 1] Concurrent Queries ({num_concurrent} parallel)...")

    queries = [
        "architecture", "testing", "performance", "security", "database",
        "API", "configuration", "deployment", "integration", "optimization"
    ]

    start_time = time.time()
    timings = []
    success_count = 0
    response_sizes = []

    with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
        futures = {executor.submit(socket_query, queries[i % len(queries)]): i
                  for i in range(num_concurrent)}

        for future in as_completed(futures):
            success, elapsed, response = future.result()
            timings.append(elapsed)
            if success:
                success_count += 1
                if isinstance(response, dict):
                    response_sizes.append(len(str(response)))

    total_time = time.time() - start_time

    extra_data = {
        "total_duration_seconds": round(total_time, 2),
        "concurrent_workers": num_concurrent,
        "queries_per_second": round(num_concurrent / total_time, 2),
        "avg_response_size": round(mean(response_sizes), 2) if response_sizes else 0
    }

    results.add_test("concurrent_queries", num_concurrent, success_count, timings, extra_data)

    print(f"  ✓ Success: {success_count}/{num_concurrent} ({success_count/num_concurrent*100:.1f}%)")
    print(f"  ✓ Duration: {total_time:.2f}s")
    print(f"  ✓ Throughput: {extra_data['queries_per_second']:.2f} q/s")


def test_sequential_throughput(results, num_queries=50):
    """Test 2: Sequential Throughput."""
    print(f"\n[TEST 2] Sequential Throughput ({num_queries} queries)...")

    queries = ["test", "architecture", "database", "performance", "security"]

    start_time = time.time()
    timings = []
    success_count = 0

    for i in range(num_queries):
        query = queries[i % len(queries)]
        success, elapsed, _ = socket_query(query, timeout=3)
        timings.append(elapsed)
        if success:
            success_count += 1

    total_time = time.time() - start_time

    extra_data = {
        "queries_per_second": round(num_queries / total_time, 2),
        "total_duration_seconds": round(total_time, 2)
    }

    results.add_test("sequential_throughput", num_queries, success_count, timings, extra_data)

    print(f"  ✓ Success: {success_count}/{num_queries} ({success_count/num_queries*100:.1f}%)")
    print(f"  ✓ Throughput: {extra_data['queries_per_second']:.2f} q/s")


def test_rapid_connections(results, num_connections=100):
    """Test 3: Rapid Connection Open/Close."""
    print(f"\n[TEST 3] Rapid Connections ({num_connections} pings)...")

    start_time = time.time()
    timings = []
    success_count = 0

    for i in range(num_connections):
        success, elapsed, _ = socket_ping(timeout=1)
        timings.append(elapsed)
        if success:
            success_count += 1

    total_time = time.time() - start_time

    extra_data = {
        "connections_per_second": round(num_connections / total_time, 2),
        "total_duration_seconds": round(total_time, 2)
    }

    results.add_test("rapid_connections", num_connections, success_count, timings, extra_data)

    print(f"  ✓ Success: {success_count}/{num_connections} ({success_count/num_connections*100:.1f}%)")
    print(f"  ✓ Rate: {extra_data['connections_per_second']:.2f} conn/s")


def test_sustained_load(results, duration_seconds=10):
    """Test 4: Sustained Load."""
    print(f"\n[TEST 4] Sustained Load ({duration_seconds}s continuous queries)...")

    start_time = time.time()
    timings = []
    success_count = 0
    total_queries = 0

    queries = ["test", "search", "query", "data", "info"]

    while (time.time() - start_time) < duration_seconds:
        query = queries[total_queries % len(queries)]
        success, elapsed, _ = socket_query(query, timeout=2)
        timings.append(elapsed)
        total_queries += 1
        if success:
            success_count += 1

    total_time = time.time() - start_time

    extra_data = {
        "queries_per_second": round(total_queries / total_time, 2),
        "total_duration_seconds": round(total_time, 2),
        "target_duration_seconds": duration_seconds
    }

    results.add_test("sustained_load", total_queries, success_count, timings, extra_data)

    print(f"  ✓ Success: {success_count}/{total_queries} ({success_count/total_queries*100:.1f}%)")
    print(f"  ✓ Avg throughput: {extra_data['queries_per_second']:.2f} q/s")


def test_memory_stability(results):
    """Test 5: Memory Stability."""
    print(f"\n[TEST 5] Memory Stability (under load)...")

    mem_before = get_memory_usage()
    server_mem_before = get_server_memory()

    print(f"  Test process before: {mem_before:.2f} MB")
    if server_mem_before:
        print(f"  Server process before: {server_mem_before:.2f} MB")

    # Run load
    timings = []
    success_count = 0
    num_queries = 50

    for i in range(num_queries):
        success, elapsed, _ = socket_query(f"query {i}", timeout=3)
        timings.append(elapsed)
        if success:
            success_count += 1

    mem_after = get_memory_usage()
    server_mem_after = get_server_memory()
    mem_delta = mem_after - mem_before
    server_delta = (server_mem_after - server_mem_before) if (server_mem_after and server_mem_before) else None

    print(f"  Test process after: {mem_after:.2f} MB")
    if server_mem_after:
        print(f"  Server process after: {server_mem_after:.2f} MB")
    print(f"  Test delta: {mem_delta:+.2f} MB")
    if server_delta is not None:
        print(f"  Server delta: {server_delta:+.2f} MB")

    extra_data = {
        "test_memory_before_mb": round(mem_before, 2),
        "test_memory_after_mb": round(mem_after, 2),
        "test_delta_mb": round(mem_delta, 2),
        "server_memory_before_mb": round(server_mem_before, 2) if server_mem_before else None,
        "server_memory_after_mb": round(server_mem_after, 2) if server_mem_after else None,
        "server_delta_mb": round(server_delta, 2) if server_delta else None,
        "potential_leak": mem_delta > 50 or (server_delta and server_delta > 100)
    }

    results.add_test("memory_stability", num_queries, success_count, timings, extra_data)


def main():
    """Run all stress tests."""
    print("=" * 80)
    print("K-LEAN Knowledge Database - Direct Socket Stress Tests")
    print("=" * 80)
    print(f"Start time: {datetime.now().isoformat()}")
    print(f"Project: {PROJECT_DIR}")
    print(f"Socket: {KB_SOCKET_PATH}")

    # Verify socket exists
    if not os.path.exists(KB_SOCKET_PATH):
        print(f"\n✗ ERROR: Socket not found at {KB_SOCKET_PATH}")
        print("  Please ensure knowledge server is running:")
        print(f"  ~/.venvs/knowledge-db/bin/python ~/.claude/scripts/knowledge-server.py start {PROJECT_DIR}")
        sys.exit(1)

    results = StressTestResults()

    try:
        # Warmup
        print("\nWarming up...")
        socket_query("warmup", timeout=5)
        time.sleep(0.5)

        # Run tests
        test_concurrent_queries(results, num_concurrent=10)
        test_sequential_throughput(results, num_queries=50)
        test_rapid_connections(results, num_connections=100)
        test_sustained_load(results, duration_seconds=10)
        test_memory_stability(results)

        # Results
        print("\n" + "=" * 80)
        print("STRESS TEST RESULTS")
        print("=" * 80)
        print(results.to_json())

        # Save
        output_file = os.path.join(PROJECT_DIR, "stress_test_results_direct.json")
        with open(output_file, "w") as f:
            f.write(results.to_json())

        print(f"\n✓ Results saved to: {output_file}")

        # Summary
        summary = results.results
        print("\n" + "=" * 80)
        print("SUMMARY")
        print("=" * 80)
        for test_name, data in summary.items():
            status = "✓ PASS" if data["success_rate_percent"] >= 95 else "✗ FAIL"
            print(f"{status} {test_name}: {data['success_rate_percent']:.1f}% success")

    except KeyboardInterrupt:
        print("\n\n✗ Tests interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
