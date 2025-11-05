"""
Enhanced memory system for storing and retrieving tool execution results.

This module provides a structured memory system that allows the agent to:
- Store tool execution results with rich metadata
- Retrieve results by tool type, entity, or semantic query
- Track entities (projects, issues, files, users) across tool calls
- Summarize memory for context building
- Maintain temporal ordering of events
"""

from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from collections import defaultdict
import re


class MemoryEntry:
    """
    A single memory entry representing a tool execution and its result.
    """

    def __init__(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Dict[str, Any],
        reasoning: str = "",
        timestamp: Optional[datetime] = None,
    ):
        """
        Initialize a memory entry.

        Args:
            tool_name: Name of the tool that was executed
            parameters: Parameters passed to the tool
            result: Result returned by the tool
            reasoning: Reasoning for executing this tool
            timestamp: Time of execution (defaults to now)
        """
        self.tool_name = tool_name
        self.parameters = parameters
        self.result = result
        self.reasoning = reasoning
        self.timestamp = timestamp or datetime.now()

        # Extract metadata
        self.success = result.get("success", False)
        self.error = result.get("error")

        # Extract entities mentioned in this operation
        self.entities = self._extract_entities()

        # Categorize the tool
        self.category = self._categorize_tool()

    def _extract_entities(self) -> Dict[str, Set[str]]:
        """
        Extract entities (projects, issues, files, users) from parameters and results.

        Returns:
            Dictionary of entity types to sets of entity names
        """
        entities = {
            "projects": set(),
            "issues": set(),
            "files": set(),
            "users": set(),
            "channels": set(),
            "repositories": set(),
        }

        # Extract from parameters
        if "project_name" in self.parameters:
            entities["projects"].add(self.parameters["project_name"])
        if "project_id" in self.parameters:
            entities["projects"].add(str(self.parameters["project_id"]))

        if "file_path" in self.parameters:
            entities["files"].add(self.parameters["file_path"])

        if "username" in self.parameters:
            entities["users"].add(self.parameters["username"])

        if "channel_name" in self.parameters:
            entities["channels"].add(self.parameters["channel_name"])

        if "issue_iid" in self.parameters or "issue_id" in self.parameters:
            issue_id = self.parameters.get("issue_iid") or self.parameters.get("issue_id")
            entities["issues"].add(str(issue_id))

        # Extract from results
        if self.success and isinstance(self.result, dict):
            # Projects from GitLab
            if "project" in self.result and isinstance(self.result["project"], dict):
                proj = self.result["project"]
                if "name" in proj:
                    entities["projects"].add(proj["name"])
                if "path_with_namespace" in proj:
                    entities["repositories"].add(proj["path_with_namespace"])

            # Issues
            if "issue" in self.result and isinstance(self.result["issue"], dict):
                issue = self.result["issue"]
                if "iid" in issue:
                    entities["issues"].add(str(issue["iid"]))

            # Files from file operations
            if "file_path" in self.result:
                entities["files"].add(self.result["file_path"])

        # Remove empty sets
        return {k: v for k, v in entities.items() if v}

    def _categorize_tool(self) -> str:
        """
        Categorize the tool into broad categories.

        Returns:
            Category name
        """
        if self.tool_name.startswith("gitlab_"):
            return "gitlab"
        elif self.tool_name.startswith("rocketchat_"):
            return "rocketchat"
        elif self.tool_name.startswith("owncloud_"):
            return "owncloud"
        elif self.tool_name.startswith("plane_"):
            return "plane"
        elif self.tool_name.startswith("browser_"):
            return "browser"
        elif self.tool_name in ("bash", "file_read", "file_write"):
            return "system"
        else:
            return "other"

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert memory entry to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            "tool_name": self.tool_name,
            "parameters": self.parameters,
            "result": self.result,
            "reasoning": self.reasoning,
            "timestamp": self.timestamp.isoformat(),
            "success": self.success,
            "error": self.error,
            "entities": {k: list(v) for k, v in self.entities.items()},
            "category": self.category,
        }

    def get_summary(self, max_length: int = 200) -> str:
        """
        Get a concise summary of this memory entry.

        Args:
            max_length: Maximum length of summary

        Returns:
            Summary string
        """
        status = "✓" if self.success else "✗"

        # Format parameters concisely
        param_str = ", ".join(f"{k}={v}" for k, v in list(self.parameters.items())[:3])
        if len(self.parameters) > 3:
            param_str += "..."

        summary = f"{status} {self.tool_name}({param_str})"

        # Add key result info
        if self.success:
            if "count" in self.result:
                summary += f" → {self.result['count']} items"
            elif "issue" in self.result:
                summary += f" → issue created/updated"
            elif "message" in self.result:
                summary += f" → message sent"
        else:
            summary += f" → Error: {self.error}"

        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."

        return summary


