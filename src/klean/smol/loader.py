"""Load and parse SmolKLN agent .md files.

This module is INDEPENDENT - no imports from src/klean/droids/.
"""

from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional
import yaml
import re


@dataclass
class AgentConfig:
    """Parsed agent configuration from YAML frontmatter."""
    name: str
    description: str
    model: str = "qwen3-coder"
    tools: List[str] = field(default_factory=lambda: ["knowledge_search", "read_file", "search_files"])

    def __post_init__(self):
        if self.tools is None:
            self.tools = ["knowledge_search", "read_file", "search_files"]


@dataclass
class Agent:
    """Complete agent with config and system prompt."""
    config: AgentConfig
    system_prompt: str
    source_path: Path


def parse_agent_file(path: Path) -> Agent:
    """Parse an agent .md file into config and system prompt.

    File format:
    ---
    name: security-auditor
    description: Security audit specialist
    model: glm-4.6-thinking
    tools: ["knowledge_search", "read_file"]
    ---

    # System Prompt Content
    You are a security auditor...
    """
    content = path.read_text()

    # Split on YAML frontmatter delimiters
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)

    if match:
        yaml_content = match.group(1)
        markdown_content = match.group(2).strip()
        config_dict = yaml.safe_load(yaml_content)
    else:
        # No frontmatter, use defaults
        config_dict = {"name": path.stem, "description": ""}
        markdown_content = content

    config = AgentConfig(
        name=config_dict.get("name", path.stem),
        description=config_dict.get("description", ""),
        model=config_dict.get("model", "qwen3-coder"),
        tools=config_dict.get("tools"),
    )

    # Handle "inherit" model - default to qwen3-coder
    if config.model == "inherit":
        config.model = "qwen3-coder"

    return Agent(
        config=config,
        system_prompt=markdown_content,
        source_path=path,
    )


def list_available_agents(agents_dir: Path = None) -> List[str]:
    """List all available agent names."""
    if agents_dir is None:
        agents_dir = Path.home() / ".klean" / "agents"

    if not agents_dir.exists():
        return []

    return [p.stem for p in agents_dir.glob("*.md")]


def load_agent(name: str, agents_dir: Path = None) -> Agent:
    """Load an agent by name."""
    if agents_dir is None:
        agents_dir = Path.home() / ".klean" / "agents"

    path = agents_dir / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Agent not found: {name}")

    return parse_agent_file(path)
