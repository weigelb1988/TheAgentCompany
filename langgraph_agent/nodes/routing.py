"""
Routing node - Determines next action in the agent workflow.
"""

from ..state import AgentState
from ..config import config


def routing_node(state: AgentState) -> str:
    """
    Decide the next action based on current state.

    This function determines whether the agent should:
    - Execute tools (if pending actions exist)
    - Reflect on progress
    - Complete the task

    Args:
        state: Current agent state

    Returns:
        Route name: "tool_call", "reflect", or "complete"
    """
    # Check if max iterations reached
    if state["iteration"] >= state["max_iterations"]:
        return "complete"

    # Check if agent has decided to stop
    if not state["should_continue"]:
        return "complete"

    # If there are pending actions, execute them
    if state["pending_actions"]:
        return "tool_call"

    # If plan is empty and no pending actions, might be done
    if not state["current_plan"] and not state["pending_actions"]:
        return "complete"

    # If it's time to reflect (every N iterations)
    if config.enable_reflection and state["iteration"] % config.reflection_frequency == 0:
        return "reflect"

    # Default: reflect to determine next actions
    return "reflect"


def route_decision(state: AgentState) -> str:
    """
    Wrapper for routing_node to be used in conditional edges.

    Args:
        state: Current agent state

    Returns:
        Route name
    """
    return routing_node(state)
