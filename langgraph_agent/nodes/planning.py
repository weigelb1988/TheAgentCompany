"""
Planning node - Analyzes task and creates initial action plan.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from ..state import AgentState
from ..utils.llm_client import get_llm_client
from ..utils.prompts import SYSTEM_PROMPT, PLANNING_PROMPT
from ..utils.trajectory import log_planning_action
import re


async def planning_node(state: AgentState) -> dict:
    """
    Analyze the task and create an initial action plan.

    Args:
        state: Current agent state

    Returns:
        Updated state with plan
    """
    llm = get_llm_client()

    task_instruction = state["task_instruction"]

    # Create planning prompt
    planning_prompt = PLANNING_PROMPT.format(task_instruction=task_instruction)

    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=planning_prompt)]

    # Get plan from LLM
    response = await llm.ainvoke(messages)
    plan_text = response.content

    # Parse plan into list of steps
    plan_steps = parse_plan(plan_text)

    # Log planning action to trajectory
    trajectory = log_planning_action(state["trajectory"], plan_steps)

    return {
        "current_plan": plan_steps,
        "iteration": 0,
        "should_continue": True,
        "trajectory": trajectory,
        "messages": [HumanMessage(content=f"Task: {task_instruction}"), response],
    }


def parse_plan(plan_text: str) -> list[str]:
    """
    Parse plan text into a list of steps.

    Args:
        plan_text: Raw plan text from LLM

    Returns:
        List of plan steps
    """
    steps = []

    # Split by lines and extract numbered items or bullet points
    for line in plan_text.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Match numbered items (1. Step, 1) Step, etc.)
        if re.match(r"^\d+[\.\)]\s+", line):
            step = re.sub(r"^\d+[\.\)]\s+", "", line)
            steps.append(step)
        # Match bullet points
        elif line.startswith("-") or line.startswith("*"):
            step = line.lstrip("-*").strip()
            steps.append(step)
        # If line looks substantial and we have no steps yet, include it
        elif len(line) > 20 and not steps:
            steps.append(line)

    return steps
