# K-LEAN Test Implementation Plan

## Executive Summary

This document outlines a comprehensive test implementation plan for the K-LEAN project.
Based on analysis of existing test coverage and project modules.

**Current State:**
- 4 test files exist (28 tests total)
- Core LLMClient functionality covered
- Many critical modules have zero test coverage

**Target State:**
- 12+ test files (~100+ tests)
- Full coverage of core functionality
- Unit + Integration test separation

---

## Existing Test Coverage (DO NOT DUPLICATE)

### Already Tested:

| File | Tests | What's Covered |
|------|-------|----------------|
| `test_llm_client.py` | 12 | LLMClient: discover_models, _proxy_model, completion, reasoning_content, enable_telemetry |
| `test_async_completion.py` | 4 | LLMClient.acompletion, parallel async calls |
| `test_cli_integration.py` | 12 | CLI commands (quick, multi, rethink), httpx removal verification |
| `test_doctor_hooks.py` | 10 | merge_klean_hooks, KLEAN_HOOKS_CONFIG structure |

**Total: 38 tests**

---

## New Tests to Implement

### Priority 1: Core Discovery & Models (HIGH VALUE)

#### 1.1 `tests/unit/test_discovery.py`
**Module:** `src/klean/discovery.py` (93 lines)
**Current Coverage:** 0%

```python
# Functions to test:
- list_models() - Model discovery from LiteLLM
- list_models(force_refresh=True) - Cache bypass
- get_model() - Default model selection
- get_model(override="x") - Override handling
- clear_cache() - Cache clearing
- is_available() - Proxy health check

# Test Cases (8 tests):
class TestListModels:
    test_returns_model_list_from_proxy()
    test_uses_cache_when_fresh()
    test_refreshes_cache_when_stale()
    test_force_refresh_bypasses_cache()
    test_returns_stale_cache_on_error()
    test_handles_empty_response()

class TestGetModel:
    test_returns_first_available()
    test_override_bypasses_discovery()

class TestIsAvailable:
    test_returns_true_when_proxy_healthy()
    test_returns_false_on_connection_error()
```

**Note:** Uses httpx, not litellm. Consider migrating like klean_core.py.

---

#### 1.2 `tests/unit/test_loader.py`
**Module:** `src/klean/smol/loader.py` (104 lines)
**Current Coverage:** 0%

```python
# Functions to test:
- parse_agent_file() - YAML frontmatter parsing
- list_available_agents() - Agent discovery
- load_agent() - Agent loading

# Test Cases (8 tests):
class TestParseAgentFile:
    test_parses_yaml_frontmatter()
    test_extracts_name_description_model()
    test_parses_tools_list()
    test_handles_no_frontmatter()
    test_resolves_inherit_model()
    test_system_prompt_extraction()

class TestListAvailableAgents:
    test_lists_md_files()
    test_returns_empty_for_missing_dir()

class TestLoadAgent:
    test_loads_existing_agent()
    test_raises_for_missing_agent()
```

---

### Priority 2: SmolKLN Tools (HIGH VALUE)

#### 2.1 `tests/unit/test_tools_citations.py`
**Module:** `src/klean/smol/tools.py` (citation functions)
**Current Coverage:** 0%

```python
# Functions to test:
- validate_citations() - Citation validation
- get_citation_stats() - Statistics generation

# Test Cases (10 tests):
class TestValidateCitations:
    test_returns_true_for_no_citations()
    test_returns_true_for_valid_citations()
    test_returns_false_for_many_invalid()
    test_tolerates_20_percent_invalid()
    test_extracts_file_line_patterns()
    test_handles_line_ranges()
    test_matches_basename_fallback()

class TestGetCitationStats:
    test_counts_total_citations()
    test_separates_valid_invalid()
    test_reports_validation_passed()
```

---

#### 2.2 `tests/unit/test_tools_file_ops.py`
**Module:** `src/klean/smol/tools.py` (@tool functions)
**Current Coverage:** 0%

