"""Tests for klean.smol.reflection module.

Tests cover:
- CritiqueVerdict enum values
- Critique dataclass structure
- ReflectionEngine initialization
- Critique parsing from LLM response
- Execute with reflection loop
- Factory function
"""

from unittest.mock import MagicMock, patch

# =============================================================================
# CritiqueVerdict Tests
# =============================================================================


class TestCritiqueVerdict:
    """Tests for CritiqueVerdict enum."""

    def test_has_pass_value(self):
        """Should have PASS verdict."""
        from klean.smol.reflection import CritiqueVerdict

        assert CritiqueVerdict.PASS.value == "pass"

    def test_has_retry_value(self):
        """Should have RETRY verdict."""
        from klean.smol.reflection import CritiqueVerdict

        assert CritiqueVerdict.RETRY.value == "retry"

    def test_has_fail_value(self):
        """Should have FAIL verdict."""
        from klean.smol.reflection import CritiqueVerdict

        assert CritiqueVerdict.FAIL.value == "fail"


# =============================================================================
# Critique Dataclass Tests
# =============================================================================


class TestCritique:
    """Tests for Critique dataclass."""

    def test_creates_critique_with_all_fields(self):
        """Should create Critique with all required fields."""
        from klean.smol.reflection import Critique, CritiqueVerdict

        critique = Critique(
            verdict=CritiqueVerdict.PASS,
            feedback="Good work",
            issues=["issue1"],
            suggestions=["suggestion1"],
            confidence=0.9,
        )

        assert critique.verdict == CritiqueVerdict.PASS
        assert critique.feedback == "Good work"
        assert critique.issues == ["issue1"]
        assert critique.suggestions == ["suggestion1"]
        assert critique.confidence == 0.9


# =============================================================================
# ReflectionEngine Initialization Tests
# =============================================================================


class TestReflectionEngineInit:
    """Tests for ReflectionEngine.__init__()."""

    def test_sets_model_factory(self):
        """Should store the model factory."""
        from klean.smol.reflection import ReflectionEngine

        factory = MagicMock()
        with patch("klean.smol.reflection.get_model", return_value="test-model"):
            engine = ReflectionEngine(factory)

            assert engine.model_factory == factory

    def test_default_max_retries_is_2(self):
        """Should default to 2 max retries."""
        from klean.smol.reflection import ReflectionEngine

        factory = MagicMock()
        with patch("klean.smol.reflection.get_model", return_value="test-model"):
            engine = ReflectionEngine(factory)

            assert engine.max_retries == 2

    def test_accepts_custom_max_retries(self):
        """Should accept custom max_retries."""
        from klean.smol.reflection import ReflectionEngine

        factory = MagicMock()
        with patch("klean.smol.reflection.get_model", return_value="test-model"):
            engine = ReflectionEngine(factory, max_retries=5)

            assert engine.max_retries == 5

    def test_uses_first_available_model_when_none_specified(self):
        """Should use first available model from discovery."""
        from klean.smol.reflection import ReflectionEngine

        factory = MagicMock()
        with patch("klean.smol.reflection.get_model", return_value="discovered-model"):
            engine = ReflectionEngine(factory)

            assert engine.critic_model == "discovered-model"

    def test_uses_auto_when_no_models_available(self):
        """Should use 'auto' when no models found."""
        from klean.smol.reflection import ReflectionEngine

        factory = MagicMock()
        with patch("klean.smol.reflection.get_model", return_value=None):
            engine = ReflectionEngine(factory)

            assert engine.critic_model == "auto"


# =============================================================================
# Parse Critique Tests
# =============================================================================


