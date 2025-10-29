"""
Trajectory logging utilities for TheAgentCompany evaluation.
"""

from datetime import datetime
from typing import Any


def log_action(
    trajectory: list[dict[str, Any]],
    action_type: str,
    details: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Log an action to the trajectory.

    Args:
        trajectory: Current trajectory list
        action_type: Type of action (bash, browser, api_call, etc.)
        details: Action-specific details

    Returns:
        Updated trajectory list
    """
    step_number = len(trajectory) + 1

    entry = {
        "step_number": step_number,
        "action": action_type,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        **details,
    }

    trajectory.append(entry)
    return trajectory


def log_bash_action(
    trajectory: list[dict[str, Any]],
    command: str,
    output: str,
    return_code: int,
) -> list[dict[str, Any]]:
    """Log a bash command execution."""
    return log_action(
        trajectory,
        "bash",
        {
            "command": command,
            "output": output[:1000],  # Limit output length
            "return_code": return_code,
        },
    )


def log_browser_action(
    trajectory: list[dict[str, Any]],
    action: str,
    url: str,
    observation: str,
) -> list[dict[str, Any]]:
    """Log a browser action."""
    return log_action(
        trajectory,
        "browser",
        {
            "browser_action": action,
            "url": url,
            "observation": observation[:500],  # Limit observation length
        },
    )


def log_api_action(
    trajectory: list[dict[str, Any]],
    service: str,
    endpoint: str,
    method: str,
    response_summary: str,
) -> list[dict[str, Any]]:
    """Log an API call."""
    return log_action(
        trajectory,
        "api_call",
        {
            "service": service,
            "endpoint": endpoint,
            "method": method,
            "response": response_summary[:500],
        },
    )


def log_planning_action(
    trajectory: list[dict[str, Any]],
    plan: list[str],
) -> list[dict[str, Any]]:
    """Log the initial planning step."""
    return log_action(
        trajectory,
        "planning",
        {
            "plan": plan,
        },
    )


def log_reflection_action(
    trajectory: list[dict[str, Any]],
    reflection: str,
    decision: str,
) -> list[dict[str, Any]]:
    """Log a reflection step."""
    return log_action(
        trajectory,
        "reflection",
        {
            "reflection": reflection[:500],
            "decision": decision,
        },
    )
