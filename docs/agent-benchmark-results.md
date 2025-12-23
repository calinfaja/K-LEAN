# K-LEAN Agent Benchmark Results

**Date**: 2025-12-23
**Test Subject**: MicroPython Zephyr Cryptographic Module (last 3 commits)
**Telemetry**: Phoenix at http://localhost:6006

---

## Executive Summary

This benchmark evaluates K-LEAN's agent variants on real-world embedded cryptographic code from MicroPython's Zephyr port. The test includes:
- ~1055 lines of diff across modcrypto.c, modcrypto_ext.c, modcrypto_ext.h
- Recent commits: ECDH-P224, ECDSA-P224, HMAC-SHA-1, HMAC-SHA-224, SHA-1, SHA-224
- Target: nRF5340-DK with TrustZone CryptoCell CC312, PSA Crypto API

### Key Findings

| Metric | T1 (Direct) | T2 (SmolKLN) | T3 (3-Agent) | T4 (4-Agent) | T5 (Deep) | T6 (Claude+Tools) |
|--------|-------------|--------------|--------------|--------------|-----------|-------------------|
| **Execution Time** | 13.6s | 181.9s | 1140.4s | 1545.4s | 455.9s | ~180s |
| **Critical/High** | 2 | 2 | 2 | 5 | 0 | 3 |
| **Warnings** | 4 | 5 | 7 | 12 | 1 | 10 |
| **Grade** | - | - | - | - | A- | B+ |
| **Verdict** | REQUEST_CHANGES | REQUEST_CHANGES | REQUEST_CHANGES | REQUEST_CHANGES | APPROVE | REQUEST_CHANGES |

**Winner by Category:**
- **Speed**: T1 (13.6s) - Direct API, no tools
- **Thoroughness**: T6 (Claude Opus + tools) - Most detailed analysis
- **Multi-Agent**: T4 (4-agent) - Best coverage with 13 unique issues
- **Cost-Effectiveness**: T5 (qwen3-coder + tools) - Good depth at 7.5 min
- **Most Optimistic**: T5 gave A- grade vs others requesting changes

---

## Methodology

### Benchmark Standards Reference

Industry benchmarks for AI code review agents:

| Benchmark | What It Measures |
|-----------|-----------------|
| **SWE-bench** | Issue resolution rate on real GitHub issues |
| **HumanEval** | Code generation accuracy |
| **AgentBench** | Multi-turn task completion |
| **ToolBench** | Tool usage effectiveness |

### Our Metrics

| Metric | Description |
|--------|-------------|
| **Execution Time** | Wall clock time to completion |
| **Issues Found** | Count by severity (CRITICAL/HIGH/MEDIUM/LOW) |
| **False Positive Rate** | Subjective assessment of incorrect findings |
| **Coverage** | Categories of issues detected |
| **Coordination Quality** | For multi-agent: delegation effectiveness |
| **Unique Findings** | Issues found by this variant but not others |

### Test Matrix

| Test ID | Tool | Model(s) | Description |
|---------|------|----------|-------------|
| T1 | LiteLLM Direct | qwen3-coder | Single model, direct review via curl |
| T2 | SmolKLN Agent | code-reviewer (qwen3-coder) | Agentic review with tools |
| T3 | k-lean multi | GLM-4.6-thinking → qwen3-coder → deepseek-v3 | 3-agent orchestrated |
| T4 | k-lean multi --thorough | 4-agent with security specialist | Most comprehensive |
| T5 | deep-review.sh | qwen3-coder | Claude headless + LiteLLM with tools |
| T6 | Task agent | Claude Opus | Claude native with Read/Grep/Glob/Bash |

### Test Prompt (Consistent)

```
Review the latest 3 commits in modcrypto.c and modcrypto_ext.c for:
1. Security vulnerabilities (CRITICAL for crypto code)
2. Memory safety issues (buffer overflows, leaks)
3. Logic errors and bugs
4. Code quality and standards compliance
```

---

## Test Results

### T1: LiteLLM Direct with Qwen3-Coder

**Status**: ✅ Completed

```
Command: curl http://localhost:4000/v1/chat/completions (qwen3-coder)
Time: 13.6s
```

**Summary**:
| Severity | Count | Issues |
|----------|-------|--------|
| CRITICAL | 1 | SHA-1 usage (cryptographically broken) |
| HIGH | 1 | Shared static buffers (data leakage) |
| MEDIUM | 3 | Buffer sizing, error handling inconsistency |
| LOW | 2 | Missing input validation, documentation |

