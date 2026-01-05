"""SmolKLN - Smolagents Integration for K-LEAN.

A production-grade agent system using Smolagents + LiteLLM.
"""

import warnings

# Suppress Pydantic serialization warnings from smolagents/LiteLLM
# These occur when LiteLLM response fields don't match smolagents' Pydantic models exactly
warnings.filterwarnings(
    "ignore",
    message="Pydantic serializer warnings",
    category=UserWarning,
    module="pydantic",
)

# Core  # noqa: E402 - warning filter must run before imports
from klean.discovery import get_model, list_models  # noqa: E402

from .async_executor import (  # noqa: E402
    AsyncExecutor,
    get_async_executor,
    get_task_status,
    submit_async,
)
from .context import (  # noqa: E402
    ProjectContext,
    detect_project_root,
    format_context_for_prompt,
    gather_project_context,
)
from .executor import SmolKLNExecutor  # noqa: E402
from .loader import Agent, AgentConfig, list_available_agents, load_agent  # noqa: E402
from .mcp_tools import (  # noqa: E402
    get_mcp_server_config,
    get_mcp_tools,
    list_available_mcp_servers,
    load_mcp_config,
)
from .memory import AgentMemory, MemoryEntry, SessionMemory  # noqa: E402
from .models import create_model  # noqa: E402
from .orchestrator import SmolKLNOrchestrator, quick_orchestrate  # noqa: E402
from .reflection import (  # noqa: E402
    Critique,
    CritiqueVerdict,
    ReflectionEngine,
    create_reflection_engine,
)
from .task_queue import QueuedTask, TaskQueue, TaskState  # noqa: E402
from .tools import KnowledgeRetrieverTool, get_default_tools  # noqa: E402

__all__ = [
    # Core
    "SmolKLNExecutor",
    "load_agent",
    "list_available_agents",
    "Agent",
    "AgentConfig",
    "create_model",
    "get_model",
    "list_models",
    # Tools
    "KnowledgeRetrieverTool",
    "get_default_tools",
    # Context
    "ProjectContext",
    "gather_project_context",
    "format_context_for_prompt",
    "detect_project_root",
    # Memory
    "AgentMemory",
    "SessionMemory",
    "MemoryEntry",
    # Reflection
    "ReflectionEngine",
    "Critique",
    "CritiqueVerdict",
    "create_reflection_engine",
    # MCP Tools
    "get_mcp_tools",
    "get_mcp_server_config",
    "list_available_mcp_servers",
    "load_mcp_config",
    # Orchestrator
    "SmolKLNOrchestrator",
    "quick_orchestrate",
    # Async Execution
    "TaskQueue",
    "QueuedTask",
    "TaskState",
    "AsyncExecutor",
    "get_async_executor",
    "submit_async",
    "get_task_status",
]