```python
# Functions to test:
- read_file() - File reading with pagination
- search_files() - Glob pattern matching
- grep() - Text pattern search
- git_diff/status/log() - Git operations
- list_directory() - Directory listing
- get_file_info() - File metadata

# Test Cases (12 tests):
class TestReadFile:
    test_reads_existing_file()
    test_handles_missing_file()
    test_pagination_start_line()
    test_pagination_max_lines()
    test_adds_line_numbers()

class TestSearchFiles:
    test_glob_pattern_matching()
    test_recursive_search()
    test_handles_missing_path()

class TestGrep:
    test_regex_pattern_search()
    test_literal_pattern_fallback()
    test_limits_results_to_50()
```

---

### Priority 3: Context & Memory (MEDIUM VALUE)

#### 3.1 `tests/unit/test_context.py`
**Module:** `src/klean/smol/context.py` (253 lines)
**Current Coverage:** 0%

```python
# Functions to test:
- detect_project_root() - Git root detection
- get_git_info() - Branch/status extraction
- load_claude_md() - CLAUDE.md loading
- find_knowledge_db() - KB path detection
- gather_project_context() - Full context assembly
- format_context_for_prompt() - Prompt formatting

# Test Cases (10 tests):
class TestDetectProjectRoot:
    test_finds_git_root()
    test_fallback_to_cwd()
    test_walks_up_directories()

class TestGetGitInfo:
    test_extracts_branch_name()
    test_extracts_status_summary()
    test_handles_not_git_repo()

class TestGatherProjectContext:
    test_assembles_full_context()
    test_includes_claude_md()
    test_detects_knowledge_db()
```

---

#### 3.2 `tests/unit/test_memory.py`
**Module:** `src/klean/smol/memory.py` (347 lines)
**Current Coverage:** 0%

```python
# Classes/functions to test:
- MemoryEntry - Serialization
- SessionMemory - Add/trim/get_context
- AgentMemory - Integration with Knowledge DB

# Test Cases (12 tests):
class TestMemoryEntry:
    test_to_dict_serialization()
    test_from_dict_deserialization()

class TestSessionMemory:
    test_add_entry()
    test_trims_to_max_entries()
    test_get_context_token_limit()
    test_get_history()
    test_serialization_roundtrip()

class TestAgentMemory:
    test_start_session()
    test_record_to_session()
    test_query_knowledge_fallback()
    test_get_augmented_context()
    test_persist_session_to_kb()
```

---

### Priority 4: CLI & Integration (MEDIUM VALUE)

#### 4.1 `tests/integration/test_executor.py`
**Module:** `src/klean/smol/executor.py`
**Current Coverage:** 0%

```python
# Class to test:
- SmolKLNExecutor - Agent execution

# Test Cases (6 tests):
class TestSmolKLNExecutor:
    test_initialization_with_project_path()
    test_output_directory_creation()
    test_format_result_extracts_content()
    test_save_result_creates_file()
    test_list_agents()
    test_get_agent_info()
```

---

#### 4.2 `tests/integration/test_knowledge_db.py`
**Module:** `src/klean/data/scripts/knowledge_db.py`
**Current Coverage:** 0%

```python
# Test semantic search and capture

# Test Cases (8 tests):
class TestKnowledgeDB:
    test_initialization()
    test_add_document()
    test_semantic_search()
    test_hybrid_search()
    test_search_with_filters()
    test_handles_empty_db()
    test_index_persistence()
    test_project_isolation()
```

---

### Priority 5: Model Discovery Utils (LOW-MEDIUM)

#### 5.1 `tests/unit/test_model_discovery_utils.py`
**Module:** `src/klean/utils/model_discovery.py` (110 lines)
**Current Coverage:** 0%

```python
# Functions to test:
- get_available_models() - LiteLLM proxy discovery
- get_model_metadata() - Config merging
- get_model_for_task() - Task-based selection
- is_litellm_available() - Health check
- get_model_info() - Info summary

# Test Cases (8 tests):
class TestGetModelForTask:
    test_security_selects_qwen3()
    test_architecture_selects_deepseek()
    test_fallback_to_first_available()
    test_handles_empty_models()

class TestGetModelMetadata:
    test_loads_from_yaml_config()
    test_merges_with_defaults()
    test_handles_missing_config()
```

