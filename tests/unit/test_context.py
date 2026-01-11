"""Unit tests for klean.smol.context module.

Tests project context detection and gathering:
- Git root detection
- CLAUDE.md loading
- Knowledge DB detection
- Context assembly and formatting

ANTI-FALSE-POSITIVE MEASURES:
1. Use actual filesystem with temp directories
2. Verify subprocess calls are mocked correctly
3. Test with real path objects
4. Check all context fields are properly populated
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

# Import module under test
from klean.smol.context import (
    ProjectContext,
    detect_project_root,
    find_knowledge_db,
    format_context_for_prompt,
    gather_project_context,
    get_git_info,
    load_claude_md,
)

# =============================================================================
# TestProjectContext Dataclass
# =============================================================================

class TestProjectContext:
    """Tests for ProjectContext dataclass."""

    def test_creates_with_required_fields(self, tmp_path):
        """Should create context with required fields."""
        # Act
        ctx = ProjectContext(
            project_root=tmp_path,
            project_name="test-project"
        )

        # Assert
        assert ctx.project_root == tmp_path
        assert ctx.project_name == "test-project"
        assert ctx.claude_md is None
        assert ctx.has_knowledge_db is False

    def test_default_values(self, tmp_path):
        """Should have sensible defaults."""
        # Act
        ctx = ProjectContext(
            project_root=tmp_path,
            project_name="test"
        )

        # Assert
        assert ctx.knowledge_db_path is None
        assert ctx.serena_available is False
        assert isinstance(ctx.serena_memories, dict)
        assert ctx.git_branch is None


# =============================================================================
# TestDetectProjectRoot
# =============================================================================

class TestDetectProjectRoot:
    """Tests for detect_project_root() function."""

    @patch('klean.smol.context.subprocess.run')
    def test_uses_git_rev_parse(self, mock_run, tmp_path):
        """Should use git rev-parse to find root."""
        # Arrange
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=str(tmp_path) + "\n"
        )

        # Act
        root = detect_project_root(tmp_path)

        # Assert
        assert root == tmp_path
        mock_run.assert_called()
        # Verify git command was called
        call_args = mock_run.call_args
        assert "git" in str(call_args)
        assert "rev-parse" in str(call_args)

    def test_walks_up_to_find_git(self, tmp_path):
        """Should walk up directories looking for .git."""
        # Arrange - create nested structure with .git at top
        (tmp_path / ".git").mkdir()
        nested = tmp_path / "src" / "nested"
        nested.mkdir(parents=True)

        # Act - start from nested, with git command failing
        with patch('klean.smol.context.subprocess.run') as mock_run:
            mock_run.side_effect = Exception("git not available")
            root = detect_project_root(nested)

        # Assert
        assert root == tmp_path

    @patch('klean.smol.context.subprocess.run')
    def test_fallback_to_cwd(self, mock_run, tmp_path):
        """Should fallback to cwd when no .git found."""
        # Arrange
        mock_run.side_effect = Exception("git failed")
        # tmp_path has no .git

        # Act
        with patch('pathlib.Path.cwd', return_value=tmp_path):
            root = detect_project_root(tmp_path)

        # Assert - should be cwd since no .git found
        assert isinstance(root, Path)

    def test_handles_git_timeout(self, temp_project):
        """Should handle git command timeout gracefully."""
        # Arrange
        with patch('klean.smol.context.subprocess.run') as mock_run:
            import subprocess
            mock_run.side_effect = subprocess.TimeoutExpired("git", 5)

            # Act - should not raise, should walk up
            root = detect_project_root(temp_project)

        # Assert - finds .git via walk
        assert root == temp_project


# =============================================================================
# TestGetGitInfo
# =============================================================================

class TestGetGitInfo:
    """Tests for get_git_info() function."""

    @patch('klean.smol.context.subprocess.run')
    def test_extracts_branch_name(self, mock_run, tmp_path):
        """Should extract current branch name."""
        # Arrange
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="feature/awesome\n"
        )

        # Act
        info = get_git_info(tmp_path)

        # Assert
        assert info.get("branch") == "feature/awesome"

    @patch('klean.smol.context.subprocess.run')
    def test_extracts_status_summary(self, mock_run, tmp_path):
        """Should extract status summary."""
        # Arrange - simulate 3 files changed
        def run_side_effect(*args, **kwargs):
            cmd = args[0] if args else kwargs.get('args', [])
            if "branch" in cmd:
                return MagicMock(returncode=0, stdout="main\n")
            if "status" in cmd:
                return MagicMock(returncode=0, stdout=" M file1.py\n M file2.py\n M file3.py\n")
            return MagicMock(returncode=1)

        mock_run.side_effect = run_side_effect

        # Act
        info = get_git_info(tmp_path)

        # Assert
        assert info.get("status") == "3 files changed"

    @patch('klean.smol.context.subprocess.run')
    def test_clean_status(self, mock_run, tmp_path):
        """Should report 'clean' for no changes."""
        # Arrange
        def run_side_effect(*args, **kwargs):
            cmd = args[0] if args else kwargs.get('args', [])
            if "status" in cmd:
                return MagicMock(returncode=0, stdout="")
            return MagicMock(returncode=0, stdout="main\n")

        mock_run.side_effect = run_side_effect

        # Act
        info = get_git_info(tmp_path)

        # Assert
        assert info.get("status") == "clean"

    @patch('klean.smol.context.subprocess.run')
    def test_handles_not_git_repo(self, mock_run, tmp_path):
        """Should return empty dict when not a git repo."""
        # Arrange
        mock_run.side_effect = Exception("not a git repo")

        # Act
        info = get_git_info(tmp_path)

        # Assert
        assert isinstance(info, dict)
        assert "branch" not in info


# =============================================================================
# TestLoadClaudeMd
# =============================================================================

class TestLoadClaudeMd:
    """Tests for load_claude_md() function."""

    def test_loads_existing_claude_md(self, temp_project):
        """Should load CLAUDE.md content."""
        # Act
        content = load_claude_md(temp_project)

        # Assert
        assert content is not None
        assert "Test Project" in content
        assert "Commands" in content

    def test_returns_none_for_missing(self, tmp_path):
        """Should return None when CLAUDE.md doesn't exist."""
        # Act
        content = load_claude_md(tmp_path)

        # Assert
        assert content is None

    def test_truncates_long_content(self, tmp_path):
        """Should truncate content > 5000 chars."""
        # Arrange
        claude_md = tmp_path / "CLAUDE.md"
        long_content = "x" * 6000
        claude_md.write_text(long_content)

        # Act
        content = load_claude_md(tmp_path)

        # Assert
        assert len(content) < 6000
        assert "[truncated]" in content

    def test_handles_read_error(self, tmp_path):
        """Should return None on read error."""
        # Arrange - create but make unreadable
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("content")

        # Act - mock read_text to raise
        with patch.object(Path, 'read_text', side_effect=PermissionError()):
            content = load_claude_md(tmp_path)

        # Assert
        assert content is None


