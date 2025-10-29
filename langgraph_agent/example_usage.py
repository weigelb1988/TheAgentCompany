"""
Example usage of the LangGraph agent.

This script demonstrates how to use the agent for a simple task.
"""

import asyncio
import json
from langgraph_agent import create_agent_graph, create_initial_state


async def main():
    """Run a simple example task."""

    # Define a simple task
    task_instruction = """
    You need to find all Python files in the /workspace directory,
    count the total number of lines of code, and report the result.
    """

    # Create initial state
    print("Creating initial state...")
    state = create_initial_state(
        task_instruction=task_instruction,
        task_name="example-count-lines",
        container_name=None,  # Set to container name if using Docker
        max_iterations=20,  # Fewer iterations for simple task
    )

    # Create and run the agent graph
    print("\nCreating agent graph...")
    graph = create_agent_graph(use_checkpointer=True)

    print("\nRunning agent...\n")
    print("=" * 60)

    try:
        # Execute the graph
        final_state = await graph.ainvoke(
            state, config={"configurable": {"thread_id": "example-1"}}
        )

        # Display results
        print("\n" + "=" * 60)
        print("AGENT EXECUTION COMPLETE")
        print("=" * 60)
        print(f"\nTask: {task_instruction.strip()}")
        print(f"\nTotal Iterations: {final_state['iteration']}")
        print(f"Completed Steps: {len(final_state['completed_steps'])}")
        print(f"\nTrajectory Steps: {len(final_state['trajectory'])}")

        # Show completed steps
        if final_state["completed_steps"]:
            print("\nCompleted Steps:")
            for i, step in enumerate(final_state["completed_steps"], 1):
                print(f"  {i}. {step}")

        # Show recent tool results
        if final_state["tool_results"]:
            print("\nRecent Tool Results:")
            for result in final_state["tool_results"][-5:]:  # Last 5
                tool_name = result.get("tool_name", "unknown")
                success = result.get("success", False)
                status = "✓" if success else "✗"
                print(f"  {status} {tool_name}")

        # Save trajectory to file
        trajectory_data = {
            "task_name": final_state["task_name"],
            "agent": "langgraph-vllm",
            "trajectory": final_state["trajectory"],
            "total_iterations": final_state["iteration"],
            "completed_steps": final_state["completed_steps"],
        }

        output_file = "example_trajectory.json"
        with open(output_file, "w") as f:
            json.dump(trajectory_data, f, indent=2)

        print(f"\nTrajectory saved to: {output_file}")

    except Exception as e:
        print(f"\nError during execution: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    print("=" * 60)
    print("LangGraph Agent Example")
    print("=" * 60)
    print("\nNote: This example requires a running vLLM server.")
    print("Make sure to configure your .env file with the correct settings.\n")

    asyncio.run(main())
