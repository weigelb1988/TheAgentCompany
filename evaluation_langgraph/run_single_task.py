#!/usr/bin/env python3
"""
Single task runner for LangGraph agent on TheAgentCompany benchmark.

This script runs the LangGraph agent on a single task and evaluates the results.
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from datetime import datetime
import argparse

# Add parent directory to path to import langgraph_agent
sys.path.insert(0, str(Path(__file__).parent.parent))

from langgraph_agent import create_agent_graph, create_initial_state


async def run_task(
    task_image: str,
    task_name: str,
    output_dir: Path,
    server_hostname: str = "localhost",
    max_iterations: int = 100,
    cleanup: bool = True,
):
    """
    Run the LangGraph agent on a single TheAgentCompany task.

    Args:
        task_image: Docker image name (e.g., ghcr.io/theagentcompany/example-image:1.0.0)
        task_name: Task identifier (e.g., "example")
        output_dir: Directory to save outputs
        server_hostname: Hostname for services (default: localhost)
        max_iterations: Maximum agent iterations
        cleanup: Whether to cleanup container after completion

    Returns:
        Dict with evaluation results
    """

    print(f"{'='*70}")
    print(f"Running Task: {task_name}")
    print(f"{'='*70}")
    print(f"Image: {task_image}")
    print(f"Output: {output_dir}")
    print(f"Max Iterations: {max_iterations}")
    print()

    # Step 1: Start container
    container_name = f"tac_{task_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"[1/6] Starting container: {container_name}")

    try:
        subprocess.run(
            ["docker", "run", "--name", container_name, "--network", "host", "-d", task_image, "sleep", "infinity"],
            check=True,
            capture_output=True,
        )
        print(f"✓ Container started successfully")
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to start container: {e.stderr.decode()}")
        return {"error": "Container start failed", "task_name": task_name}

    try:
        # Step 2: Initialize environment
        print(f"\n[2/6] Initializing task environment...")

        env_llm_api_key = os.getenv("ENV_LLM_API_KEY", "")
        env_llm_base_url = os.getenv("ENV_LLM_BASE_URL", "")
        env_llm_model = os.getenv("ENV_LLM_MODEL", "")

        init_cmd = f"""
SERVER_HOSTNAME={server_hostname} \
LITELLM_API_KEY={env_llm_api_key} \
LITELLM_BASE_URL={env_llm_base_url} \
LITELLM_MODEL={env_llm_model} \
bash /utils/init.sh
"""

        try:
            result = subprocess.run(
                ["docker", "exec", container_name, "bash", "-c", init_cmd],
                check=True,
                capture_output=True,
                timeout=300,
            )
            print(f"✓ Environment initialized")
        except subprocess.TimeoutExpired:
            print(f"✗ Initialization timed out after 300s")
            return {"error": "Init timeout", "task_name": task_name}
        except subprocess.CalledProcessError as e:
            print(f"✗ Initialization failed: {e.stderr.decode()}")
            return {"error": "Init failed", "task_name": task_name}

        # Step 3: Read task instruction
        print(f"\n[3/6] Reading task instruction...")

        try:
            result = subprocess.run(
                ["docker", "exec", container_name, "cat", "/instruction/task.md"],
                capture_output=True,
                text=True,
                check=True,
            )
            task_instruction = result.stdout
            print(f"✓ Task instruction loaded ({len(task_instruction)} chars)")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to read task instruction")
            return {"error": "Cannot read task.md", "task_name": task_name}

        # Step 4: Run agent
        print(f"\n[4/6] Running LangGraph agent...")
        print(f"Task preview: {task_instruction[:200]}...")
        print()

        graph = create_agent_graph(use_checkpointer=True)

        initial_state = create_initial_state(
            task_instruction=task_instruction,
            task_name=task_name,
            container_name=container_name,
            max_iterations=max_iterations,
            service_credentials={
                "gitlab": {
                    "url": f"http://{server_hostname}:8929",
                    "username": "root",
                    "password": "theagentcompany",
                },
                "rocketchat": {
                    "url": f"http://{server_hostname}:3000",
                    "username": "theagentcompany",
                    "password": "theagentcompany",
                },
                "owncloud": {
                    "url": f"http://{server_hostname}:8092",
                    "username": "theagentcompany",
                    "password": "theagentcompany",
                },
                "plane": {
                    "url": f"http://{server_hostname}:8091",
                    "email": "agent@company.com",
                    "password": "theagentcompany",
                },
            },
        )

        # Execute graph with progress tracking
        start_time = datetime.now()

        try:
            final_state = await graph.ainvoke(
                initial_state,
                config={"configurable": {"thread_id": f"task_{task_name}"}},
            )
            elapsed = (datetime.now() - start_time).total_seconds()

            print(f"\n✓ Agent execution completed in {elapsed:.1f}s")
            print(f"  - Iterations: {final_state['iteration']}")
            print(f"  - Completed steps: {len(final_state['completed_steps'])}")
            print(f"  - Trajectory steps: {len(final_state['trajectory'])}")

        except Exception as e:
            print(f"\n✗ Agent execution failed: {e}")
            import traceback
            traceback.print_exc()
            return {"error": f"Agent failed: {str(e)}", "task_name": task_name}

        # Step 5: Save trajectory
        print(f"\n[5/6] Saving trajectory...")

        trajectory_data = {
            "task_name": task_name,
            "agent": "langgraph-vllm",
            "trajectory": final_state["trajectory"],
            "total_iterations": final_state["iteration"],
            "completed_steps": final_state["completed_steps"],
            "execution_time_seconds": elapsed,
        }

        trajectory_path = output_dir / f"traj_{task_name}.json"
        with open(trajectory_path, "w") as f:
            json.dump(trajectory_data, f, indent=2)

        print(f"✓ Trajectory saved: {trajectory_path}")

        # Copy trajectory to container for evaluation
        subprocess.run(
            ["docker", "cp", str(trajectory_path), f"{container_name}:/outputs/traj_{task_name}.json"],
            check=True,
            capture_output=True,
        )

        # Step 6: Run evaluation
        print(f"\n[6/6] Running evaluation...")

        eval_cmd = f"""
