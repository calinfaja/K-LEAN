# Agent SDK Droids Comparison

## Overview

K-LEAN provides three specialized Agent SDK droids for comprehensive code analysis:

| Droid | Purpose | Turns | Recommended Model | Focus |
|-------|---------|-------|-------------------|-------|
| **SecurityAuditorDroid** | Security vulnerability analysis | 3 | Any (auto-selected) | OWASP, CWE, exploitability |
| **ArchitectReviewerDroid** | Architecture and design analysis | 4 | deepseek-v3-thinking | SOLID, patterns, structure |
| **PerformanceAnalyzerDroid** | Performance and optimization | 4 | qwen3-coder | Complexity, memory, speed |

## Quick Comparison

### SecurityAuditorDroid

**Best for**: Security audits, vulnerability scanning, compliance checks

**Analysis Process**:
1. Initial vulnerability scan
2. OWASP/CWE cross-reference
3. Prioritization and remediation

**Key Output**:
- Vulnerability findings with severity
- CWE/OWASP mappings
- Exploitability scores
- Fix recommendations

**Use When**:
- Security audits required
- Pre-deployment checks
- Compliance validation
- After dependency updates

---

### ArchitectReviewerDroid

**Best for**: Architecture review, design pattern analysis, SOLID principles

**Analysis Process**:
1. Component mapping and dependencies
2. Design pattern detection
3. SOLID principle evaluation
4. Architectural recommendations

**Key Output**:
- Component dependency graph
- Design patterns identified
- SOLID violations
- Refactoring suggestions

**Use When**:
- Planning refactors
- Code review process
- Onboarding new developers
- Architecture documentation

---

### PerformanceAnalyzerDroid

**Best for**: Performance optimization, bottleneck identification, complexity analysis

**Analysis Process**:
1. Bottleneck identification
2. Complexity analysis (Big-O)
3. Memory leak detection
4. Optimization recommendations

**Key Output**:
- Performance bottlenecks
- Time/space complexity
- Memory issues
- Expected improvements

**Use When**:
- Performance issues reported
- Before production deployment
- Scaling concerns
- Resource optimization needed

## Feature Comparison Matrix

| Feature | Security | Architecture | Performance |
|---------|----------|--------------|-------------|
| **Multi-turn analysis** | ✓ (3 turns) | ✓ (4 turns) | ✓ (4 turns) |
| **JSON output** | ✓ | ✓ | ✓ |
| **Severity scoring** | ✓ | ✗ | ✓ |
| **Code examples** | ✓ | ✗ | ✗ |
| **External standards** | ✓ (OWASP/CWE) | ✓ (SOLID) | ✓ (Big-O) |
| **Priority ranking** | ✓ | ✓ | ✓ |
| **Quick wins** | ✗ | ✗ | ✓ |
| **Expected impact** | ✗ | ✓ | ✓ |
| **Focus areas** | ✓ | ✓ | ✓ |
| **Depth levels** | ✓ | ✓ | ✓ |

## Usage Patterns

### Complete Code Review Workflow

```python
from klean.agents import (
    SecurityAuditorDroid,
    ArchitectReviewerDroid,
    PerformanceAnalyzerDroid
)
import asyncio
import json

async def comprehensive_review(path: str):
    """Run all three droids on the same codebase."""

    # Security audit
    security = SecurityAuditorDroid()
    sec_result = await security.execute(path, depth="medium")
    sec_findings = json.loads(sec_result['output'])

    # Architecture review
    architect = ArchitectReviewerDroid()
    arch_result = await architect.execute(path, depth="medium")
    arch_findings = json.loads(arch_result['output'])

    # Performance analysis
    performance = PerformanceAnalyzerDroid()
    perf_result = await performance.execute(path, depth="medium")
    perf_findings = json.loads(perf_result['output'])

    # Compile summary
    summary = {
        "security": {
            "critical_issues": sec_findings.get('severity_counts', {}).get('critical', 0),
            "total_findings": sec_findings.get('total_findings', 0),
        },
        "architecture": {
            "solid_score": arch_findings.get('overall_solid_score', 0),
            "anti_patterns": len(arch_findings.get('anti_patterns', [])),
            "total_components": arch_findings.get('total_components', 0),
        },
        "performance": {
            "performance_score": perf_findings.get('overall_performance_score', 0),
            "memory_score": perf_findings.get('memory_score', 0),
            "worst_complexity": perf_findings.get('worst_complexity', 'Unknown'),
        }
    }

    return summary

# Run
result = asyncio.run(comprehensive_review('src/'))
print(json.dumps(result, indent=2))
```

