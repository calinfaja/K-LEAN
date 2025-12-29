# Phoenix Telemetry Error Analysis: SmolKLN Agents

**Date:** 2024-12-24 (Historical Reference)
**Last Reviewed:** 2025-12-29
**Database:** ~/.phoenix/phoenix.db
**Analysis Period:** 2025-12-23 to 2025-12-24

> **Note:** This analysis documents historical errors during initial development. Many issues have been addressed through prompt improvements and model selection guidance. See QA_REPORT_2025-12-29.md for current status.

---

## Executive Summary

| Category | Count | Percentage | Severity |
|----------|-------|------------|----------|
| AgentParsingError | 198 | 80.5% | CRITICAL |
| Restricted Import Errors | 12 | 4.9% | CRITICAL |
| Code Syntax Errors | 10 | 4.1% | HIGH |
| Runtime Type Errors | 8 | 3.3% | MEDIUM |
| Other Errors | 18 | 7.2% | MEDIUM |
| **TOTAL** | **246** | **100%** | |

**Affected Models:**
1. openai/kimi-k2-thinking (123 error traces)
2. openai/glm-4.6-thinking (75 error traces)
3. openai/qwen3-coder (25 error traces)

---

## Category 1: Agent Parsing Errors (198 occurrences)

### Root Cause
Models are producing invalid JSON code blocks. The smolagents response structure expects valid JSON with `{"thought": "...", "code": "..."}` but models are returning empty, malformed, or truncated JSON.

### Error Patterns

#### Pattern 1: "Expecting value: line 1 column 1 (char 0)"
- **Count:** 134 occurrences
- **Date Range:** 2025-12-23 09:49:36 to 2025-12-24 16:22:11
- **Issue:** Empty JSON or leading whitespace prevents parsing
- **Example:** Model returns `""` or whitespace instead of JSON

#### Pattern 2: "Expecting value: line 2 column 1 (char 1)"
- **Count:** 60 occurrences
- **Date Range:** 2025-12-24 15:51:02 to 2025-12-24 16:27:42
- **Issue:** JSON first line valid, but second line empty/incomplete
- **Example:** `{"thought": "...",\n` (missing closing brace and code field)

#### Pattern 3: "regex pattern `<code>(.*?)</code>` not found"
- **Count:** 4 occurrences
- **Issue:** Response contains formatted text instead of JSON structure

### Proposed Solutions

| Solution | Effort | Impact | Description |
|----------|--------|--------|-------------|
| **1A: Improve Prompt Engineering** | LOW | 70-80% | Add explicit JSON examples, validation instructions |
| **1B: JSON Validation with Retry** | MEDIUM | 50-60% | Catch JSONDecodeError, retry with stricter prompt |
| **1C: Response Streaming Validation** | HIGH | 80%+ | Stream and validate JSON incrementally |

**Implementation File:** `src/klean/smol/models.py`

**Example Prompt Addition:**
```
CRITICAL: Always output valid JSON matching this structure:
{"thought": "your reasoning here", "code": "python_code_here"}
Validate JSON syntax before responding.
```

---

## Category 2: Restricted Import Errors (12 occurrences)

### Root Cause
The smolagents execution environment restricts certain imports for security. Agents attempt to use `os`, `subprocess`, `sys` without knowing the constraints.

### Detailed Breakdown

#### Error 2A: Import of 'os' is not allowed (6 occurrences)

| Timestamp | Trace ID |
|-----------|----------|
| 2025-12-24 17:06:17.555168 | dd290f249a515efb8b56cf4e1e83e51a |
| 2025-12-24 16:30:12.798370 | f837447fdb136dc920af76e8d50d285d |
| 2025-12-23 18:46:32.562111 | 04d092aaf35b08f8b8457e1492dc68a7 |
| 2025-12-23 18:27:02.577444 | 308aca6993db6c80e150cbd32e9d57f0 |
| 2025-12-23 18:01:47.076370 | 71a37c99c3bd5c73fa853db026e65f42 |
| 2025-12-23 15:16:08.762568 | (unknown) |

**Use Cases:** File operations (getcwd, getenv, path manipulation)

#### Error 2B: Import of 'subprocess' is not allowed (5 occurrences)

| Timestamp | Trace ID |
|-----------|----------|
| 2025-12-24 16:30:19.197039 | f837447fdb136dc920af76e8d50d285d |
| 2025-12-24 15:47:47.271851 | 8bae135ce5cebb2e3f254c514f344849 |
| 2025-12-24 15:44:47.520745 | 3a41ddb8741002ad602732c5e7c11914 |
| 2025-12-23 18:23:00.131405 | 0bb4b52f498dc4ab9fbac2aa5761dab3 |
| 2025-12-23 15:16:07.151129 | (unknown) |

