# SWE-bench Integration Roadmap

## Overview

Integration with SWE-bench for benchmarking SmolKLN agents against industry-standard coding agent evaluations.

**Status**: Planned
**Priority**: Medium
**Effort**: 1-2 weeks

## Why SWE-bench?

- Industry standard benchmark for coding agents
- Credibility: "SmolKLN scores X% on SWE-bench Verified"
- Comparison with SWE-Agent (72%), mini-SWE (74%), Letta Code (~65%)
- Marketing material for open source release

## Benchmarks to Support

| Benchmark | Instances | Focus | Priority |
|-----------|-----------|-------|----------|
| SWE-bench Verified | 500 | GitHub issue resolution | High |
| SWE-bench Lite | 300 | Faster evaluation | Medium |
| Terminal-Bench | ~200 | CLI/terminal tasks | Medium |
| SWE-bench Pro | Enterprise-scale | Enterprise complexity | Low |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SWE-bench Harness                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  src/klean/smol/swebench.py                                     │
│  ├── SWEBenchHarness        # Main harness class                │
│  ├── run_instance()         # Single instance execution         │
│  ├── run_dataset()          # Full benchmark run                │
│  └── evaluate_patch()       # Patch validation                  │
│                                                                 │
│  CLI: python -m klean.smol.swebench                             │
│  ├── --instance ID          # Run single instance               │
│  ├── --dataset NAME         # Run full dataset                  │
│  ├── --agent NAME           # Which SmolKLN agent               │
│  ├── --model NAME           # Model override                    │
│  └── --limit N              # Limit instances                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Minimal Harness (MVP)

**Goal**: Run SmolKLN agents on SWE-bench instances and generate predictions

```python
# Core functionality
class SWEBenchHarness:
    def run_instance(self, instance: dict) -> dict:
        """
        1. Clone repo at base_commit
        2. Run SmolKLN agent with problem_statement
        3. Extract patch from git diff
        4. Return prediction dict
        """

    def run_dataset(self, dataset: str, limit: int = None) -> list:
        """Run on multiple instances with checkpointing."""
```

**Deliverables**:
- `src/klean/smol/swebench.py` - Harness code (~200 lines)
- `pyproject.toml` - Add `benchmark` optional dependency
- Basic CLI interface

**Dependencies**:
```toml
[project.optional-dependencies]
benchmark = [
    "swebench>=2.0.0",
    "datasets>=2.0.0",
]
```

### Phase 2: Evaluation Pipeline

**Goal**: Run official SWE-bench evaluation and calculate scores

```bash
# Generate predictions
python -m klean.smol.swebench \
    --dataset princeton-nlp/SWE-bench_Verified \
    --agent code-reviewer \
    --output predictions.json

# Run official evaluation (requires Docker)
python -m swebench.harness.run_evaluation \
    --dataset_name princeton-nlp/SWE-bench_Verified \
    --predictions_path predictions.json \
    --run_id smolkln_v1
```

**Deliverables**:
- Predictions file format matching SWE-bench spec
- Score calculation and reporting
- Results storage in `.klean/benchmarks/`

### Phase 3: Advanced Features

**Goal**: Production-ready benchmarking with optimizations

- Parallel execution (multiple instances simultaneously)
- Checkpointing and resume
- Cost tracking per instance
- Multiple agent comparison
- Results dashboard / leaderboard view

## SWE-bench Instance Structure

```python
{
    "instance_id": "django__django-11099",      # Unique ID
    "repo": "django/django",                     # GitHub repo
    "base_commit": "abc123...",                  # Commit to checkout
    "problem_statement": "Bug description...",   # The task
    "hints_text": "",                            # Optional hints
    "patch": "diff...",                          # Gold solution (hidden)
    "test_patch": "diff...",                     # Tests to verify
    "FAIL_TO_PASS": ["test_foo"],               # Tests that should pass
    "PASS_TO_PASS": ["test_bar"],               # Tests that should stay passing
}
```

## Agent Prompt Template

