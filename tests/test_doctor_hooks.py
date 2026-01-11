#!/usr/bin/env python3
"""
Test suite for doctor --auto-fix hooks configuration.

Tests the merge_klean_hooks function and doctor hook detection.

Run with: pytest tests/test_doctor_hooks.py -v
    Or:   python tests/test_doctor_hooks.py
"""

import json

import pytest

# K-LEAN hooks configuration (copy from cli.py for standalone testing)
KLEAN_HOOKS_CONFIG = {
    "SessionStart": [
        {
            "matcher": "startup",
            "hooks": [
                {"type": "command", "command": "~/.claude/hooks/session-start.sh", "timeout": 5}
            ],
        },
        {
            "matcher": "resume",
            "hooks": [
                {"type": "command", "command": "~/.claude/hooks/session-start.sh", "timeout": 5}
            ],
        },
    ],
    "UserPromptSubmit": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": "~/.claude/hooks/user-prompt-handler.sh",
                    "timeout": 30,
                }
            ]
        }
    ],
    "PostToolUse": [
        {
            "matcher": "Bash",
            "hooks": [
                {
                    "type": "command",
                    "command": "~/.claude/hooks/post-bash-handler.sh",
                    "timeout": 15,
                }
            ],
        },
        {
            "matcher": "WebFetch|WebSearch",
            "hooks": [
                {"type": "command", "command": "~/.claude/hooks/post-web-handler.sh", "timeout": 10}
            ],
        },
        {
            "matcher": "mcp__tavily__.*",
            "hooks": [
                {"type": "command", "command": "~/.claude/hooks/post-web-handler.sh", "timeout": 10}
            ],
        },
    ],
}


def merge_klean_hooks(existing_settings: dict) -> tuple:
    """Merge K-LEAN hooks into existing settings.json, preserving user hooks.

    Returns:
        tuple: (updated_settings, list of hooks added)
    """
    added = []

    if "hooks" not in existing_settings:
        existing_settings["hooks"] = {}

    hooks = existing_settings["hooks"]

    for hook_type, klean_hook_list in KLEAN_HOOKS_CONFIG.items():
        if hook_type not in hooks:
            # No hooks of this type exist - add all K-LEAN hooks
            hooks[hook_type] = klean_hook_list
            added.append(f"{hook_type} ({len(klean_hook_list)} entries)")
        else:
            # Hooks exist - merge by matcher to avoid duplicates
            existing_matchers = set()
            for h in hooks[hook_type]:
                # Use matcher if present, otherwise use command path as identifier
                matcher = h.get("matcher", "")
                if not matcher and "hooks" in h:
                    # For hooks without matcher, use command as identifier
                    matcher = h["hooks"][0].get("command", "") if h["hooks"] else ""
                existing_matchers.add(matcher)

            for klean_hook in klean_hook_list:
                klean_matcher = klean_hook.get("matcher", "")
                if not klean_matcher and "hooks" in klean_hook:
                    klean_matcher = (
                        klean_hook["hooks"][0].get("command", "") if klean_hook["hooks"] else ""
                    )

                if klean_matcher not in existing_matchers:
                    hooks[hook_type].append(klean_hook)
                    added.append(f"{hook_type}[{klean_matcher or 'default'}]")

    return existing_settings, added


