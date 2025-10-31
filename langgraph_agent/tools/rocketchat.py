"""
RocketChat API client for TheAgentCompany.

Provides comprehensive RocketChat operations for team communication,
channels, direct messages, and user management.
"""

import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime


class RocketChatClient:
    """
    RocketChat API client for TheAgentCompany tasks.

    Supports operations on:
    - Channels (public rooms)
    - Direct messages
    - Messages
    - Users
    """

    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize RocketChat client.

        Args:
            base_url: RocketChat base URL (e.g., http://localhost:3000)
            username: RocketChat username
            password: RocketChat password
        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.password = password
        self.auth_token: Optional[str] = None
        self.user_id: Optional[str] = None
        self.client = httpx.AsyncClient(timeout=30.0)

    async def login(self) -> Dict[str, Any]:
        """
        Login to RocketChat and get auth token.

        Returns:
            Login response with auth token and user ID
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/login",
            json={"username": self.username, "password": self.password},
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") == "success":
            auth_data = data["data"]
            self.auth_token = auth_data["authToken"]
            self.user_id = auth_data["userId"]
            return auth_data
        else:
            raise ValueError(f"Login failed: {data}")

    def _headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        if not self.auth_token or not self.user_id:
            raise ValueError("Not authenticated. Call login() first.")
        return {"X-Auth-Token": self.auth_token, "X-User-Id": self.user_id}

    # ==================== Channels ====================

    async def list_channels(self) -> List[Dict[str, Any]]:
        """
        List all public channels.

        Returns:
            List of channel objects
        """
        if not self.auth_token:
            await self.login()

        response = await self.client.get(
            f"{self.base_url}/api/v1/channels.list", headers=self._headers()
        )
        response.raise_for_status()
        return response.json()["channels"]

    async def get_channel_info(
        self, room_id: Optional[str] = None, room_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get channel information.

        Args:
            room_id: Channel ID
            room_name: Channel name (without #)

        Returns:
            Channel object
        """
        params = {}
        if room_id:
            params["roomId"] = room_id
        elif room_name:
            params["roomName"] = room_name
        else:
            raise ValueError("Either room_id or room_name must be provided")

        response = await self.client.get(
            f"{self.base_url}/api/v1/channels.info", headers=self._headers(), params=params
        )
        response.raise_for_status()
        return response.json()["channel"]

    async def create_channel(
        self, name: str, members: Optional[List[str]] = None, read_only: bool = False
    ) -> Dict[str, Any]:
        """
        Create a new channel.

        Args:
            name: Channel name (without #)
            members: List of usernames to add
            read_only: Make channel read-only

        Returns:
            Created channel object
        """
        data = {"name": name, "readOnly": read_only}

        if members:
            data["members"] = members

        response = await self.client.post(
            f"{self.base_url}/api/v1/channels.create", headers=self._headers(), json=data
        )
        response.raise_for_status()
        return response.json()["channel"]

    async def get_channel_history(
        self,
        room_id: str,
        count: int = 50,
        oldest: Optional[str] = None,
        latest: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get channel message history.

        Args:
            room_id: Channel ID
            count: Number of messages to retrieve
            oldest: Oldest message timestamp
            latest: Latest message timestamp

        Returns:
            List of message objects
        """
        params = {"roomId": room_id, "count": count}

        if oldest:
            params["oldest"] = oldest
        if latest:
            params["latest"] = latest

        response = await self.client.get(
            f"{self.base_url}/api/v1/channels.history", headers=self._headers(), params=params
        )
        response.raise_for_status()
        return response.json()["messages"]

    async def join_channel(
        self, room_id: Optional[str] = None, room_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Join a channel.

        Args:
            room_id: Channel ID
            room_name: Channel name (without #)

        Returns:
            Join response
        """
        data = {}
        if room_id:
            data["roomId"] = room_id
        elif room_name:
            data["roomName"] = room_name
        else:
            raise ValueError("Either room_id or room_name must be provided")

        response = await self.client.post(
            f"{self.base_url}/api/v1/channels.join", headers=self._headers(), json=data
        )
        response.raise_for_status()
        return response.json()

    async def leave_channel(self, room_id: str) -> Dict[str, Any]:
        """
        Leave a channel.

        Args:
            room_id: Channel ID

        Returns:
            Leave response
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/channels.leave",
            headers=self._headers(),
            json={"roomId": room_id},
        )
        response.raise_for_status()
        return response.json()

    # ==================== Direct Messages ====================

    async def list_direct_messages(self) -> List[Dict[str, Any]]:
        """
        List all direct message conversations.

        Returns:
            List of DM objects
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/im.list", headers=self._headers()
        )
        response.raise_for_status()
        return response.json()["ims"]

    async def create_direct_message(self, username: str) -> Dict[str, Any]:
        """
        Create a direct message conversation.

        Args:
            username: Username to start DM with

        Returns:
            Created DM object
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/im.create",
            headers=self._headers(),
            json={"username": username},
        )
        response.raise_for_status()
        return response.json()["room"]

    async def get_direct_message_history(
        self, room_id: str, count: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get direct message history.

        Args:
            room_id: DM room ID
            count: Number of messages to retrieve

        Returns:
            List of message objects
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/im.history",
            headers=self._headers(),
            params={"roomId": room_id, "count": count},
        )
        response.raise_for_status()
        return response.json()["messages"]

    # ==================== Messages ====================

    async def send_message(
        self,
        room_id: str,
        text: str,
        alias: Optional[str] = None,
        emoji: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a message to a channel or DM.

        Args:
            room_id: Room ID (channel or DM)
            text: Message text
            alias: Display name override
            emoji: Avatar emoji

        Returns:
            Sent message object
        """
        data = {"roomId": room_id, "text": text}

        if alias:
            data["alias"] = alias
        if emoji:
            data["emoji"] = emoji

        response = await self.client.post(
            f"{self.base_url}/api/v1/chat.postMessage", headers=self._headers(), json=data
        )
        response.raise_for_status()
        return response.json()

    async def update_message(self, message_id: str, text: str) -> Dict[str, Any]:
        """
        Update an existing message.

        Args:
            message_id: Message ID
            text: New message text

        Returns:
            Updated message object
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/chat.update",
            headers=self._headers(),
            json={"msgId": message_id, "text": text},
        )
        response.raise_for_status()
        return response.json()

    async def delete_message(self, room_id: str, message_id: str) -> Dict[str, Any]:
        """
        Delete a message.

        Args:
            room_id: Room ID
            message_id: Message ID

        Returns:
            Delete response
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/chat.delete",
            headers=self._headers(),
            json={"roomId": room_id, "msgId": message_id},
        )
        response.raise_for_status()
        return response.json()

    async def get_message(self, message_id: str) -> Dict[str, Any]:
        """
        Get a specific message.

        Args:
            message_id: Message ID

        Returns:
            Message object
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/chat.getMessage",
            headers=self._headers(),
            params={"msgId": message_id},
        )
        response.raise_for_status()
        return response.json()["message"]

    async def react_to_message(self, message_id: str, emoji: str) -> Dict[str, Any]:
        """
        React to a message with an emoji.

        Args:
            message_id: Message ID
            emoji: Emoji to react with (e.g., "thumbsup")

        Returns:
            Reaction response
        """
        response = await self.client.post(
            f"{self.base_url}/api/v1/chat.react",
            headers=self._headers(),
            json={"messageId": message_id, "emoji": emoji},
        )
        response.raise_for_status()
        return response.json()

    # ==================== Users ====================

    async def get_user_info(
        self, user_id: Optional[str] = None, username: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get user information.

        Args:
            user_id: User ID
            username: Username

        Returns:
            User object
        """
        params = {}
        if user_id:
            params["userId"] = user_id
        elif username:
            params["username"] = username
        else:
            raise ValueError("Either user_id or username must be provided")

        response = await self.client.get(
            f"{self.base_url}/api/v1/users.info", headers=self._headers(), params=params
        )
        response.raise_for_status()
        return response.json()["user"]

    async def list_users(self) -> List[Dict[str, Any]]:
        """
        List all users.

        Returns:
            List of user objects
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/users.list", headers=self._headers()
        )
        response.raise_for_status()
        return response.json()["users"]

    async def search_users(self, query: str) -> List[Dict[str, Any]]:
        """
        Search for users.

        Args:
            query: Search query

        Returns:
            List of matching user objects
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/users.list",
            headers=self._headers(),
            params={"query": {"username": {"$regex": query, "$options": "i"}}},
        )
        response.raise_for_status()
        return response.json()["users"]

    async def get_user_presence(self, user_id: str) -> Dict[str, Any]:
        """
        Get user's online status.

        Args:
            user_id: User ID

        Returns:
            Presence object with status
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/users.getPresence",
            headers=self._headers(),
            params={"userId": user_id},
        )
        response.raise_for_status()
        return response.json()["presence"]

    # ==================== Groups (Private Channels) ====================

    async def list_groups(self) -> List[Dict[str, Any]]:
        """
        List all private groups/channels.

        Returns:
            List of group objects
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/groups.list", headers=self._headers()
        )
        response.raise_for_status()
        return response.json()["groups"]

    async def get_group_history(
        self, room_id: str, count: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get private group message history.

        Args:
            room_id: Group ID
            count: Number of messages to retrieve

        Returns:
            List of message objects
        """
        response = await self.client.get(
            f"{self.base_url}/api/v1/groups.history",
            headers=self._headers(),
            params={"roomId": room_id, "count": count},
        )
        response.raise_for_status()
        return response.json()["messages"]

    # ==================== Utility Methods ====================

    async def get_room_id(self, room_name: str) -> Optional[str]:
        """
        Get room ID from room name.

        Args:
            room_name: Room name (without # or @)

        Returns:
            Room ID if found, None otherwise
        """
        # Try channels first
        try:
            channel = await self.get_channel_info(room_name=room_name)
            return channel["_id"]
        except:
            pass

        # Try groups
        try:
            groups = await self.list_groups()
            for group in groups:
                if group["name"] == room_name:
                    return group["_id"]
        except:
            pass

        # Try DMs
        try:
            dms = await self.list_direct_messages()
            for dm in dms:
                if dm.get("name") == room_name:
                    return dm["_id"]
        except:
            pass

        return None

    async def send_message_to_room(self, room_name: str, text: str) -> Dict[str, Any]:
        """
        Send message to a room by name.

        Args:
            room_name: Room name
            text: Message text

        Returns:
            Sent message object
        """
        room_id = await self.get_room_id(room_name)
        if not room_id:
            raise ValueError(f"Room not found: {room_name}")

        return await self.send_message(room_id, text)

    async def get_messages_from_user(
        self, room_id: str, username: str, count: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a specific user in a room.

        Args:
            room_id: Room ID
            username: Username to filter by
            count: Max messages to retrieve

        Returns:
            List of messages from user
        """
        # Get room type and history
        try:
            history = await self.get_channel_history(room_id, count=count)
        except:
            try:
                history = await self.get_direct_message_history(room_id, count=count)
            except:
                history = await self.get_group_history(room_id, count=count)

        # Filter by username
        return [msg for msg in history if msg.get("u", {}).get("username") == username]

    async def send_direct_message_to_user(
        self, username: str, text: str
    ) -> Dict[str, Any]:
        """
        Send a direct message to a user by username.

        This is a convenience method that handles the DM room lookup/creation
        automatically.

        Args:
            username: Username to send DM to
            text: Message text

        Returns:
            Sent message object
        """
        # Try to find existing DM
        dms = await self.list_direct_messages()
        room_id = None

        for dm in dms:
            # Check if this DM is with the target user
            usernames = dm.get("usernames", [])
            if username in usernames:
                room_id = dm["_id"]
                break

        # If no existing DM, create one
        if not room_id:
            dm = await self.create_direct_message(username)
            room_id = dm["_id"]

        # Send message
        return await self.send_message(room_id, text)

    async def get_channel_history_by_name(
        self, channel_name: str, count: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get channel history by channel name.

        Args:
            channel_name: Channel name (without #)
            count: Number of messages to retrieve

        Returns:
            List of message objects
        """
        room_id = await self.get_room_id(channel_name)
        if not room_id:
            raise ValueError(f"Channel not found: {channel_name}")

        return await self.get_channel_history(room_id, count)

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
