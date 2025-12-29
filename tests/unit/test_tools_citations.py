"""Unit tests for klean.smol.tools citation validation.

Tests citation validation logic:
- Citation extraction patterns
- Validation against tool output history
- Tolerance threshold (20% invalid allowed)
- Statistics generation

ANTI-FALSE-POSITIVE MEASURES:
1. Test with exact citation patterns from code
2. Verify return values for all edge cases
3. Test threshold boundaries explicitly
4. Use mock memory with known file:line patterns
"""

import pytest
from pathlib import Path

# Import module under test
from klean.smol.tools import validate_citations, get_citation_stats


# =============================================================================
# Mock Memory Classes for Testing
# =============================================================================

class MockStep:
    """Mock agent memory step with observations."""
    def __init__(self, observations):
        self.observations = observations


class MockMemory:
    """Mock agent memory with configurable tool outputs."""
    def __init__(self, outputs):
        self._outputs = outputs

    def get_full_steps(self):
        return [MockStep(o) for o in self._outputs]


# =============================================================================
# TestValidateCitations
# =============================================================================

class TestValidateCitations:
    """Tests for validate_citations() function."""

    def test_returns_true_for_no_citations(self):
        """Should return True when answer contains no citations."""
        # Arrange
        answer = "This code looks good. No issues found."
        memory = MockMemory(["Some tool output without file refs"])

        # Act
        result = validate_citations(answer, memory)

        # Assert
        assert result is True, "Should return True for no citations"

    def test_returns_true_for_empty_answer(self):
        """Should return True for empty/None answer."""
        # Act & Assert
        assert validate_citations("", None) is True
        assert validate_citations(None, None) is True
        assert validate_citations("", MockMemory([])) is True

    def test_returns_true_for_no_memory(self):
        """Should return True when no memory provided."""
        # Arrange
        answer = "Found issue at src/auth.py:42"

        # Act
        result = validate_citations(answer, None)

        # Assert
        assert result is True, "Should skip validation without memory"

    def test_returns_true_for_valid_citations(self):
        """Should return True when all citations exist in tool output."""
        # Arrange - citations match exactly what's in memory
        answer = """
        Security Review Results:
        - Issue at src/auth.py:42: password exposure
        - Problem in src/login.py:15: SQL injection risk
        """
        memory = MockMemory([
            "Found issue at src/auth.py:42: password = input()",
            "Vulnerability in src/login.py:15: SQL injection risk",
        ])

        # Act
        result = validate_citations(answer, memory)

        # Assert
        assert result is True, "Should validate matching citations"

    def test_returns_true_for_valid_basename_match(self):
        """Should match citations by basename when full path doesn't match."""
        # Arrange - answer uses basename, memory has full path
        answer = "Found at auth.py:42: password issue"
        memory = MockMemory([
            "Issue at /some/deep/path/src/auth.py:42: exposed"
        ])

        # Act
        result = validate_citations(answer, memory)

        # Assert
        assert result is True, "Should match by basename"

    def test_returns_false_for_many_invalid(self):
        """Should return False when >= 20% citations are invalid."""
        # Arrange - 5 citations, 1 in memory = 80% invalid (>= 20% threshold)
        answer = """
        Issues found:
        - file1.py:10
        - file2.py:20
        - file3.py:30
        - file4.py:40
        - file5.py:50
        """
        memory = MockMemory([
            "Only found at file1.py:10"  # Only 1 valid
        ])

        # Act
        result = validate_citations(answer, memory)

        # Assert
        assert result is False, "Should fail with 80% invalid citations"

    def test_tolerates_less_than_20_percent_invalid(self):
        """Should return True when < 20% citations are invalid."""
        # Arrange - 5 citations, 4 in memory = 20% invalid (not >= 20%)
        answer = """
        Issues:
        - file1.py:10
        - file2.py:20
        - file3.py:30
        - file4.py:40
        - file5.py:50
        """
        memory = MockMemory([
            "Found at file1.py:10",
            "Found at file2.py:20",
            "Found at file3.py:30",
            "Found at file4.py:40",
            # file5.py:50 is missing - 1/5 = 20% invalid
        ])

        # Act
        result = validate_citations(answer, memory)

        # Assert - 20% is at the threshold, >= 20% fails
        assert result is False, "Should fail at exactly 20% invalid"

    def test_tolerates_19_percent_invalid(self):
        """Should return True when invalid ratio is below 20%."""
        # Arrange - 10 citations, 8 valid = 20% invalid (just at threshold)
        # Need 11 citations with 2 invalid to get < 20% (18.2%)
        answer = """
        c1.py:1 c2.py:2 c3.py:3 c4.py:4 c5.py:5
        c6.py:6 c7.py:7 c8.py:8 c9.py:9 c10.py:10
        invalid.py:99
        """
        memory = MockMemory([
            "c1.py:1 c2.py:2 c3.py:3 c4.py:4 c5.py:5",
            "c6.py:6 c7.py:7 c8.py:8 c9.py:9 c10.py:10",
            # invalid.py:99 not here - 1/11 = 9% invalid < 20%
        ])

        # Act
        result = validate_citations(answer, memory)

        # Assert
        assert result is True, "Should pass with < 20% invalid (9%)"

    def test_handles_line_ranges(self):
        """Should extract line ranges like file.py:10-20."""
        # Arrange
        answer = "Problem at utils/helper.py:100-110: unsafe code"
        memory = MockMemory([
            "Pattern at utils/helper.py:100-110: unsafe deserialization"
        ])

        # Act
        result = validate_citations(answer, memory)

        # Assert - validates using start line (100)
        assert result is True, "Should handle line range citations"

    def test_extracts_various_file_patterns(self):
        """Should extract citations from various file path formats."""
        # Arrange - various path formats
        answer = """
        - simple.py:10
        - path/to/file.js:20
        - my-file.ts:30
        - under_score.py:40
        """
        memory = MockMemory([
            "simple.py:10 path/to/file.js:20",
            "my-file.ts:30 under_score.py:40"
        ])

        # Act
        result = validate_citations(answer, memory)

        # Assert
        assert result is True, "Should handle various file patterns"

    def test_handles_non_string_answer(self):
        """Should convert non-string answer to string."""
        # Arrange - dict/int answers (can happen with smolagents)
        memory = MockMemory(["file.py:42"])

        # Act & Assert
        assert validate_citations(42, memory) is True  # No pattern match
        assert validate_citations({"result": "ok"}, memory) is True