**Use Case:** External command execution

#### Error 2C: Import of 'json' is not allowed (1 occurrence)

| Timestamp | Trace ID |
|-----------|----------|
| 2025-12-23 18:06:23.382107 | 196a1ef294fccb1f5f5309c3a6f14d8f |

**Note:** json appears inconsistently - sometimes allowed, sometimes blocked. This needs standardization.

### Import Restriction Reference

**ALWAYS ALLOWED:**
- decimal, math, typing, queue, re, statistics, copy
- enum, random, stat, unicodedata, itertools, textwrap
- string, functools, datetime, operator, time
- dataclasses, collections

**SOMETIMES ALLOWED:**
- json (inconsistent - needs fix)

**NEVER ALLOWED:**
- os, subprocess, sys

### Proposed Solutions

| Solution | Effort | Impact | Description |
|----------|--------|--------|-------------|
| **2A: Document Constraints in Prompt** | LOW | 90% | Add IMPORT RESTRICTIONS section to system prompt |
| **2B: Create Safe Wrapper Functions** | MEDIUM | 100% | Provide safe_getcwd(), safe_getenv(), execute_command() |
| **2C: Standardize Interpreter Config** | HIGH | 100% | Define canonical AUTHORIZED_IMPORTS list |

**Example Prompt Addition:**
```
IMPORT RESTRICTIONS:
The following imports are NOT available:
  - os (use pathlib or provided file utilities)
  - subprocess (use the execute_command tool)
  - sys (use provided system utilities)

Available modules: math, json, datetime, re, pathlib, collections, itertools

Use these tools instead:
  - read_file(path) - read file contents
  - execute_command(cmd) - run shell commands
  - list_directory(path) - list directory contents
```

---

## Category 3: Code Syntax Errors (10 occurrences)

### Root Cause
Models generate syntactically invalid Python code that fails the parser before execution.

### Detailed Breakdown

#### Error 3A: Unterminated String Literals (4 occurrences)

| Timestamp | Step | Line | Issue |
|-----------|------|------|-------|
| 2025-12-23 18:27:57.764417 | 2 | 2 | Missing closing quote |
| 2025-12-23 18:05:45.099852 | 2 | 3 | Missing closing quote |
| 2025-12-23 18:02:21.326700 | 4 | 1 | Missing closing quote |
| 2025-12-23 18:02:11.320586 | 2 | 1 | Missing closing quote |

**Example:** `task="Please analyze ...` (no closing quote)

#### Error 3B: Unterminated Triple-Quoted String (1 occurrence)

| Timestamp | Step | Line |
|-----------|------|------|
| 2025-12-23 18:03:05.303105 | 3 | 106 |

**Issue:** `"""..."""` block not properly closed

#### Error 3C: Unclosed Bracket/Parenthesis (1 occurrence)

| Timestamp | Step | Line |
|-----------|------|------|
| 2025-12-23 20:35:47.342841 | 8 | 65 |

**Example:** `error_patterns = ['if.*psa_', ...]` missing closing `]`

#### Error 3D: Indentation Error (1 occurrence)

| Timestamp | Step | Line |
|-----------|------|------|
| 2025-12-23 19:09:26.376939 | 2 | 140 |

**Issue:** Missing indented block after `for` statement

#### Error 3E: Invalid Character - Emoji (1 occurrence)

| Timestamp | Step | Line |
|-----------|------|------|
| 2025-12-23 09:50:59.888893 | 5 | 7 |

**Issue:** Emoji character (0x1F534 - red circle) in code

#### Error 3F: Forbidden Function Call (1 occurrence)

| Timestamp | Step |
|-----------|------|
| 2025-12-23 21:16:36.538085 | 3 |

**Issue:** Attempt to use `open()` function (blocked for security)

### Proposed Solutions

| Solution | Effort | Impact | Description |
|----------|--------|--------|-------------|
| **3A: Code Validation Before Execution** | MEDIUM | 80% | Use ast.parse() before running code |
| **3B: Enhanced Agent Prompt** | MEDIUM | 70% | Add validation checklist to prompt |
| **3C: Automatic Error Recovery** | HIGH | 90% | Auto-fix common syntax errors |