LITELLM_API_KEY={env_llm_api_key} \
LITELLM_BASE_URL={env_llm_base_url} \
LITELLM_MODEL={env_llm_model} \
DECRYPTION_KEY='theagentcompany is all you need' \
python_default /utils/eval.py \
--trajectory_path /outputs/traj_{task_name}.json \
--result_path /outputs/eval_{task_name}.json
"""

        try:
            result = subprocess.run(
                ["docker", "exec", container_name, "bash", "-c", eval_cmd],
                check=True,
                capture_output=True,
                timeout=120,
            )
            print(f"✓ Evaluation completed")
        except subprocess.TimeoutExpired:
            print(f"⚠ Evaluation timed out (but may have succeeded)")
        except subprocess.CalledProcessError as e:
            print(f"✗ Evaluation failed: {e.stderr.decode()}")
            # Don't return error - evaluation might have succeeded anyway

        # Copy evaluation result back
        eval_path = output_dir / f"eval_{task_name}.json"
        try:
            subprocess.run(
                ["docker", "cp", f"{container_name}:/outputs/eval_{task_name}.json", str(eval_path)],
                check=True,
                capture_output=True,
            )

            # Read and display results
            with open(eval_path) as f:
                results = json.load(f)

            final_score = results.get("final_score", {})
            score = final_score.get("result", 0)
            total = final_score.get("total", 0)
            percentage = (score / total * 100) if total > 0 else 0

            print(f"\n{'='*70}")
            print(f"RESULTS")
            print(f"{'='*70}")
            print(f"Task: {task_name}")
            print(f"Score: {score}/{total} ({percentage:.1f}%)")

            # Show checkpoint details
            checkpoints = results.get("checkpoints", [])
            if checkpoints:
                print(f"\nCheckpoints:")
                for i, cp in enumerate(checkpoints, 1):
                    cp_score = cp.get("result", 0)
                    cp_total = cp.get("total", 0)
                    status = "✓" if cp_score == cp_total else "✗"
                    print(f"  {status} Checkpoint {i}: {cp_score}/{cp_total}")

            print(f"{'='*70}\n")

            return {
                "task_name": task_name,
                "score": score,
                "total": total,
                "percentage": percentage,
                "checkpoints": checkpoints,
                "execution_time": elapsed,
                "iterations": final_state["iteration"],
            }

        except subprocess.CalledProcessError:
            print(f"✗ Could not retrieve evaluation results")
            return {
                "task_name": task_name,
                "error": "Evaluation result not found",
                "execution_time": elapsed,
            }
        except Exception as e:
            print(f"✗ Error processing results: {e}")
            return {"task_name": task_name, "error": str(e)}

    finally:
        # Cleanup: Stop and remove container
        if cleanup:
            print(f"\nCleaning up container...")
            subprocess.run(["docker", "stop", container_name], capture_output=True)
            subprocess.run(["docker", "rm", container_name], capture_output=True)
            print(f"✓ Container removed")
        else:
            print(f"\nContainer kept for debugging: {container_name}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run LangGraph agent on TheAgentCompany task")
    parser.add_argument("--task-image", required=True, help="Task Docker image")
    parser.add_argument("--task-name", required=True, help="Task name")
    parser.add_argument("--output-dir", default="./outputs", help="Output directory")
    parser.add_argument("--server-hostname", default="localhost", help="Services hostname")
    parser.add_argument("--max-iterations", type=int, default=100, help="Max iterations")
    parser.add_argument("--no-cleanup", action="store_true", help="Keep container for debugging")

    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Check environment variables
    required_vars = ["VLLM_BASE_URL", "ENV_LLM_API_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]
    if missing:
        print(f"Error: Missing environment variables: {', '.join(missing)}")
        print("\nRequired environment variables:")
        print("  VLLM_BASE_URL - vLLM server URL")
        print("  VLLM_API_KEY - vLLM API key")
        print("  ENV_LLM_API_KEY - Environment LLM API key")
        print("  ENV_LLM_BASE_URL - Environment LLM base URL")
        print("  ENV_LLM_MODEL - Environment LLM model")
        sys.exit(1)

    result = asyncio.run(
        run_task(
            task_image=args.task_image,
            task_name=args.task_name,
            output_dir=output_dir,
            server_hostname=args.server_hostname,
            max_iterations=args.max_iterations,
            cleanup=not args.no_cleanup,
        )
    )

    # Exit with error code if task failed
    if "error" in result:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