class MemoryStore:
    """
    Enhanced memory storage with indexing and retrieval capabilities.
    """

    def __init__(self):
        """Initialize the memory store."""
        # Chronological list of all memories
        self.memories: List[MemoryEntry] = []

        # Indexes for fast retrieval
        self.by_tool: Dict[str, List[int]] = defaultdict(list)
        self.by_category: Dict[str, List[int]] = defaultdict(list)
        self.by_entity: Dict[str, Dict[str, List[int]]] = defaultdict(lambda: defaultdict(list))

        # Entity tracking - what we know about each entity
        self.entity_info: Dict[str, Dict[str, Any]] = {}

    def add(self, entry: MemoryEntry) -> int:
        """
        Add a memory entry to the store.

        Args:
            entry: Memory entry to add

        Returns:
            Index of the added memory
        """
        idx = len(self.memories)
        self.memories.append(entry)

        # Update indexes
        self.by_tool[entry.tool_name].append(idx)
        self.by_category[entry.category].append(idx)

        # Update entity indexes
        for entity_type, entity_names in entry.entities.items():
            for entity_name in entity_names:
                self.by_entity[entity_type][entity_name].append(idx)

        return idx

    def add_from_tool_call(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        result: Dict[str, Any],
        reasoning: str = "",
    ) -> int:
        """
        Convenience method to add memory directly from tool call.

        Args:
            tool_name: Name of the tool
            parameters: Tool parameters
            result: Tool result
            reasoning: Reasoning for the call

        Returns:
            Index of the added memory
        """
        entry = MemoryEntry(tool_name, parameters, result, reasoning)
        return self.add(entry)

    def get_by_tool(self, tool_name: str, limit: Optional[int] = None) -> List[MemoryEntry]:
        """
        Retrieve memories by tool name.

        Args:
            tool_name: Name of the tool
            limit: Maximum number of memories to return (most recent)

        Returns:
            List of memory entries
        """
        indices = self.by_tool.get(tool_name, [])
        if limit:
            indices = indices[-limit:]
        return [self.memories[idx] for idx in indices]

    def get_by_category(self, category: str, limit: Optional[int] = None) -> List[MemoryEntry]:
        """
        Retrieve memories by category (gitlab, rocketchat, etc.).

        Args:
            category: Category name
            limit: Maximum number of memories to return (most recent)

        Returns:
            List of memory entries
        """
        indices = self.by_category.get(category, [])
        if limit:
            indices = indices[-limit:]
        return [self.memories[idx] for idx in indices]

    def get_by_entity(
        self, entity_type: str, entity_name: str, limit: Optional[int] = None
    ) -> List[MemoryEntry]:
        """
        Retrieve memories related to a specific entity.

        Args:
            entity_type: Type of entity (projects, issues, files, users, channels)
            entity_name: Name/ID of the entity
            limit: Maximum number of memories to return (most recent)

        Returns:
            List of memory entries
        """
        indices = self.by_entity.get(entity_type, {}).get(entity_name, [])
        if limit:
            indices = indices[-limit:]
        return [self.memories[idx] for idx in indices]

    def get_recent(self, limit: int = 10) -> List[MemoryEntry]:
        """
        Get most recent memories.

        Args:
            limit: Number of recent memories to return

        Returns:
            List of memory entries
        """
        return self.memories[-limit:]

    def get_successful(self, limit: Optional[int] = None) -> List[MemoryEntry]:
        """
        Get successful tool executions only.

        Args:
            limit: Maximum number to return (most recent)

        Returns:
            List of successful memory entries
        """
        successful = [m for m in self.memories if m.success]
        if limit:
            successful = successful[-limit:]
        return successful

    def get_failed(self, limit: Optional[int] = None) -> List[MemoryEntry]:
        """
        Get failed tool executions only.

        Args:
            limit: Maximum number to return (most recent)

        Returns:
            List of failed memory entries
        """
        failed = [m for m in self.memories if not m.success]
        if limit:
            failed = failed[-limit:]
        return failed

    def search(self, query: str, limit: int = 10) -> List[MemoryEntry]:
        """
        Search memories by keyword/pattern.

        Args:
            query: Search query (searches in tool names, parameters, results)
            limit: Maximum number of results

        Returns:
            List of matching memory entries
        """
        query_lower = query.lower()
        matches = []

        for memory in reversed(self.memories):  # Search recent first
            # Search in tool name
            if query_lower in memory.tool_name.lower():
                matches.append(memory)
                continue

            # Search in parameters
            if any(query_lower in str(v).lower() for v in memory.parameters.values()):
                matches.append(memory)
                continue

            # Search in result
            if query_lower in str(memory.result).lower():
                matches.append(memory)
                continue

            if len(matches) >= limit:
                break

        return matches[:limit]

    def get_entities_of_type(self, entity_type: str) -> List[str]:
        """
        Get all known entities of a specific type.

        Args:
            entity_type: Type of entity

        Returns:
            List of entity names
        """
        return list(self.by_entity.get(entity_type, {}).keys())

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get memory statistics.

        Returns:
            Dictionary with statistics
        """
        total = len(self.memories)
        successful = sum(1 for m in self.memories if m.success)
        failed = total - successful

        tool_counts = {tool: len(indices) for tool, indices in self.by_tool.items()}
        category_counts = {cat: len(indices) for cat, indices in self.by_category.items()}

        return {
            "total_memories": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total if total > 0 else 0,
            "by_tool": tool_counts,
            "by_category": category_counts,
            "entities": {
                entity_type: len(entities)
                for entity_type, entities in self.by_entity.items()
            },
        }

    def summarize(self, limit: int = 20) -> str:
        """
        Generate a concise summary of recent memories.

        Args:
            limit: Number of recent memories to summarize

        Returns:
            Summary string
        """
        recent = self.get_recent(limit)

        if not recent:
            return "No memories yet."

        lines = ["Recent Operations:"]
        for memory in recent:
            lines.append(f"  {memory.get_summary()}")

        stats = self.get_statistics()
        lines.append(f"\nStatistics:")
        lines.append(f"  Total: {stats['total_memories']}, "
                    f"Success: {stats['successful']}, "
                    f"Failed: {stats['failed']}")

        return "\n".join(lines)

    def summarize_by_category(self) -> Dict[str, str]:
        """
        Generate summaries grouped by category.

        Returns:
            Dictionary mapping categories to summaries
        """
        summaries = {}

        for category in self.by_category.keys():
            memories = self.get_by_category(category, limit=10)
            if memories:
                lines = [f"{category.upper()} Operations:"]
                for memory in memories:
                    lines.append(f"  {memory.get_summary()}")
                summaries[category] = "\n".join(lines)

        return summaries

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert memory store to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "memories": [m.to_dict() for m in self.memories],
            "statistics": self.get_statistics(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryStore":
        """
        Restore memory store from dictionary.

        Args:
            data: Dictionary representation

        Returns:
            Restored MemoryStore
        """
        store = cls()

        for mem_dict in data.get("memories", []):
            entry = MemoryEntry(
                tool_name=mem_dict["tool_name"],
                parameters=mem_dict["parameters"],
                result=mem_dict["result"],
                reasoning=mem_dict.get("reasoning", ""),
                timestamp=datetime.fromisoformat(mem_dict["timestamp"]),
            )
            store.add(entry)

        return store

    def clear(self):
        """Clear all memories and indexes."""
        self.memories.clear()
        self.by_tool.clear()
        self.by_category.clear()
        self.by_entity.clear()
        self.entity_info.clear()
