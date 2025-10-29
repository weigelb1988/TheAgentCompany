"""
LangGraph Agent for TheAgentCompany Benchmark.

This package provides a modular LangGraph-based agent that connects to
locally hosted vLLM and integrates with TheAgentCompany benchmark.
"""

from .graph import create_agent_graph, visualize_graph
from .state import AgentState, create_initial_state
from .config import AgentConfig, config

__version__ = "0.1.0"

__all__ = [
    "create_agent_graph",
    "visualize_graph",
    "AgentState",
    "create_initial_state",
    "AgentConfig",
    "config",
]
