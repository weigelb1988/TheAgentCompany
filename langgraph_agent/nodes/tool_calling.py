"""
Tool calling node - Generates tool calls based on current state and plan.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from ..state import AgentState
from ..utils.llm_client import get_structured_llm
from ..utils.prompts import SYSTEM_PROMPT, TOOL_CALLING_PROMPT


class ToolCall(BaseModel):
    """A single tool call with parameters."""

    tool_name: str = Field(description="Name of the tool to call")
    parameters: dict = Field(description="Parameters for the tool call")
    reasoning: str = Field(description="Why this tool call is needed")


class ToolCallPlan(BaseModel):
    """Plan for the next tool calls."""

    tool_calls: list[ToolCall] = Field(description="List of tool calls to execute")


async def tool_calling_node(state: AgentState) -> dict:
    """
    Generate tool calls based on the current state.

    Args:
        state: Current agent state

    Returns:
        Updated state with pending actions
    """
    # Use structured output to get tool calls
    llm = get_structured_llm(ToolCallPlan, temperature=0.7)

    # Format recent tool results
    recent_results = format_recent_results(state["tool_results"][-3:])

    # Create tool calling prompt
    tool_prompt = TOOL_CALLING_PROMPT.format(
        current_plan="\n".join(f"{i+1}. {step}" for i, step in enumerate(state["current_plan"])),
        completed_steps="\n".join(
            f"- {step}" for step in state["completed_steps"][-5:]
        ),  # Last 5
        recent_tool_results=recent_results,
    )

    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=tool_prompt)]

    try:
        # Get structured tool calls from LLM
        response = await llm.ainvoke(messages)

        # Convert to pending actions format
        pending_actions = [
            {
                "tool_name": call.tool_name,
                "parameters": call.parameters,
                "reasoning": call.reasoning,
            }
            for call in response.tool_calls
        ]

        return {
            "pending_actions": pending_actions,
            "iteration": state["iteration"] + 1,
        }

    except Exception as e:
        # If structured output fails, fall back to no actions
        print(f"Tool calling failed: {e}")
        return {
            "pending_actions": [],
            "error_message": f"Tool calling error: {str(e)}",
            "iteration": state["iteration"] + 1,
        }


def format_recent_results(tool_results: list[dict]) -> str:
    """
    Format recent tool results for the prompt.

    Args:
        tool_results: List of recent tool results

    Returns:
        Formatted string
    """
    if not tool_results:
        return "No recent results"

    formatted = []
    for result in tool_results:
        tool_name = result.get("tool_name", "unknown")
        success = result.get("success", False)
        output = result.get("output", result.get("error", ""))

        # Truncate long outputs
        if isinstance(output, str) and len(output) > 500:
            output = output[:500] + "..."

        formatted.append(f"- {tool_name}: {'✓' if success else '✗'} {output}")

    return "\n".join(formatted)
