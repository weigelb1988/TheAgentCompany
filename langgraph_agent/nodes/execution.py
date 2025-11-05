"""
Execution node - Executes pending tool calls.
"""

from ..state import AgentState
from ..tools.registry import ToolRegistry
from ..utils.trajectory import log_bash_action, log_action
from ..utils.memory import MemoryStore


async def execution_node(state: AgentState) -> dict:
    """
    Execute pending tool calls and store results in enhanced memory.

    Args:
        state: Current agent state

    Returns:
        Updated state with tool results and memory
    """
    tool_registry = ToolRegistry(container_name=state.get("container_name"))

    pending_actions = state["pending_actions"]
    tool_results = list(state["tool_results"])
    trajectory = list(state["trajectory"])

    # Load memory store from state
    memory_store = MemoryStore.from_dict(state.get("memory", {"memories": []}))

    executed_actions = []

    # Execute each pending action
    for action in pending_actions:
        tool_name = action["tool_name"]
        parameters = action["parameters"]
        reasoning = action.get("reasoning", "")

        # Execute tool
        result = await tool_registry.call_tool(tool_name, parameters)

        # Add to tool results (legacy)
        tool_results.append({**result, "reasoning": reasoning})

        # Add to memory store (new)
        memory_store.add_from_tool_call(
            tool_name=tool_name,
            parameters=parameters,
            result=result,
            reasoning=reasoning,
        )

        # Log to trajectory based on tool type
        if tool_name == "bash":
            trajectory = log_bash_action(
                trajectory,
                command=parameters.get("command", ""),
                output=result.get("output", ""),
                return_code=result.get("return_code", -1),
            )
        else:
            # Generic action logging
            trajectory = log_action(
                trajectory,
                action_type=tool_name,
                details={
                    "parameters": parameters,
                    "result": str(result)[:500],  # Truncate
                },
            )

        executed_actions.append(action)

    return {
        "pending_actions": [],  # Clear pending actions
        "tool_results": tool_results,
        "memory": memory_store.to_dict(),  # Save memory back to state
        "trajectory": trajectory,
    }
