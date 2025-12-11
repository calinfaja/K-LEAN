# PerformanceAnalyzerDroid Documentation

## Overview

The **PerformanceAnalyzerDroid** is a specialized AI agent that performs comprehensive performance analysis through multi-turn conversations with Claude. It identifies bottlenecks, analyzes algorithmic complexity, detects memory issues, and provides optimization recommendations.

## Features

- **4-Turn Analysis Process**: Progressive analysis that builds context
- **Bottleneck Identification**: Detects nested loops, inefficient patterns, blocking I/O
- **Complexity Analysis**: Analyzes time and space complexity (Big-O notation)
- **Memory Analysis**: Identifies memory leaks, excessive usage, and optimization opportunities
- **Optimization Recommendations**: Prioritized suggestions with expected improvements
- **Structured JSON Output**: Machine-readable results for integration
- **Multiple Depth Levels**: Light, medium, and deep analysis modes

## Architecture

```
PerformanceAnalyzerDroid (extends SDKDroid)
│
├── Turn 1: Bottleneck Identification
│   ├── Detects performance bottlenecks
│   ├── Identifies hot paths
│   └── Flags inefficient operations
│
├── Turn 2: Complexity Analysis
│   ├── Analyzes time complexity (Big-O)
│   ├── Analyzes space complexity
│   └── Identifies improvement opportunities
│
├── Turn 3: Memory Analysis
│   ├── Detects memory leaks
│   ├── Identifies excessive usage
│   └── Flags peak memory concerns
│
└── Turn 4: Optimization Recommendations
    ├── Prioritizes optimizations
    ├── Estimates expected improvements
    └── Provides implementation strategies
```

## Usage

### Basic Usage

```python
from klean.agents import PerformanceAnalyzerDroid
import asyncio

async def analyze_performance():
    # Initialize the droid
    droid = PerformanceAnalyzerDroid()

    # Analyze a file
    result = await droid.execute(
        path="/path/to/file.py",
        depth="medium"
    )

    print(result['summary'])
    print(result['output'])  # JSON with detailed findings

asyncio.run(analyze_performance())
```

### With Focus Area

```python
# Focus on specific performance aspects
result = await droid.execute(
    path="/path/to/file.py",
    depth="deep",
    focus="database queries"
)
```

### Custom Model

```python
# Use a specific model
droid = PerformanceAnalyzerDroid(model="claude-opus-4-5-20251101")
```

### Analyze Directory

```python
# Analyze multiple files in a directory
result = await droid.execute(
    path="/path/to/project/src",
    depth="medium"
)
```

## Parameters

### `execute()` Method

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `path` | str | Yes | - | File or directory to analyze |
| `focus` | str | No | None | Specific area to focus on (e.g., "database", "loops", "I/O") |
| `depth` | str | No | "medium" | Analysis depth: "light", "medium", or "deep" |

### Analysis Depths

- **light**: Quick scan for obvious performance bottlenecks
- **medium**: Standard analysis with bottlenecks, complexity, and memory issues
- **deep**: Thorough analysis including subtle issues and detailed patterns

## Output Format

The droid returns a dictionary with:

```python
{
    "output": str,      # JSON string with structured findings
    "format": "json",   # Output format
    "droid": str,       # Droid identifier
    "turns": int,       # Number of turns completed (4)
    "summary": str      # Brief summary of findings
}
```

### Structured Output Schema

