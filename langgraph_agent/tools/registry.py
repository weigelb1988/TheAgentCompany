"""
Tool registry for managing and executing tools.
"""

from typing import Dict, Any, Optional
from .bash import execute_bash
from .gitlab import GitLabClient
from .rocketchat import RocketChatClient
from .owncloud import OwnCloudClient
from .plane import PlaneClient
from .browser import BrowserClient


class ToolRegistry:
    """
    Central registry for all agent tools.

    This class manages tool execution and provides a unified interface
    for the execution node.
    """

    def __init__(
        self,
        container_name: Optional[str] = None,
        service_credentials: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the tool registry.

        Args:
            container_name: Docker container name for bash execution
            service_credentials: Credentials for API services
        """
        self.container_name = container_name
        self.service_credentials = service_credentials or {}

        # Initialize API clients (lazy initialization)
        self._gitlab: Optional[GitLabClient] = None
        self._rocketchat: Optional[RocketChatClient] = None
        self._owncloud: Optional[OwnCloudClient] = None
        self._plane: Optional[PlaneClient] = None
        self._browser: Optional[BrowserClient] = None

    def _get_gitlab(self) -> GitLabClient:
        """Get or create GitLab client."""
        if not self._gitlab:
            creds = self.service_credentials.get("gitlab", {})
            self._gitlab = GitLabClient(
                base_url=creds.get("url", "http://localhost:8929"),
                username=creds.get("username", "root"),
                password=creds.get("password", "theagentcompany"),
            )
        return self._gitlab

    def _get_rocketchat(self) -> RocketChatClient:
        """Get or create RocketChat client."""
        if not self._rocketchat:
            creds = self.service_credentials.get("rocketchat", {})
            self._rocketchat = RocketChatClient(
                base_url=creds.get("url", "http://localhost:3000"),
                username=creds.get("username", "theagentcompany"),
                password=creds.get("password", "theagentcompany"),
            )
        return self._rocketchat

    def _get_owncloud(self) -> OwnCloudClient:
        """Get or create ownCloud client."""
        if not self._owncloud:
            creds = self.service_credentials.get("owncloud", {})
            self._owncloud = OwnCloudClient(
                base_url=creds.get("url", "http://localhost:8092"),
                username=creds.get("username", "theagentcompany"),
                password=creds.get("password", "theagentcompany"),
            )
        return self._owncloud

    def _get_plane(self) -> PlaneClient:
        """Get or create Plane client."""
        if not self._plane:
            creds = self.service_credentials.get("plane", {})
            self._plane = PlaneClient(
                base_url=creds.get("url", "http://localhost:8091"),
                email=creds.get("email", "agent@company.com"),
                password=creds.get("password", "theagentcompany"),
            )
        return self._plane

    def _get_browser(self) -> BrowserClient:
        """Get or create Browser client."""
        if not self._browser:
            self._browser = BrowserClient(headless=True)
        return self._browser

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
            # Basic tools
            "bash": self._call_bash,
            "file_read": self._call_file_read,
            "file_write": self._call_file_write,
            # GitLab tools (low-level)
            "gitlab_list_projects": self._gitlab_list_projects,
            "gitlab_get_file": self._gitlab_get_file,
            "gitlab_create_file": self._gitlab_create_file,
            "gitlab_update_file": self._gitlab_update_file,
            "gitlab_list_issues": self._gitlab_list_issues,
            "gitlab_create_issue": self._gitlab_create_issue,
            "gitlab_update_issue": self._gitlab_update_issue,
            "gitlab_list_merge_requests": self._gitlab_list_merge_requests,
            "gitlab_create_merge_request": self._gitlab_create_merge_request,
            # GitLab convenience tools (high-level, recommended)
            "gitlab_get_file_by_name": self._gitlab_get_file_by_name,
            "gitlab_create_issue_by_name": self._gitlab_create_issue_by_name,
            # RocketChat tools (low-level)
            "rocketchat_list_channels": self._rocketchat_list_channels,
            "rocketchat_get_history": self._rocketchat_get_history,
            "rocketchat_send_message": self._rocketchat_send_message,
            "rocketchat_list_dms": self._rocketchat_list_dms,
            "rocketchat_create_dm": self._rocketchat_create_dm,
            # RocketChat convenience tools (high-level, recommended)
            "rocketchat_send_dm_to_user": self._rocketchat_send_dm_to_user,
            "rocketchat_send_to_channel": self._rocketchat_send_to_channel,
            "rocketchat_get_channel_history_by_name": self._rocketchat_get_channel_history_by_name,
            # ownCloud tools
            "owncloud_list_folder": self._owncloud_list_folder,
            "owncloud_get_file": self._owncloud_get_file,
            "owncloud_upload_file": self._owncloud_upload_file,
            "owncloud_create_folder": self._owncloud_create_folder,
            "owncloud_delete": self._owncloud_delete,
            "owncloud_create_share": self._owncloud_create_share,
            # Plane tools (low-level)
            "plane_list_projects": self._plane_list_projects,
            "plane_list_issues": self._plane_list_issues,
            "plane_create_issue": self._plane_create_issue,
            "plane_update_issue": self._plane_update_issue,
            "plane_list_states": self._plane_list_states,
            # Plane convenience tools (high-level, recommended)
            "plane_create_issue_by_project_name": self._plane_create_issue_by_project_name,
            # Browser tools
            "browser_goto": self._browser_goto,
            "browser_click": self._browser_click,
            "browser_type": self._browser_type,
            "browser_fill": self._browser_fill,
            "browser_get_text": self._browser_get_text,
            "browser_get_elements": self._browser_get_elements,
            "browser_screenshot": self._browser_screenshot,
            "browser_scroll": self._browser_scroll,
            "browser_wait": self._browser_wait,
            "browser_back": self._browser_back,
            "browser_forward": self._browser_forward,
            "browser_refresh": self._browser_refresh,
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

    # ==================== Basic Tools ====================

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

    # ==================== GitLab Tools ====================

    async def _gitlab_list_projects(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List GitLab projects."""
        client = self._get_gitlab()
        projects = await client.list_projects()
        return {
            "success": True,
            "projects": projects[:10],  # Limit to avoid token overflow
            "count": len(projects),
        }

    async def _gitlab_get_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get file from GitLab repository."""
        client = self._get_gitlab()
        project_id = params.get("project_id")
        file_path = params.get("file_path")
        ref = params.get("ref", "main")

        content = await client.get_file_raw(project_id, file_path, ref)
        return {"success": True, "content": content, "file_path": file_path}

    async def _gitlab_create_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create file in GitLab repository."""
        client = self._get_gitlab()
        result = await client.create_file(
            project_id=params.get("project_id"),
            file_path=params.get("file_path"),
            content=params.get("content"),
            commit_message=params.get("commit_message", "Create file"),
            branch=params.get("branch", "main"),
        )
        return {"success": True, "file": result}

    async def _gitlab_update_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update file in GitLab repository."""
        client = self._get_gitlab()
        result = await client.update_file(
            project_id=params.get("project_id"),
            file_path=params.get("file_path"),
            content=params.get("content"),
            commit_message=params.get("commit_message", "Update file"),
            branch=params.get("branch", "main"),
        )
        return {"success": True, "file": result}

    async def _gitlab_list_issues(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List GitLab issues."""
        client = self._get_gitlab()
        issues = await client.list_issues(
            project_id=params.get("project_id"), state=params.get("state")
        )
        return {"success": True, "issues": issues[:20], "count": len(issues)}

    async def _gitlab_create_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitLab issue."""
        client = self._get_gitlab()
        issue = await client.create_issue(
            project_id=params.get("project_id"),
            title=params.get("title"),
            description=params.get("description"),
            labels=params.get("labels"),
        )
        return {"success": True, "issue": issue}

    async def _gitlab_update_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update GitLab issue."""
        client = self._get_gitlab()
        issue = await client.update_issue(
            project_id=params.get("project_id"),
            issue_iid=params.get("issue_iid"),
            title=params.get("title"),
            description=params.get("description"),
            state_event=params.get("state_event"),
        )
        return {"success": True, "issue": issue}

    async def _gitlab_list_merge_requests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List GitLab merge requests."""
        client = self._get_gitlab()
        mrs = await client.list_merge_requests(
            project_id=params.get("project_id"), state=params.get("state")
        )
        return {"success": True, "merge_requests": mrs[:20], "count": len(mrs)}

    async def _gitlab_create_merge_request(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitLab merge request."""
        client = self._get_gitlab()
        mr = await client.create_merge_request(
            project_id=params.get("project_id"),
            source_branch=params.get("source_branch"),
            target_branch=params.get("target_branch"),
            title=params.get("title"),
            description=params.get("description"),
        )
        return {"success": True, "merge_request": mr}

    # GitLab Convenience Tools

    async def _gitlab_get_file_by_name(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get file from GitLab by project name (convenience method)."""
        client = self._get_gitlab()
        content = await client.get_file_by_project_name(
            project_name=params.get("project_name"),
            file_path=params.get("file_path"),
            ref=params.get("ref", "main"),
        )
        return {"success": True, "content": content, "file_path": params.get("file_path")}

    async def _gitlab_create_issue_by_name(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create GitLab issue by project name (convenience method)."""
        client = self._get_gitlab()
        issue = await client.create_issue_by_project_name(
            project_name=params.get("project_name"),
            title=params.get("title"),
            description=params.get("description"),
            labels=params.get("labels"),
        )
        return {"success": True, "issue": issue}

    # ==================== RocketChat Tools ====================

    async def _rocketchat_list_channels(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List RocketChat channels."""
        client = self._get_rocketchat()
        channels = await client.list_channels()
        return {"success": True, "channels": channels, "count": len(channels)}

    async def _rocketchat_get_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get RocketChat channel history."""
        client = self._get_rocketchat()
        room_id = params.get("room_id")
        count = params.get("count", 50)

        history = await client.get_channel_history(room_id, count)
        return {"success": True, "messages": history, "count": len(history)}

    async def _rocketchat_send_message(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send RocketChat message."""
        client = self._get_rocketchat()
        result = await client.send_message(
            room_id=params.get("room_id"), text=params.get("text")
        )
        return {"success": True, "message": result}

    async def _rocketchat_list_dms(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List RocketChat direct messages."""
        client = self._get_rocketchat()
        dms = await client.list_direct_messages()
        return {"success": True, "direct_messages": dms, "count": len(dms)}

    async def _rocketchat_create_dm(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create RocketChat direct message."""
        client = self._get_rocketchat()
        dm = await client.create_direct_message(username=params.get("username"))
        return {"success": True, "direct_message": dm}

    # RocketChat Convenience Tools

    async def _rocketchat_send_dm_to_user(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send direct message to user by username (convenience method)."""
        client = self._get_rocketchat()
        result = await client.send_direct_message_to_user(
            username=params.get("username"),
            text=params.get("text")
        )
        return {"success": True, "message": result}

    async def _rocketchat_send_to_channel(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send message to channel by name (convenience method)."""
        client = self._get_rocketchat()
        result = await client.send_message_to_room(
            room_name=params.get("channel_name"),
            text=params.get("text")
        )
        return {"success": True, "message": result}

    async def _rocketchat_get_channel_history_by_name(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get channel history by name (convenience method)."""
        client = self._get_rocketchat()
        messages = await client.get_channel_history_by_name(
            channel_name=params.get("channel_name"),
            count=params.get("count", 50)
        )
        return {"success": True, "messages": messages, "count": len(messages)}

    # ==================== ownCloud Tools ====================

    async def _owncloud_list_folder(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List ownCloud folder contents."""
        client = self._get_owncloud()
        path = params.get("path", "/")
        items = await client.list_folder(path)
        return {"success": True, "items": items, "count": len(items)}

    async def _owncloud_get_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get file from ownCloud."""
        client = self._get_owncloud()
        path = params.get("path")
        content = await client.get_file_text(path)
        return {"success": True, "content": content, "path": path}

    async def _owncloud_upload_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Upload file to ownCloud."""
        client = self._get_owncloud()
        result = await client.upload_file_text(
            path=params.get("path"), content=params.get("content")
        )
        return result

    async def _owncloud_create_folder(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create ownCloud folder."""
        client = self._get_owncloud()
        result = await client.create_folder(path=params.get("path"))
        return result

    async def _owncloud_delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete ownCloud file/folder."""
        client = self._get_owncloud()
        result = await client.delete(path=params.get("path"))
        return result

    async def _owncloud_create_share(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create ownCloud share link."""
        client = self._get_owncloud()
        url = await client.get_share_link(
            path=params.get("path"), password=params.get("password")
        )
        return {"success": True, "share_url": url}

    # ==================== Plane Tools ====================

    async def _plane_list_projects(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List Plane projects."""
        client = self._get_plane()
        workspace_slug = params.get("workspace_slug")
        projects = await client.list_projects(workspace_slug)
        return {"success": True, "projects": projects, "count": len(projects)}

    async def _plane_list_issues(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List Plane issues."""
        client = self._get_plane()
        issues = await client.list_issues(
            project_id=params.get("project_id"),
            workspace_slug=params.get("workspace_slug"),
            state=params.get("state"),
        )
        return {"success": True, "issues": issues[:20], "count": len(issues)}

    async def _plane_create_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create Plane issue."""
        client = self._get_plane()
        issue = await client.create_issue(
            project_id=params.get("project_id"),
            name=params.get("name"),
            description=params.get("description"),
            workspace_slug=params.get("workspace_slug"),
            priority=params.get("priority"),
        )
        return {"success": True, "issue": issue}

    async def _plane_update_issue(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update Plane issue."""
        client = self._get_plane()
        issue = await client.update_issue(
            project_id=params.get("project_id"),
            issue_id=params.get("issue_id"),
            name=params.get("name"),
            description=params.get("description"),
            state_id=params.get("state_id"),
            workspace_slug=params.get("workspace_slug"),
        )
        return {"success": True, "issue": issue}

    async def _plane_list_states(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List Plane issue states."""
        client = self._get_plane()
        states = await client.list_states(
            project_id=params.get("project_id"), workspace_slug=params.get("workspace_slug")
        )
        return {"success": True, "states": states, "count": len(states)}

    # Plane Convenience Tools

    async def _plane_create_issue_by_project_name(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create Plane issue by project name (convenience method)."""
        client = self._get_plane()
        issue = await client.create_issue_by_project_name(
            project_name=params.get("project_name"),
            name=params.get("name"),
            description=params.get("description"),
            state_id=params.get("state_id"),
            priority=params.get("priority"),
            assignees=params.get("assignees"),
            workspace_slug=params.get("workspace_slug"),
        )
        return {"success": True, "issue": issue}

    # ==================== Browser Tools ====================

    async def _browser_goto(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate browser to URL."""
        client = self._get_browser()
        result = await client.goto(
            url=params.get("url"),
            wait_until=params.get("wait_until", "load")
        )
        return result

    async def _browser_click(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Click an element in browser."""
        client = self._get_browser()
        result = await client.click(
            selector=params.get("selector"),
            timeout=params.get("timeout")
        )
        return result

    async def _browser_type(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Type text into an element."""
        client = self._get_browser()
        result = await client.type_text(
            selector=params.get("selector"),
            text=params.get("text"),
            delay=params.get("delay", 0),
            timeout=params.get("timeout")
        )
        return result

    async def _browser_fill(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Fill an input element (clears first)."""
        client = self._get_browser()
        result = await client.fill(
            selector=params.get("selector"),
            value=params.get("value"),
            timeout=params.get("timeout")
        )
        return result

    async def _browser_get_text(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get text content from element or page."""
        client = self._get_browser()
        text = await client.get_text(selector=params.get("selector"))
        return {
            "success": True,
            "text": text,
            "selector": params.get("selector")
        }

    async def _browser_get_elements(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get all elements matching selector."""
        client = self._get_browser()
        elements = await client.get_elements(selector=params.get("selector"))
        return {
            "success": True,
            "elements": elements,
            "count": len(elements)
        }

    async def _browser_screenshot(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Take a screenshot."""
        client = self._get_browser()
        result = await client.screenshot(
            path=params.get("path"),
            full_page=params.get("full_page", False)
        )
        return result

    async def _browser_scroll(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Scroll the page."""
        client = self._get_browser()
        result = await client.scroll(
            direction=params.get("direction", "down"),
            amount=params.get("amount", 500)
        )
        return result

    async def _browser_wait(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Wait for specified milliseconds."""
        client = self._get_browser()
        result = await client.wait(milliseconds=params.get("milliseconds", 1000))
        return result

    async def _browser_back(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate back in browser history."""
        client = self._get_browser()
        result = await client.back()
        return result

    async def _browser_forward(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Navigate forward in browser history."""
        client = self._get_browser()
        result = await client.forward()
        return result

    async def _browser_refresh(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Refresh the current page."""
        client = self._get_browser()
        result = await client.refresh()
        return result

    async def cleanup(self):
        """Cleanup API clients."""
        if self._gitlab:
            await self._gitlab.close()
        if self._rocketchat:
            await self._rocketchat.close()
        if self._owncloud:
            await self._owncloud.close()
        if self._plane:
            await self._plane.close()
        if self._browser:
            await self._browser.close()