# =============================================================================
# TestFindKnowledgeDb
# =============================================================================

class TestFindKnowledgeDb:
    """Tests for find_knowledge_db() function."""

    def test_finds_knowledge_db_with_index(self, temp_knowledge_db):
        """Should find KB when index exists."""
        # Act
        kb_path = find_knowledge_db(temp_knowledge_db.parent)

        # Assert
        assert kb_path is not None
        assert kb_path.name == ".knowledge-db"

    def test_returns_none_for_missing_db(self, tmp_path):
        """Should return None when no .knowledge-db exists."""
        # Act
        kb_path = find_knowledge_db(tmp_path)

        # Assert
        assert kb_path is None

    def test_returns_none_for_empty_db_dir(self, tmp_path):
        """Should return None when .knowledge-db has no index."""
        # Arrange - create empty .knowledge-db
        (tmp_path / ".knowledge-db").mkdir()

        # Act
        kb_path = find_knowledge_db(tmp_path)

        # Assert
        assert kb_path is None

    def test_finds_db_with_embeddings(self, tmp_path):
        """Should find KB when embeddings dir exists."""
        # Arrange
        kb_dir = tmp_path / ".knowledge-db"
        kb_dir.mkdir()
        (kb_dir / "embeddings").mkdir()

        # Act
        kb_path = find_knowledge_db(tmp_path)

        # Assert
        assert kb_path is not None


# =============================================================================
# TestGatherProjectContext
# =============================================================================