**Implementation Pattern:**
```python
import ast
try:
    ast.parse(code)  # Validates syntax
except SyntaxError as e:
    return {"error": f"Syntax error at line {e.lineno}: {e.msg}"}

# Only execute if syntax is valid
exec(code)
```

---

## Category 4: Other Execution Errors (8 occurrences)

### Detailed Breakdown

#### Error 4A: TypeError - Unexpected Keyword Argument (1 occurrence)

| Timestamp | Error |
|-----------|-------|
| 2025-12-23 21:14:46.311920 | `project_read_file() got unexpected keyword argument 'max_levels'` |

#### Error 4B: TypeError - Set Object Not Subscriptable (2 occurrences)

| Timestamp |
|-----------|
| 2025-12-23 18:53:06.963472 |
| 2025-12-23 18:55:32.544931 |

**Issue:** Attempting to index a set with `[]` instead of dict/list

#### Error 4C: Regex Error - Unterminated Subpattern (1 occurrence)

| Timestamp | Error |
|-----------|-------|
| 2025-12-23 20:33:10.283665 | `error: missing ), unterminated subpattern at position 6` |

#### Error 4D: Unpacking Non-Tuple Error (1 occurrence)

| Timestamp |
|-----------|
| 2025-12-23 10:26:52.491690 |

#### Error 4E: Wrong Number of Arguments (1 occurrence)

| Timestamp | Error |
|-----------|-------|
| 2025-12-23 21:12:46.233572 | `MultiStepAgent.__call__() takes 2 positional arguments but 3 were given` |

### Proposed Solutions

| Solution | Effort | Impact | Description |
|----------|--------|--------|-------------|
| **4A: Document Function Signatures** | LOW | 70% | Include exact signatures in prompt |
| **4B: Runtime Type Checking** | MEDIUM | 60% | Validate arguments before execution |

---

## Implementation Roadmap

### Phase 1: Immediate (2-4 hours, 75% error reduction)

1. **Update SmolKLN agent prompts:**
   - Add explicit JSON format examples
   - List import restrictions upfront
   - Include function signatures for available tools
   - Add code validation checklist

2. **Standardize interpreter configuration:**
   - Define consistent AUTHORIZED_IMPORTS list
   - Apply to all SmolKLN agent instances
   - Resolve json module inconsistency

**Files to modify:** `src/klean/smol/models.py`

### Phase 2: Short-Term (1-2 weeks, 90% error reduction)

1. **Implement JSON validation with retry:**
   - Add try/except for JSON parsing
   - Detect common error patterns (empty JSON, truncation)
   - Auto-retry with improved prompt

2. **Add code syntax validation:**
   - Use ast.parse() before execution
   - Return helpful error messages

3. **Create safe wrapper functions:**
   - Implement file operation alternatives
   - Wrap subprocess/system calls

**Files to modify:** `src/klean/smol/`, `src/klean/smol/tools.py`

### Phase 3: Long-Term (2-4 weeks, 95%+ error reduction)

1. Implement response streaming & validation
2. Add code self-validation to agent logic
3. Create comprehensive function documentation
4. Implement automatic error recovery mechanisms

---

## Key Observations

### Error Spike Analysis
- **Peak errors:** 2025-12-24 16:22-16:27 (60 parsing errors in 5 minutes)
- **Possible cause:** Recent model API change or configuration update
- **Recommendation:** Investigate model behavior changes in this time window

### Model Performance Comparison
| Model | Error Traces | Relative Performance |
|-------|--------------|---------------------|
| qwen3-coder | 25 | Best (lowest errors) |
| glm-4.6-thinking | 75 | Fair |
| kimi-k2-thinking | 123 | Poor (highest errors) |

**Recommendation:** Prioritize qwen3-coder for SmolKLN tasks, avoid glm-4.6-thinking and kimi-k2-thinking for critical operations.

### JSON Module Inconsistency
- json appears inconsistently in AUTHORIZED_IMPORTS
- Sometimes allowed, sometimes blocked
- **Action Required:** Standardize - explicitly allow json in all configurations

---

## Appendix: Files Needing Modification

| File | Changes Needed |
|------|----------------|
| `src/klean/smol/models.py` | Update prompts, add constraints, function signatures |
| `src/klean/smol/` | Add JSON validation, retry logic, syntax checking |
| `src/klean/smol/tools.py` | Create safe wrapper functions, document signatures |
| Configuration files | Define AUTHORIZED_IMPORTS, document restrictions |

---

*This report documents errors only. No fixes have been implemented.*