### CI/CD Integration

```python
async def ci_quality_gate(path: str):
    """Quality gate for CI/CD pipeline."""

    # Run all checks in parallel
    security = SecurityAuditorDroid()
    architect = ArchitectReviewerDroid()
    performance = PerformanceAnalyzerDroid()

    results = await asyncio.gather(
        security.execute(path, depth="light"),
        architect.execute(path, depth="light"),
        performance.execute(path, depth="light"),
    )

    sec_findings = json.loads(results[0]['output'])
    arch_findings = json.loads(results[1]['output'])
    perf_findings = json.loads(results[2]['output'])

    # Define quality gates
    critical_security = sec_findings.get('severity_counts', {}).get('critical', 0)
    solid_score = arch_findings.get('overall_solid_score', 0)
    perf_score = perf_findings.get('overall_performance_score', 0)

    # Fail if any gate violated
    if critical_security > 0:
        print(f"FAIL: {critical_security} critical security issues")
        return False

    if solid_score < 6.0:
        print(f"FAIL: SOLID score {solid_score} below threshold 6.0")
        return False

    if perf_score < 6.0:
        print(f"FAIL: Performance score {perf_score} below threshold 6.0")
        return False

    print("PASS: All quality gates met")
    return True
```

### Targeted Analysis

```python
async def targeted_analysis(issue_type: str, path: str):
    """Run specific droid based on issue type."""

    if issue_type == "security":
        droid = SecurityAuditorDroid()
        return await droid.execute(path, depth="deep", focus="authentication")

    elif issue_type == "architecture":
        droid = ArchitectReviewerDroid()
        return await droid.execute(path, depth="deep", focus="coupling")

    elif issue_type == "performance":
        droid = PerformanceAnalyzerDroid()
        return await droid.execute(path, depth="deep", focus="database")

    else:
        raise ValueError(f"Unknown issue type: {issue_type}")
```

## Model Recommendations

### Default Auto-Selection

Each droid automatically selects the best available model:

```python
# Auto-selection based on task type
security = SecurityAuditorDroid()     # Auto-selects best for security
architect = ArchitectReviewerDroid()  # Auto-selects deepseek-v3-thinking
performance = PerformanceAnalyzerDroid()  # Auto-selects qwen3-coder
```

### LiteLLM Model Mapping

| Task | Recommended Model | Fallback |
|------|------------------|----------|
| Security | Any available | claude-opus-4-5 |
| Architecture | deepseek-v3-thinking | claude-opus-4-5 |
| Performance | qwen3-coder | claude-opus-4-5 |

### Custom Model Selection

```python
# Use specific models
security = SecurityAuditorDroid(model="claude-opus-4-5-20251101")
architect = ArchitectReviewerDroid(model="deepseek-v3-thinking")
performance = PerformanceAnalyzerDroid(model="qwen3-coder")
```

## Output Format Comparison

### Security Output Structure

```json
{
  "audit_summary": {...},
  "total_findings": 5,
  "findings": [...],
  "cwe_mappings": [...],
  "owasp_mappings": [...],
  "recommendations": [...],
  "severity_counts": {
    "critical": 1,
    "high": 2,
    "medium": 2,
    "low": 0
  }
}
```

### Architecture Output Structure

```json
{
  "review_summary": {...},
  "total_components": 15,
  "components": [...],
  "dependencies": [...],
  "patterns_found": [...],
  "anti_patterns": [...],
  "solid_violations": [...],
  "solid_scores": {...},
  "overall_solid_score": 7.5,
  "recommendations": [...]
}
```

### Performance Output Structure

```json
{
  "analysis_summary": {...},
  "total_bottlenecks": 3,
  "bottlenecks": [...],
  "hot_paths": [...],
  "complexity_issues": [...],
  "worst_complexity": "O(n²)",
  "memory_issues": [...],
  "memory_score": 6.5,
  "overall_performance_score": 7.0,
  "recommendations": [...],
  "quick_wins": [...]
}
```

## Best Practices

### When to Use Which Droid

1. **Start with Architecture** if:
   - New to the codebase
   - Planning major refactoring
   - Need documentation
   - Onboarding team members

2. **Use Security** when:
   - Pre-deployment checks
   - After dependency updates
   - Compliance required
   - Handling sensitive data

