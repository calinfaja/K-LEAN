"""Load and parse SmolKLN agent .md files.

Agent prompt loader for SmolKLN.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from klean.discovery import get_model


@dataclass
class AgentConfig:
    """Parsed agent configuration from YAML frontmatter."""

    name: str
    description: str
    model: str = ""  # Empty = use first available from LiteLLM
    tools: list[str] = field(
        default_factory=lambda: ["knowledge_search", "read_file", "search_files"]
    )

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
    pattern = r"^---\s*\n(.*?)\n---\s*\n(.*)$"
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
        model=config_dict.get("model", ""),
        tools=config_dict.get("tools"),
    )

    # Resolve model: empty, "auto", or "inherit" = first available from LiteLLM
    if not config.model or config.model in ("auto", "inherit"):
        config.model = get_model() or "auto"

    return Agent(
        config=config,
        system_prompt=markdown_content,
        source_path=path,
    )


def list_available_agents(agents_dir: Path = None) -> list[str]:
    """List all available agent names.

    Filters out template files (TEMPLATE.md) from the listing.
    """
    if agents_dir is None:
        agents_dir = Path.home() / ".klean" / "agents"

    if not agents_dir.exists():
        return []

    return [p.stem for p in agents_dir.glob("*.md") if p.stem.upper() != "TEMPLATE"]


def load_agent(name: str, agents_dir: Path = None) -> Agent:
    """Load an agent by name."""
    if agents_dir is None:
        agents_dir = Path.home() / ".klean" / "agents"

    path = agents_dir / f"{name}.md"
    if not path.exists():
        raise FileNotFoundError(f"Agent not found: {name}")

    return parse_agent_file(path)
