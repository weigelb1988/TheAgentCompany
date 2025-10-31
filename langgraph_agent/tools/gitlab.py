"""
GitLab API client for TheAgentCompany.

Provides comprehensive GitLab operations for repository management,
issue tracking, and merge requests.
"""

import httpx
from typing import List, Dict, Any, Optional
from urllib.parse import quote


class GitLabClient:
    """
    GitLab API client for TheAgentCompany tasks.

    Supports operations on:
    - Projects and repositories
    - Files and commits
    - Issues
    - Merge requests
    - Users
    """

    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize GitLab client.

        Args:
            base_url: GitLab base URL (e.g., http://localhost:8929)
            username: GitLab username
            password: GitLab password
        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.token: Optional[str] = None
        self.client = httpx.AsyncClient(verify=False, timeout=30.0)

    async def authenticate(self) -> Dict[str, Any]:
        """
        Authenticate and get access token.

        Returns:
            Authentication response with token
        """
        response = await self.client.post(
            f"{self.base_url}/api/v4/session",
            data={"login": self.username, "password": self.password},
        )
        response.raise_for_status()
        data = response.json()
        self.token = data.get("private_token")
        return data

    def _headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        if not self.token:
            raise ValueError("Not authenticated. Call authenticate() first.")
        return {"PRIVATE-TOKEN": self.token}

    # ==================== Projects ====================

    async def list_projects(
        self, visibility: Optional[str] = None, owned: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List all accessible projects.

        Args:
            visibility: Filter by visibility (public, internal, private)
            owned: Only owned projects

        Returns:
            List of project objects
        """
        if not self.token:
            await self.authenticate()

        params = {}
        if visibility:
            params["visibility"] = visibility
        if owned:
            params["owned"] = "true"

        response = await self.client.get(
            f"{self.base_url}/api/v4/projects", headers=self._headers(), params=params
        )
        response.raise_for_status()
        return response.json()

    async def get_project(self, project_id: int) -> Dict[str, Any]:
        """
        Get project details.

        Args:
            project_id: Project ID

        Returns:
            Project object
        """
        response = await self.client.get(
            f"{self.base_url}/api/v4/projects/{project_id}", headers=self._headers()
        )
        response.raise_for_status()
        return response.json()

    async def search_projects(self, search: str) -> List[Dict[str, Any]]:
        """
        Search projects by name.

        Args:
            search: Search query

        Returns:
            List of matching projects
        """
        response = await self.client.get(
            f"{self.base_url}/api/v4/projects",
            headers=self._headers(),
            params={"search": search},
        )
        response.raise_for_status()
        return response.json()

    # ==================== Repository Files ====================

    async def list_repository_tree(
        self, project_id: int, path: str = "", ref: str = "main", recursive: bool = False
    ) -> List[Dict[str, Any]]:
        """
        List files in repository.

        Args:
            project_id: Project ID
            path: Path within repository
            ref: Branch or tag name
            recursive: List recursively

        Returns:
            List of file/directory objects
        """
        params = {"path": path, "ref": ref, "recursive": recursive}

        response = await self.client.get(
            f"{self.base_url}/api/v4/projects/{project_id}/repository/tree",
            headers=self._headers(),
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def get_file(
        self, project_id: int, file_path: str, ref: str = "main"
    ) -> Dict[str, Any]:
        """
        Get file metadata and content.

        Args:
            project_id: Project ID
            file_path: Path to file in repository
            ref: Branch or tag name

        Returns:
            File object with content
        """
        encoded_path = quote(file_path, safe="")

        response = await self.client.get(
            f"{self.base_url}/api/v4/projects/{project_id}/repository/files/{encoded_path}",
            headers=self._headers(),
            params={"ref": ref},
        )
        response.raise_for_status()
        return response.json()

    async def get_file_raw(self, project_id: int, file_path: str, ref: str = "main") -> str:
        """
        Get raw file contents.

        Args:
            project_id: Project ID
            file_path: Path to file in repository
            ref: Branch or tag name

        Returns:
            Raw file contents as string
        """
        encoded_path = quote(file_path, safe="")

        response = await self.client.get(
            f"{self.base_url}/api/v4/projects/{project_id}/repository/files/{encoded_path}/raw",
            headers=self._headers(),
            params={"ref": ref},
        )
        response.raise_for_status()
        return response.text

    async def create_file(
        self,
        project_id: int,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str = "main",
        author_email: Optional[str] = None,
        author_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a new file in repository.

        Args:
            project_id: Project ID
            file_path: Path for new file
            content: File contents
            commit_message: Commit message
            branch: Target branch
            author_email: Author email
            author_name: Author name

        Returns:
            Created file object
        """
        encoded_path = quote(file_path, safe="")

        data = {
            "branch": branch,
            "content": content,
            "commit_message": commit_message,
        }

        if author_email:
            data["author_email"] = author_email
        if author_name:
            data["author_name"] = author_name

        response = await self.client.post(
            f"{self.base_url}/api/v4/projects/{project_id}/repository/files/{encoded_path}",
            headers=self._headers(),
            json=data,
        )
        response.raise_for_status()
        return response.json()

    async def update_file(
        self,
        project_id: int,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str = "main",
        author_email: Optional[str] = None,
        author_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing file in repository.

        Args:
            project_id: Project ID
            file_path: Path to file
            content: New file contents
            commit_message: Commit message
            branch: Target branch
            author_email: Author email
            author_name: Author name

        Returns:
            Updated file object
        """
        encoded_path = quote(file_path, safe="")

        data = {
            "branch": branch,
            "content": content,
            "commit_message": commit_message,
        }

        if author_email:
            data["author_email"] = author_email
        if author_name:
            data["author_name"] = author_name

        response = await self.client.put(
            f"{self.base_url}/api/v4/projects/{project_id}/repository/files/{encoded_path}",
            headers=self._headers(),
            json=data,
        )
        response.raise_for_status()
        return response.json()

    # ==================== Issues ====================

    async def list_issues(
        self,
        project_id: Optional[int] = None,
        state: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        List issues.

        Args:
            project_id: Project ID (None for all projects)
            state: Filter by state (opened, closed, all)
            labels: Filter by labels

        Returns:
            List of issue objects
        """
        if project_id:
            url = f"{self.base_url}/api/v4/projects/{project_id}/issues"
        else:
            url = f"{self.base_url}/api/v4/issues"

        params = {}
        if state:
            params["state"] = state
        if labels:
            params["labels"] = ",".join(labels)

        response = await self.client.get(url, headers=self._headers(), params=params)
        response.raise_for_status()
        return response.json()

    async def get_issue(self, project_id: int, issue_iid: int) -> Dict[str, Any]:
        """
        Get issue details.

        Args:
            project_id: Project ID
            issue_iid: Issue IID (not ID)

        Returns:
            Issue object
        """
        response = await self.client.get(
            f"{self.base_url}/api/v4/projects/{project_id}/issues/{issue_iid}",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    async def create_issue(
        self,
        project_id: int,
        title: str,
        description: Optional[str] = None,
        labels: Optional[List[str]] = None,
        assignee_ids: Optional[List[int]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new issue.

        Args:
            project_id: Project ID
            title: Issue title
            description: Issue description
            labels: Issue labels
            assignee_ids: User IDs to assign

        Returns:
            Created issue object
        """
        data = {"title": title}

        if description:
            data["description"] = description
        if labels:
            data["labels"] = ",".join(labels)
        if assignee_ids:
            data["assignee_ids"] = assignee_ids

        response = await self.client.post(
            f"{self.base_url}/api/v4/projects/{project_id}/issues",
            headers=self._headers(),
            json=data,
        )
        response.raise_for_status()
        return response.json()

    async def update_issue(
        self,
        project_id: int,
        issue_iid: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        state_event: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Update an issue.

        Args:
            project_id: Project ID
            issue_iid: Issue IID
            title: New title
            description: New description
            state_event: State change (close, reopen)
            labels: New labels

        Returns:
            Updated issue object
        """
        data = {}

        if title:
            data["title"] = title
        if description:
            data["description"] = description
        if state_event:
            data["state_event"] = state_event
        if labels:
            data["labels"] = ",".join(labels)

        response = await self.client.put(
            f"{self.base_url}/api/v4/projects/{project_id}/issues/{issue_iid}",
            headers=self._headers(),
            json=data,
        )
        response.raise_for_status()
        return response.json()

    # ==================== Merge Requests ====================

    async def list_merge_requests(
        self, project_id: int, state: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List merge requests.

        Args:
            project_id: Project ID
            state: Filter by state (opened, closed, merged, all)

        Returns:
            List of merge request objects
        """
        params = {}
        if state:
            params["state"] = state

        response = await self.client.get(
            f"{self.base_url}/api/v4/projects/{project_id}/merge_requests",
            headers=self._headers(),
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def get_merge_request(self, project_id: int, mr_iid: int) -> Dict[str, Any]:
        """
        Get merge request details.

        Args:
            project_id: Project ID
            mr_iid: MR IID (not ID)

        Returns:
            Merge request object
        """
        response = await self.client.get(
            f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    async def create_merge_request(
        self,
        project_id: int,
        source_branch: str,
        target_branch: str,
        title: str,
        description: Optional[str] = None,
        assignee_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a merge request.

        Args:
            project_id: Project ID
            source_branch: Source branch name
            target_branch: Target branch name
            title: MR title
            description: MR description
            assignee_id: User ID to assign

        Returns:
            Created merge request object
        """
        data = {
            "source_branch": source_branch,
            "target_branch": target_branch,
            "title": title,
        }

        if description:
            data["description"] = description
        if assignee_id:
            data["assignee_id"] = assignee_id

        response = await self.client.post(
            f"{self.base_url}/api/v4/projects/{project_id}/merge_requests",
            headers=self._headers(),
            json=data,
        )
        response.raise_for_status()
        return response.json()

    async def update_merge_request(
        self,
        project_id: int,
        mr_iid: int,
        title: Optional[str] = None,
        description: Optional[str] = None,
        state_event: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Update a merge request.

        Args:
            project_id: Project ID
            mr_iid: MR IID
            title: New title
            description: New description
            state_event: State change (close, reopen, merge)

        Returns:
            Updated merge request object
        """
        data = {}

        if title:
            data["title"] = title
        if description:
            data["description"] = description
        if state_event:
            data["state_event"] = state_event

        response = await self.client.put(
            f"{self.base_url}/api/v4/projects/{project_id}/merge_requests/{mr_iid}",
            headers=self._headers(),
            json=data,
        )
        response.raise_for_status()
        return response.json()

    # ==================== Branches ====================

    async def list_branches(self, project_id: int) -> List[Dict[str, Any]]:
        """
        List repository branches.

        Args:
            project_id: Project ID

        Returns:
            List of branch objects
        """
        response = await self.client.get(
            f"{self.base_url}/api/v4/projects/{project_id}/repository/branches",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    async def create_branch(
        self, project_id: int, branch: str, ref: str
    ) -> Dict[str, Any]:
        """
        Create a new branch.

        Args:
            project_id: Project ID
            branch: New branch name
            ref: Source branch/commit

        Returns:
            Created branch object
        """
        data = {"branch": branch, "ref": ref}

        response = await self.client.post(
            f"{self.base_url}/api/v4/projects/{project_id}/repository/branches",
            headers=self._headers(),
            json=data,
        )
        response.raise_for_status()
        return response.json()

    # ==================== Commits ====================

    async def list_commits(
        self, project_id: int, ref_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List repository commits.

        Args:
            project_id: Project ID
            ref_name: Branch/tag name

        Returns:
            List of commit objects
        """
        params = {}
        if ref_name:
            params["ref_name"] = ref_name

        response = await self.client.get(
            f"{self.base_url}/api/v4/projects/{project_id}/repository/commits",
            headers=self._headers(),
            params=params,
        )
        response.raise_for_status()
        return response.json()

    async def get_commit(self, project_id: int, sha: str) -> Dict[str, Any]:
        """
        Get commit details.

        Args:
            project_id: Project ID
            sha: Commit SHA

        Returns:
            Commit object
        """
        response = await self.client.get(
            f"{self.base_url}/api/v4/projects/{project_id}/repository/commits/{sha}",
            headers=self._headers(),
        )
        response.raise_for_status()
        return response.json()

    # ==================== Utility Methods ====================

    async def get_project_by_name(self, project_name: str) -> Optional[Dict[str, Any]]:
        """
        Get project by name.

        Args:
            project_name: Project name or path (e.g., "root/my-project")

        Returns:
            Project object or None if not found
        """
        projects = await self.search_projects(project_name)

        # Try exact match first
        for project in projects:
            if project["path_with_namespace"] == project_name or project["name"] == project_name:
                return project

        # Return first result if no exact match
        return projects[0] if projects else None

    async def get_file_by_project_name(
        self, project_name: str, file_path: str, ref: str = "main"
    ) -> str:
        """
        Get file from repository by project name.

        This is a convenience method that looks up the project ID first.

        Args:
            project_name: Project name
            file_path: Path to file in repository
            ref: Branch or tag name

        Returns:
            Raw file contents as string
        """
        project = await self.get_project_by_name(project_name)
        if not project:
            raise ValueError(f"Project not found: {project_name}")

        return await self.get_file_raw(project["id"], file_path, ref)

    async def create_issue_by_project_name(
        self,
        project_name: str,
        title: str,
        description: Optional[str] = None,
        labels: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create issue by project name.

        Args:
            project_name: Project name
            title: Issue title
            description: Issue description
            labels: Issue labels

        Returns:
            Created issue object
        """
        project = await self.get_project_by_name(project_name)
        if not project:
            raise ValueError(f"Project not found: {project_name}")

        return await self.create_issue(project["id"], title, description, labels)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
