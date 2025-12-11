# PerformanceAnalyzerDroid Quick Start

## Installation

```bash
pipx install k-lean[agent-sdk]
```

## 30-Second Quick Start

```python
from klean.agents import PerformanceAnalyzerDroid
import asyncio

async def analyze():
    droid = PerformanceAnalyzerDroid()
    result = await droid.execute(path="your_code.py")
    print(result['summary'])

asyncio.run(analyze())
```

## Common Use Cases

### 1. Find Performance Bottlenecks
```python
result = await droid.execute(
    path="slow_module.py",
    depth="medium"
)
```

### 2. Analyze Complexity
```python
result = await droid.execute(
    path="algorithm.py",
    focus="algorithmic complexity"
)
```

### 3. Check Memory Leaks
```python
result = await droid.execute(
    path="long_running.py",
    focus="memory leaks"
)
```

### 4. Quick CI/CD Check
```python
result = await droid.execute(
    path="src/",
    depth="light"  # Fast scan
)
findings = json.loads(result['output'])
if findings['overall_performance_score'] < 6.0:
    sys.exit(1)  # Fail build
```

## Output Fields

```python
findings = json.loads(result['output'])

# Key metrics
findings['overall_performance_score']  # 0-10
findings['memory_score']               # 0-10
findings['worst_complexity']           # e.g., "O(n²)"

# Issues found
findings['bottlenecks']                # List of bottlenecks
findings['complexity_issues']          # Complexity problems
findings['memory_issues']              # Memory problems

# Recommendations
findings['quick_wins']                 # Easy high-impact fixes
findings['priority_optimizations']     # Top 3-5 to do first
findings['expected_improvements']      # Estimated gains
```

## Depth Levels

| Depth | Time | Use For |
|-------|------|---------|
| light | ~20s | CI/CD, quick checks |
| medium | ~40s | Regular review |
| deep | ~80s | Comprehensive analysis |

## Example Output

```json
{
  "overall_performance_score": 6.5,
  "memory_score": 7.0,
  "worst_complexity": "O(n²)",
  "bottlenecks": [
    {
      "name": "find_duplicates",
      "severity_score": 8,
      "type": "algorithmic"
    }
  ],
  "quick_wins": [
    "Replace nested loop with set operations",
    "Add memoization to recursive function"
  ],
  "expected_improvements": {
    "time_improvement_percent": 50,
    "memory_improvement_percent": 25
  }
}
```

## Common Patterns

### Pattern 1: Pre-commit Hook
```python
if PerformanceAnalyzerDroid().execute(path, depth="light"):
    print("✓ Performance OK")
```

### Pattern 2: Full Analysis
```python
from klean.agents import *

results = await asyncio.gather(
    SecurityAuditorDroid().execute(path),
    ArchitectReviewerDroid().execute(path),
    PerformanceAnalyzerDroid().execute(path),
)
```

### Pattern 3: Focus on Hot Path
```python
result = await droid.execute(
    path="critical_function.py",
    depth="deep",
    focus="database queries"
)
```

## Troubleshooting

**Problem**: Takes too long
**Solution**: Use `depth="light"`

**Problem**: Need specific analysis
**Solution**: Use `focus="area"` parameter

**Problem**: API not available
**Solution**: Install with `pipx install k-lean[agent-sdk]`

## Full Documentation

See `/docs/performance_analyzer_droid.md` for complete API reference.