**Key Findings**:
1. **CRITICAL: SHA-1 Usage** - Multiple locations implementing deprecated SHA-1
2. **HIGH: Shared Static Buffers** - Line 960: `hmac_mac_buf[HMAC_MAX_MAC_SIZE]` shared across operations
3. **HIGH: Code Duplication** - Lines 1086-1167 vs 1170-1251 (HMAC-SHA1 vs HMAC-SHA224)

**Unique to T1**: Code duplication analysis, documentation inconsistencies

---

### T2: SmolKLN Code-Reviewer Agent

**Status**: ✅ Completed

```
Command: smol-kln code-reviewer "<prompt>" --telemetry
Time: 181.9s (3 minutes)
Agent Steps: 28
```

**Summary**:
| Severity | Count | Issues |
|----------|-------|--------|
| CRITICAL | 2 | Integer overflow, Buffer overflow |
| WARNING | 5 | Side-channel, Thread safety, Nonce reuse |
| SUGGESTION | 3 | Performance, Resource cleanup |

**Key Findings**:
1. **CRITICAL: Integer Overflow** - modcrypto.c:838 - HMAC update check can wrap
2. **CRITICAL: Buffer Overflow** - modcrypto_ext.c:321 - ChaCha20-Poly1305 tag concat
3. **WARNING: Side-channel** - modcrypto.c:426-441 - Non-constant-time CTR operations
4. **WARNING: Predictable Nonces** - modcrypto_ext.c:124-147 - ChaCha20-Poly1305 nonce

**Unique to T2**: ChaCha20-Poly1305 nonce reuse vulnerability, ECB per-block inefficiency

---

### T3: Multi 3-Agent Review

**Status**: ✅ Completed

```
Command: k-lean multi "<prompt>" --telemetry
Time: 1140.4s (19 minutes)
Agents: manager (GLM-4.6-thinking) → file_scout (qwen3-coder) → analyzer (deepseek-v3)
```

**Summary**:
| Severity | Count | Issues |
|----------|-------|--------|
| CRITICAL | 2 | Buffer overflows (HMAC, ChaCha20) |
| WARNING | 7 | Side-channel, thread safety, error handling |
| SUGGESTION | 3 | Performance optimizations |

**Key Findings**:
1. **CRITICAL: HMAC Buffer Overflow** - Integer overflow in size check
2. **CRITICAL: ChaCha20-Poly1305 Buffer Overflow** - Tag concatenation without bounds
3. **WARNING: IV Update Before Error Check** - modcrypto.c:382-388
4. **WARNING: Thread Safety** - Static buffers shared across instances

**Agent Coordination**: Good delegation from manager to specialists. file_scout successfully located target files.

---

### T4: Multi 4-Agent Thorough Review

**Status**: ✅ Completed

```
Command: k-lean multi --thorough "<prompt>" --telemetry
Time: 1545.4s (26 minutes)
Agents: manager (GLM-4.6) → file_scout (qwen3) + code_analyzer (deepseek) + security_auditor (deepseek) + synthesizer (deepseek)
```

**Summary**:
| Severity | Count | Issues |
|----------|-------|--------|
| HIGH | 5 | ECB mode, random(), integer underflow, buffer overflow, thread safety |
| MEDIUM | 7 | SHA-1, memcpy bounds, debug logs, PSA error handling |
| LOW | 1 | Side-channel comparisons |

**Key Findings**:
1. **HIGH: ECB Mode Insecure** - Multiple locations using PSA_ALG_ECB
2. **HIGH: Non-cryptographic random()** - Replace with psa_generate_random()
3. **HIGH: Integer Underflow** - modcrypto_ext.c:256 - `ciphertext_len - 16` without bounds check
4. **HIGH: RSA Buffer Overflow** - modcrypto_ext.c:1206 - Key import vulnerability
5. **HIGH: Thread Safety** - Static variables in multi-core nRF5340 environment

**Security Auditor Deep Analysis**:
- Identified 8 calls to random() (verified all use psa_generate_random - TRNG)
- Found 51 calls to mbedtls_platform_zeroize (proper memory cleanup)
- Flagged 7 SHA-1 references (deprecated algorithm)
- Flagged 5 ECB mode references (insecure mode)

**Risk Assessment**: HIGH risk, HIGH confidence
**Verdict**: REQUEST_CHANGES

