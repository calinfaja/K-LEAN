"""Tests for klean.reviews module.

Tests cover:
- Content extraction from regular and thinking models
- Think tag stripping
- Quick review with health check
- Consensus review with parallel calls
- Second opinion with fallback
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Configure pytest-anyio for async tests
pytestmark = pytest.mark.anyio


# =============================================================================
# Content Extraction Tests
# =============================================================================


class TestExtractContent:
    """Tests for _extract_content() function."""

    def test_extracts_regular_content(self):
        """Should extract content from regular model response."""
        from klean.reviews import _extract_content

        response = {
            "choices": [
                {"message": {"content": "This is the review content."}}
            ]
        }

        result = _extract_content(response)
        assert result == "This is the review content."

    def test_extracts_reasoning_content(self):
        """Should extract reasoning_content from thinking models."""
        from klean.reviews import _extract_content

        response = {
            "choices": [
                {"message": {"reasoning_content": "Thinking model output."}}
            ]
        }

        result = _extract_content(response)
        assert result == "Thinking model output."

    def test_prefers_content_over_reasoning(self):
        """Should prefer content over reasoning_content when both present."""
        from klean.reviews import _extract_content

        response = {
            "choices": [
                {
                    "message": {
                        "content": "Regular content",
                        "reasoning_content": "Reasoning content",
                    }
                }
            ]
        }

        result = _extract_content(response)
        assert result == "Regular content"

    def test_returns_empty_for_missing_choices(self):
        """Should return empty string when no choices."""
        from klean.reviews import _extract_content

        result = _extract_content({})
        assert result == ""

        result = _extract_content({"choices": []})
        assert result == ""


class TestStripThinkTags:
    """Tests for _strip_think_tags() function."""

    def test_strips_single_think_tag(self):
        """Should strip single think tag."""
        from klean.reviews import _strip_think_tags

        content = "<think>Internal reasoning here</think>Actual output."

        result = _strip_think_tags(content)
        assert result == "Actual output."

    def test_strips_multiline_think_tag(self):
        """Should strip multiline think tags."""
        from klean.reviews import _strip_think_tags

        content = """<think>
This is
multiline
thinking
</think>
The actual review content."""

        result = _strip_think_tags(content)
        assert "think" not in result.lower()
        assert "actual review content" in result.lower()

    def test_strips_multiple_think_tags(self):
        """Should strip multiple think tags."""
        from klean.reviews import _strip_think_tags

        content = "<think>First</think>Middle<think>Second</think>End"

        result = _strip_think_tags(content)
        assert result == "MiddleEnd"

    def test_preserves_content_without_tags(self):
        """Should preserve content without think tags."""
        from klean.reviews import _strip_think_tags

        content = "No tags here, just content."

        result = _strip_think_tags(content)
        assert result == content


# =============================================================================
# Review Result Tests
# =============================================================================


class TestReviewResult:
    """Tests for ReviewResult dataclass."""

    def test_creates_successful_result(self):
        """Should create successful result."""
        from klean.reviews import ReviewResult

        result = ReviewResult(
            model="test-model",
            content="Review content",
            success=True,
            duration_ms=1000,
        )

        assert result.model == "test-model"
        assert result.content == "Review content"
        assert result.success is True
        assert result.error is None
        assert result.duration_ms == 1000

    def test_creates_failed_result(self):
        """Should create failed result with error."""
        from klean.reviews import ReviewResult

        result = ReviewResult(
            model="test-model",
            content="",
            success=False,
            error="Connection failed",
        )

        assert result.success is False
        assert result.error == "Connection failed"


class TestConsensusResult:
    """Tests for ConsensusResult dataclass."""

    def test_aggregates_results(self):
        """Should aggregate multiple review results."""
        from klean.reviews import ConsensusResult, ReviewResult

        results = [
            ReviewResult(model="model1", content="Review 1", success=True),
            ReviewResult(model="model2", content="Review 2", success=True),
            ReviewResult(model="model3", content="", success=False, error="Failed"),
        ]

        consensus = ConsensusResult(
            results=results,
            total_duration_ms=5000,
            successful_count=2,
            failed_count=1,
        )

        assert len(consensus.results) == 3
        assert consensus.successful_count == 2
        assert consensus.failed_count == 1


# =============================================================================
# Quick Review Tests
# =============================================================================


class TestQuickReview:
    """Tests for quick_review() function."""

    async def test_returns_result_on_success(self):
        """Should return successful result when model responds."""
        from klean.reviews import quick_review

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Grade: A\nVerdict: APPROVE"}}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("klean.reviews.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await quick_review(
                model="test-model",
                focus="Security review",
                context="def foo(): pass",
            )

            assert result.success is True
            assert "APPROVE" in result.content
            assert result.model == "test-model"

    async def test_handles_connection_error(self):
        """Should return failed result on connection error."""
        from klean.reviews import quick_review

        with patch("klean.reviews.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = Exception("Connection refused")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            # Also mock health check to fail
            with patch("klean.reviews._check_model_health", return_value=False):
                with patch("klean.reviews._get_healthy_models", return_value=[]):
                    result = await quick_review(
                        model="test-model",
                        focus="Review",
                        context="code",
                    )

                    assert result.success is False
                    assert result.error is not None


# =============================================================================
# Consensus Review Tests
# =============================================================================


class TestConsensusReview:
    """Tests for consensus_review() function."""

    async def test_calls_multiple_models(self):
        """Should call multiple models in parallel."""
        from klean.reviews import consensus_review

        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {
                "choices": [{"message": {"content": f"Review {call_count}"}}]
            }
            mock_resp.raise_for_status = MagicMock()
            return mock_resp

        with patch("klean.reviews.httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.get = AsyncMock(return_value=MagicMock(
                status_code=200,
                json=MagicMock(return_value={
                    "data": [
                        {"id": "model1"},
                        {"id": "model2"},
                        {"id": "model3"},
                    ]
                })
            ))
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            _result = await consensus_review(
                focus="Review",
                context="code",
                model_count=3,
            )

            # Should have attempted health checks + actual reviews
            assert call_count >= 3

    async def test_returns_empty_when_no_healthy_models(self):
        """Should return failed result when no healthy models."""
        from klean.reviews import consensus_review

        with patch("klean.reviews._get_healthy_models", return_value=[]):
            with patch("klean.reviews.httpx.AsyncClient") as mock_client_class:
                mock_client = AsyncMock()
                mock_client.__aenter__.return_value = mock_client
                mock_client.__aexit__.return_value = None
                mock_client_class.return_value = mock_client

                result = await consensus_review(
                    focus="Review",
                    context="code",
                )

                assert result.successful_count == 0
                assert result.failed_count >= 1


# =============================================================================
# Second Opinion Tests
# =============================================================================


class TestSecondOpinion:
    """Tests for second_opinion() function."""

    async def test_uses_primary_model_when_healthy(self):
        """Should use primary model when it's healthy."""
        from klean.reviews import second_opinion

        with patch("klean.reviews._check_model_health", return_value=True):
            with patch("klean.reviews.quick_review") as mock_quick:
                from klean.reviews import ReviewResult
                mock_quick.return_value = ReviewResult(
                    model="primary-model",
                    content="Review",
                    success=True,
                )

                result = await second_opinion(
                    focus="Review",
                    context="code",
                    primary_model="primary-model",
                )

                assert result.model == "primary-model"

    async def test_falls_back_when_primary_unhealthy(self):
        """Should fall back to other models when primary is unhealthy."""
        from klean.reviews import second_opinion

        health_results = {"primary": False, "fallback1": True}

        async def mock_health(client, model):
            return health_results.get(model, model == "fallback1")

        with patch("klean.reviews._check_model_health", side_effect=mock_health):
            with patch("klean.reviews.quick_review") as mock_quick:
                from klean.reviews import ReviewResult
                mock_quick.return_value = ReviewResult(
                    model="fallback1",
                    content="Review",
                    success=True,
                )

                result = await second_opinion(
                    focus="Review",
                    context="code",
                    primary_model="primary",
                    fallback_models=["fallback1"],
                )

                # Should succeed with fallback
                assert result.success is True


