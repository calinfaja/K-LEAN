"""Configuration for multi-agent system.

Simple dataclass-based configuration for 3-agent and 4-agent variants.
Based on research: GLM for orchestration (90.6% tool-calling), Qwen3 for speed,
Kimi/DeepSeek for deep reasoning.
"""

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class AgentConfig:
    """Configuration for a single agent in the multi-agent system."""
    name: str
    model: str
    tools: List[str]
    max_steps: int
    description: str


# Model assignments based on research
# Note: CodeAgent requires models that output proper code blocks
MODELS = {
    "manager": "glm-4.6-thinking",      # 90.6% tool-calling success
    "file-scout": "qwen3-coder",         # Fastest for file navigation
    "analyzer": "deepseek-v3-thinking",  # Changed: better code generation
    "code-analyzer": "deepseek-v3-thinking",  # Best for code bugs
    "security-auditor": "deepseek-v3-thinking",  # Deep security analysis
    "synthesizer": "qwen3-coder",        # Changed: reliable code output
}


def get_3_agent_config() -> Dict[str, AgentConfig]:
    """Return 3-agent configuration (default).

    Manager orchestrates file_scout and analyzer.
    Simpler, faster, fewer API calls.
    """
    return {
        "manager": AgentConfig(
            name="manager",
            model=MODELS["manager"],
            tools=[],  # Manager only delegates
            max_steps=15,
            description="Orchestrates the review. Delegates file reading to file_scout and analysis to analyzer.",
        ),
        "file_scout": AgentConfig(
            name="file_scout",
            model=MODELS["file-scout"],
            tools=["read_file", "search_files", "grep", "knowledge_search", "git_diff", "git_status", "git_log", "list_directory"],
            max_steps=10,
            description="Fast file discovery. Give it paths, patterns, or topics to find and read files. Can also get git diff, status, log, and list directories.",
        ),
        "analyzer": AgentConfig(
            name="analyzer",
            model=MODELS["analyzer"],
            tools=["read_file", "grep", "get_file_info"],
            max_steps=15,
            description="Deep code analyzer. Give it code to analyze for bugs, security, and quality issues.",
        ),
    }


def get_4_agent_config() -> Dict[str, AgentConfig]:
    """Return 4-agent configuration (--thorough flag).

    Manager orchestrates file_scout, code_analyzer, security_auditor, and synthesizer.
    More thorough, specialized analysis.
    """
    return {
        "manager": AgentConfig(
            name="manager",
            model=MODELS["manager"],
            tools=[],
            max_steps=15,
            description="Orchestrates the review process.",
        ),
        "file_scout": AgentConfig(
            name="file_scout",
            model=MODELS["file-scout"],
            tools=["read_file", "search_files", "grep", "knowledge_search", "git_diff", "git_status", "git_log", "list_directory"],
            max_steps=10,
            description="Fast file discovery, git operations, and knowledge lookup.",
        ),
        "code_analyzer": AgentConfig(
            name="code_analyzer",
            model=MODELS["code-analyzer"],
            tools=["read_file", "grep", "get_file_info"],
            max_steps=12,
            description="Code quality analyzer. Finds bugs, logic errors, and maintainability issues.",
        ),
        "security_auditor": AgentConfig(
            name="security_auditor",
            model=MODELS["security-auditor"],
            tools=["read_file", "grep", "web_search", "get_file_info"],
            max_steps=12,
            description="Security analyzer. Finds vulnerabilities using OWASP Top 10 framework.",
        ),
        "synthesizer": AgentConfig(
            name="synthesizer",
            model=MODELS["synthesizer"],
            tools=["read_file"],
            max_steps=8,
            description="Report formatter. Creates structured final report from analysis findings.",
        ),
    }
