"""
Tool registry for managing and executing tools.
"""

from typing import Dict, Any, Optional
from .bash import execute_bash


class ToolRegistry:
    """
    Central registry for all agent tools.

    This class manages tool execution and provides a unified interface
    for the execution node.
    """

    def __init__(self, container_name: Optional[str] = None):
        """
        Initialize the tool registry.

        Args:
            container_name: Docker container name for bash execution
        """
        self.container_name = container_name

    async def call_tool(self, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool by name with parameters.

        Args:
            tool_name: Name of tool to call
            parameters: Tool-specific parameters

        Returns:
            Tool execution result
        """
        # Map tool names to implementations
        tool_map = {
            "bash": self._call_bash,
            "file_read": self._call_file_read,
            "file_write": self._call_file_write,
            # More tools will be added in Phase 4
        }

        handler = tool_map.get(tool_name)
        if not handler:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "tool_name": tool_name,
            }

        try:
            result = await handler(parameters)
            result["tool_name"] = tool_name
            return result
        except Exception as e:
            return {
                "success": False,
                "error": f"Tool execution failed: {str(e)}",
                "tool_name": tool_name,
            }

    async def _call_bash(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute bash command."""
        command = params.get("command", "")
        working_dir = params.get("working_dir", "/workspace")

        result = await execute_bash(
            command=command,
            container_name=self.container_name,
            working_dir=working_dir,
        )

        return {
            "success": result["success"],
            "output": result["stdout"],
            "error": result["stderr"],
            "return_code": result["return_code"],
        }

    async def _call_file_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Read a file."""
        file_path = params.get("file_path", "")

        # Use bash to read file
        result = await execute_bash(
            command=f"cat {file_path}",
            container_name=self.container_name,
        )

        if result["success"]:
            return {
                "success": True,
                "content": result["stdout"],
                "file_path": file_path,
            }
        else:
            return {
                "success": False,
                "error": result["stderr"],
                "file_path": file_path,
            }

    async def _call_file_write(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Write to a file."""
        file_path = params.get("file_path", "")
        content = params.get("content", "")

        # Use bash heredoc to write file
        escaped_content = content.replace("'", "'\"'\"'")
        command = f"cat > {file_path} << 'EOF'\n{escaped_content}\nEOF"

        result = await execute_bash(
            command=command,
            container_name=self.container_name,
        )

        return {
            "success": result["success"],
            "file_path": file_path,
            "error": result["stderr"] if not result["success"] else None,
        }