3. **Use Performance** if:
   - Speed issues reported
   - Scaling concerns
   - High resource usage
   - Before optimization work

### Combining Droids

**Best Combination for Production Readiness**:
```bash
1. Architecture review (understand structure)
2. Security audit (fix vulnerabilities)
3. Performance analysis (optimize critical paths)
```

**Best Combination for Legacy Code**:
```bash
1. Architecture review (understand design)
2. Performance analysis (find quick wins)
3. Security audit (address risks)
```

**Best Combination for CI/CD**:
```bash
All three in parallel with light depth
```

## Performance Characteristics

| Droid | Light Depth | Medium Depth | Deep Depth |
|-------|-------------|--------------|------------|
| Security | ~15-20s | ~30-40s | ~60-80s |
| Architecture | ~20-30s | ~40-50s | ~70-100s |
| Performance | ~15-25s | ~35-45s | ~60-90s |

*Times approximate, vary by code size and model*

## Common Patterns

### Pattern 1: Pre-Commit Hook

```python
async def pre_commit_check():
    """Fast check before commit."""
    changed_files = get_git_changed_files()

    security = SecurityAuditorDroid()
    results = await security.execute(
        path=changed_files[0],
        depth="light"
    )

    findings = json.loads(results['output'])
    critical = findings.get('severity_counts', {}).get('critical', 0)

    if critical > 0:
        print("❌ Critical security issues found!")
        return False
    return True
```

### Pattern 2: Nightly Full Analysis

```python
async def nightly_analysis():
    """Comprehensive nightly analysis."""

    results = await asyncio.gather(
        SecurityAuditorDroid().execute('src/', depth='deep'),
        ArchitectReviewerDroid().execute('src/', depth='deep'),
        PerformanceAnalyzerDroid().execute('src/', depth='deep'),
    )

    # Store results in database
    # Generate report
    # Send notifications if issues found
```

### Pattern 3: Hot Path Optimization

```python
async def optimize_hot_path(function_name: str):
    """Optimize specific hot path."""

    # First, confirm it's actually slow
    perf = PerformanceAnalyzerDroid()
    result = await perf.execute(
        path=f'src/{function_name}.py',
        depth='deep',
        focus=function_name
    )

    findings = json.loads(result['output'])

    # Get specific recommendations for this function
    recommendations = [
        r for r in findings['recommendations']
        if function_name in r['issue']
    ]

    return recommendations
```

## Integration Examples

### With GitHub Actions

```yaml
name: Code Quality Analysis

on: [pull_request]

jobs:
  analyze:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Run Security Audit
        run: |
          python3 -c "
          from klean.agents import SecurityAuditorDroid
          import asyncio
          result = asyncio.run(SecurityAuditorDroid().execute('src/', depth='light'))
          print(result['summary'])
          "
```

### With Jupyter Notebook

```python
# In Jupyter notebook
from klean.agents import PerformanceAnalyzerDroid
import asyncio
import json

# Enable async in Jupyter
%load_ext asyncio

droid = PerformanceAnalyzerDroid()
result = await droid.execute('src/main.py', depth='medium')

findings = json.loads(result['output'])

# Visualize results
import matplotlib.pyplot as plt

bottlenecks = findings['bottlenecks']
names = [b['name'] for b in bottlenecks]
scores = [b['severity_score'] for b in bottlenecks]

plt.barh(names, scores)
plt.xlabel('Severity Score')
plt.title('Performance Bottlenecks')
plt.show()
```

## Troubleshooting

### Issue: Analysis takes too long

**Solution**: Use `depth="light"` for faster analysis

```python
# Fast analysis
result = await droid.execute(path, depth="light")
```

### Issue: Token limit exceeded

**Solution**: Analyze smaller files or directories

```python
# Analyze specific files
for file in large_directory.glob('*.py'):
    result = await droid.execute(str(file))
```

### Issue: Model not available

**Solution**: Specify fallback model

```python
try:
    droid = PerformanceAnalyzerDroid(model="qwen3-coder")
except:
    droid = PerformanceAnalyzerDroid(model="claude-opus-4-5-20251101")
```

## See Also

- [SecurityAuditorDroid Documentation](./security_auditor_droid.md)
- [ArchitectReviewerDroid Documentation](./architect_reviewer_droid.md)
- [PerformanceAnalyzerDroid Documentation](./performance_analyzer_droid.md)
- [Agent SDK Guide](./agent_sdk.md)