---

### T5: Deep Review (Claude Headless + qwen3-coder via LiteLLM)

**Status**: ✅ Completed

```
Command: ~/.claude/scripts/deep-review.sh qwen3-coder "<prompt>"
Time: 455.9s (7.6 minutes)
Tools: Read, Grep, Glob, Bash (via ~/.claude-nano config)
```

**Summary**:
| Severity | Count | Issues |
|----------|-------|--------|
| CRITICAL | 0 | None identified |
| WARNING | 1 | SHA-1 deprecated |
| SUGGESTION | 2 | Concurrency docs, algorithm options |

**Key Findings**:
- **GRADE: A-** (most optimistic of all tests)
- **RISK: LOW**
- Praised memory safety with `mbedtls_platform_zeroize()`
- Approved buffer overflow protection
- Found constant-time comparisons adequate
- Only flagged SHA-1 as legacy concern

**Unique to T5**: Most positive assessment - approved code as "production-ready"

**Analysis**: Same model (qwen3-coder) gave very different results:
- T1 (no tools): Found 6 issues, REQUEST_CHANGES
- T5 (with tools): Found 1 issue, APPROVE with A- grade

This suggests tool access may lead to more context but less critical analysis.

---

### T6: Claude Opus with Full Tools

**Status**: ✅ Completed

```
Command: Task agent (subagent_type=general-purpose)
Time: ~180s (3 minutes)
Tools: Read, Grep, Glob, Bash
Model: Claude Opus 4.5
```

**Summary**:
| Severity | Count | Issues |
|----------|-------|--------|
| CRITICAL | 2 | ChaCha20 nonce race, static buffer race |
| HIGH | 1 | Integer overflow in decrypt |
| MEDIUM | 7 | SHA-1, timing leaks, input validation, memory leaks |
| LOW | 3 | Error messages, buffer limits, X25519 validation |

**Key Findings**:
- **GRADE: B+**
- **RISK: MEDIUM**
1. **CRITICAL: Nonce Counter Race** - modcrypto_ext.c:109-143 - `chacha20_nonce_counter++` not atomic
2. **CRITICAL: Static Buffer Race** - Multiple locations - No mutex on shared buffers
3. **HIGH: Integer Overflow** - modcrypto_ext.c:322 - `ct_info.len + 16` can wrap

**Security Auditor Deep Analysis**:
- Traced 117 calls to `mbedtls_platform_zeroize()` (proper cleanup)
- Identified 221 buffer bounds checks (comprehensive)
- Found race conditions across 7 functions using static buffers
- Provided specific fix recommendations with code examples

**Unique to T6**:
- Most detailed thread-safety analysis
- Specific CWE references (CWE-362, CWE-190, CWE-208)
- Exploitation scenarios with code examples
- Estimated remediation time (5-7 days)

**Verdict**: REQUEST_CHANGES

---

## Comparison Analysis

### Issue Detection Comparison

| Issue Category | T1 | T2 | T3 | T4 | T5 | T6 |
|----------------|----|----|----|----|----|----|
| Memory Safety | 1 | 2 | 2 | 3 | 0 | 2 |
| Security/Crypto | 2 | 3 | 3 | 5 | 1 | 4 |
| Thread Safety | 1 | 1 | 1 | 1 | 0 | 2 |
| Logic Errors | 2 | 2 | 2 | 2 | 0 | 3 |
| Code Quality | 3 | 2 | 3 | 3 | 2 | 2 |
| **Total Issues** | 9 | 10 | 11 | 14 | 3 | 13 |

### Performance Comparison

| Metric | T1 | T2 | T3 | T4 | T5 | T6 |
|--------|----|----|----|----|----|----|
| Execution Time | 13.6s | 181.9s | 1140.4s | 1545.4s | 455.9s | ~180s |
| Relative Speed | 1x | 13x | 84x | 114x | 34x | 13x |
| Has Tools | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Model | qwen3 | qwen3 | multi | multi | qwen3 | Opus |
| Grade Given | - | - | - | - | A- | B+ |

### Unique Findings

Issues found by only one variant:

- **T1 Only**: Code duplication analysis (DRY violations), documentation inconsistencies
- **T2 Only**: ECB per-block performance inefficiency, ChaCha20 nonce reuse specifics
- **T3 Only**: IV update timing issue before error check
- **T4 Only**: Debug logging security (keys in logs), RSA key import buffer overflow, comprehensive PSA error handling gaps (63 instances)
- **T5 Only**: Most optimistic - gave A- grade and APPROVE verdict (production-ready)
- **T6 Only**: CWE references, exploitation scenarios, remediation time estimates, most detailed thread-safety analysis