```json
{
  "analysis_summary": {
    "file_path": "string",
    "depth": "medium",
    "turns_completed": 4,
    "focus_area": "general"
  },
  "total_bottlenecks": 0,
  "bottlenecks": [
    {
      "name": "string",
      "location": "line 10",
      "type": "algorithmic",
      "severity_score": 8,
      "description": "string"
    }
  ],
  "hot_paths": [
    {
      "path_description": "string",
      "estimated_frequency": "high",
      "impact_score": 7
    }
  ],
  "inefficient_operations": [
    {
      "operation": "string",
      "location": "string",
      "waste_type": "string",
      "impact": "string"
    }
  ],
  "overall_performance_score": 6.0,
  "complexity_issues": [
    {
      "component": "string",
      "current_time_complexity": "O(n²)",
      "optimal_time_complexity": "O(n)",
      "current_space_complexity": "O(1)",
      "optimal_space_complexity": "O(n)",
      "improvement_potential": "high"
    }
  ],
  "time_complexity": {
    "component_name": "O(n²)"
  },
  "space_complexity": {
    "component_name": "O(n)"
  },
  "worst_complexity": "O(n²)",
  "improvement_opportunities": 3,
  "memory_issues": [
    {
      "issue_type": "memory_leak",
      "location": "string",
      "description": "string",
      "severity": "high",
      "estimated_memory_waste": "100MB+"
    }
  ],
  "memory_leak_risks": ["unbounded_cache"],
  "memory_optimization_opportunities": ["implement_lru_cache"],
  "memory_score": 7.0,
  "peak_memory_concerns": ["cache_growth"],
  "recommendations": [
    {
      "issue": "string",
      "recommendation": "string",
      "priority_score": 8,
      "complexity": "moderate",
      "expected_improvement": "50% faster",
      "trade_offs": "string",
      "implementation_notes": "string"
    }
  ],
  "priority_optimizations": [
    "Optimize nested loop in function X",
    "Implement caching for expensive calculations",
    "Use generators for large data processing"
  ],
  "optimization_complexity": "moderate",
  "expected_improvements": {
    "time_improvement_percent": 50,
    "memory_improvement_percent": 30,
    "overall_impact": "high"
  },
  "profiling_recommendations": [
    "Profile database query performance",
    "Measure memory usage during large file processing"
  ],
  "quick_wins": [
    "Add memoization to recursive function",
    "Replace list comprehension with generator"
  ]
}
```

## Model Selection

The droid automatically selects the best available model:

1. **LiteLLM Available**: Uses `qwen3-coder` (optimized for code performance analysis)
2. **LiteLLM Unavailable**: Falls back to `claude-opus-4-5-20251101` (native Anthropic API)
3. **Custom Model**: Can specify any Claude model explicitly

## Examples

### Example 1: Analyze Code with Performance Issues

```python
import asyncio
from klean.agents import PerformanceAnalyzerDroid

code_with_issues = '''
def find_duplicates(data):
    """Find duplicates - O(n²) implementation."""
    duplicates = []
    for i in range(len(data)):
        for j in range(i + 1, len(data)):
            if data[i] == data[j]:
                duplicates.append(data[i])
    return duplicates
'''

async def main():
    droid = PerformanceAnalyzerDroid()

    # Save code to file
    with open('/tmp/test.py', 'w') as f:
        f.write(code_with_issues)

    # Analyze
    result = await droid.execute(
        path='/tmp/test.py',
        depth='deep',
        focus='algorithmic complexity'
    )

    import json
    findings = json.loads(result['output'])

    print(f"Bottlenecks found: {findings['total_bottlenecks']}")
    print(f"Worst complexity: {findings['worst_complexity']}")
    print(f"Performance score: {findings['overall_performance_score']}/10")

    for rec in findings['recommendations'][:3]:
        print(f"\n{rec['issue']}")
        print(f"  → {rec['recommendation']}")
        print(f"  → Expected: {rec['expected_improvement']}")

asyncio.run(main())
```

### Example 2: Analyze Project Directory

```python
async def analyze_project():
    droid = PerformanceAnalyzerDroid()

    result = await droid.execute(
        path='/path/to/project/src',
        depth='medium'
    )

    import json
    findings = json.loads(result['output'])

    # Get quick wins
    quick_wins = findings.get('quick_wins', [])
    print("Quick Wins:")
    for win in quick_wins:
        print(f"  ✓ {win}")

    # Get priority optimizations
    priority = findings.get('priority_optimizations', [])
    print("\nPriority Optimizations:")
    for i, opt in enumerate(priority, 1):
        print(f"  {i}. {opt}")

asyncio.run(analyze_project())
```

### Example 3: Integration with CI/CD

```python
import sys
import json
from klean.agents import PerformanceAnalyzerDroid

async def ci_performance_check():
    droid = PerformanceAnalyzerDroid()

    result = await droid.execute(
        path='src/',
        depth='light'
    )

    findings = json.loads(result['output'])

    # Fail if critical performance issues found
    critical_issues = sum(
        1 for b in findings['bottlenecks']
        if b['severity_score'] >= 8
    )

    if critical_issues > 0:
        print(f"FAIL: {critical_issues} critical performance issues found")
        sys.exit(1)

    print(f"PASS: Performance score {findings['overall_performance_score']}/10")
    sys.exit(0)

asyncio.run(ci_performance_check())
```

## Turn-by-Turn Analysis Details

### Turn 1: Bottleneck Identification

**Purpose**: Identify performance bottlenecks and hot paths

