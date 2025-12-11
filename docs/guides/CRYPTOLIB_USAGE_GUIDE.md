# CryptolibImplementationDroid - Complete Usage Guide

**Version:** 1.0.0
**Date:** 2025-12-11
**Status:** Production-Ready

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [System Prompt Explanation](#system-prompt-explanation)
3. [Basic Usage](#basic-usage)
4. [Advanced Usage](#advanced-usage)
5. [Real-World Examples](#real-world-examples)
6. [Understanding Output](#understanding-output)
7. [Best Practices](#best-practices)

---

## Quick Start

### Installation

The droid is already part of K-LEAN v2.0.0+. Ensure you have the Agent SDK installed:

```bash
pipx install k-lean[agent-sdk]
```

### Minimal Example

```python
from klean.agents import CryptolibImplementationDroid
import asyncio
import json

async def main():
    # Create droid instance
    droid = CryptolibImplementationDroid()

    # Analyze crypto code
    result = await droid.execute(
        target="src/crypto/aes_implementation.c",
        depth="medium"
    )

    # Parse and print results
    output = json.loads(result["output"])
    print(json.dumps(output["overall_findings"], indent=2))

asyncio.run(main())
```

**Output:**
```
{
  "analysis_complete": true,
  "crypto_libraries": ["MbedTLS", "CryptoCell-310"],
  "compliance_level": "2",
  "security_score": 0.92,
  "overall_readiness": "PRODUCTION_READY"
}
```

---

## System Prompt Explanation

### What is the System Prompt?

The system prompt is the **instruction given to Claude** that defines the droid's behavior, expertise, and analysis approach. It acts as the "personality" and "knowledge base" for the analysis.

### CryptolibImplementationDroid System Prompt

```
You are an expert cryptographer specializing in embedded systems and Nordic nRF SDK implementations.

Your expertise includes:
- PSA Certified Crypto APIs
- MbedTLS cryptography library
- Oberon PSA Crypto implementations
- nRF52/nRF53/nRF91 CryptoCell hardware acceleration
- FIPS 140-3 compliance validation (Levels 1-4)
- Side-channel attack resistance
- Secure key management
- DFU and secure boot integration
- Nordic nRF Connect SDK best practices

Analysis Depth: [light|medium|deep]
Focus Area: [psa_api|key_management|performance|fips_compliance|none]

Provide detailed, security-focused analysis in JSON format. Focus on:
1. Correct algorithm implementation
2. FIPS 140-3 compliance
3. Side-channel vulnerabilities
4. Key management security
5. Hardware acceleration usage
6. Memory footprint optimization
7. Nordic SDK compliance
```

### How the System Prompt Works

The system prompt is **dynamically built** based on your analysis parameters:

```python
def _build_system_prompt(self, depth: str, focus: Optional[str]) -> str:
    """Build system prompt for cryptographic analysis."""
    return f"""You are an expert cryptographer specializing in embedded systems...

    Analysis Depth: {depth}           # "light", "medium", or "deep"
    Focus Area: {focus or "general"}  # "psa_api", "key_management", etc.

    Provide detailed, security-focused analysis in JSON format...
    """
```

**Example Generated Prompts:**

**Prompt 1 (Medium depth, PSA focus):**
```
You are an expert cryptographer...
Analysis Depth: medium
Focus Area: psa_api
Provide detailed, security-focused analysis...
```

**Prompt 2 (Deep depth, FIPS compliance focus):**
```
You are an expert cryptographer...
Analysis Depth: deep
Focus Area: fips_compliance
Provide detailed, security-focused analysis...
```

---

## Basic Usage

### Usage 1: Quick Scan

```python
from klean.agents import CryptolibImplementationDroid
import asyncio

async def quick_scan():
    droid = CryptolibImplementationDroid()

    # Light analysis - fast, high-level
    result = await droid.execute(
        target="src/crypto/aes.c",
        depth="light"
    )

    print(f"Turns completed: {result['turns']}")
    print(f"Analysis complete: {'output' in result}")

asyncio.run(quick_scan())
```

**Expected Result:**
- Duration: 5-10 seconds
- Output: Basic findings, pattern recognition
- Use Case: Initial screening before detailed review

### Usage 2: Standard Analysis

```python
async def standard_analysis():
    droid = CryptolibImplementationDroid()

    # Medium analysis - detailed, recommended
    result = await droid.execute(
        target="src/crypto/",  # Can analyze directory
        depth="medium"
    )

    output = json.loads(result["output"])

    # Check security score
    security_score = output["turn_3_security_analysis"]["security_score"]

    if security_score >= 0.85:
        print("✅ Cryptographic implementation is secure")
    else:
        print(f"⚠️  Security issues found (score: {security_score})")

    # Print recommendations
    recommendations = output["turn_5_recommendations"]["priority_fixes"]
    for fix in recommendations:
        print(f"  - {fix['issue']} (Priority: {fix['priority']})")

asyncio.run(standard_analysis())
```

**Expected Result:**
- Duration: 10-20 seconds
- Output: Comprehensive findings across all 5 turns
- Use Case: Full security review

### Usage 3: Deep Compliance Audit

```python
async def compliance_audit():
    droid = CryptolibImplementationDroid()

    # Deep analysis with FIPS focus
    result = await droid.execute(
        target="src/bootloader/dfu_crypto.c",
        depth="deep",
        focus="fips_compliance"
    )

    output = json.loads(result["output"])

    # Check FIPS level
    fips_level = output["turn_2_compliance_assessment"]["fips_140_3_level"]

    print(f"FIPS 140-3 Level: {fips_level}")

    # Check DFU security
    dfu_security = output["turn_5_recommendations"]["dfu_security"]["secure"]
    print(f"DFU Security: {'✅ SECURE' if dfu_security else '❌ INSECURE'}")

asyncio.run(compliance_audit())
```

**Expected Result:**
- Duration: 20-30 seconds
- Output: Exhaustive analysis with optimization suggestions
- Use Case: Certification preparation, compliance validation

---

## Advanced Usage

### Usage 4: Focused Analysis

```python
async def key_management_audit():
    """Focus specifically on key management practices."""
    droid = CryptolibImplementationDroid()

    result = await droid.execute(
        target="src/security/key_manager.c",
        depth="deep",
        focus="key_management"
    )

    output = json.loads(result["output"])

    # Get key management findings
    key_issues = output["turn_3_security_analysis"]["key_management_issues"]

    if not key_issues:
        print("✅ No key management issues detected")
    else:
        for issue in key_issues:
            print(f"❌ {issue}")

    # Get recommendations
    kd_recs = output["turn_5_recommendations"]["secure_key_derivation"]
    print("\nRecommendations:")
    for rec in kd_recs:
        print(f"  • {rec}")

asyncio.run(key_management_audit())
```

### Usage 5: Performance Optimization

```python
async def optimize_crypto():
    """Find memory optimization opportunities."""
    droid = CryptolibImplementationDroid()

    result = await droid.execute(
        target="src/crypto/",
        depth="medium",
        focus="performance"
    )

    output = json.loads(result["output"])

    # Get memory estimate
    memory = output["turn_4_performance_metrics"]["memory_estimate"]
    print(f"Current footprint:")
    print(f"  Flash: {memory['flash_kb']} KB")
    print(f"  RAM: {memory['ram_kb']} KB")
    print(f"  Stack: {memory['stack_kb']} KB")

    # Get optimization opportunities
    optimizations = output["turn_4_performance_metrics"]["optimization_opportunities"]
    print("\nOptimization opportunities:")
    for opt in optimizations:
        print(f"  • {opt['type']}: Save ~{opt['expected_savings_kb']} KB")

    # Check device compatibility
    devices = output["turn_4_performance_metrics"]["nrf_device_compatibility"]
    print(f"\nCompatible devices: {', '.join(devices)}")

asyncio.run(optimize_crypto())
```

### Usage 6: Batch Analysis

```python
import glob

async def analyze_all_crypto():
    """Analyze all cryptographic files in project."""
    droid = CryptolibImplementationDroid()

    results = {}

    # Find all C files in crypto directories
    crypto_files = glob.glob("src/**/crypto/*.c", recursive=True)

    for file_path in crypto_files:
        print(f"Analyzing {file_path}...")

        result = await droid.execute(
            target=file_path,
            depth="light"  # Use light for batch analysis speed
        )

        output = json.loads(result["output"])
        findings = output["overall_findings"]

        results[file_path] = {
            "security_score": findings.get("security_score"),
            "crypto_libs": findings.get("crypto_libraries"),
            "readiness": findings.get("overall_readiness")
        }

        # Print summary
        status = "✅" if findings.get("overall_readiness") == "PRODUCTION_READY" else "⚠️"
        print(f"  {status} Security: {findings['security_score']:.2f}")

    # Print summary
    print("\n" + "="*60)
    print("BATCH ANALYSIS SUMMARY")
    print("="*60)

    total = len(results)
    ready = sum(1 for r in results.values() if r["readiness"] == "PRODUCTION_READY")

    print(f"Total files analyzed: {total}")
    print(f"Production-ready: {ready}/{total} ({ready*100//total}%)")

asyncio.run(analyze_all_crypto())
```

---

## Real-World Examples

### Example 1: Analyzing Nordic nRF DFU Implementation

```python
async def analyze_dfu():
    """Analyze secure DFU implementation."""
    droid = CryptolibImplementationDroid()

    result = await droid.execute(
        target="nrfx/bootloader/dfu/dfu_crypto.c",
        depth="deep",
        focus="fips_compliance"
    )

    output = json.loads(result["output"])

    # Extract key information
    print("DFU SECURITY ANALYSIS")
    print("=" * 60)

    # Turn 1: What crypto is used?
    turn1 = output["turn_1_crypto_patterns"]
    print(f"\n1. Detected Algorithms:")
    for algo_type, algos in turn1["algorithms_identified"].items():
        if algos:
            print(f"   {algo_type}: {', '.join(algos)}")

    # Turn 2: Is it FIPS compliant?
    turn2 = output["turn_2_compliance_assessment"]
    print(f"\n2. FIPS 140-3 Compliance:")
    print(f"   Level: {turn2['fips_140_3_level']}")
    print(f"   Score: {turn2['compliance_score']:.2f}")

    # Turn 3: Any vulnerabilities?
    turn3 = output["turn_3_security_analysis"]
    if turn3["vulnerabilities"]:
        print(f"\n3. Vulnerabilities Found:")
        for vuln in turn3["vulnerabilities"]:
            print(f"   [{vuln['severity']}] {vuln['id']}: {vuln['description']}")
    else:
        print(f"\n3. ✅ No vulnerabilities detected")

    # Turn 4: Memory ok for device?
    turn4 = output["turn_4_performance_metrics"]
    mem = turn4["memory_estimate"]
    print(f"\n4. Memory Footprint:")
    print(f"   Flash: {mem['flash_kb']} KB")
    print(f"   RAM: {mem['ram_kb']} KB")
    print(f"   Compatible with: {', '.join(turn4['nrf_device_compatibility'])}")

    # Turn 5: What are the fixes?
    turn5 = output["turn_5_recommendations"]
    if turn5["priority_fixes"]:
        print(f"\n5. Recommended Fixes (by priority):")
        for fix in turn5["priority_fixes"][:3]:  # Top 3
            print(f"   [{fix['priority']}] {fix['issue']}")
            print(f"       Effort: {fix['effort']}")

    # Overall readiness
    readiness = output["overall_findings"]["overall_readiness"]
    print(f"\n{'='*60}")
    print(f"OVERALL READINESS: {readiness}")

asyncio.run(analyze_dfu())
```

**Output Example:**
```
DFU SECURITY ANALYSIS
============================================================

1. Detected Algorithms:
   symmetric: AES-128
   asymmetric: ECDSA
   hash: SHA-256

2. FIPS 140-3 Compliance:
   Level: 2
   Score: 0.95

3. ✅ No vulnerabilities detected

4. Memory Footprint:
   Flash: 45 KB
   RAM: 12 KB
   Compatible with: nRF52840, nRF5340

5. Recommended Fixes (by priority):
   [high] Use PSA Crypto API instead of direct MbedTLS
       Effort: medium

============================================================
OVERALL READINESS: PRODUCTION_READY
```

### Example 2: Comparing Two Implementations

```python
async def compare_implementations():
    """Compare old vs new crypto implementation."""
    droid = CryptolibImplementationDroid()

    print("COMPARING IMPLEMENTATIONS")
    print("=" * 60)

    implementations = {
        "old": "src/crypto_v1/aes.c",
        "new": "src/crypto_v2/aes.c"
    }

    results = {}

    for name, path in implementations.items():
        result = await droid.execute(
            target=path,
            depth="medium"
        )

        output = json.loads(result["output"])
        findings = output["overall_findings"]

        results[name] = {
            "security_score": findings["security_score"],
            "memory_score": findings.get("memory_score", 0),
            "libs": findings["crypto_libraries"],
            "readiness": findings["overall_readiness"]
        }

    # Compare
    old = results["old"]
    new = results["new"]

    print(f"\nSecurity Score:")
    print(f"  Old: {old['security_score']:.2f}")
    print(f"  New: {new['security_score']:.2f}")
    print(f"  Improvement: {(new['security_score'] - old['security_score'])*100:.1f}%")

    print(f"\nMemory Efficiency:")
    print(f"  Old: {old['memory_score']:.2f}")
    print(f"  New: {new['memory_score']:.2f}")

    print(f"\nLibraries:")
    print(f"  Old: {', '.join(old['libs'])}")
    print(f"  New: {', '.join(new['libs'])}")

asyncio.run(compare_implementations())
```

---

## Understanding Output

### Output Structure

Every analysis returns a comprehensive JSON structure:

```json
{
  "format": "json",
  "droid": "CryptolibImplementationDroid",
  "version": "1.0.0",
  "target": "src/crypto/aes.c",
  "depth": "medium",
  "turns": 5,
  "output": {
    "summary": { ... },
    "turn_1_crypto_patterns": { ... },
    "turn_2_compliance_assessment": { ... },
    "turn_3_security_analysis": { ... },
    "turn_4_performance_metrics": { ... },
    "turn_5_recommendations": { ... },
    "overall_findings": { ... }
  }
}
```

### Key Metrics Explained

#### Security Score (0.0 - 1.0)
- **0.85+:** Excellent - Production ready
- **0.70-0.84:** Good - Minor issues
- **0.50-0.69:** Fair - Significant work needed
- **<0.50:** Poor - Not ready for production

#### Memory Score (0.0 - 1.0)
- **0.90+:** Excellent - Highly optimized
- **0.70-0.89:** Good - Acceptable for most devices
- **0.50-0.69:** Fair - Optimization possible
- **<0.50:** Poor - Memory footprint too large

#### Compliance Score (0.0 - 1.0)
- **0.95+:** Excellent - Fully compliant
- **0.85-0.94:** Good - Minor compliance gaps
- **0.70-0.84:** Fair - Notable compliance issues
- **<0.70:** Poor - Significant compliance concerns

### Interpreting Vulnerabilities

Each vulnerability in Turn 3 includes:

```json
{
  "id": "CWE-330",           // Weakness identifier
  "severity": "high",        // critical|high|medium|low
  "description": "...",      // What the issue is
  "location": "line_45"      // Where in code
}
```

**Severity Levels:**
- **CRITICAL:** Can be exploited immediately, causes complete failure
- **HIGH:** Serious security impact, likely exploitable
- **MEDIUM:** Moderate risk, requires specific conditions
- **LOW:** Minor issue, unlikely to be exploited

---

## Best Practices

### Practice 1: Always Run Medium Depth Analysis
```python
# ✅ GOOD: Balanced detail and speed
result = await droid.execute(target="file.c", depth="medium")

# ❌ BAD: Too fast, misses important issues
result = await droid.execute(target="file.c", depth="light")
```

### Practice 2: Use Focus Areas for Specific Concerns
```python
# ✅ GOOD: Targeted analysis
result = await droid.execute(
    target="key_manager.c",
    depth="deep",
    focus="key_management"
)

# ❌ BAD: Generic analysis misses subtleties
result = await droid.execute(target="key_manager.c", depth="medium")
```

### Practice 3: Act on Priority Fixes
```python
# ✅ GOOD: Fix high-priority issues first
output = json.loads(result["output"])
for fix in output["turn_5_recommendations"]["priority_fixes"]:
    if fix["priority"] == "critical":
        # Fix this issue immediately
        pass

# ❌ BAD: Ignore findings
# (just ignore the output)
```

### Practice 4: Validate PSA API Usage
```python
# ✅ GOOD: Use PSA Certified APIs
output["turn_1_crypto_patterns"]["crypto_libraries_detected"]
# Should include: "PSA Crypto API"

# ❌ BAD: Using older MbedTLS directly
# (less portable, no hardware acceleration)
```

### Practice 5: Check Device Compatibility
```python
# ✅ GOOD: Verify your device is compatible
compatible_devices = output["turn_4_performance_metrics"]["nrf_device_compatibility"]
if "nRF52840" in compatible_devices:
    print("✅ Compatible with your device")

# ❌ BAD: Assume code works on any device
# (may require specific hardware acceleration)
```

---

## Troubleshooting

### Issue 1: "Agent SDK not installed"
**Solution:**
```bash
pipx install k-lean[agent-sdk]
```

### Issue 2: Droid returns empty output
**Possible Causes:**
- File path doesn't exist
- File is not readable
- Claude API key not set

**Solution:**
```python
try:
    result = await droid.execute(target="file.c", depth="medium")
except Exception as e:
    print(f"Error: {e}")
```

### Issue 3: Analysis takes too long
**Solution:** Use `depth="light"` for initial screening
```python
# Fast: 5-10 seconds
result = await droid.execute(target="file.c", depth="light")
```

### Issue 4: JSON parsing error
**Solution:** Check if output is valid JSON
```python
try:
    output = json.loads(result["output"])
except json.JSONDecodeError:
    print("Output is not valid JSON")
    print(result["output"])
```

---

## Advanced System Prompt Customization

You can override the model and get custom system prompts:

```python
# Use different model if available
droid = CryptolibImplementationDroid(model="deepseek-v3-thinking")

# The system prompt automatically adapts:
system_prompt = droid._build_system_prompt(depth="deep", focus="psa_api")
print(system_prompt)
```

**Output:**
```
You are an expert cryptographer specializing in embedded systems and Nordic nRF SDK implementations.

Your expertise includes:
- PSA Certified Crypto APIs
- MbedTLS cryptography library
...

Analysis Depth: deep
Focus Area: psa_api

Provide detailed, security-focused analysis in JSON format...
```

---

## Summary

The **CryptolibImplementationDroid** provides:

✅ **Easy to use:** Simple API for complex crypto analysis
✅ **Comprehensive:** 5-turn analysis for thorough assessment
✅ **Nordic-focused:** Deep knowledge of nRF SDK
✅ **Standards-aligned:** FIPS 140-3 and PSA Certified
✅ **Production-ready:** Security-focused, optimized for embedded

**Get started:**
```python
from klean.agents import CryptolibImplementationDroid
import asyncio

droid = CryptolibImplementationDroid()
result = await droid.execute("src/crypto/aes.c", depth="medium")
```

---

**For more information, see:**
- `CRYPTOLIB_IMPLEMENTATION_DROID.md` - Full feature documentation
- `PHASE_6_CRYPTOLIB_SUMMARY.md` - Implementation details
- K-LEAN GitHub: https://github.com/calinfaja/K-LEAN-Companion