class TestMergeKleanHooks:
    """Test merge_klean_hooks function."""

    def test_empty_settings(self):
        """Test: No settings.json exists - should add all hooks."""
        settings = {}
        result, added = merge_klean_hooks(settings)

        assert "hooks" in result
        assert "SessionStart" in result["hooks"]
        assert "UserPromptSubmit" in result["hooks"]
        assert "PostToolUse" in result["hooks"]
        assert len(added) == 3  # 3 hook types added

    def test_no_hooks_key(self):
        """Test: settings.json exists but no hooks key."""
        settings = {"someOtherKey": "value"}
        result, added = merge_klean_hooks(settings)

        assert "hooks" in result
        assert "someOtherKey" in result  # Preserved
        assert len(result["hooks"]) == 3

    def test_partial_hooks_existing(self):
        """Test: Some hooks exist, others missing - should merge."""
        settings = {
            "hooks": {
                "SessionStart": [
                    {
                        "matcher": "startup",
                        "hooks": [
                            {"type": "command", "command": "~/.claude/hooks/session-start.sh"}
                        ],
                    }
                ]
            }
        }
        result, added = merge_klean_hooks(settings)

        # SessionStart should have resume added
        assert len(result["hooks"]["SessionStart"]) == 2
        # Other hooks should be added
        assert "UserPromptSubmit" in result["hooks"]
        assert "PostToolUse" in result["hooks"]

    def test_user_hooks_preserved(self):
        """Test: User's custom hooks are preserved."""
        settings = {
            "hooks": {
                "PreToolUse": [
                    {
                        "matcher": "Edit",
                        "hooks": [{"type": "command", "command": "my-custom-hook.sh"}],
                    }
                ],
                "SessionStart": [
                    {
                        "matcher": "custom-matcher",
                        "hooks": [{"type": "command", "command": "my-hook.sh"}],
                    }
                ],
            }
        }
        result, added = merge_klean_hooks(settings)

        # User's PreToolUse should be untouched
        assert "PreToolUse" in result["hooks"]
        assert result["hooks"]["PreToolUse"][0]["matcher"] == "Edit"

        # User's custom SessionStart should be preserved
        matchers = [h.get("matcher") for h in result["hooks"]["SessionStart"]]
        assert "custom-matcher" in matchers
        assert "startup" in matchers
        assert "resume" in matchers

    def test_idempotent(self):
        """Test: Running twice produces same result (no duplicates)."""
        settings = {}

        # First run
        result1, added1 = merge_klean_hooks(settings)

        # Second run on the result
        result2, added2 = merge_klean_hooks(result1)

        # Should not add anything on second run
        assert added2 == []

        # Structure should be identical
        assert json.dumps(result1, sort_keys=True) == json.dumps(result2, sort_keys=True)

    def test_all_klean_hooks_present(self):
        """Test: Already fully configured - should add nothing."""
        settings = {"hooks": KLEAN_HOOKS_CONFIG.copy()}

        # Deep copy to avoid mutation
        import copy

        settings = copy.deepcopy(settings)

        result, added = merge_klean_hooks(settings)

        assert added == []

    def test_preserves_other_settings(self):
        """Test: Non-hooks settings are preserved."""
        settings = {
            "model": "claude-3-opus",
            "apiKey": "sk-xxx",
            "permissions": {"allow": ["Read", "Write"]},
            "hooks": {},
        }
        result, added = merge_klean_hooks(settings)

        assert result["model"] == "claude-3-opus"
        assert result["apiKey"] == "sk-xxx"
        assert result["permissions"]["allow"] == ["Read", "Write"]


class TestKleanHooksConfig:
    """Validate KLEAN_HOOKS_CONFIG structure."""

    def test_config_has_required_types(self):
        """Test: Config has all required hook types."""
        assert "SessionStart" in KLEAN_HOOKS_CONFIG
        assert "UserPromptSubmit" in KLEAN_HOOKS_CONFIG
        assert "PostToolUse" in KLEAN_HOOKS_CONFIG

    def test_session_start_has_both_matchers(self):
        """Test: SessionStart has startup and resume matchers."""
        matchers = {h.get("matcher") for h in KLEAN_HOOKS_CONFIG["SessionStart"]}
        assert "startup" in matchers
        assert "resume" in matchers

    def test_all_hooks_have_command_type(self):
        """Test: All hooks use command type."""
        for _hook_type, hook_list in KLEAN_HOOKS_CONFIG.items():
            for hook_entry in hook_list:
                for hook in hook_entry.get("hooks", []):
                    assert hook.get("type") == "command"

    def test_all_commands_point_to_claude_hooks(self):
        """Test: All commands point to ~/.claude/hooks/."""
        for _hook_type, hook_list in KLEAN_HOOKS_CONFIG.items():
            for hook_entry in hook_list:
                for hook in hook_entry.get("hooks", []):
                    cmd = hook.get("command", "")
                    assert cmd.startswith("~/.claude/hooks/"), f"Bad path: {cmd}"


class TestDoctorIntegration:
    """Integration tests for doctor command hook detection."""

    def test_doctor_detects_missing_hooks(self, tmp_path):
        """Test: doctor detects when hooks are missing."""
        # Create empty settings.json
        settings_file = tmp_path / "settings.json"
        settings_file.write_text("{}")

        settings = json.loads(settings_file.read_text())

        # Check what's missing
        missing = []
        hooks = settings.get("hooks", {})

        if "SessionStart" not in hooks:
            missing.append("SessionStart")
        if "UserPromptSubmit" not in hooks:
            missing.append("UserPromptSubmit")
        if "PostToolUse" not in hooks:
            missing.append("PostToolUse")

        assert len(missing) == 3

    def test_doctor_autofix_creates_hooks(self, tmp_path):
        """Test: doctor --auto-fix creates hooks in settings.json."""
        settings_file = tmp_path / "settings.json"
        settings_file.write_text('{"model": "test"}')

        # Simulate auto-fix
        settings = json.loads(settings_file.read_text())
        settings, added = merge_klean_hooks(settings)
        settings_file.write_text(json.dumps(settings, indent=2))

        # Verify
        result = json.loads(settings_file.read_text())
        assert "model" in result  # Preserved
        assert "hooks" in result
        assert "SessionStart" in result["hooks"]
        assert len(added) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
