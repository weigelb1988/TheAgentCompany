"""
Main LangGraph agent workflow construction.
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import AgentState
from .nodes.planning import planning_node
from .nodes.routing import route_decision
from .nodes.tool_calling import tool_calling_node
from .nodes.execution import execution_node
from .nodes.reflection import reflection_node
from .nodes.output import output_node


def create_agent_graph(use_checkpointer: bool = True):
    """
    Create the LangGraph agent workflow.

    The graph implements a ReAct-style agent loop with planning and reflection:

    1. Planning: Analyze task and create action plan
    2. Routing: Decide next action (tool call, reflect, or complete)
    3. Tool Calling: Generate tool calls based on current state
    4. Execution: Execute pending tool calls
    5. Reflection: Review progress and adjust strategy
    6. Output: Format final results

    Flow:
        planning -> routing -> {tool_call, reflect, complete}
        tool_call -> execution -> reflection -> routing
        reflect -> routing
        complete -> output -> END

    Args:
        use_checkpointer: Whether to enable state checkpointing (for resumption)

    Returns:
        Compiled LangGraph workflow
    """
    # Initialize graph with AgentState
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("planning", planning_node)
    workflow.add_node("tool_calling", tool_calling_node)
    workflow.add_node("execution", execution_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("output", output_node)

    # Set entry point
    workflow.set_entry_point("planning")

    # Add edge from planning to routing
    workflow.add_conditional_edges(
        "planning",
        route_decision,
        {
            "tool_call": "tool_calling",
            "reflect": "reflection",
            "complete": "output",
        },
    )

    # Tool calling leads to execution
    workflow.add_edge("tool_calling", "execution")

    # Execution leads to reflection
    workflow.add_edge("execution", "reflection")

    # Reflection leads back to routing
    workflow.add_conditional_edges(
        "reflection",
        route_decision,
        {
            "tool_call": "tool_calling",
            "reflect": "reflection",
            "complete": "output",
        },
    )

    # Output leads to END
    workflow.add_edge("output", END)

    # Compile graph with optional checkpointing
    if use_checkpointer:
        memory = MemorySaver()
        graph = workflow.compile(checkpointer=memory)
    else:
        graph = workflow.compile()

    return graph


def visualize_graph(output_path: str = "agent_graph.png"):
    """
    Visualize the agent graph and save to file.

    Args:
        output_path: Path to save visualization

    Note:
        Requires graphviz to be installed
    """
    try:
        from IPython.display import Image

        graph = create_agent_graph(use_checkpointer=False)

        # Generate visualization
        png_data = graph.get_graph().draw_mermaid_png()

        # Save to file
        with open(output_path, "wb") as f:
            f.write(png_data)

        print(f"Graph visualization saved to: {output_path}")

    except ImportError:
        print("To visualize graphs, install: pip install grandalf pygraphviz")
    except Exception as e:
        print(f"Failed to visualize graph: {e}")
