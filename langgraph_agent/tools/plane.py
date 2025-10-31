"""
Plane API client for TheAgentCompany.

Provides comprehensive Plane operations for project management,
issue tracking, and team collaboration.
"""

import httpx
from typing import List, Dict, Any, Optional


class PlaneClient:
    """
    Plane API client for TheAgentCompany tasks.

    Supports operations on:
    - Workspaces
    - Projects
    - Issues
    - Cycles
    - Modules
    - States
    """

    def __init__(self, base_url: str, email: str, password: str):
        """
        Initialize Plane client.

        Args:
            base_url: Plane base URL (e.g., http://localhost:8091)
            email: Plane user email
            password: Plane user password
        """
        self.base_url = base_url.rstrip("/")
        self.email = email
        self.password = password
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.workspace_slug: Optional[str] = None
        self.client = httpx.AsyncClient(verify=False, timeout=30.0)

    async def sign_in(self) -> Dict[str, Any]:
        """
        Sign in and get access token.

        Returns:
            Sign in response with tokens
        """
        response = await self.client.post(
            f"{self.base_url}/api/sign-in/",
            json={"email": self.email, "password": self.password},
        )
        response.raise_for_status()
        data = response.json()

        self.access_token = data.get("access_token")
        self.refresh_token = data.get("refresh_token")

        return data

    def _headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        if not self.access_token:
            raise ValueError("Not authenticated. Call sign_in() first.")
        return {"Authorization": f"Bearer {self.access_token}"}

    # ==================== Workspaces ====================

    async def list_workspaces(self) -> List[Dict[str, Any]]:
        """
        List all workspaces.

        Returns:
            List of workspace objects
        """
        if not self.access_token:
            await self.sign_in()

        response = await self.client.get(
            f"{self.base_url}/api/workspaces/", headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    async def get_workspace(self, workspace_slug: str) -> Dict[str, Any]:
        """
        Get workspace details.

        Args:
            workspace_slug: Workspace slug

        Returns:
            Workspace object
        """
        response = await self.client.get(
            f"{self.base_url}/api/workspaces/{workspace_slug}/", headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    async def set_workspace(self, workspace_slug: str):
        """
        Set the default workspace for subsequent operations.

        Args:
            workspace_slug: Workspace slug
        """
        self.workspace_slug = workspace_slug

    # ==================== Projects ====================

    async def list_projects(self, workspace_slug: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List projects in workspace.

        Args:
            workspace_slug: Workspace slug (uses default if not provided)

        Returns:
            List of project objects
        """
        ws = workspace_slug or self.workspace_slug
        if not ws:
            raise ValueError("Workspace slug not set. Call set_workspace() first.")

        response = await self.client.get(
            f"{self.base_url}/api/workspaces/{ws}/projects/", headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    async def get_project(
        self, project_id: str, workspace_slug: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get project details.

        Args:
            project_id: Project ID
            workspace_slug: Workspace slug

        Returns:
            Project object
        """
        ws = workspace_slug or self.workspace_slug
        if not ws:
            raise ValueError("Workspace slug not set")

        response = await self.client.get(
            f"{self.base_url}/api/workspaces/{ws}/projects/{project_id}/",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    async def create_project(
        self,
        name: str,
        description: Optional[str] = None,
        workspace_slug: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new project.

        Args:
            name: Project name
            description: Project description
            workspace_slug: Workspace slug

        Returns:
            Created project object
        """
        ws = workspace_slug or self.workspace_slug
        if not ws:
            raise ValueError("Workspace slug not set")

        data = {"name": name}
        if description:
            data["description"] = description

        response = await self.client.post(
            f"{self.base_url}/api/workspaces/{ws}/projects/",
            headers=self._headers(),
            json=data,
        )
        response.raise_for_status()
        return response.json()

    # ==================== Issues ====================

    async def list_issues(
        self,
        project_id: str,
        workspace_slug: Optional[str] = None,
        state: Optional[str] = None,
        priority: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        List issues in project.

        Args:
            project_id: Project ID
            workspace_slug: Workspace slug
            state: Filter by state
            priority: Filter by priority

        Returns:
            List of issue objects
        """
        ws = workspace_slug or self.workspace_slug
        if not ws:
            raise ValueError("Workspace slug not set")

        params = {}
        if state:
            params["state"] = state
        if priority:
            params["priority"] = priority

        response = await self.client.get(
            f"{self.base_url}/api/workspaces/{ws}/projects/{project_id}/issues/",
            headers=self._headers(),
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def get_issue(
        self, project_id: str, issue_id: str, workspace_slug: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get issue details.

        Args:
            project_id: Project ID
            issue_id: Issue ID
            workspace_slug: Workspace slug

        Returns:
            Issue object
        """
        ws = workspace_slug or self.workspace_slug
        if not ws:
            raise ValueError("Workspace slug not set")

        response = await self.client.get(
            f"{self.base_url}/api/workspaces/{ws}/projects/{project_id}/issues/{issue_id}/",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    async def create_issue(
        self,
        project_id: str,
        name: str,
        description: Optional[str] = None,
        state_id: Optional[str] = None,
        priority: Optional[str] = None,
        assignees: Optional[List[str]] = None,
        workspace_slug: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new issue.

        Args:
            project_id: Project ID
            name: Issue title
            description: Issue description
            state_id: State ID
            priority: Priority (urgent, high, medium, low, none)
            assignees: List of user IDs to assign
            workspace_slug: Workspace slug

        Returns:
            Created issue object
        """
        ws = workspace_slug or self.workspace_slug
        if not ws:
            raise ValueError("Workspace slug not set")

        data = {"name": name, "project": project_id}

        if description:
            data["description"] = description
        if state_id:
            data["state"] = state_id
        if priority:
            data["priority"] = priority
        if assignees:
            data["assignees"] = assignees

        response = await self.client.post(
            f"{self.base_url}/api/workspaces/{ws}/projects/{project_id}/issues/",
            headers=self._headers(),
            json=data,
        )
        response.raise_for_status()
        return response.json()

    async def update_issue(
        self,
        project_id: str,
        issue_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        state_id: Optional[str] = None,
        priority: Optional[str] = None,
        assignees: Optional[List[str]] = None,
        workspace_slug: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an issue.

        Args:
            project_id: Project ID
            issue_id: Issue ID
            name: New title
            description: New description
            state_id: New state ID
            priority: New priority
            assignees: New assignees
            workspace_slug: Workspace slug

        Returns:
            Updated issue object
        """
        ws = workspace_slug or self.workspace_slug
        if not ws:
            raise ValueError("Workspace slug not set")

        data = {}
        if name:
            data["name"] = name
        if description:
            data["description"] = description
        if state_id:
            data["state"] = state_id
        if priority:
            data["priority"] = priority
        if assignees:
            data["assignees"] = assignees

        response = await self.client.patch(
            f"{self.base_url}/api/workspaces/{ws}/projects/{project_id}/issues/{issue_id}/",
            headers=self._headers(),
            json=data,
        )
        response.raise_for_status()
        return response.json()

    async def delete_issue(
        self, project_id: str, issue_id: str, workspace_slug: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Delete an issue.

        Args:
            project_id: Project ID
            issue_id: Issue ID
            workspace_slug: Workspace slug

        Returns:
            Deletion response
        """
        ws = workspace_slug or self.workspace_slug
        if not ws:
            raise ValueError("Workspace slug not set")

        response = await self.client.delete(
            f"{self.base_url}/api/workspaces/{ws}/projects/{project_id}/issues/{issue_id}/",
            headers=self._headers(),
        )
        response.raise_for_status()
        return {"success": True, "issue_id": issue_id}

    # ==================== States ====================

    async def list_states(
        self, project_id: str, workspace_slug: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List issue states in project.

        Args:
            project_id: Project ID
            workspace_slug: Workspace slug

        Returns:
            List of state objects
        """
        ws = workspace_slug or self.workspace_slug
        if not ws:
            raise ValueError("Workspace slug not set")

        response = await self.client.get(
            f"{self.base_url}/api/workspaces/{ws}/projects/{project_id}/states/",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    async def get_state_by_name(
        self, project_id: str, state_name: str, workspace_slug: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get state by name.

        Args:
            project_id: Project ID
            state_name: State name (e.g., "Todo", "In Progress", "Done")
            workspace_slug: Workspace slug

        Returns:
            State object or None if not found
        """
        states = await self.list_states(project_id, workspace_slug)

        for state in states:
            if state.get("name", "").lower() == state_name.lower():
                return state

        return None

    # ==================== Cycles ====================

    async def list_cycles(
        self, project_id: str, workspace_slug: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List cycles in project.

        Args:
            project_id: Project ID
            workspace_slug: Workspace slug

        Returns:
            List of cycle objects
        """
        ws = workspace_slug or self.workspace_slug
        if not ws:
            raise ValueError("Workspace slug not set")

        response = await self.client.get(
            f"{self.base_url}/api/workspaces/{ws}/projects/{project_id}/cycles/",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    async def create_cycle(
        self,
        project_id: str,
        name: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        workspace_slug: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new cycle.

        Args:
            project_id: Project ID
            name: Cycle name
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            workspace_slug: Workspace slug

        Returns:
            Created cycle object
        """
        ws = workspace_slug or self.workspace_slug
        if not ws:
            raise ValueError("Workspace slug not set")

        data = {"name": name, "project": project_id}

        if start_date:
            data["start_date"] = start_date
        if end_date:
            data["end_date"] = end_date

        response = await self.client.post(
            f"{self.base_url}/api/workspaces/{ws}/projects/{project_id}/cycles/",
            headers=self._headers(),
            json=data,
        )
        response.raise_for_status()
        return response.json()

    # ==================== Modules ====================

    async def list_modules(
        self, project_id: str, workspace_slug: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List modules in project.

        Args:
            project_id: Project ID
            workspace_slug: Workspace slug

        Returns:
            List of module objects
        """
        ws = workspace_slug or self.workspace_slug
        if not ws:
            raise ValueError("Workspace slug not set")

        response = await self.client.get(
            f"{self.base_url}/api/workspaces/{ws}/projects/{project_id}/modules/",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    # ==================== Members ====================

    async def list_project_members(
        self, project_id: str, workspace_slug: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List members of a project.

        Args:
            project_id: Project ID
            workspace_slug: Workspace slug

        Returns:
            List of member objects
        """
        ws = workspace_slug or self.workspace_slug
        if not ws:
            raise ValueError("Workspace slug not set")

        response = await self.client.get(
            f"{self.base_url}/api/workspaces/{ws}/projects/{project_id}/members/",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    # ==================== Comments ====================

    async def add_comment(
        self,
        project_id: str,
        issue_id: str,
        comment: str,
        workspace_slug: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Add a comment to an issue.

        Args:
            project_id: Project ID
            issue_id: Issue ID
            comment: Comment text
            workspace_slug: Workspace slug

        Returns:
            Created comment object
        """
        ws = workspace_slug or self.workspace_slug
        if not ws:
            raise ValueError("Workspace slug not set")

        data = {"comment": comment, "issue": issue_id}

        response = await self.client.post(
            f"{self.base_url}/api/workspaces/{ws}/projects/{project_id}/issues/{issue_id}/comments/",
            headers=self._headers(),
            json=data,
        )
        response.raise_for_status()
        return response.json()

    # ==================== Utility Methods ====================

    async def search_issues(
        self, project_id: str, query: str, workspace_slug: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Search issues by name.

        Args:
            project_id: Project ID
            query: Search query
            workspace_slug: Workspace slug

        Returns:
            List of matching issues
        """
        all_issues = await self.list_issues(project_id, workspace_slug)

        # Filter by query
        query_lower = query.lower()
        matches = [
            issue
            for issue in all_issues
            if query_lower in issue.get("name", "").lower()
            or query_lower in issue.get("description", "").lower()
        ]

        return matches

    async def get_project_by_name(
        self, name: str, workspace_slug: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get project by name.

        Args:
            name: Project name
            workspace_slug: Workspace slug

        Returns:
            Project object or None if not found
        """
        projects = await self.list_projects(workspace_slug)

        for project in projects:
            if project.get("name", "").lower() == name.lower():
                return project

        return None

    async def create_issue_by_project_name(
        self,
        project_name: str,
        name: str,
        description: Optional[str] = None,
        state_id: Optional[str] = None,
        priority: Optional[str] = None,
        assignees: Optional[List[str]] = None,
        workspace_slug: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an issue by project name (convenience method).

        Args:
            project_name: Project name
            name: Issue title
            description: Issue description
            state_id: State ID
            priority: Priority (urgent, high, medium, low, none)
            assignees: List of user IDs to assign
            workspace_slug: Workspace slug

        Returns:
            Created issue object
        """
        project = await self.get_project_by_name(project_name, workspace_slug)
        if not project:
            raise ValueError(f"Project not found: {project_name}")

        return await self.create_issue(
            project_id=project["id"],
            name=name,
            description=description,
            state_id=state_id,
            priority=priority,
            assignees=assignees,
            workspace_slug=workspace_slug,
        )

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
