# LangGraph Agent Implementation Roadmap
## For TheAgentCompany Benchmark with Local vLLM

**Version:** 1.0
**Last Updated:** 2025-10-29
**Status:** Planning Phase

---

## Executive Summary

This roadmap outlines the implementation of a LangGraph-based agent system that:
1. Connects to a locally hosted vLLM server for efficient, cost-effective inference
2. Integrates with TheAgentCompany benchmark (175 professional tasks)
3. Provides a modular, extensible architecture for agent development
4. Achieves competitive performance on real-world professional tasks

**Timeline:** 8-12 weeks
**Team Size:** 2-3 developers
**Key Technologies:** LangGraph, vLLM, Docker, Python, OpenAI-compatible APIs

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Phase 1: vLLM Setup & Integration](#phase-1-vllm-setup--integration)
3. [Phase 2: LangGraph Agent Architecture](#phase-2-langgraph-agent-architecture)
4. [Phase 3: TheAgentCompany Integration](#phase-3-theagentcompany-integration)
5. [Phase 4: Tool Implementation](#phase-4-tool-implementation)
6. [Phase 5: Testing & Optimization](#phase-5-testing--optimization)
7. [Phase 6: Full Benchmark Evaluation](#phase-6-full-benchmark-evaluation)
8. [Appendix](#appendix)

---

## Prerequisites

### Infrastructure Requirements

**Hardware:**
- GPU Server for vLLM:
  - NVIDIA GPU with 24GB+ VRAM (e.g., RTX 4090, A100, L4)
  - 64GB+ System RAM
  - 500GB+ SSD storage
- Evaluation Server:
  - 8+ CPU cores
  - 32GB+ RAM
  - 100GB+ disk space for Docker containers

**Software:**
- Docker & Docker Compose
- Python 3.10+
- CUDA 12.1+ (for GPU)
- Git
- Poetry (Python dependency management)

### Knowledge Requirements

- Python programming
- LangGraph/LangChain concepts (graphs, nodes, state)
- Docker containerization
- REST API integration
- LLM prompting and agent design

### Time Estimates

| Phase | Duration | Dependencies |
|-------|----------|--------------|
| Phase 1 | 1-2 weeks | None |
| Phase 2 | 2-3 weeks | Phase 1 |
| Phase 3 | 1-2 weeks | Phase 1, 2 |
| Phase 4 | 2-3 weeks | Phase 2, 3 |
| Phase 5 | 1-2 weeks | Phase 4 |
| Phase 6 | 1-2 weeks | Phase 5 |

---

## Phase 1: vLLM Setup & Integration

**Goal:** Deploy a production-ready vLLM server with OpenAI-compatible API and validate performance.

### 1.1 vLLM Installation

**Tasks:**
- [ ] Install vLLM on GPU server
- [ ] Select and download model (recommend: Qwen2.5-72B-Instruct, Llama-3.1-70B-Instruct)
- [ ] Configure vLLM server parameters
- [ ] Launch vLLM with OpenAI-compatible API server

**Implementation:**

```bash
# Install vLLM
pip install vllm

# Download model (example: Qwen2.5-72B-Instruct)
huggingface-cli download Qwen/Qwen2.5-72B-Instruct-AWQ

# Launch vLLM server with OpenAI API compatibility
vllm serve Qwen/Qwen2.5-72B-Instruct-AWQ \
  --host 0.0.0.0 \
  --port 8000 \
  --api-key "your-secret-key" \
  --tensor-parallel-size 1 \
  --gpu-memory-utilization 0.9 \
  --max-model-len 32768 \
  --enable-chunked-prefill
```

**Key Configuration Options:**
- `--tensor-parallel-size`: Number of GPUs for model parallelism
- `--gpu-memory-utilization`: GPU memory allocation (0.9 = 90%)
- `--max-model-len`: Maximum context length
- `--enable-chunked-prefill`: Improve throughput for long contexts

**Deliverables:**
- ✅ Running vLLM server accessible at `http://localhost:8000`
- ✅ OpenAI-compatible `/v1/chat/completions` endpoint
- ✅ Health check script validating model responses

### 1.2 vLLM Performance Testing

**Tasks:**
- [ ] Benchmark inference latency (time to first token, tokens/sec)
- [ ] Test context length handling (4K, 8K, 16K, 32K tokens)
- [ ] Measure throughput (requests/second)
- [ ] Validate function calling support (if using Qwen2.5/Llama 3.1)

**Test Script:**

```python
# vllm_test.py
import openai
import time

client = openai.OpenAI(
    base_url="http://localhost:8000/v1",
    api_key="your-secret-key"
)

# Test 1: Basic completion
start = time.time()
response = client.chat.completions.create(
    model="Qwen/Qwen2.5-72B-Instruct-AWQ",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a Python function to calculate Fibonacci numbers."}
    ],
    temperature=0.7,
    max_tokens=500
)
latency = time.time() - start
print(f"Latency: {latency:.2f}s")
print(f"Response: {response.choices[0].message.content}")

# Test 2: Long context (if needed for complex tasks)
# Test 3: Function calling (if supported)
```

**Success Criteria:**
- Latency < 5 seconds for first token
- Throughput > 20 tokens/second
- Successfully handles 16K+ context
- Function calling works (if applicable)

**Deliverables:**
- ✅ Performance benchmark report (latency, throughput, memory usage)
- ✅ Validated vLLM configuration for production use

### 1.3 LiteLLM Integration (Optional but Recommended)

**Why LiteLLM?**
- Unified API for switching between vLLM, OpenAI, Anthropic, etc.
- Built-in retry logic, rate limiting, cost tracking
- TheAgentCompany already uses LiteLLM for NPCs and evaluators

**Tasks:**
- [ ] Install LiteLLM proxy
- [ ] Configure LiteLLM to route to vLLM
- [ ] Add fallback models (e.g., OpenAI GPT-4 for critical tasks)

**Implementation:**

```bash
# Install LiteLLM
pip install litellm[proxy]

# Create config.yaml
cat > litellm_config.yaml << EOF
model_list:
  - model_name: qwen-local
    litellm_params:
      model: openai/Qwen/Qwen2.5-72B-Instruct-AWQ
      api_base: http://localhost:8000/v1
      api_key: your-secret-key

  - model_name: gpt-4-fallback
    litellm_params:
      model: gpt-4-turbo
      api_key: sk-...

router_settings:
  routing_strategy: simple-shuffle
  model_group_alias:
    agent-model: ["qwen-local", "gpt-4-fallback"]
EOF

# Launch LiteLLM proxy
litellm --config litellm_config.yaml --port 4000
```

**Deliverables:**
- ✅ LiteLLM proxy running at `http://localhost:4000`
- ✅ Configuration with vLLM primary + cloud fallback
- ✅ Test script validating routing logic

---

## Phase 2: LangGraph Agent Architecture

**Goal:** Design and implement a modular LangGraph agent with state management, tool calling, and reasoning capabilities.

### 2.1 Architecture Design

**Core Components:**

```
┌─────────────────────────────────────────────────────────────┐
│                   LangGraph Agent System                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌───────────┐      ┌──────────┐      ┌──────────────┐     │
│  │   Input   │─────▶│ Planning │─────▶│ Tool Calling │     │
│  │  Parser   │      │   Node   │      │     Node     │     │
│  └───────────┘      └──────────┘      └──────────────┘     │
│                           │                    │             │
│                           ▼                    ▼             │
│                    ┌──────────┐      ┌──────────────┐     │
│                    │ Routing  │◀─────│  Execution   │     │
│                    │   Node   │      │     Node     │     │
│                    └──────────┘      └──────────────┘     │
│                           │                    │             │
│                           ▼                    ▼             │
│                    ┌──────────┐      ┌──────────────┐     │
│                    │ Reflect  │      │  Trajectory  │     │
│                    │   Node   │      │   Logger     │     │
│                    └──────────┘      └──────────────┘     │
│                           │                                  │
│                           ▼                                  │
│                    ┌──────────┐                             │
│                    │  Output  │                             │
│                    │  Node    │                             │
│                    └──────────┘                             │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

**State Schema:**

```python
from typing import TypedDict, Annotated, Sequence
from langgraph.graph import add_messages

class AgentState(TypedDict):
    """The state of the agent at any point in time."""

    # Core conversation
    messages: Annotated[Sequence, add_messages]

    # Task information
    task_instruction: str
    task_name: str

    # Execution tracking
    current_plan: list[str]
    completed_steps: list[str]
    iteration: int
    max_iterations: int

    # Tool execution
    pending_actions: list[dict]
    tool_results: list[dict]

    # Environment state
    current_directory: str
    browser_state: dict
    service_credentials: dict

    # Trajectory for evaluation
    trajectory: list[dict]

    # Meta
    should_continue: bool
    error_message: str | None
```

**Node Definitions:**

1. **Planning Node**: Analyzes task and creates action plan
2. **Routing Node**: Decides next action (tool call, reflection, completion)
3. **Tool Calling Node**: Executes bash commands, API calls, browser actions
4. **Execution Node**: Runs tools and collects results
5. **Reflection Node**: Analyzes progress and adjusts strategy
6. **Output Node**: Formats final response and trajectory

**Deliverables:**
- ✅ Architecture diagram (detailed version)
- ✅ State schema documentation
- ✅ Node specification document

### 2.2 LangGraph Implementation

**Tasks:**
- [ ] Create project structure
- [ ] Implement state schema
- [ ] Implement core nodes
- [ ] Define graph flow with conditional edges
- [ ] Add checkpointing for state persistence

**Project Structure:**

```
langgraph_agent/
├── __init__.py
├── config.py              # Configuration (vLLM endpoint, credentials)
├── state.py               # AgentState definition
├── graph.py               # Main graph construction
├── nodes/
│   ├── __init__.py
│   ├── planning.py        # Planning node
│   ├── routing.py         # Routing logic
│   ├── tool_calling.py    # Tool call generation
│   ├── execution.py       # Tool execution
│   ├── reflection.py      # Self-reflection
│   └── output.py          # Output formatting
├── tools/
│   ├── __init__.py
│   ├── bash.py            # Shell command execution
│   ├── browser.py         # Web browser control (Playwright)
│   ├── gitlab.py          # GitLab API client
│   ├── rocketchat.py      # RocketChat API client
│   ├── owncloud.py        # ownCloud API client
│   ├── plane.py           # Plane API client
│   └── file_ops.py        # File read/write operations
├── utils/
│   ├── __init__.py
│   ├── llm_client.py      # vLLM/LiteLLM wrapper
│   ├── trajectory.py      # Trajectory logging
│   └── prompts.py         # Prompt templates
├── tests/
│   ├── test_graph.py
│   ├── test_nodes.py
│   └── test_tools.py
└── pyproject.toml         # Poetry dependencies
```

**Key Dependencies:**

```toml
[tool.poetry.dependencies]
python = "^3.10"
langgraph = "^0.2.0"
langchain = "^0.3.0"
langchain-openai = "^0.2.0"
openai = "^1.50.0"
playwright = "^1.48.0"
httpx = "^0.27.0"
pydantic = "^2.9.0"
python-dotenv = "^1.0.0"
```

**Core Graph Implementation:**

```python
# graph.py
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from .state import AgentState
from .nodes import (
    planning_node,
    routing_node,
    tool_calling_node,
    execution_node,
    reflection_node,
    output_node
)

def create_agent_graph():
    """Create the LangGraph agent workflow."""

    # Initialize graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("planning", planning_node)
    workflow.add_node("routing", routing_node)
    workflow.add_node("tool_calling", tool_calling_node)
    workflow.add_node("execution", execution_node)
    workflow.add_node("reflection", reflection_node)
    workflow.add_node("output", output_node)

    # Define edges
    workflow.set_entry_point("planning")

    workflow.add_edge("planning", "routing")

    workflow.add_conditional_edges(
        "routing",
        lambda state: route_decision(state),
        {
            "tool_call": "tool_calling",
            "reflect": "reflection",
            "complete": "output"
        }
    )

    workflow.add_edge("tool_calling", "execution")
    workflow.add_edge("execution", "reflection")
    workflow.add_edge("reflection", "routing")
    workflow.add_edge("output", END)

    # Compile with checkpointing
    memory = MemorySaver()
    graph = workflow.compile(checkpointer=memory)

    return graph

def route_decision(state: AgentState) -> str:
    """Decide next action based on current state."""
    if state["iteration"] >= state["max_iterations"]:
        return "complete"

    if state["should_continue"] is False:
        return "complete"

    # If no pending actions and plan is empty, reflect
    if not state["pending_actions"] and not state["current_plan"]:
        return "reflect"

    # If pending actions exist, execute tools
    if state["pending_actions"]:
        return "tool_call"

    # Default: reflect on progress
    return "reflect"
```

**Node Implementation Example (Planning):**

```python
# nodes/planning.py
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from ..state import AgentState
from ..utils.llm_client import get_llm_client

async def planning_node(state: AgentState) -> AgentState:
    """
    Analyze the task and create an initial action plan.
    """
    llm = get_llm_client()

    task_instruction = state["task_instruction"]

    system_prompt = """You are an expert AI agent capable of completing professional tasks.

Your capabilities include:
- Executing bash commands
- Browsing web pages
- Interacting with GitLab (code repos, issues, MRs)
- Sending messages via RocketChat
- Managing files in ownCloud
- Updating project tasks in Plane

Given a task instruction, create a step-by-step plan to complete it.
Be specific and actionable. Break complex tasks into smaller steps.

Output your plan as a numbered list."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"Task:\n{task_instruction}\n\nCreate a detailed plan:")
    ]

    response = await llm.ainvoke(messages)
    plan_text = response.content

    # Parse plan into list
    plan_steps = [
        line.strip()
        for line in plan_text.split("\n")
        if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith("-"))
    ]

    # Update state
    state["current_plan"] = plan_steps
    state["iteration"] = 0
    state["should_continue"] = True

    # Add to trajectory
    state["trajectory"].append({
        "step": "planning",
        "plan": plan_steps,
        "iteration": 0
    })

    return state
```

**Deliverables:**
- ✅ Complete LangGraph agent implementation
- ✅ Unit tests for each node
- ✅ Integration test for full graph flow
- ✅ Configuration file for vLLM connection

### 2.3 LLM Client Implementation

**Tasks:**
- [ ] Create unified LLM client supporting vLLM and fallbacks
- [ ] Implement retry logic and error handling
- [ ] Add streaming support (optional)
- [ ] Implement function calling wrapper

**Implementation:**

```python
# utils/llm_client.py
from langchain_openai import ChatOpenAI
from typing import Optional
import os

def get_llm_client(
    model: Optional[str] = None,
    temperature: float = 0.7,
    max_tokens: int = 2000
) -> ChatOpenAI:
    """
    Create an LLM client connected to vLLM or fallback.

    Args:
        model: Model name (defaults to env var LLM_MODEL)
        temperature: Sampling temperature
        max_tokens: Maximum tokens to generate

    Returns:
        ChatOpenAI: Configured LLM client
    """
    base_url = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
    api_key = os.getenv("VLLM_API_KEY", "dummy-key")
    model = model or os.getenv("LLM_MODEL", "Qwen/Qwen2.5-72B-Instruct-AWQ")

    return ChatOpenAI(
        base_url=base_url,
        api_key=api_key,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=120,
        max_retries=3
    )
```

**Deliverables:**
- ✅ LLM client utility with vLLM support
- ✅ Environment variable configuration
- ✅ Error handling and retry logic

---

## Phase 3: TheAgentCompany Integration

**Goal:** Integrate the LangGraph agent with TheAgentCompany benchmark infrastructure.

### 3.1 Understanding Evaluation Requirements

**Key Requirements:**
1. Task instruction input: Read from `/instruction/task.md`
2. Trajectory output: Write to `/outputs/traj_{task_name}.json`
3. Docker container execution: Agent runs inside task container
4. Service access: Connect to GitLab, RocketChat, ownCloud, Plane via `localhost`
5. Initialization: Run `/utils/init.sh` before starting

**Trajectory Format (Compatible with evaluators):**

```json
{
  "task_name": "example-task",
  "agent": "langgraph-vllm",
  "steps": [
    {
      "step_number": 1,
      "action": "bash",
      "command": "cd /workspace && ls -la",
      "output": "total 16\ndrwxr-xr-x ...",
      "timestamp": "2025-10-29T10:30:00Z"
    },
    {
      "step_number": 2,
      "action": "browser",
      "url": "http://localhost:8929/root/api-server",
      "observation": "GitLab project page loaded",
      "timestamp": "2025-10-29T10:30:15Z"
    }
  ],
  "final_state": "completed",
  "total_iterations": 42,
  "total_time_seconds": 180.5
}
```

**Deliverables:**
- ✅ Trajectory format specification
- ✅ Integration requirements documentation

### 3.2 Evaluation Harness Development

**Tasks:**
- [ ] Create wrapper script for running agent in task containers
- [ ] Implement trajectory logging to required format
- [ ] Build evaluation runner similar to `evaluation/run_eval.py`
- [ ] Add result aggregation and reporting

**Project Structure:**

```
evaluation_langgraph/
├── __init__.py
├── config.toml            # LLM configs for agent and environment
├── run_single_task.py     # Run agent on single task
├── run_eval.sh            # Run all 175 tasks
├── aggregate_results.py   # Analyze results
└── README.md
```

**Single Task Runner:**

```python
# evaluation_langgraph/run_single_task.py
import asyncio
import json
import subprocess
import sys
from pathlib import Path
from datetime import datetime
from langgraph_agent.graph import create_agent_graph
from langgraph_agent.state import AgentState

async def run_task(
    task_image: str,
    task_name: str,
    output_dir: Path,
    server_hostname: str = "localhost",
    max_iterations: int = 100
):
    """
    Run the LangGraph agent on a single TheAgentCompany task.

    Args:
        task_image: Docker image name (e.g., ghcr.io/theagentcompany/example-image:1.0.0)
        task_name: Task identifier (e.g., "example")
        output_dir: Directory to save outputs
        server_hostname: Hostname for services (default: localhost)
        max_iterations: Maximum agent iterations
    """

    print(f"[INFO] Starting task: {task_name}")
    print(f"[INFO] Image: {task_image}")

    # Step 1: Start container
    container_name = f"tac_{task_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"[INFO] Starting container: {container_name}")

    subprocess.run([
        "docker", "run",
        "--name", container_name,
        "--network", "host",
        "-d",
        task_image,
        "sleep", "infinity"
    ], check=True)

    try:
        # Step 2: Initialize environment
        print("[INFO] Initializing task environment...")
        init_cmd = f"""
        SERVER_HOSTNAME={server_hostname} \
        LITELLM_API_KEY={os.getenv('ENV_LLM_API_KEY')} \
        LITELLM_BASE_URL={os.getenv('ENV_LLM_BASE_URL')} \
        LITELLM_MODEL={os.getenv('ENV_LLM_MODEL')} \
        bash /utils/init.sh
        """
        subprocess.run([
            "docker", "exec", container_name,
            "bash", "-c", init_cmd
        ], check=True)

        # Step 3: Read task instruction
        print("[INFO] Reading task instruction...")
        result = subprocess.run([
            "docker", "exec", container_name,
            "cat", "/instruction/task.md"
        ], capture_output=True, text=True, check=True)
        task_instruction = result.stdout

        # Step 4: Run agent
        print("[INFO] Running LangGraph agent...")
        graph = create_agent_graph()

        initial_state = AgentState(
            messages=[],
            task_instruction=task_instruction,
            task_name=task_name,
            current_plan=[],
            completed_steps=[],
            iteration=0,
            max_iterations=max_iterations,
            pending_actions=[],
            tool_results=[],
            current_directory="/workspace",
            browser_state={},
            service_credentials={
                "gitlab": {"url": f"http://{server_hostname}:8929", "user": "root", "password": "theagentcompany"},
                "rocketchat": {"url": f"http://{server_hostname}:3000", "user": "theagentcompany", "password": "theagentcompany"},
                "owncloud": {"url": f"http://{server_hostname}:8092", "user": "theagentcompany", "password": "theagentcompany"},
                "plane": {"url": f"http://{server_hostname}:8091", "email": "agent@company.com", "password": "theagentcompany"}
            },
            trajectory=[],
            should_continue=True,
            error_message=None,
            container_name=container_name  # Pass container for tool execution
        )

        # Execute graph
        final_state = await graph.ainvoke(initial_state)

        # Step 5: Save trajectory
        trajectory_path = output_dir / f"traj_{task_name}.json"
        with open(trajectory_path, "w") as f:
            json.dump({
                "task_name": task_name,
                "agent": "langgraph-vllm",
                "trajectory": final_state["trajectory"],
                "total_iterations": final_state["iteration"],
                "completed_steps": final_state["completed_steps"]
            }, f, indent=2)

        print(f"[INFO] Trajectory saved to: {trajectory_path}")

        # Step 6: Run evaluation
        print("[INFO] Running evaluation...")
        eval_cmd = f"""
        LITELLM_API_KEY={os.getenv('ENV_LLM_API_KEY')} \
        LITELLM_BASE_URL={os.getenv('ENV_LLM_BASE_URL')} \
        LITELLM_MODEL={os.getenv('ENV_LLM_MODEL')} \
        DECRYPTION_KEY='theagentcompany is all you need' \
        python_default /utils/eval.py \
        --trajectory_path /outputs/traj_{task_name}.json \
        --result_path /outputs/eval_{task_name}.json
        """

        # Copy trajectory to container
        subprocess.run([
            "docker", "cp",
            str(trajectory_path),
            f"{container_name}:/outputs/traj_{task_name}.json"
        ], check=True)

        # Run evaluation
        subprocess.run([
            "docker", "exec", container_name,
            "bash", "-c", eval_cmd
        ], check=True)

        # Copy evaluation result back
        eval_path = output_dir / f"eval_{task_name}.json"
        subprocess.run([
            "docker", "cp",
            f"{container_name}:/outputs/eval_{task_name}.json",
            str(eval_path)
        ], check=True)

        # Read and display results
        with open(eval_path) as f:
            results = json.load(f)

        final_score = results["final_score"]
        print(f"[SUCCESS] Task completed!")
        print(f"[RESULT] Score: {final_score['result']}/{final_score['total']}")

        return results

    finally:
        # Cleanup: Stop and remove container
        print(f"[INFO] Cleaning up container: {container_name}")
        subprocess.run(["docker", "stop", container_name], check=False)
        subprocess.run(["docker", "rm", container_name], check=False)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run LangGraph agent on TheAgentCompany task")
    parser.add_argument("--task-image", required=True, help="Task Docker image")
    parser.add_argument("--task-name", required=True, help="Task name")
    parser.add_argument("--output-dir", default="./outputs", help="Output directory")
    parser.add_argument("--server-hostname", default="localhost", help="Services hostname")
    parser.add_argument("--max-iterations", type=int, default=100, help="Max iterations")

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    asyncio.run(run_task(
        task_image=args.task_image,
        task_name=args.task_name,
        output_dir=output_dir,
        server_hostname=args.server_hostname,
        max_iterations=args.max_iterations
    ))
```

**Batch Runner Script:**

```bash
#!/bin/bash
# evaluation_langgraph/run_eval.sh

set -e

OUTPUTS_PATH=${OUTPUTS_PATH:-"./outputs"}
SERVER_HOSTNAME=${SERVER_HOSTNAME:-"localhost"}
VERSION=${VERSION:-"1.0.0"}
MAX_ITERATIONS=${MAX_ITERATIONS:-100}

# Load task list
TASK_LIST=(
    "ghcr.io/theagentcompany/example-image:${VERSION}"
    "ghcr.io/theagentcompany/sde-find-answer-in-codebase:${VERSION}"
    # ... (all 175 tasks)
)

mkdir -p "$OUTPUTS_PATH"

echo "[INFO] Starting TheAgentCompany evaluation with LangGraph agent"
echo "[INFO] Total tasks: ${#TASK_LIST[@]}"
echo "[INFO] Output directory: $OUTPUTS_PATH"

for task_image in "${TASK_LIST[@]}"; do
    # Extract task name from image
    task_name=$(echo "$task_image" | sed 's/.*\/\(.*\):.*/\1/')

    echo "========================================"
    echo "[INFO] Running task: $task_name"
    echo "========================================"

    python run_single_task.py \
        --task-image "$task_image" \
        --task-name "$task_name" \
        --output-dir "$OUTPUTS_PATH" \
        --server-hostname "$SERVER_HOSTNAME" \
        --max-iterations "$MAX_ITERATIONS" \
        || echo "[ERROR] Task $task_name failed"

    echo ""
done

echo "[INFO] Evaluation complete!"
echo "[INFO] Aggregating results..."

python aggregate_results.py "$OUTPUTS_PATH"
```

**Deliverables:**
- ✅ Single task runner script
- ✅ Batch evaluation script
- ✅ Configuration file for LLM endpoints
- ✅ Result aggregation tool

### 3.3 Docker Integration

**Tasks:**
- [ ] Create Dockerfile for LangGraph agent
- [ ] Build agent image with all dependencies
- [ ] Test agent image with example task

**Dockerfile:**

```dockerfile
# Dockerfile
FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    jq \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy project files
COPY pyproject.toml poetry.lock ./
COPY langgraph_agent/ ./langgraph_agent/
COPY evaluation_langgraph/ ./evaluation_langgraph/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-dev --no-interaction --no-ansi

# Install Playwright browsers
RUN playwright install chromium
RUN playwright install-deps chromium

# Set environment variables
ENV PYTHONPATH=/app
ENV VLLM_BASE_URL=http://localhost:8000/v1

# Default command
CMD ["bash"]
```

**Deliverables:**
- ✅ Dockerfile for agent deployment
- ✅ Docker Compose configuration (optional)
- ✅ Build and deployment instructions

---

## Phase 4: Tool Implementation

**Goal:** Implement all necessary tools for TheAgentCompany tasks.

### 4.1 Core Tools

**Required Tool Categories:**

1. **Shell/Bash** - Execute terminal commands
2. **Browser** - Web navigation and interaction
3. **File Operations** - Read, write, edit files
4. **GitLab API** - Code repos, issues, merge requests
5. **RocketChat API** - Team communication
6. **ownCloud API** - File sharing
7. **Plane API** - Project management

### 4.2 Bash Tool

```python
# tools/bash.py
import subprocess
from typing import Dict, Any

def execute_bash(
    command: str,
    container_name: str,
    working_dir: str = "/workspace",
    timeout: int = 60
) -> Dict[str, Any]:
    """
    Execute a bash command inside the task container.

    Args:
        command: Bash command to execute
        container_name: Docker container name
        working_dir: Working directory for command
        timeout: Command timeout in seconds

    Returns:
        Dict with stdout, stderr, return_code
    """
    try:
        # Execute command in container
        result = subprocess.run(
            [
                "docker", "exec",
                "-w", working_dir,
                container_name,
                "bash", "-c", command
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "command": command
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "return_code": -1,
            "command": command
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "return_code": -1,
            "command": command
        }
```

### 4.3 Browser Tool (Playwright)

```python
# tools/browser.py
from playwright.async_api import async_playwright, Page, Browser
from typing import Optional, Dict, Any
import asyncio

class BrowserTool:
    """Browser automation tool using Playwright."""

    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None

    async def start(self):
        """Initialize browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=True)
        context = await self.browser.new_context(
            viewport={"width": 1280, "height": 720}
        )
        self.page = await context.new_page()

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to URL."""
        if not self.page:
            await self.start()

        try:
            await self.page.goto(url, wait_until="networkidle", timeout=30000)

            # Take screenshot
            screenshot = await self.page.screenshot()

            # Get page text
            text_content = await self.page.inner_text("body")

            return {
                "success": True,
                "url": self.page.url,
                "title": await self.page.title(),
                "text": text_content[:2000],  # Limit for LLM context
                "screenshot": screenshot  # Binary data
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def click(self, selector: str) -> Dict[str, Any]:
        """Click element by selector."""
        try:
            await self.page.click(selector, timeout=10000)
            await self.page.wait_for_load_state("networkidle")

            return {
                "success": True,
                "url": self.page.url
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def fill_form(self, selector: str, value: str) -> Dict[str, Any]:
        """Fill form field."""
        try:
            await self.page.fill(selector, value)
            return {"success": True}
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    async def close(self):
        """Close browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
```

### 4.4 GitLab API Tool

```python
# tools/gitlab.py
import httpx
from typing import List, Dict, Any, Optional

class GitLabTool:
    """GitLab API client for TheAgentCompany."""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.token: Optional[str] = None
        self.client = httpx.AsyncClient(verify=False, timeout=30.0)

    async def authenticate(self):
        """Get personal access token."""
        # In TheAgentCompany, token might be pre-configured
        # or we use session-based auth
        response = await self.client.post(
            f"{self.base_url}/api/v4/session",
            data={"login": self.username, "password": self.password}
        )
        response.raise_for_status()
        self.token = response.json().get("private_token")

    async def list_projects(self) -> List[Dict[str, Any]]:
        """List all projects."""
        if not self.token:
            await self.authenticate()

        response = await self.client.get(
            f"{self.base_url}/api/v4/projects",
            headers={"PRIVATE-TOKEN": self.token}
        )
        response.raise_for_status()
        return response.json()

    async def get_file(self, project_id: int, file_path: str, ref: str = "main") -> str:
        """Get file contents from repository."""
        response = await self.client.get(
            f"{self.base_url}/api/v4/projects/{project_id}/repository/files/{file_path.replace('/', '%2F')}/raw",
            headers={"PRIVATE-TOKEN": self.token},
            params={"ref": ref}
        )
        response.raise_for_status()
        return response.text

    async def create_merge_request(
        self,
        project_id: int,
        source_branch: str,
        target_branch: str,
        title: str,
        description: str = ""
    ) -> Dict[str, Any]:
        """Create a merge request."""
        response = await self.client.post(
            f"{self.base_url}/api/v4/projects/{project_id}/merge_requests",
            headers={"PRIVATE-TOKEN": self.token},
            json={
                "source_branch": source_branch,
                "target_branch": target_branch,
                "title": title,
                "description": description
            }
        )
        response.raise_for_status()
        return response.json()
```

### 4.5 RocketChat API Tool

```python
# tools/rocketchat.py
import httpx
from typing import List, Dict, Any, Optional

class RocketChatTool:
    """RocketChat API client for TheAgentCompany."""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.auth_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def login(self):
        """Login to RocketChat."""
        response = await self.client.post(
            f"{self.base_url}/api/v1/login",
            json={"username": self.username, "password": self.password}
        )
        response.raise_for_status()
        data = response.json()["data"]
        self.auth_token = data["authToken"]
        self.user_id = data["userId"]

    def _headers(self) -> Dict[str, str]:
        """Get auth headers."""
        return {
            "X-Auth-Token": self.auth_token,
            "X-User-Id": self.user_id
        }

    async def get_channels(self) -> List[Dict[str, Any]]:
        """List all channels."""
        if not self.auth_token:
            await self.login()

        response = await self.client.get(
            f"{self.base_url}/api/v1/channels.list",
            headers=self._headers()
        )
        response.raise_for_status()
        return response.json()["channels"]

    async def get_channel_history(
        self,
        room_id: str,
        count: int = 50
    ) -> List[Dict[str, Any]]:
        """Get channel message history."""
        response = await self.client.get(
            f"{self.base_url}/api/v1/channels.history",
            headers=self._headers(),
            params={"roomId": room_id, "count": count}
        )
        response.raise_for_status()
        return response.json()["messages"]

    async def send_message(self, room_id: str, text: str) -> Dict[str, Any]:
        """Send message to channel."""
        response = await self.client.post(
            f"{self.base_url}/api/v1/chat.postMessage",
            headers=self._headers(),
            json={"roomId": room_id, "text": text}
        )
        response.raise_for_status()
        return response.json()
```

### 4.6 Tool Registry

```python
# tools/__init__.py
from typing import Dict, Callable, Any
from .bash import execute_bash
from .browser import BrowserTool
from .gitlab import GitLabTool
from .rocketchat import RocketChatTool
# ... other tools

class ToolRegistry:
    """Central registry for all agent tools."""

    def __init__(self, container_name: str, service_credentials: Dict[str, Any]):
        self.container_name = container_name
        self.credentials = service_credentials

        # Initialize tools
        self.browser = BrowserTool()
        self.gitlab = GitLabTool(**service_credentials["gitlab"])
        self.rocketchat = RocketChatTool(**service_credentials["rocketchat"])
        # ... other tools

    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """
        Call a tool by name with arguments.

        Args:
            tool_name: Name of tool to call
            **kwargs: Tool-specific arguments

        Returns:
            Tool execution result
        """
        if tool_name == "bash":
            return execute_bash(
                command=kwargs["command"],
                container_name=self.container_name,
                working_dir=kwargs.get("working_dir", "/workspace")
            )

        elif tool_name == "browser_navigate":
            return await self.browser.navigate(kwargs["url"])

        elif tool_name == "browser_click":
            return await self.browser.click(kwargs["selector"])

        elif tool_name == "gitlab_list_projects":
            return await self.gitlab.list_projects()

        elif tool_name == "rocketchat_send_message":
            return await self.rocketchat.send_message(
                kwargs["room_id"],
                kwargs["text"]
            )

        # ... more tools

        else:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}"
            }

    async def cleanup(self):
        """Cleanup resources."""
        await self.browser.close()
        await self.gitlab.client.aclose()
        await self.rocketchat.client.aclose()
```

**Deliverables:**
- ✅ Bash tool implementation
- ✅ Browser tool implementation (Playwright)
- ✅ GitLab API client
- ✅ RocketChat API client
- ✅ ownCloud API client (similar to GitLab)
- ✅ Plane API client (similar to GitLab)
- ✅ File operations tool
- ✅ Tool registry and dispatcher
- ✅ Unit tests for each tool

---

## Phase 5: Testing & Optimization

**Goal:** Validate agent performance and optimize for TheAgentCompany tasks.

### 5.1 Unit Testing

**Tasks:**
- [ ] Write tests for each node
- [ ] Test tool execution in isolation
- [ ] Validate state transitions
- [ ] Test error handling

**Example Test:**

```python
# tests/test_nodes.py
import pytest
from langgraph_agent.nodes.planning import planning_node
from langgraph_agent.state import AgentState

@pytest.mark.asyncio
async def test_planning_node():
    """Test planning node creates valid plan."""

    state = AgentState(
        messages=[],
        task_instruction="Find all Python files in /workspace and count lines of code.",
        task_name="test-task",
        current_plan=[],
        completed_steps=[],
        iteration=0,
        max_iterations=100,
        pending_actions=[],
        tool_results=[],
        current_directory="/workspace",
        browser_state={},
        service_credentials={},
        trajectory=[],
        should_continue=True,
        error_message=None
    )

    result = await planning_node(state)

    # Assertions
    assert len(result["current_plan"]) > 0
    assert result["iteration"] == 0
    assert result["should_continue"] is True
    assert len(result["trajectory"]) == 1
    assert result["trajectory"][0]["step"] == "planning"
```

### 5.2 Integration Testing

**Tasks:**
- [ ] Run agent on example task
- [ ] Validate trajectory output format
- [ ] Test evaluation pipeline
- [ ] Verify score calculation

**Example Task Test:**

```bash
# Run on example task
python evaluation_langgraph/run_single_task.py \
    --task-image ghcr.io/theagentcompany/example-image:1.0.0 \
    --task-name example \
    --output-dir ./test_outputs

# Expected output:
# [SUCCESS] Task completed!
# [RESULT] Score: 4/5 (80%)
```

### 5.3 Performance Testing

**Metrics to Track:**
- Task completion rate (%)
- Average score per task
- Iterations per task
- Time per task
- Token usage
- Error rate

**Test Suite:**

```python
# tests/test_performance.py
import pytest
from pathlib import Path
import json

# Test on 10 diverse tasks
SAMPLE_TASKS = [
    "example",
    "sde-find-answer-in-codebase",
    "pm-create-plan",
    # ... 7 more
]

@pytest.mark.slow
@pytest.mark.parametrize("task_name", SAMPLE_TASKS)
async def test_task_completion(task_name):
    """Test agent can complete task within iteration limit."""

    # Run task
    result = await run_task(...)

    # Check score
    assert result["final_score"]["result"] > 0, f"Task {task_name} scored 0"

    # Check iterations
    assert result["total_iterations"] <= 100, f"Task {task_name} exceeded iteration limit"
```

### 5.4 Prompt Optimization

**Tasks:**
- [ ] A/B test different system prompts
- [ ] Optimize few-shot examples
- [ ] Test different reasoning strategies (ReAct, CoT, Reflexion)
- [ ] Tune temperature and sampling parameters

**Prompt Engineering Tips:**
- Be explicit about available tools and their usage
- Include examples of successful task completions
- Emphasize the importance of verification steps
- Encourage breaking down complex tasks
- Remind agent to check work before marking tasks complete

### 5.5 Error Analysis

**Tasks:**
- [ ] Categorize failure modes
- [ ] Identify common mistakes
- [ ] Add error recovery strategies
- [ ] Implement retry logic

**Common Failure Patterns:**
- Incorrect bash commands (syntax errors)
- Navigation failures (wrong URLs)
- API authentication issues
- Timeout errors
- Incomplete task execution

**Deliverables:**
- ✅ Complete test suite (unit + integration)
- ✅ Performance benchmark report on sample tasks
- ✅ Optimized prompts and hyperparameters
- ✅ Error analysis and mitigation strategies

---

## Phase 6: Full Benchmark Evaluation

**Goal:** Run complete evaluation on all 175 tasks and analyze results.

### 6.1 Full Evaluation Run

**Prerequisites:**
- All services running (GitLab, RocketChat, ownCloud, Plane)
- vLLM server stable and responsive
- Sufficient compute resources (expect 24-48 hours runtime)

**Execution:**

```bash
# Set environment variables
export VLLM_BASE_URL=http://localhost:8000/v1
export VLLM_API_KEY=your-secret-key
export LLM_MODEL=Qwen/Qwen2.5-72B-Instruct-AWQ
export ENV_LLM_API_KEY=sk-...
export ENV_LLM_BASE_URL=https://api.openai.com/v1
export ENV_LLM_MODEL=gpt-4o

# Run evaluation
cd evaluation_langgraph
bash run_eval.sh
```

**Monitoring:**
- Track progress (tasks completed / 175)
- Monitor vLLM server load
- Watch for errors or crashes
- Log resource usage (GPU, RAM, disk)

### 6.2 Result Analysis

**Tasks:**
- [ ] Aggregate scores across all tasks
- [ ] Calculate category-wise performance
- [ ] Compare with baseline (OpenHands)
- [ ] Identify strengths and weaknesses

**Analysis Script:**

```python
# evaluation_langgraph/aggregate_results.py
import json
from pathlib import Path
from collections import defaultdict
import pandas as pd

def analyze_results(output_dir: Path):
    """Analyze evaluation results from all tasks."""

    results = []

    for eval_file in output_dir.glob("eval_*.json"):
        with open(eval_file) as f:
            data = json.load(f)

        task_name = eval_file.stem.replace("eval_", "")
        category = task_name.split("-")[0]  # e.g., "sde", "pm", "ds"

        final_score = data["final_score"]

        results.append({
            "task": task_name,
            "category": category,
            "score": final_score["result"],
            "total": final_score["total"],
            "percentage": (final_score["result"] / final_score["total"] * 100) if final_score["total"] > 0 else 0
        })

    df = pd.DataFrame(results)

    # Overall statistics
    print("=" * 50)
    print("OVERALL RESULTS")
    print("=" * 50)
    print(f"Total tasks: {len(df)}")
    print(f"Average score: {df['percentage'].mean():.2f}%")
    print(f"Perfect scores: {len(df[df['percentage'] == 100])}")
    print(f"Partial scores: {len(df[(df['percentage'] > 0) & (df['percentage'] < 100)])}")
    print(f"Failed (0%): {len(df[df['percentage'] == 0])}")
    print()

    # Category breakdown
    print("=" * 50)
    print("CATEGORY BREAKDOWN")
    print("=" * 50)
    category_stats = df.groupby("category")["percentage"].agg(["mean", "count"])
    print(category_stats)
    print()

    # Top 10 best performing tasks
    print("=" * 50)
    print("TOP 10 TASKS")
    print("=" * 50)
    print(df.nlargest(10, "percentage")[["task", "percentage"]])
    print()

    # Bottom 10 worst performing tasks
    print("=" * 50)
    print("BOTTOM 10 TASKS")
    print("=" * 50)
    print(df.nsmallest(10, "percentage")[["task", "percentage"]])

    # Save report
    df.to_csv(output_dir / "results_summary.csv", index=False)
    print(f"\nFull results saved to: {output_dir / 'results_summary.csv'}")

if __name__ == "__main__":
    import sys
    output_dir = Path(sys.argv[1])
    analyze_results(output_dir)
```

### 6.3 Comparison with Baselines

**Baseline Results** (from leaderboard):
- Claude-3.5-Sonnet (OpenHands): ~24% average score
- GPT-4o (OpenHands): ~20% average score

**Target Performance:**
- Minimum: 15% (proof of concept works)
- Good: 20% (comparable to baselines)
- Excellent: 25%+ (exceeds baselines)

**Comparison Metrics:**
- Overall average score
- Category-wise performance
- Task completion rate
- Perfect score rate

### 6.4 Leaderboard Submission

**Submission Requirements:**
1. Agent name and description
2. Model information (vLLM, base model)
3. Complete evaluation results (175 tasks)
4. Agent code repository (GitHub)
5. Reproduction instructions

**Leaderboard URL:** https://the-agent-company.com/#/leaderboard

**Deliverables:**
- ✅ Complete evaluation results (175 tasks)
- ✅ Performance analysis report
- ✅ Comparison with baselines
- ✅ Leaderboard submission (optional)
- ✅ Final documentation and reproduction guide

---

## Appendix

### A. Recommended Models for vLLM

| Model | Size | VRAM | Strengths |
|-------|------|------|-----------|
| Qwen2.5-72B-Instruct-AWQ | 72B (quantized) | 24GB | Strong coding, function calling, multilingual |
| Llama-3.1-70B-Instruct-AWQ | 70B (quantized) | 24GB | Good reasoning, broad knowledge |
| Mixtral-8x22B-Instruct-v0.1 | 141B (MoE) | 48GB | Excellent coding, very fast |
| DeepSeek-Coder-V2-Instruct | 236B (MoE) | 80GB | Best for coding tasks |

**Recommendation:** Start with **Qwen2.5-72B-Instruct-AWQ** for best balance of performance and resource requirements.

### B. Estimated Costs

**Infrastructure:**
- GPU server (cloud): $2-5/hour
- Evaluation server: $0.50/hour
- Storage: $0.10/GB/month

**Full benchmark run:**
- vLLM inference: $50-150 (depending on model and runtime)
- Environment LLM (for NPCs): $20-50 (OpenAI API)
- Total: ~$100-200 per full run

**Development:**
- ~$500-1000 total (multiple test runs, debugging)

Compare to pure cloud API costs:
- Claude-3.5-Sonnet: ~$3000+ per full benchmark run

### C. Troubleshooting Guide

**Issue: vLLM out of memory**
- Solution: Reduce `--gpu-memory-utilization` or use smaller model

**Issue: Agent gets stuck in loops**
- Solution: Add iteration limits, improve reflection node logic

**Issue: Tasks timeout**
- Solution: Increase timeout values, optimize tool execution

**Issue: Poor performance on coding tasks**
- Solution: Use coding-specialized model (DeepSeek-Coder, Qwen2.5)

**Issue: Service connection failures**
- Solution: Verify services running, check `SERVER_HOSTNAME` configuration

### D. Resources and References

**Documentation:**
- LangGraph: https://langchain-ai.github.io/langgraph/
- vLLM: https://docs.vllm.ai/
- TheAgentCompany: https://the-agent-company.com/

**Papers:**
- TheAgentCompany: https://arxiv.org/abs/2412.14161
- ReAct: https://arxiv.org/abs/2210.03629
- Reflexion: https://arxiv.org/abs/2303.11366

**Code Examples:**
- OpenHands baseline: https://github.com/TheAgentCompany/TheAgentCompany/tree/main/evaluation
- LangGraph examples: https://github.com/langchain-ai/langgraph/tree/main/examples

### E. Success Metrics

**Phase 1 Complete:**
- ✅ vLLM server running stably
- ✅ Sub-5s latency, 20+ tokens/sec throughput

**Phase 2 Complete:**
- ✅ LangGraph agent executes tasks end-to-end
- ✅ State management working correctly
- ✅ All nodes tested

**Phase 3 Complete:**
- ✅ Agent runs in TheAgentCompany containers
- ✅ Trajectories saved in correct format
- ✅ Evaluations run successfully

**Phase 4 Complete:**
- ✅ All 7 tool categories implemented
- ✅ Tools work in integration tests
- ✅ Error handling robust

**Phase 5 Complete:**
- ✅ 10+ sample tasks passing
- ✅ Average score > 15%
- ✅ Prompts optimized

**Phase 6 Complete:**
- ✅ 175 tasks evaluated
- ✅ Results analyzed and documented
- ✅ Comparison with baselines complete

---

## Conclusion

This roadmap provides a comprehensive path from zero to a fully functional LangGraph-based agent evaluated on TheAgentCompany benchmark. By following these phases systematically, you will:

1. Build a cost-effective agent using local vLLM inference
2. Leverage LangGraph's powerful state management and workflow capabilities
3. Integrate seamlessly with TheAgentCompany's evaluation infrastructure
4. Achieve competitive performance on real-world professional tasks

The modular architecture allows for continuous improvement through prompt engineering, tool enhancement, and reasoning strategy refinement.

**Next Steps:**
1. Review and approve this roadmap
2. Set up development environment
3. Begin Phase 1: vLLM Setup & Integration

Good luck with the implementation!
