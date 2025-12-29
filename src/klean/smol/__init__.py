"""SmolKLN - Smolagents Integration for K-LEAN.

A production-grade agent system using Smolagents + LiteLLM.

Features:
- Project-aware: Auto-detects project root, loads CLAUDE.md
- Knowledge DB integration: Queries prior solutions and lessons
- Memory: Session memory and long-term knowledge persistence
- Reflection: Self-critique and retry for quality improvement
- MCP integration: Use MCP servers (Serena, filesystem) for tools
- Multi-agent: Orchestrate multiple agents for complex tasks
- Async execution: Background task queue with persistence

Usage:
    from klean.smol import SmolKLNExecutor

    executor = SmolKLNExecutor()
    print(f"Project: {executor.project_root}")
    result = executor.execute("security-auditor", "audit auth module")

Async usage:
    from klean.smol import submit_async, get_task_status

    task_id = submit_async("code-reviewer", "review main.py")
    status = get_task_status(task_id)

Multi-agent:
    from klean.smol import SmolKLNOrchestrator

    orchestrator = SmolKLNOrchestrator(executor)
    result = orchestrator.execute("Full security audit", agents=["security-auditor", "code-reviewer"])
"""

# Core
from .executor import SmolKLNExecutor
from .loader import load_agent, list_available_agents, Agent, AgentConfig
from .models import create_model
from klean.discovery import get_model, list_models

# Tools
from .tools import KnowledgeRetrieverTool, get_default_tools

# Context
from .context import (
    ProjectContext,
    gather_project_context,
    format_context_for_prompt,
    detect_project_root,
)

# Memory
from .memory import AgentMemory, SessionMemory, MemoryEntry

# Reflection
from .reflection import (
    ReflectionEngine,
    Critique,
    CritiqueVerdict,
    create_reflection_engine,
)

# MCP Tools
from .mcp_tools import (
    get_mcp_tools,
    get_mcp_server_config,
    list_available_mcp_servers,
    load_mcp_config,
)

# Orchestrator
from .orchestrator import SmolKLNOrchestrator, quick_orchestrate

# Async Execution
from .task_queue import TaskQueue, QueuedTask, TaskState
from .async_executor import (
    AsyncExecutor,
    get_async_executor,
    submit_async,
    get_task_status,
)

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