**Analyzes**:
- Nested loops and inefficient algorithms
- Blocking I/O operations
- Database query inefficiencies (N+1 queries)
- Repeated calculations
- Unnecessary object creation

**Output**:
- List of bottlenecks with severity scores
- Hot paths with estimated frequency
- Inefficient operations
- Overall performance score (0-10)

### Turn 2: Complexity Analysis

**Purpose**: Analyze algorithmic complexity using Big-O notation

**Analyzes**:
- Time complexity (execution time)
- Space complexity (memory usage)
- Suboptimal complexity patterns
- Opportunities for caching/memoization

**Output**:
- Complexity issues with current vs optimal
- Time/space complexity mappings
- Worst complexity found
- Count of improvement opportunities

### Turn 3: Memory Analysis

**Purpose**: Identify memory usage patterns and leaks

**Analyzes**:
- Memory leak risks (unclosed resources, circular refs)
- Excessive memory usage
- Memory allocation patterns
- Object reuse opportunities
- Long-lived object issues

**Output**:
- List of memory issues with severity
- Memory leak risks
- Optimization opportunities
- Memory score (0-10)
- Peak memory concerns

### Turn 4: Optimization Recommendations

**Purpose**: Provide prioritized optimization recommendations

**Analyzes**:
- Impact vs implementation complexity
- Expected performance improvements
- Trade-offs (speed vs memory, etc.)
- Implementation strategies

**Output**:
- Prioritized recommendations (1-10 priority score)
- Top 3-5 priority optimizations
- Expected improvements (time/memory percentages)
- Quick wins (easy high-impact changes)
- Profiling recommendations

## Best Practices

1. **Start with Light Analysis**: Use `depth="light"` for quick scans
2. **Use Focus Areas**: Specify `focus` for targeted analysis
3. **Validate with Profiling**: Use profiling tools to validate recommendations
4. **Implement Quick Wins First**: Start with low-complexity, high-impact optimizations
5. **Monitor Memory Score**: Scores below 5.0 indicate serious memory issues
6. **Check Worst Complexity**: O(n²) or worse often indicates optimization needs

## Limitations

- **Token Limits**: Large files (>5000 chars) are truncated
- **Directory Limits**: Maximum 10 files per directory analysis
- **Language**: Currently optimized for Python code
- **API Dependency**: Requires Anthropic API or LiteLLM proxy

## Error Handling

The droid gracefully handles errors:

```python
result = await droid.execute(path='/invalid/path')

if 'error' in json.loads(result['output']):
    print("Analysis failed:", result['summary'])
else:
    print("Analysis succeeded")
```

## Integration Examples

### With Logging

```python
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def analyze_with_logging():
    droid = PerformanceAnalyzerDroid()

    logger.info("Starting performance analysis")
    result = await droid.execute(path='src/')

    findings = json.loads(result['output'])

    logger.info(f"Analysis complete: {result['summary']}")
    logger.info(f"Performance score: {findings['overall_performance_score']}/10")
    logger.info(f"Memory score: {findings['memory_score']}/10")

    return findings
```

### With Pytest

```python
import pytest
from klean.agents import PerformanceAnalyzerDroid

@pytest.mark.asyncio
async def test_performance_acceptable():
    droid = PerformanceAnalyzerDroid()
    result = await droid.execute(path='src/critical_module.py')

    findings = json.loads(result['output'])

    # Assert performance standards
    assert findings['overall_performance_score'] >= 7.0
    assert findings['memory_score'] >= 7.0
    assert findings['worst_complexity'] not in ['O(n³)', 'O(2^n)', 'O(n!)']
```

## FAQ

**Q: How long does analysis take?**
A: Depends on depth and code size. Light: ~10-20s, Medium: ~30-40s, Deep: ~60-90s

**Q: Can I analyze non-Python code?**
A: The droid is optimized for Python but can analyze other languages with reduced accuracy.

**Q: What's the difference between bottlenecks and complexity issues?**
A: Bottlenecks are specific performance problems; complexity issues are algorithmic inefficiencies (Big-O).

**Q: How accurate are the expected improvements?**
A: Estimates are based on typical patterns. Actual improvements should be validated with profiling.

**Q: Can I use this in CI/CD?**
A: Yes! Use light analysis mode and fail builds on critical issues (severity >= 8).

## See Also

- [ArchitectReviewerDroid](./architect_reviewer_droid.md) - Architecture analysis
- [SecurityAuditorDroid](./security_auditor_droid.md) - Security analysis
- [Agent SDK Documentation](./agent_sdk.md) - SDK reference