### Coverage Heat Map

| Issue Type | T1 | T2 | T3 | T4 | T5 | T6 |
|------------|:--:|:--:|:--:|:--:|:--:|:--:|
| SHA-1 Deprecation | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ |
| ECB Mode Insecurity | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Buffer Overflow | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Integer Overflow | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Side-channel | ❌ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Thread Safety | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Nonce Security | ❌ | ✅ | ✅ | ❌ | ❌ | ✅ |
| Error Handling | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ |
| Memory Leaks | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |

---

## Recommendations

### For Quick Reviews (T1)
- **Best for**: Fast feedback, pre-commit checks, initial triage
- **Limitations**: Misses side-channel, nonce issues, deep security analysis
- **Cost**: ~$0.01 per review

### For Standard Reviews (T2)
- **Best for**: Feature branches, regular development workflow
- **Limitations**: Limited subprocess access, can't run git commands
- **Cost**: ~$0.10 per review

### For Deep Single-Model Review (T5)
- **Best for**: When you want qwen3-coder with tool access
- **Limitations**: May be too optimistic (gave A- to code others flagged)
- **Cost**: ~$0.05 per review
- **Command**: `~/.claude/scripts/deep-review.sh qwen3-coder "<prompt>"`

### For Security-Critical Code (T3/T4)
- **Best for**: Cryptographic code, security audits, release reviews
- **T3 vs T4**: T4 adds 35% more time for 30% more findings
- **Cost**: ~$0.50-1.00 per review

### For Maximum Thoroughness (T6)
- **Best for**: Critical security audits, final release review
- **Strengths**: CWE references, exploitation scenarios, fix estimates
- **Limitations**: Uses Claude Opus (higher cost)
- **Cost**: ~$1-2 per review

### Optimal Workflow

```
Pre-commit → T1 (quick, 14s)
Feature Branch → T2 or T5 (standard, 3-8m)
Security Audit → T4 (multi-agent, 26m)
Final Review → T6 (Claude Opus, most thorough)
```

---

## Appendix: Raw Outputs

Full outputs stored at:
- T1: `.claude/kln/benchmark/T1_headless_qwen3.md`
- T2: `.claude/kln/benchmark/T2_smolkln_agent.md`
- T3: `/home/calin/Project/micropython_nRF/.claude/kln/multiAgent/2025-12-23_20-45-46_multi-3-agent_*.md`
- T4: `/home/calin/Project/micropython_nRF/.claude/kln/multiAgent/2025-12-23_21-12-04_multi-4-agent_*.md`
- T5: `/home/calin/Project/micropython_nRF/.claude/kln/deepInspect/2025-12-23_21-48-47_qwen3-coder_*.md`
- T6: (inline in this benchmark session)

Phoenix Traces: http://localhost:6006 (project: klean-multi)

---

## Conclusions

1. **Speed vs Depth Tradeoff**: T1 is 114x faster but finds ~60% of the issues T4 finds
2. **Multi-Agent Value**: T4 found unique issues (RSA overflow, debug logging) that simpler approaches missed
3. **Agentic Tools Matter**: T2/T3/T4/T5/T6 could read actual files and analyze code context
4. **Security Specialization**: T4's dedicated security_auditor found the most crypto-specific vulnerabilities
5. **Model Quality Matters**: T6 (Claude Opus) provided the most actionable report with CWE refs and fix estimates
6. **Tool Access ≠ Better Critique**: T5 (qwen3 + tools) was MORE optimistic than T1 (qwen3, no tools)

### Key Insight: Same Model, Different Results

| qwen3-coder | Tools | Issues | Verdict |
|-------------|-------|--------|---------|
| T1 (direct API) | ❌ | 9 | REQUEST_CHANGES |
| T5 (deep-review.sh) | ✅ | 3 | APPROVE (A-) |

Having tool access made qwen3-coder **less critical**, possibly because:
- Seeing well-structured code created positive bias
- Tool overhead reduced analysis depth
- Context window filled with code rather than analysis

**Recommended Workflow**:
- Quick checks: T1 (14s)
- Standard review: T2 (3m)
- Security audit: T4 (26m)
- Final sign-off: T6 (Claude Opus, most thorough)