```markdown
You are a software engineer tasked with fixing a bug in a repository.

## Problem Statement
{problem_statement}

## Instructions
1. Explore the repository structure to understand the codebase
2. Locate the relevant files mentioned in the problem
3. Understand the bug by reading the code
4. Create a fix for the bug
5. Output your fix as a git diff patch

## Output Format
When you have the fix, output it as:
```diff
<your patch here>
```

Make minimal changes - only fix the specific bug described.
```

## Resource Requirements

| Resource | Requirement |
|----------|-------------|
| Docker | Required for sandboxed evaluation |
| Disk | ~50GB for repo clones |
| Memory | 8GB+ recommended |
| Time | 5-15 min per instance |
| API Cost | $0.10-0.50 per instance |

### Cost Estimates

| Run Type | Instances | Time | Est. Cost |
|----------|-----------|------|-----------|
| Quick test | 1 | 10 min | $0.10 |
| Mini test | 10 | 2 hours | $1-5 |
| SWE-bench Lite | 300 | 50 hours | $30-150 |
| SWE-bench Verified | 500 | 80 hours | $50-250 |

## Comparison with Competitors

| Agent | SWE-bench Verified | Approach |
|-------|-------------------|----------|
| SWE-Agent + Claude 4.5 | 72% | Full tool suite |
| mini-SWE + Gemini 3 | 74% | Bash-only, 100 lines |
| Letta Code | ~65% | Memory-first |
| SmolKLN (target) | TBD | Multi-agent, knowledge |

## SmolKLN Advantages for Benchmarking

1. **Multi-model consensus**: Run same instance with 3-5 models, pick best
2. **Knowledge DB**: Prior solutions inform new attempts
3. **Specialist agents**: security-auditor, debugger for different issue types
4. **Cost efficiency**: Use cheap models (NanoGPT) for exploration, expensive for final patch

## Potential Strategies

### Strategy 1: Single Agent
```bash
python -m klean.smol.swebench --agent code-reviewer --model qwen3-coder
```

### Strategy 2: Best-of-N
Run multiple models, submit best patch:
```bash
for model in qwen3-coder deepseek-v3 claude-sonnet; do
    python -m klean.smol.swebench --model $model --output predictions_$model.json
done
# Merge best predictions
```

### Strategy 3: Agent Routing
Route to specialist agents based on issue type:
- Security issues -> security-auditor
- Performance issues -> performance-engineer
- General bugs -> code-reviewer

## File Structure

```
src/klean/smol/
├── swebench.py           # Main harness
├── swebench_prompt.py    # Prompt templates
└── swebench_eval.py      # Evaluation helpers

.klean/benchmarks/
├── predictions/          # Generated predictions
├── results/              # Evaluation results
└── trajectories/         # Full agent trajectories
```

## CLI Commands

```bash
# Run single instance
k-lean benchmark --instance django__django-11099

# Run full benchmark
k-lean benchmark --dataset swe-bench-verified --agent code-reviewer

# Run with specific model
k-lean benchmark --dataset swe-bench-lite --model qwen3-coder --limit 10

# Resume interrupted run
k-lean benchmark --resume predictions.json

# View results
k-lean benchmark --results
```

## Success Metrics

| Metric | Target | Notes |
|--------|--------|-------|
| SWE-bench Verified | >50% | Competitive with Letta Code |
| SWE-bench Verified | >65% | Match mini-SWE baseline |
| SWE-bench Verified | >70% | Best-in-class for multi-agent |
| Cost per instance | <$0.20 | Via NanoGPT/OpenRouter |

## Next Steps

1. [ ] Create minimal harness (`swebench.py`)
2. [ ] Add `benchmark` optional dependency
3. [ ] Test on 10 instances
4. [ ] Run full SWE-bench Lite (300)
5. [ ] Optimize prompts based on failures
6. [ ] Run SWE-bench Verified (500)
7. [ ] Document results in README

## References

- [SWE-bench Paper](https://arxiv.org/abs/2310.06770)
- [SWE-bench GitHub](https://github.com/princeton-nlp/SWE-bench)
- [SWE-bench Leaderboard](https://www.swebench.com/)
- [mini-SWE-agent](https://github.com/SWE-agent/mini-SWE-agent) - 100-line reference
- [SWE-agent](https://github.com/SWE-agent/SWE-agent) - Full-featured reference