class TestParseCritique:
    """Tests for ReflectionEngine._parse_critique()."""

    def test_parses_pass_verdict(self):
        """Should parse PASS verdict correctly."""
        from klean.smol.reflection import CritiqueVerdict, ReflectionEngine

        factory = MagicMock()
        with patch("klean.smol.reflection.get_model", return_value="test"):
            engine = ReflectionEngine(factory)

            response = """VERDICT: PASS
CONFIDENCE: 0.9
ISSUES:
SUGGESTIONS:
FEEDBACK: Looks good"""

            critique = engine._parse_critique(response)

            assert critique.verdict == CritiqueVerdict.PASS
            assert critique.confidence == 0.9

    def test_parses_retry_verdict(self):
        """Should parse RETRY verdict correctly."""
        from klean.smol.reflection import CritiqueVerdict, ReflectionEngine

        factory = MagicMock()
        with patch("klean.smol.reflection.get_model", return_value="test"):
            engine = ReflectionEngine(factory)

            response = """VERDICT: RETRY
CONFIDENCE: 0.7
ISSUES:
- Missing file references
- No specific line numbers
SUGGESTIONS:
- Add file:line citations
FEEDBACK: Needs more evidence"""

            critique = engine._parse_critique(response)

            assert critique.verdict == CritiqueVerdict.RETRY
            assert len(critique.issues) == 2
            assert "Missing file references" in critique.issues
            assert len(critique.suggestions) == 1
            assert critique.feedback == "Needs more evidence"

    def test_parses_fail_verdict(self):
        """Should parse FAIL verdict correctly."""
        from klean.smol.reflection import CritiqueVerdict, ReflectionEngine

        factory = MagicMock()
        with patch("klean.smol.reflection.get_model", return_value="test"):
            engine = ReflectionEngine(factory)

            response = """VERDICT: FAIL
CONFIDENCE: 0.3
ISSUES:
- Completely wrong
SUGGESTIONS:
FEEDBACK: Not worth retrying"""

            critique = engine._parse_critique(response)

            assert critique.verdict == CritiqueVerdict.FAIL

    def test_defaults_to_pass_on_unknown_verdict(self):
        """Should default to PASS for unknown verdicts."""
        from klean.smol.reflection import CritiqueVerdict, ReflectionEngine

        factory = MagicMock()
        with patch("klean.smol.reflection.get_model", return_value="test"):
            engine = ReflectionEngine(factory)

            response = """VERDICT: UNKNOWN
CONFIDENCE: 0.5"""

            critique = engine._parse_critique(response)

            assert critique.verdict == CritiqueVerdict.PASS


# =============================================================================
# Critique Method Tests
# =============================================================================


class TestCritiqueMethod:
    """Tests for ReflectionEngine.critique()."""

    def test_calls_model_with_formatted_prompt(self):
        """Should call model with task and output in prompt."""
        from klean.smol.reflection import ReflectionEngine

        mock_model = MagicMock()
        mock_model.return_value = "VERDICT: PASS\nCONFIDENCE: 0.9"

        factory = MagicMock(return_value=mock_model)
        with patch("klean.smol.reflection.get_model", return_value="test"):
            engine = ReflectionEngine(factory)

            engine.critique("Review auth module", "Found 3 issues...")

            factory.assert_called_with("test")
            # Check the prompt contains task and output
            call_args = mock_model.call_args[0][0]
            assert "Review auth module" in call_args
            assert "Found 3 issues" in call_args

    def test_returns_pass_on_model_error(self):
        """Should return PASS verdict on model error."""
        from klean.smol.reflection import CritiqueVerdict, ReflectionEngine

        factory = MagicMock(side_effect=Exception("Model error"))
        with patch("klean.smol.reflection.get_model", return_value="test"):
            engine = ReflectionEngine(factory)

            critique = engine.critique("task", "output")

            assert critique.verdict == CritiqueVerdict.PASS
            assert "Critique error" in critique.feedback


# =============================================================================
# Execute With Reflection Tests
# =============================================================================