---

## Test Infrastructure

### Directory Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── unit/
│   ├── __init__.py
│   ├── test_discovery.py
│   ├── test_loader.py
│   ├── test_tools_citations.py
│   ├── test_tools_file_ops.py
│   ├── test_context.py
│   ├── test_memory.py
│   └── test_model_discovery_utils.py
├── integration/
│   ├── __init__.py
│   ├── test_executor.py
│   ├── test_knowledge_db.py
│   └── test_cli_commands.py   # Existing: test_cli_integration.py
└── fixtures/
    ├── sample_agents/
    │   └── test-agent.md
    ├── sample_projects/
    │   └── CLAUDE.md
    └── mock_responses.py
```

### Shared Fixtures (conftest.py)

```python
import pytest
from pathlib import Path
import tempfile
import json

@pytest.fixture
def temp_project():
    """Create temporary project directory with .git."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir)
        (project / ".git").mkdir()
        (project / "CLAUDE.md").write_text("# Test Project")
        yield project

@pytest.fixture
def mock_litellm_response():
    """Mock LiteLLM /models response."""
    return {
        "data": [
            {"id": "qwen3-coder"},
            {"id": "deepseek-r1"},
            {"id": "kimi-k2"}
        ]
    }

@pytest.fixture
def sample_agent_md():
    """Sample agent .md file content."""
    return '''---
name: test-auditor
description: Test security auditor
model: inherit
tools: ["read_file", "grep"]
---

# System Prompt
You are a test auditor.
'''

@pytest.fixture
def mock_agent_memory():
    """Mock smolagents memory with tool outputs."""
    class MockStep:
        def __init__(self, output):
            self.observations = output

    class MockMemory:
        def get_full_steps(self):
            return [
                MockStep("Found at src/auth.py:42: password = input()"),
                MockStep("Found at src/login.py:15-20: hardcoded secret")
            ]

    return MockMemory()
```

---

## Implementation Order

### Phase 1: Core Unit Tests (Week 1)
1. `test_discovery.py` - Model discovery (critical path)
2. `test_loader.py` - Agent loading
3. `test_tools_citations.py` - Citation validation

### Phase 2: SmolKLN Tests (Week 2)
4. `test_tools_file_ops.py` - File operations
5. `test_context.py` - Project context
6. `test_memory.py` - Session memory

### Phase 3: Integration Tests (Week 3)
7. `test_executor.py` - Agent execution
8. `test_knowledge_db.py` - Knowledge DB
9. `test_model_discovery_utils.py` - Model selection

---

## Test Coverage Metrics

| Priority | Module | Tests | Est. Coverage |
|----------|--------|-------|---------------|
| P1 | discovery.py | 10 | 90% |
| P1 | loader.py | 10 | 95% |
| P1 | tools.py (citations) | 10 | 85% |
| P2 | tools.py (file ops) | 12 | 70% |
| P2 | context.py | 10 | 80% |
| P2 | memory.py | 12 | 85% |
| P3 | executor.py | 6 | 60% |
| P3 | knowledge_db.py | 8 | 70% |
| P3 | model_discovery.py | 8 | 80% |

**Total New Tests: ~86**
**Total After Implementation: ~124 tests**

---

## Running Tests

```bash
# All tests
pytest tests/ -v

# Unit tests only (fast)
pytest tests/unit/ -v

# Integration tests (requires LiteLLM)
pytest tests/integration/ -v

# Specific module
pytest tests/unit/test_discovery.py -v

# With coverage
pytest tests/ --cov=klean --cov-report=html
```

---

## Notes

1. **httpx vs litellm**: `discovery.py` still uses httpx. Consider migrating to urllib+litellm like klean_core.py for consistency.

2. **Mocking Strategy**: Use `unittest.mock.patch` for external calls (LiteLLM, git, file system).

3. **Fixtures**: Create reusable fixtures in `conftest.py` for common test data.

4. **CI Integration**: Tests should pass without running services (mock external deps).
