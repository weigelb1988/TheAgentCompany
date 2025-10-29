"""
Output node - Formats final results and summary.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from ..state import AgentState
from ..utils.llm_client import get_llm_client
from ..utils.prompts import SYSTEM_PROMPT, OUTPUT_PROMPT


async def output_node(state: AgentState) -> dict:
    """
    Generate final output summary.

    Args:
        state: Current agent state

    Returns:
        Updated state with final summary
    """
    llm = get_llm_client(temperature=0.5)

    # Create output prompt
    output_prompt = OUTPUT_PROMPT.format(
        task_instruction=state["task_instruction"],
        completed_steps="\n".join(f"- {step}" for step in state["completed_steps"]),
    )

    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=output_prompt)]

    # Get summary from LLM
    response = await llm.ainvoke(messages)
    summary = response.content

    # Mark task as complete in trajectory
    trajectory = list(state["trajectory"])
    trajectory.append(
        {
            "step_number": len(trajectory) + 1,
            "action": "completion",
            "summary": summary,
            "total_iterations": state["iteration"],
            "completed_steps": len(state["completed_steps"]),
        }
    )

    return {
        "trajectory": trajectory,
        "should_continue": False,
        "messages": [response],
    }