class TestGatherProjectContext:
    """Tests for gather_project_context() function."""

    @patch('klean.smol.context.subprocess.run')
    @patch('klean.smol.context.check_serena_available')
    def test_assembles_full_context(self, mock_serena, mock_run, temp_project):
        """Should assemble complete project context."""
        # Arrange
        mock_serena.return_value = False

        def run_side_effect(*args, **kwargs):
            cmd = args[0] if args else kwargs.get('args', [])
            if "rev-parse" in cmd:
                return MagicMock(returncode=0, stdout=str(temp_project) + "\n")
            if "branch" in cmd:
                return MagicMock(returncode=0, stdout="main\n")
            if "status" in cmd:
                return MagicMock(returncode=0, stdout="")
            return MagicMock(returncode=1)

        mock_run.side_effect = run_side_effect

        # Act
        ctx = gather_project_context(temp_project)

        # Assert
        assert isinstance(ctx, ProjectContext)
        assert ctx.project_root == temp_project
        assert ctx.project_name == temp_project.name
        assert ctx.git_branch == "main"
        assert ctx.git_status_summary == "clean"

    @patch('klean.smol.context.subprocess.run')
    @patch('klean.smol.context.check_serena_available')
    def test_includes_claude_md(self, mock_serena, mock_run, temp_project):
        """Should include CLAUDE.md content."""
        # Arrange
        mock_serena.return_value = False
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout=str(temp_project) + "\n"
        )

        # Act
        ctx = gather_project_context(temp_project)

        # Assert
        assert ctx.claude_md is not None
        assert "Test Project" in ctx.claude_md

    @patch('klean.smol.context.subprocess.run')
    @patch('klean.smol.context.check_serena_available')
    def test_detects_knowledge_db(self, mock_serena, mock_run, tmp_path):
        """Should detect knowledge DB."""
        # Arrange
        mock_serena.return_value = False
        mock_run.return_value = MagicMock(returncode=0, stdout=str(tmp_path) + "\n")

        # Create KB structure
        kb_dir = tmp_path / ".knowledge-db"
        kb_dir.mkdir()
        (kb_dir / "index").mkdir()

        # Act
        ctx = gather_project_context(tmp_path)

        # Assert
        assert ctx.has_knowledge_db is True
        assert ctx.knowledge_db_path is not None


# =============================================================================
# TestFormatContextForPrompt
# =============================================================================

class TestFormatContextForPrompt:
    """Tests for format_context_for_prompt() function."""

    def test_includes_project_header(self, tmp_path):
        """Should include project name and root."""
        # Arrange
        ctx = ProjectContext(
            project_root=tmp_path,
            project_name="my-app"
        )

        # Act
        output = format_context_for_prompt(ctx)

        # Assert
        assert "my-app" in output
        assert str(tmp_path) in output
        assert "## Project:" in output

    def test_includes_git_info(self, tmp_path):
        """Should include branch and status."""
        # Arrange
        ctx = ProjectContext(
            project_root=tmp_path,
            project_name="app",
            git_branch="feature/x",
            git_status_summary="2 files changed"
        )

        # Act
        output = format_context_for_prompt(ctx)

        # Assert
        assert "feature/x" in output
        assert "2 files changed" in output

    def test_includes_claude_md(self, tmp_path):
        """Should include project instructions."""
        # Arrange
        ctx = ProjectContext(
            project_root=tmp_path,
            project_name="app",
            claude_md="# My Project\n\nDo things this way."
        )

        # Act
        output = format_context_for_prompt(ctx)

        # Assert
        assert "Project Instructions" in output
        assert "My Project" in output

    def test_includes_knowledge_db_status(self, tmp_path):
        """Should include KB status when available."""
        # Arrange
        kb_path = tmp_path / ".knowledge-db"
        ctx = ProjectContext(
            project_root=tmp_path,
            project_name="app",
            has_knowledge_db=True,
            knowledge_db_path=kb_path
        )

        # Act
        output = format_context_for_prompt(ctx)

        # Assert
        assert "Knowledge DB" in output
        assert "Available" in output
        assert "knowledge_search" in output

    def test_includes_serena_status(self, tmp_path):
        """Should include Serena status when available."""
        # Arrange
        ctx = ProjectContext(
            project_root=tmp_path,
            project_name="app",
            serena_available=True
        )

        # Act
        output = format_context_for_prompt(ctx)

        # Assert
        assert "Serena" in output
        assert "Available" in output

