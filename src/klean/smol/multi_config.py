"""Configuration for multi-agent system.

Simple dataclass-based configuration for 3-agent and 4-agent variants.
Uses dynamic model discovery - all agents use first available model from LiteLLM.
"""

from dataclasses import dataclass

from klean.discovery import get_model


@dataclass
class AgentConfig:
    """Configuration for a single agent in the multi-agent system."""

    name: str
    model: str
    tools: list[str]
    max_steps: int
    description: str
    planning_interval: int = 3  # Plan every N steps to stay on track


def get_default_model() -> str:
    """Get default model from LiteLLM (first available)."""
    return get_model() or "auto"


def get_models() -> dict[str, str]:
    """Get model assignments - all use first available from LiteLLM.

    User controls model priority via their LiteLLM config order.
    """
    default = get_default_model()
    return {
        "manager": default,
        "file-scout": default,
        "analyzer": default,
        "code-analyzer": default,
        "security-auditor": default,
        "synthesizer": default,
    }


def get_3_agent_config() -> dict[str, AgentConfig]:
    """Return 3-agent configuration (default).

    Manager orchestrates file_scout and analyzer.
    Simpler, faster, fewer API calls.
    """
    models = get_models()
    return {
        "manager": AgentConfig(
            name="manager",
            model=models["manager"],
            tools=[],  # Manager only delegates
            max_steps=7,
            description="Orchestrates the review. Delegates file reading to file_scout and analysis to analyzer.",
        ),
        "file_scout": AgentConfig(
            name="file_scout",
            model=models["file-scout"],
            tools=[
                "read_file",
                "search_files",
                "grep",
                "knowledge_search",
                "git_diff",
                "git_status",
                "git_log",
                "list_directory",
            ],
            max_steps=6,
            description="Fast file discovery. Give it paths, patterns, or topics to find and read files. Can also get git diff, status, log, and list directories.",
        ),
        "analyzer": AgentConfig(
            name="analyzer",
            model=models["analyzer"],
            tools=["read_file", "grep", "get_file_info"],
            max_steps=6,
            description="Deep code analyzer. Give it code to analyze for bugs, security, and quality issues.",
        ),
    }


def get_thorough_agent_config() -> dict[str, AgentConfig]:
    """Return thorough agent configuration (--thorough flag).

    Manager orchestrates file_scout, code_analyzer, security_auditor, and synthesizer.
    More thorough analysis with 4 specialized agents plus manager orchestrator.
    """
    models = get_models()
    return {
        "manager": AgentConfig(
            name="manager",
            model=models["manager"],
            tools=[],
            max_steps=7,
            description="Orchestrates the review process.",
        ),
        "file_scout": AgentConfig(
            name="file_scout",
            model=models["file-scout"],
            tools=[
                "read_file",
                "search_files",
                "grep",
                "knowledge_search",
                "git_diff",
                "git_status",
                "git_log",
                "list_directory",
            ],
            max_steps=6,
            description="Fast file discovery, git operations, and knowledge lookup.",
        ),
        "code_analyzer": AgentConfig(
            name="code_analyzer",
            model=models["code-analyzer"],
            tools=["read_file", "grep", "get_file_info"],
            max_steps=6,
            description="Code quality analyzer. Finds bugs, logic errors, and maintainability issues.",
        ),
        "security_auditor": AgentConfig(
            name="security_auditor",
            model=models["security-auditor"],
            tools=["read_file", "grep", "web_search", "get_file_info"],
            max_steps=6,
            description="Security analyzer. Finds vulnerabilities using OWASP Top 10 framework.",
        ),
        "synthesizer": AgentConfig(
            name="synthesizer",
            model=models["synthesizer"],
            tools=["read_file"],
            max_steps=6,
            description="Report formatter. Creates structured final report from analysis findings.",
        ),
    }