# =============================================================================
# Git Diff Tests
# =============================================================================


class TestGetGitDiff:
    """Tests for get_git_diff() function."""

    def test_returns_fallback_message_when_not_in_repo(self, tmp_path):
        """Should return fallback message when not in git repo."""
        from klean.reviews import get_git_diff

        result = get_git_diff(tmp_path)
        assert "No git changes found" in result

    def test_limits_output_lines(self, tmp_path):
        """Should limit output to max_lines."""
        from klean.reviews import get_git_diff

        # Create a mock git repo scenario
        with patch("klean.reviews.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="\n".join([f"line {i}" for i in range(500)]),
            )

            result = get_git_diff(tmp_path, max_lines=100)
            lines = result.split("\n")
            assert len(lines) <= 100


# =============================================================================
# Markdown Formatting Tests
# =============================================================================


class TestFormatReviewMarkdown:
    """Tests for format_review_markdown() function."""

    def test_formats_quick_review(self):
        """Should format quick review result as markdown."""
        from klean.reviews import ReviewResult, format_review_markdown

        result = ReviewResult(
            model="test-model",
            content="Grade: A\nVerdict: APPROVE",
            success=True,
            duration_ms=1500,
        )

        markdown = format_review_markdown(result, "Security review")

        assert "# Quick Review: Security review" in markdown
        assert "test-model" in markdown
        assert "Grade: A" in markdown
        assert "1500ms" in markdown

    def test_formats_consensus_review(self):
        """Should format consensus review result as markdown."""
        from klean.reviews import ConsensusResult, ReviewResult, format_review_markdown

        results = [
            ReviewResult(model="model1", content="Review 1", success=True),
            ReviewResult(model="model2", content="Review 2", success=True),
        ]

        consensus = ConsensusResult(
            results=results,
            total_duration_ms=5000,
            successful_count=2,
            failed_count=0,
        )

        markdown = format_review_markdown(consensus, "Code review")

        assert "# Consensus Review: Code review" in markdown
        assert "## model1" in markdown
        assert "## model2" in markdown
        assert "Review 1" in markdown
        assert "Review 2" in markdown


# =============================================================================
# Sync Wrapper Tests
# =============================================================================


class TestSyncWrappers:
    """Tests for synchronous wrapper functions."""

    def test_run_quick_review_wrapper_exists(self):
        """Should have sync wrapper for quick_review."""
        from klean.reviews import run_quick_review

        # Just verify the function exists and is callable
        assert callable(run_quick_review)

    def test_run_consensus_review_wrapper_exists(self):
        """Should have sync wrapper for consensus_review."""
        from klean.reviews import run_consensus_review

        assert callable(run_consensus_review)

    def test_run_second_opinion_wrapper_exists(self):
        """Should have sync wrapper for second_opinion."""
        from klean.reviews import run_second_opinion

        assert callable(run_second_opinion)
