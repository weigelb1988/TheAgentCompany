"""
Helper utilities for building context from memory.

These utilities help format memory content for use in prompts and decision-making.
"""

from typing import Dict, List, Any, Optional
from .memory import MemoryStore, MemoryEntry


def build_context_for_planning(memory_store: MemoryStore) -> str:
    """
    Build context string for planning node from memory.

    Args:
        memory_store: Memory store with past operations

    Returns:
        Formatted context string
    """
    if not memory_store.memories:
        return "No previous operations."

    lines = [
        "# Context from Previous Operations\n"
    ]

    stats = memory_store.get_statistics()
    lines.append(f"Completed {stats['total_memories']} operations "
                f"({stats['successful']} successful, {stats['failed']} failed)\n")

    # Group by category
    summaries = memory_store.summarize_by_category()
    for category, summary in summaries.items():
        lines.append(f"\n## {category.upper()}")
        lines.append(summary)

    return "\n".join(lines)


def build_context_for_tool_calling(
    memory_store: MemoryStore,
    current_step: Optional[str] = None
) -> str:
    """
    Build context string for tool calling node from memory.

    Args:
        memory_store: Memory store with past operations
        current_step: Current step being executed

    Returns:
        Formatted context string with relevant memories
    """
    if not memory_store.memories:
        return "No previous operations to reference."

    lines = []

    # Show recent successful operations (what's working)
    successful = memory_store.get_successful(limit=5)
    if successful:
        lines.append("Recent Successful Operations:")
        for memory in successful[-5:]:
            lines.append(f"  {memory.get_summary()}")

    # Show entities we've discovered
    projects = memory_store.get_entities_of_type("projects")
    issues = memory_store.get_entities_of_type("issues")
    files = memory_store.get_entities_of_type("files")

    if projects or issues or files:
        lines.append("\nKnown Entities:")
        if projects:
            lines.append(f"  Projects: {', '.join(list(projects)[:10])}")
        if issues:
            lines.append(f"  Issues: {', '.join(list(issues)[:10])}")
        if files:
            lines.append(f"  Files: {', '.join(list(files)[:10])}")

    # Show recent failures (what to avoid)
    failed = memory_store.get_failed(limit=3)
    if failed:
        lines.append("\nRecent Failures (avoid repeating):")
        for memory in failed:
            lines.append(f"  {memory.get_summary()}")

    return "\n".join(lines)


def get_relevant_memories_for_entity(
    memory_store: MemoryStore,
    entity_name: str,
    entity_type: Optional[str] = None
) -> List[MemoryEntry]:
    """
    Get memories relevant to a specific entity.

    Args:
        memory_store: Memory store
        entity_name: Name of the entity
        entity_type: Type of entity (projects, issues, files, etc.)
            If None, searches all types

    Returns:
        List of relevant memories
    """
    if entity_type:
        return memory_store.get_by_entity(entity_type, entity_name)

    # Search all entity types
    all_memories = []
    for etype in ["projects", "issues", "files", "users", "channels"]:
        memories = memory_store.get_by_entity(etype, entity_name)
        all_memories.extend(memories)

    # Remove duplicates
    seen = set()
    unique = []
    for mem in all_memories:
        mem_id = id(mem)
        if mem_id not in seen:
            seen.add(mem_id)
            unique.append(mem)

    return unique


def summarize_memories_for_context(
    memories: List[MemoryEntry],
    max_length: int = 500
) -> str:
    """
    Summarize a list of memories into a concise context string.

    Args:
        memories: List of memory entries
        max_length: Maximum length of summary

    Returns:
        Summary string
    """
    if not memories:
        return "No relevant memories."

    lines = []
    current_length = 0

    for memory in memories:
        summary = memory.get_summary(max_length=100)
        if current_length + len(summary) > max_length:
            lines.append(f"...and {len(memories) - len(lines)} more")
            break

        lines.append(summary)
        current_length += len(summary)

    return "\n".join(lines)


def get_context_for_error_recovery(
    memory_store: MemoryStore,
    error_tool: str
) -> str:
    """
    Build context for recovering from an error.

    Args:
        memory_store: Memory store
        error_tool: Tool that failed

    Returns:
        Context string with suggestions for recovery
    """
    lines = [f"Error occurred with: {error_tool}\n"]

    # Get history for this tool
    tool_history = memory_store.get_by_tool(error_tool, limit=5)

    successful_attempts = [m for m in tool_history if m.success]
    failed_attempts = [m for m in tool_history if not m.success]

    if successful_attempts:
        lines.append("Previous successful attempts with this tool:")
        for memory in successful_attempts:
            lines.append(f"  ✓ {memory.get_summary()}")
            # Show parameters that worked
            lines.append(f"    Parameters: {memory.parameters}")

    if failed_attempts:
        lines.append("\nPrevious failures with this tool:")
        for memory in failed_attempts[-3:]:
            lines.append(f"  ✗ {memory.get_summary()}")
            lines.append(f"    Error: {memory.error}")

    # Suggest alternative approaches
    lines.append("\nConsider:")
    lines.append("  - Checking parameters against successful attempts")
    lines.append("  - Using alternative tools")
    lines.append("  - Verifying entity names/IDs are correct")

    return "\n".join(lines)


def export_memory_summary(memory_store: MemoryStore) -> Dict[str, Any]:
    """
    Export a comprehensive memory summary for logging/debugging.

    Args:
        memory_store: Memory store

    Returns:
        Dictionary with memory summary
    """
    stats = memory_store.get_statistics()

    return {
        "statistics": stats,
        "recent_operations": [
            m.to_dict() for m in memory_store.get_recent(10)
        ],
        "entities": {
            entity_type: memory_store.get_entities_of_type(entity_type)
            for entity_type in ["projects", "issues", "files", "users", "channels"]
        },
        "failures": [
            {
                "tool": m.tool_name,
                "error": m.error,
                "parameters": m.parameters
            }
            for m in memory_store.get_failed(limit=5)
        ]
    }
