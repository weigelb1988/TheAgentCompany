"""
Reflection node - Reviews progress and determines next steps.
"""

from langchain_core.messages import SystemMessage, HumanMessage
from ..state import AgentState
from ..utils.llm_client import get_llm_client
from ..utils.prompts import SYSTEM_PROMPT, REFLECTION_PROMPT
from ..utils.trajectory import log_reflection_action
from ..utils.memory import MemoryStore


async def reflection_node(state: AgentState) -> dict:
    """
    Reflect on progress and determine next steps using enhanced memory.

    Args:
        state: Current agent state

    Returns:
        Updated state with reflection and decision
    """
    llm = get_llm_client(temperature=0.7)

    # Load memory store
    memory_store = MemoryStore.from_dict(state.get("memory", {"memories": []}))

    # Format recent results for reflection using memory
    recent_results = format_memory_for_reflection(memory_store)

    # Create reflection prompt
    reflection_prompt = REFLECTION_PROMPT.format(
        task_instruction=state["task_instruction"],
        current_plan="\n".join(f"{i+1}. {step}" for i, step in enumerate(state["current_plan"])),
        completed_steps="\n".join(f"- {step}" for step in state["completed_steps"]),
        recent_tool_results=recent_results,
        iteration=state["iteration"],
        max_iterations=state["max_iterations"],
    )

    messages = [SystemMessage(content=SYSTEM_PROMPT), HumanMessage(content=reflection_prompt)]

    # Get reflection from LLM
    response = await llm.ainvoke(messages)
    reflection_text = response.content

    # Parse decision from reflection
    decision = parse_decision(reflection_text)

    # Update state based on decision
    should_continue = decision in ["CONTINUE", "ADJUST"]

    # If adjusting, mark current step as needing revision
    updated_plan = state["current_plan"]
    if decision == "ADJUST" and state["current_plan"]:
        # Keep the plan but we'll re-evaluate in tool calling
        pass
    elif decision == "COMPLETE":
        # Clear plan to signal completion
        updated_plan = []

    # Log reflection to trajectory
    trajectory = log_reflection_action(
        state["trajectory"], reflection=reflection_text, decision=decision
    )

    return {
        "should_continue": should_continue,
        "current_plan": updated_plan,
        "trajectory": trajectory,
        "messages": [response],
    }


def format_memory_for_reflection(memory_store: MemoryStore, limit: int = 10) -> str:
    """
    Format memory for reflection prompt with rich context.

    Args:
        memory_store: Memory store with recent operations
        limit: Number of recent memories to include

    Returns:
        Formatted string with memory summary
    """
    if not memory_store.memories:
        return "No operations yet"

    lines = []

    # Get recent memories
    recent = memory_store.get_recent(limit)

    lines.append("Recent Operations:")
    for memory in recent:
        lines.append(f"  {memory.get_summary()}")

    # Add statistics
    stats = memory_store.get_statistics()
    lines.append(f"\nOverall: {stats['successful']}/{stats['total_memories']} successful")

    # Add entity summary (what we know)
    entities_found = []
    for entity_type in ["projects", "issues", "files", "users"]:
        entities = memory_store.get_entities_of_type(entity_type)
        if entities:
            entities_found.append(f"{entity_type}: {', '.join(list(entities)[:5])}")

    if entities_found:
        lines.append("\nEntities Discovered:")
        for entity_line in entities_found:
            lines.append(f"  {entity_line}")

    # Add failed operations if any (for debugging)
    failed = memory_store.get_failed(limit=3)
    if failed:
        lines.append("\nRecent Failures:")
        for memory in failed:
            lines.append(f"  {memory.get_summary()}")

    return "\n".join(lines)


def format_tool_results(tool_results: list[dict]) -> str:
    """
    Format tool results for reflection prompt (legacy).

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
        if isinstance(output, str) and len(output) > 300:
            output = output[:300] + "..."

        status = "Success" if success else "Failed"
        formatted.append(f"- {tool_name} ({status}): {output}")

    return "\n".join(formatted)


def parse_decision(reflection_text: str) -> str:
    """
    Parse decision from reflection text.

    Args:
        reflection_text: Raw reflection from LLM

    Returns:
        Decision: "CONTINUE", "ADJUST", or "COMPLETE"
    """
    text_upper = reflection_text.upper()

    # Look for explicit decision markers
    if "COMPLETE" in text_upper or "TASK IS FINISHED" in text_upper:
        return "COMPLETE"
    elif "ADJUST" in text_upper or "REVISE" in text_upper:
        return "ADJUST"
    elif "CONTINUE" in text_upper:
        return "CONTINUE"

    # Default to continue if no clear signal
    return "CONTINUE"
