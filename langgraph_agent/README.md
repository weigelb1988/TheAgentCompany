# LangGraph Agent for TheAgentCompany

A modular LangGraph-based agent system that connects to locally hosted vLLM and integrates with TheAgentCompany benchmark for evaluating LLM agents on real-world professional tasks.

## Architecture

The agent follows a ReAct-style loop with planning and reflection:

```
┌─────────────┐
│  Planning   │  Create initial action plan
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Routing   │  Decide next action
└──────┬──────┘
       │
       ├──────► Tool Calling ──► Execution ──► Reflection ──┐
       │                                                     │
       ├──────► Reflection ◄───────────────────────────────┘
       │           │
       │           └─────► Routing (loop back)
       │
       └──────► Output (if complete)
```

### Nodes

1. **Planning Node** - Analyzes task and creates step-by-step plan
2. **Routing Node** - Determines next action (tool call, reflect, or complete)
3. **Tool Calling Node** - Generates structured tool calls based on state
4. **Execution Node** - Executes pending tool calls and logs results
5. **Reflection Node** - Reviews progress and adjusts strategy
6. **Output Node** - Formats final summary and results

## Installation

### Using Poetry (Recommended)

```bash
cd langgraph_agent
poetry install
```

### Using pip

```bash
cd langgraph_agent
pip install -e .
```

## Configuration

Create a `.env` file or set environment variables:

```bash
# vLLM Configuration
VLLM_BASE_URL=http://localhost:8000/v1
VLLM_API_KEY=your-secret-key
LLM_MODEL=Qwen/Qwen2.5-72B-Instruct-AWQ

# Agent Configuration
MAX_ITERATIONS=100
ENABLE_REFLECTION=true

# TheAgentCompany Services
SERVER_HOSTNAME=localhost
```

## Usage

### Basic Example

```python
from langgraph_agent import create_agent_graph, create_initial_state

# Create the agent graph
graph = create_agent_graph()

# Create initial state for a task
initial_state = create_initial_state(
    task_instruction="Complete the task in /instruction/task.md",
    task_name="example-task",
    container_name="task_container",
)

# Run the agent
result = await graph.ainvoke(initial_state)

# Access results
print(f"Completed {len(result['completed_steps'])} steps")
print(f"Trajectory: {result['trajectory']}")
```

### With TheAgentCompany Integration

```python
from langgraph_agent import create_agent_graph, create_initial_state
import json

# Read task instruction from container
task_instruction = open("/instruction/task.md").read()

# Initialize state
state = create_initial_state(
    task_instruction=task_instruction,
    task_name="sde-find-bug",
    container_name="tac_task_container",
)

# Run agent
graph = create_agent_graph()
final_state = await graph.ainvoke(state)

# Save trajectory for evaluation
with open("/outputs/traj_sde-find-bug.json", "w") as f:
    json.dump({
        "task_name": "sde-find-bug",
        "agent": "langgraph-vllm",
        "trajectory": final_state["trajectory"],
        "total_iterations": final_state["iteration"]
    }, f, indent=2)
```

## Tools

Current tools (Phase 2):
- `bash` - Execute shell commands
- `file_read` - Read file contents
- `file_write` - Write file contents

Coming in Phase 4:
- Browser automation (Playwright)
- GitLab API
- RocketChat API
- ownCloud API
- Plane API

## Testing

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/test_nodes.py

# Run with coverage
poetry run pytest --cov=langgraph_agent
```

## Development

### Project Structure

```
langgraph_agent/
├── __init__.py
├── config.py              # Configuration settings
├── state.py               # AgentState schema
├── graph.py               # Main graph construction
├── nodes/
│   ├── planning.py        # Planning node
│   ├── routing.py         # Routing logic
│   ├── tool_calling.py    # Tool call generation
│   ├── execution.py       # Tool execution
│   ├── reflection.py      # Self-reflection
│   └── output.py          # Output formatting
├── tools/
│   ├── bash.py            # Shell commands
│   └── registry.py        # Tool registry
├── utils/
│   ├── llm_client.py      # vLLM client
│   ├── prompts.py         # Prompt templates
│   └── trajectory.py      # Trajectory logging
└── tests/
    └── test_nodes.py      # Unit tests
```

### Adding New Tools

1. Create tool implementation in `tools/`
2. Register in `tools/registry.py`
3. Update `TOOL_CALLING_PROMPT` in `utils/prompts.py`
4. Add tool-specific trajectory logging in `utils/trajectory.py`

Example:

```python
# tools/my_tool.py
async def my_tool(param1: str, param2: int) -> dict:
    # Implementation
    return {"success": True, "result": "..."}

# tools/registry.py
class ToolRegistry:
    async def _call_my_tool(self, params: dict) -> dict:
        result = await my_tool(
            param1=params.get("param1"),
            param2=params.get("param2")
        )
        return result
```

## Visualizing the Graph

```python
from langgraph_agent import visualize_graph

# Generate graph visualization
visualize_graph("my_graph.png")
```

## Performance Tips

1. **Adjust temperature** for different tasks (0.7 for creative, 0.3 for deterministic)
2. **Enable reflection** for complex tasks, disable for simple ones
3. **Tune max_iterations** based on task complexity
4. **Use checkpointing** for long-running tasks (enables resumption)

## License

MIT License - see LICENSE file for details