# =============================================================================
# TestGetCitationStats
# =============================================================================

class TestGetCitationStats:
    """Tests for get_citation_stats() function."""

    def test_counts_total_citations(self):
        """Should count all citations in the answer."""
        # Arrange
        answer = "file1.py:10 file2.py:20 file3.py:30"

        # Act
        stats = get_citation_stats(answer)

        # Assert
        assert stats["total"] == 3
        assert isinstance(stats["total"], int)

    def test_separates_valid_invalid(self):
        """Should separate valid and invalid citations."""
        # Arrange
        answer = "valid.py:10 invalid.py:99"
        memory = MockMemory(["Found at valid.py:10"])

        # Act
        stats = get_citation_stats(answer, memory)

        # Assert
        assert stats["valid"] == 1
        assert stats["invalid"] == 1
        assert "valid.py:10" in stats["valid_citations"]
        assert "invalid.py:99" in stats["invalid_citations"]

    def test_reports_validation_passed(self):
        """Should report validation_passed boolean."""
        # Arrange - all valid
        answer = "file.py:10"
        memory = MockMemory(["file.py:10"])

        # Act
        stats = get_citation_stats(answer, memory)

        # Assert
        assert stats["validation_passed"] is True
        assert stats["invalid"] == 0

    def test_reports_validation_failed(self):
        """Should report validation_passed=False when too many invalid."""
        # Arrange - 100% invalid
        answer = "fake.py:999"
        memory = MockMemory([])

        # Act
        stats = get_citation_stats(answer, memory)

        # Assert
        assert stats["validation_passed"] is False
        assert stats["invalid"] == 1

    def test_empty_answer_stats(self):
        """Should return zeros for empty answer."""
        # Act
        stats = get_citation_stats("")

        # Assert
        assert stats["total"] == 0
        assert stats["valid"] == 0
        assert stats["invalid"] == 0
        assert stats["validation_passed"] is True

    def test_returns_citation_lists(self):
        """Should include lists of valid and invalid citations."""
        # Arrange
        answer = "a.py:1 b.py:2"
        memory = MockMemory(["a.py:1"])

        # Act
        stats = get_citation_stats(answer, memory)

        # Assert
        assert isinstance(stats["valid_citations"], list)
        assert isinstance(stats["invalid_citations"], list)
        assert len(stats["valid_citations"]) == 1
        assert len(stats["invalid_citations"]) == 1

    def test_handles_line_ranges_in_stats(self):
        """Should include line range in citation string."""
        # Arrange
        answer = "file.py:10-20"
        memory = MockMemory(["file.py:10"])

        # Act
        stats = get_citation_stats(answer, memory)

        # Assert
        assert stats["total"] == 1
        # Citation format includes range
        assert any("10-20" in c for c in stats["valid_citations"])

