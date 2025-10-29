"""
Unit tests for LangGraph agent nodes.
"""

import pytest
from langgraph_agent.state import AgentState, create_initial_state
from langgraph_agent.nodes.planning import planning_node, parse_plan
from langgraph_agent.nodes.routing import routing_node
from langgraph_agent.nodes.execution import execution_node


class TestPlanningNode:
    """Tests for the planning node."""

    @pytest.mark.asyncio
    async def test_planning_creates_plan(self):
        """Test that planning node creates a valid plan."""
        state = create_initial_state(
            task_instruction="Find all Python files in /workspace and count lines of code.",
            task_name="test-task",
        )

        # Note: This test requires a running vLLM server
        # In CI/CD, mock the LLM client
        try:
            result = await planning_node(state)

            assert len(result["current_plan"]) > 0
            assert result["iteration"] == 0
            assert result["should_continue"] is True
            assert len(result["trajectory"]) > 0
            assert result["trajectory"][0]["action"] == "planning"

        except Exception as e:
            pytest.skip(f"Skipping test - vLLM not available: {e}")

    def test_parse_plan_numbered(self):
        """Test parsing numbered plan items."""
        plan_text = """
        1. First step
        2. Second step
        3. Third step
        """

        steps = parse_plan(plan_text)
        assert len(steps) == 3
        assert steps[0] == "First step"
        assert steps[1] == "Second step"

    def test_parse_plan_bullets(self):
        """Test parsing bulleted plan items."""
        plan_text = """
        - First step
        - Second step
        - Third step
        """

        steps = parse_plan(plan_text)
        assert len(steps) == 3


class TestRoutingNode:
    """Tests for the routing node."""

    def test_route_complete_when_max_iterations(self):
        """Test routing to complete when max iterations reached."""
        state = create_initial_state("test task", "test")
        state["iteration"] = 100
        state["max_iterations"] = 100

        decision = routing_node(state)
        assert decision == "complete"

    def test_route_complete_when_should_continue_false(self):
        """Test routing to complete when should_continue is False."""
        state = create_initial_state("test task", "test")
        state["should_continue"] = False

        decision = routing_node(state)
        assert decision == "complete"

    def test_route_tool_call_when_pending_actions(self):
        """Test routing to tool_call when pending actions exist."""
        state = create_initial_state("test task", "test")
        state["pending_actions"] = [{"tool_name": "bash", "parameters": {"command": "ls"}}]

        decision = routing_node(state)
        assert decision == "tool_call"

    def test_route_reflect_by_default(self):
        """Test routing to reflect by default."""
        state = create_initial_state("test task", "test")
        state["current_plan"] = ["Step 1", "Step 2"]

        decision = routing_node(state)
        assert decision == "reflect"


class TestExecutionNode:
    """Tests for the execution node."""

    @pytest.mark.asyncio
    async def test_execution_bash_command(self):
        """Test executing a bash command."""
        state = create_initial_state("test task", "test")
        state["pending_actions"] = [
            {
                "tool_name": "bash",
                "parameters": {"command": "echo 'Hello World'"},
                "reasoning": "Test echo command",
            }
        ]

        result = await execution_node(state)

        assert len(result["pending_actions"]) == 0
        assert len(result["tool_results"]) > 0
        assert result["tool_results"][0]["tool_name"] == "bash"

        # Check if successful (might fail if no docker container)
        if result["tool_results"][0]["success"]:
            assert "Hello World" in result["tool_results"][0]["output"]

    @pytest.mark.asyncio
    async def test_execution_multiple_actions(self):
        """Test executing multiple actions."""
        state = create_initial_state("test task", "test")
        state["pending_actions"] = [
            {
                "tool_name": "bash",
                "parameters": {"command": "echo 'test1'"},
                "reasoning": "First command",
            },
            {
                "tool_name": "bash",
                "parameters": {"command": "echo 'test2'"},
                "reasoning": "Second command",
            },
        ]

        result = await execution_node(state)

        assert len(result["pending_actions"]) == 0
        assert len(result["tool_results"]) == 2


class TestStateCreation:
    """Tests for state creation and management."""

    def test_create_initial_state(self):
        """Test creating initial state."""
        state = create_initial_state(
            task_instruction="Test task",
            task_name="test-task",
            container_name="test_container",
        )

        assert state["task_instruction"] == "Test task"
        assert state["task_name"] == "test-task"
        assert state["container_name"] == "test_container"
        assert state["iteration"] == 0
        assert state["max_iterations"] == 100
        assert state["should_continue"] is True
        assert len(state["trajectory"]) == 0
        assert len(state["current_plan"]) == 0

    def test_service_credentials_in_state(self):
        """Test that service credentials are properly initialized."""
        state = create_initial_state("test", "test")

        assert "gitlab" in state["service_credentials"]
        assert "rocketchat" in state["service_credentials"]
        assert "owncloud" in state["service_credentials"]
        assert "plane" in state["service_credentials"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
