"""
ownCloud API client for TheAgentCompany.

Provides comprehensive ownCloud operations for file sharing,
using WebDAV protocol for file operations.
"""

import httpx
from typing import List, Dict, Any, Optional
from xml.etree import ElementTree as ET
from urllib.parse import quote
import base64


class OwnCloudClient:
    """
    ownCloud API client for TheAgentCompany tasks.

    Supports operations on:
    - Files and folders (WebDAV)
    - Sharing
    - Users
    """

    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize ownCloud client.

        Args:
            base_url: ownCloud base URL (e.g., http://localhost:8092)
            username: ownCloud username
            password: ownCloud password
        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.webdav_url = f"{self.base_url}/remote.php/webdav"
        self.ocs_url = f"{self.base_url}/ocs/v1.php"

        # Create auth for WebDAV
        auth_string = f"{username}:{password}"
        encoded = base64.b64encode(auth_string.encode()).decode()
        self.auth_header = f"Basic {encoded}"

        self.client = httpx.AsyncClient(verify=False, timeout=30.0)

    def _webdav_headers(self) -> Dict[str, str]:
        """Get WebDAV authentication headers."""
        return {"Authorization": self.auth_header}

    def _ocs_headers(self) -> Dict[str, str]:
        """Get OCS API headers."""
        return {
            "Authorization": self.auth_header,
            "OCS-APIRequest": "true",
            "Accept": "application/json",
        }

    # ==================== File Operations (WebDAV) ====================

    async def list_folder(self, path: str = "/") -> List[Dict[str, Any]]:
        """
        List contents of a folder.

        Args:
            path: Path to folder (default: root)

        Returns:
            List of file/folder objects
        """
        # Ensure path starts with /
        if not path.startswith("/"):
            path = "/" + path

        # Remove trailing slash for non-root
        if path != "/" and path.endswith("/"):
            path = path[:-1]

        url = f"{self.webdav_url}{path}"

        response = await self.client.request(
            "PROPFIND",
            url,
            headers={
                **self._webdav_headers(),
                "Depth": "1",
                "Content-Type": "application/xml",
            },
        )
        response.raise_for_status()

        # Parse WebDAV XML response
        root = ET.fromstring(response.content)
        namespace = {"d": "DAV:"}

        items = []
        for response_elem in root.findall("d:response", namespace):
            href = response_elem.find("d:href", namespace)
            propstat = response_elem.find("d:propstat", namespace)

            if href is not None and propstat is not None:
                prop = propstat.find("d:prop", namespace)
                if prop is not None:
                    item_path = href.text

                    # Skip the parent directory itself
                    if item_path.rstrip("/") == f"/remote.php/webdav{path}".rstrip("/"):
                        continue

                    resourcetype = prop.find("d:resourcetype", namespace)
                    is_collection = (
                        resourcetype is not None
                        and resourcetype.find("d:collection", namespace) is not None
                    )

                    # Get file properties
                    getcontentlength = prop.find("d:getcontentlength", namespace)
                    getlastmodified = prop.find("d:getlastmodified", namespace)
                    getcontenttype = prop.find("d:getcontenttype", namespace)

                    # Extract name from path
                    name = item_path.rstrip("/").split("/")[-1]

                    item = {
                        "name": name,
                        "path": item_path.replace("/remote.php/webdav", ""),
                        "type": "directory" if is_collection else "file",
                        "size": (
                            int(getcontentlength.text) if getcontentlength is not None else None
                        ),
                        "modified": getlastmodified.text if getlastmodified is not None else None,
                        "content_type": (
                            getcontenttype.text if getcontenttype is not None else None
                        ),
                    }

                    items.append(item)

        return items

    async def get_file(self, path: str) -> bytes:
        """
        Download a file.

        Args:
            path: Path to file

        Returns:
            File contents as bytes
        """
        if not path.startswith("/"):
            path = "/" + path

        url = f"{self.webdav_url}{path}"

        response = await self.client.get(url, headers=self._webdav_headers())
        response.raise_for_status()
        return response.content

    async def get_file_text(self, path: str) -> str:
        """
        Download a file as text.

        Args:
            path: Path to file

        Returns:
            File contents as string
        """
        content = await self.get_file(path)
        return content.decode("utf-8")

    async def upload_file(self, path: str, content: bytes) -> Dict[str, Any]:
        """
        Upload a file.

        Args:
            path: Path for new file
            content: File contents as bytes

        Returns:
            Upload response
        """
        if not path.startswith("/"):
            path = "/" + path

        url = f"{self.webdav_url}{path}"

        response = await self.client.put(url, headers=self._webdav_headers(), content=content)
        response.raise_for_status()
        return {"success": True, "path": path, "status_code": response.status_code}

    async def upload_file_text(self, path: str, content: str) -> Dict[str, Any]:
        """
        Upload a text file.

        Args:
            path: Path for new file
            content: File contents as string

        Returns:
            Upload response
        """
        return await self.upload_file(path, content.encode("utf-8"))

    async def create_folder(self, path: str) -> Dict[str, Any]:
        """
        Create a folder.

        Args:
            path: Path for new folder

        Returns:
            Creation response
        """
        if not path.startswith("/"):
            path = "/" + path

        url = f"{self.webdav_url}{path}"

        response = await self.client.request("MKCOL", url, headers=self._webdav_headers())
        response.raise_for_status()
        return {"success": True, "path": path, "status_code": response.status_code}

    async def delete(self, path: str) -> Dict[str, Any]:
        """
        Delete a file or folder.

        Args:
            path: Path to delete

        Returns:
            Deletion response
        """
        if not path.startswith("/"):
            path = "/" + path

        url = f"{self.webdav_url}{path}"

        response = await self.client.delete(url, headers=self._webdav_headers())
        response.raise_for_status()
        return {"success": True, "path": path, "status_code": response.status_code}

    async def move(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Move or rename a file/folder.

        Args:
            source: Source path
            destination: Destination path

        Returns:
            Move response
        """
        if not source.startswith("/"):
            source = "/" + source
        if not destination.startswith("/"):
            destination = "/" + destination

        source_url = f"{self.webdav_url}{source}"
        dest_url = f"{self.webdav_url}{destination}"

        response = await self.client.request(
            "MOVE",
            source_url,
            headers={**self._webdav_headers(), "Destination": dest_url},
        )
        response.raise_for_status()
        return {
            "success": True,
            "source": source,
            "destination": destination,
            "status_code": response.status_code,
        }

    async def copy(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Copy a file/folder.

        Args:
            source: Source path
            destination: Destination path

        Returns:
            Copy response
        """
        if not source.startswith("/"):
            source = "/" + source
        if not destination.startswith("/"):
            destination = "/" + destination

        source_url = f"{self.webdav_url}{source}"
        dest_url = f"{self.webdav_url}{destination}"

        response = await self.client.request(
            "COPY",
            source_url,
            headers={**self._webdav_headers(), "Destination": dest_url},
        )
        response.raise_for_status()
        return {
            "success": True,
            "source": source,
            "destination": destination,
            "status_code": response.status_code,
        }

    async def file_exists(self, path: str) -> bool:
        """
        Check if a file or folder exists.

        Args:
            path: Path to check

        Returns:
            True if exists, False otherwise
        """
        if not path.startswith("/"):
            path = "/" + path

        url = f"{self.webdav_url}{path}"

        try:
            response = await self.client.request("PROPFIND", url, headers=self._webdav_headers())
            return response.status_code == 207  # Multi-Status = exists
        except httpx.HTTPStatusError:
            return False

    # ==================== Sharing (OCS API) ====================

    async def create_share(
        self,
        path: str,
        share_type: int = 3,  # 3 = public link
        permissions: int = 1,  # 1 = read
        password: Optional[str] = None,
        expire_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create a share (public link or user share).

        Args:
            path: Path to share
            share_type: 0=user, 1=group, 3=public link
            permissions: 1=read, 15=read+write+create+delete
            password: Share password (for public links)
            expire_date: Expiration date (YYYY-MM-DD)

        Returns:
            Share object
        """
        data = {
            "path": path if path.startswith("/") else f"/{path}",
            "shareType": share_type,
            "permissions": permissions,
        }

        if password:
            data["password"] = password
        if expire_date:
            data["expireDate"] = expire_date

        response = await self.client.post(
            f"{self.ocs_url}/apps/files_sharing/api/v1/shares",
            headers=self._ocs_headers(),
            data=data,
            params={"format": "json"},
        )
        response.raise_for_status()
        result = response.json()

        if result.get("ocs", {}).get("meta", {}).get("status") == "ok":
            return result["ocs"]["data"]
        else:
            raise ValueError(f"Share creation failed: {result}")

    async def list_shares(self, path: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List shares.

        Args:
            path: Filter by path (optional)

        Returns:
            List of share objects
        """
        params = {"format": "json"}
        if path:
            params["path"] = path if path.startswith("/") else f"/{path}"

        response = await self.client.get(
            f"{self.ocs_url}/apps/files_sharing/api/v1/shares",
            headers=self._ocs_headers(),
            params=params,
        )
        response.raise_for_status()
        result = response.json()

        if result.get("ocs", {}).get("meta", {}).get("status") == "ok":
            data = result["ocs"]["data"]
            # Handle both list and single item response
            return data if isinstance(data, list) else [data] if data else []
        else:
            raise ValueError(f"List shares failed: {result}")

    async def delete_share(self, share_id: int) -> Dict[str, Any]:
        """
        Delete a share.

        Args:
            share_id: Share ID

        Returns:
            Deletion response
        """
        response = await self.client.delete(
            f"{self.ocs_url}/apps/files_sharing/api/v1/shares/{share_id}",
            headers=self._ocs_headers(),
            params={"format": "json"},
        )
        response.raise_for_status()
        result = response.json()

        if result.get("ocs", {}).get("meta", {}).get("status") == "ok":
            return {"success": True, "share_id": share_id}
        else:
            raise ValueError(f"Delete share failed: {result}")

    async def get_share_link(self, path: str, password: Optional[str] = None) -> str:
        """
        Create a public share link for a file/folder.

        Args:
            path: Path to share
            password: Optional password protection

        Returns:
            Public share URL
        """
        share = await self.create_share(path, share_type=3, permissions=1, password=password)
        return share.get("url", "")

    # ==================== User Operations (OCS API) ====================

    async def get_user_info(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get user information.

        Args:
            user_id: User ID (default: current user)

        Returns:
            User object
        """
        user = user_id or self.username

        response = await self.client.get(
            f"{self.ocs_url}/cloud/users/{user}",
            headers=self._ocs_headers(),
            params={"format": "json"},
        )
        response.raise_for_status()
        result = response.json()

        if result.get("ocs", {}).get("meta", {}).get("status") == "ok":
            return result["ocs"]["data"]
        else:
            raise ValueError(f"Get user info failed: {result}")

    # ==================== Utility Methods ====================

    async def search_files(
        self, pattern: str, folder: str = "/"
    ) -> List[Dict[str, Any]]:
        """
        Search for files matching a pattern.

        Args:
            pattern: Search pattern (filename contains)
            folder: Folder to search in

        Returns:
            List of matching files
        """
        items = await self.list_folder(folder)

        # Search recursively
        matches = []
        for item in items:
            if pattern.lower() in item["name"].lower():
                matches.append(item)

            # Recursively search subdirectories
            if item["type"] == "directory":
                try:
                    sub_matches = await self.search_files(pattern, item["path"])
                    matches.extend(sub_matches)
                except:
                    pass  # Skip inaccessible folders

        return matches

    async def get_file_info(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a file/folder.

        Args:
            path: Path to file/folder

        Returns:
            File info object or None if not found
        """
        # Get parent folder
        parent = "/".join(path.rstrip("/").split("/")[:-1])
        if not parent:
            parent = "/"

        name = path.rstrip("/").split("/")[-1]

        try:
            items = await self.list_folder(parent)
            for item in items:
                if item["name"] == name:
                    return item
        except:
            pass

        return None

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
