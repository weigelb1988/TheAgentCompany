"""
State schema for the LangGraph agent.

This module defines the AgentState that flows through all nodes in the graph.
"""

from typing import TypedDict, Annotated, Sequence, Optional, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    The state of the agent at any point in time.

    This state is passed through all nodes in the LangGraph workflow and tracks:
    - Conversation history
    - Task information
    - Execution tracking
    - Tool execution results with enhanced memory
    - Environment state
    - Trajectory for evaluation
    """

    # Core conversation - messages are automatically merged with add_messages
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # Task information
    task_instruction: str
    task_name: str

    # Execution tracking
    current_plan: list[str]
    completed_steps: list[str]
    iteration: int
    max_iterations: int

    # Tool execution
    pending_actions: list[dict[str, Any]]
    tool_results: list[dict[str, Any]]  # Legacy: kept for backward compatibility

    # Enhanced memory system - stores structured memory with indexing
    memory: dict[str, Any]  # Serialized MemoryStore

    # Environment state
    current_directory: str
    browser_state: dict[str, Any]
    service_credentials: dict[str, Any]

    # Container information (for tool execution)
    container_name: Optional[str]

    # Trajectory for evaluation (TheAgentCompany format)
    trajectory: list[dict[str, Any]]

    # Control flow
    should_continue: bool
    error_message: Optional[str]


def create_initial_state(
    task_instruction: str,
    task_name: str,
    container_name: Optional[str] = None,
    service_credentials: Optional[dict[str, Any]] = None,
    max_iterations: int = 100,
) -> AgentState:
    """
    Create an initial agent state for a new task.

    Args:
        task_instruction: The task description from /instruction/task.md
        task_name: Identifier for the task
        container_name: Docker container name for tool execution
        service_credentials: Credentials for GitLab, RocketChat, etc.
        max_iterations: Maximum number of agent iterations

    Returns:
        Initialized AgentState ready for graph execution
    """
    return AgentState(
        messages=[],
        task_instruction=task_instruction,
        task_name=task_name,
        current_plan=[],
        completed_steps=[],
        iteration=0,
        max_iterations=max_iterations,
        pending_actions=[],
        tool_results=[],
        memory={"memories": [], "statistics": {}},  # Initialize empty memory
        current_directory="/workspace",
        browser_state={},
        service_credentials=service_credentials or {
            "gitlab": {
                "url": "http://localhost:8929",
                "username": "root",
                "password": "theagentcompany",
            },
            "rocketchat": {
                "url": "http://localhost:3000",
                "username": "theagentcompany",
                "password": "theagentcompany",
            },
            "owncloud": {
                "url": "http://localhost:8092",
                "username": "theagentcompany",
                "password": "theagentcompany",
            },
            "plane": {
                "url": "http://localhost:8091",
                "email": "agent@company.com",
                "password": "theagentcompany",
            },
        },
        container_name=container_name,
        trajectory=[],
        should_continue=True,
        error_message=None,
    )
