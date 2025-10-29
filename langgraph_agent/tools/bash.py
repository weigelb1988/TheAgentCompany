"""
Bash tool for executing shell commands.
"""

import subprocess
from typing import Dict, Any, Optional


async def execute_bash(
    command: str,
    container_name: Optional[str] = None,
    working_dir: str = "/workspace",
    timeout: int = 60,
) -> Dict[str, Any]:
    """
    Execute a bash command, optionally inside a Docker container.

    Args:
        command: Bash command to execute
        container_name: Docker container name (if None, runs locally)
        working_dir: Working directory for command
        timeout: Command timeout in seconds

    Returns:
        Dict with success, stdout, stderr, return_code
    """
    try:
        if container_name:
            # Execute in Docker container
            cmd = [
                "docker",
                "exec",
                "-w",
                working_dir,
                container_name,
                "bash",
                "-c",
                command,
            ]
        else:
            # Execute locally
            cmd = ["bash", "-c", command]

        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout, check=False
        )

        return {
            "success": result.returncode == 0,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "return_code": result.returncode,
            "command": command,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "stdout": "",
            "stderr": f"Command timed out after {timeout}s",
            "return_code": -1,
            "command": command,
        }
    except Exception as e:
        return {
            "success": False,
            "stdout": "",
            "stderr": str(e),
            "return_code": -1,
            "command": command,
        }