class TestExecuteWithReflection:
    """Tests for ReflectionEngine.execute_with_reflection()."""

    def test_returns_result_on_pass(self):
        """Should return result immediately when critique passes."""
        from klean.smol.reflection import ReflectionEngine

        mock_model = MagicMock()
        mock_model.return_value = "VERDICT: PASS\nCONFIDENCE: 0.95"

        factory = MagicMock(return_value=mock_model)
        with patch("klean.smol.reflection.get_model", return_value="test"):
            engine = ReflectionEngine(factory)

            mock_executor = MagicMock()
            mock_executor.execute.return_value = {
                "success": True,
                "output": "Analysis complete",
            }

            result = engine.execute_with_reflection(mock_executor, "test-agent", "task")

            # Should only call execute once (no retry)
            assert mock_executor.execute.call_count == 1
            assert result["success"] is True
            assert result["attempts"] == 1
            assert result["reflected"] is False

    def test_retries_on_retry_verdict(self):
        """Should retry when critique returns RETRY."""
        from klean.smol.reflection import ReflectionEngine

        # First call returns RETRY, second returns PASS
        mock_model = MagicMock()
        mock_model.side_effect = [
            "VERDICT: RETRY\nFEEDBACK: Need more detail\nISSUES:\n- Missing evidence",
            "VERDICT: PASS\nCONFIDENCE: 0.9",
        ]

        factory = MagicMock(return_value=mock_model)
        with patch("klean.smol.reflection.get_model", return_value="test"):
            engine = ReflectionEngine(factory, max_retries=2)

            mock_executor = MagicMock()
            mock_executor.execute.return_value = {
                "success": True,
                "output": "Better analysis",
            }

            result = engine.execute_with_reflection(mock_executor, "test-agent", "task")

            # Should call execute twice (initial + 1 retry)
            assert mock_executor.execute.call_count == 2
            assert result["attempts"] == 2
            assert result["reflected"] is True

    def test_stops_on_executor_failure(self):
        """Should not retry when executor fails."""
        from klean.smol.reflection import ReflectionEngine

        mock_model = MagicMock()
        factory = MagicMock(return_value=mock_model)
        with patch("klean.smol.reflection.get_model", return_value="test"):
            engine = ReflectionEngine(factory)

            mock_executor = MagicMock()
            mock_executor.execute.return_value = {
                "success": False,
                "output": "Error occurred",
            }

            result = engine.execute_with_reflection(mock_executor, "test-agent", "task")

            # Should only call execute once
            assert mock_executor.execute.call_count == 1
            assert result["success"] is False

    def test_appends_feedback_on_fail_verdict(self):
        """Should append feedback to output on FAIL verdict."""
        from klean.smol.reflection import ReflectionEngine

        mock_model = MagicMock()
        mock_model.return_value = "VERDICT: FAIL\nFEEDBACK: Not salvageable"

        factory = MagicMock(return_value=mock_model)
        with patch("klean.smol.reflection.get_model", return_value="test"):
            engine = ReflectionEngine(factory)

            mock_executor = MagicMock()
            mock_executor.execute.return_value = {
                "success": True,
                "output": "Bad output",
            }

            result = engine.execute_with_reflection(mock_executor, "test-agent", "task")

            assert "[Reflection:" in result["output"]
            assert "Not salvageable" in result["output"]


# =============================================================================
# Factory Function Tests
# =============================================================================


class TestCreateReflectionEngine:
    """Tests for create_reflection_engine() factory."""

    def test_creates_engine_with_default_api_base(self):
        """Should create engine with default localhost:4000."""
        from klean.smol.reflection import create_reflection_engine

        with patch("klean.smol.reflection.get_model", return_value="test"):
            with patch("klean.smol.models.get_model", return_value="test"):
                with patch("smolagents.LiteLLMModel"):
                    engine = create_reflection_engine()

                    assert engine is not None
                    assert engine.max_retries == 2

    def test_creates_engine_with_custom_api_base(self):
        """Should accept custom api_base."""
        from klean.smol.reflection import create_reflection_engine

        with patch("klean.smol.reflection.get_model", return_value="test"):
            with patch("klean.smol.models.get_model", return_value="test"):
                with patch("smolagents.LiteLLMModel"):
                    engine = create_reflection_engine(api_base="http://custom:5000")

                    assert engine is not None
