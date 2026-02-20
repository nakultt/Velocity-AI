"""
Velocity AI – Slack LangChain Tool
Reads channels, messages, and posts updates via Slack Web API.
Used by the Workspace Ingestor to synthesise team communication.
"""

from __future__ import annotations

import os
from typing import Optional

import httpx
from langchain_core.tools import BaseTool
from pydantic import Field


SLACK_API = "https://slack.com/api"


class SlackTool(BaseTool):
    """
    LangChain tool that wraps the Slack Web API.

    Capabilities:
    - List channels the bot is in
    - Read recent messages from a channel
    - Search messages across the workspace
    - Post a message to a channel

    Used by: IngestorNode, ContextMatcherNode, SummaryNode
    """

    name: str = "slack"
    description: str = (
        "Access Slack workspace: list channels, read messages, search, and post. "
        "Use action='channels' to list channels, 'messages #channel' to read, "
        "'search query' to search, 'post #channel message' to send."
    )
    token: str = Field(default="")

    # ── entry-point ───────────────────────────────────────
    def _run(self, query: str) -> str:
        import asyncio
        return asyncio.run(self._arun(query))

    async def _arun(self, query: str) -> str:
        from services.db_service import mongodb
        t = await mongodb.get_token("slack")
        if t:
            self.token = t.get("token", "")
            
        if not self.token:
            return "Slack not configured. Please connect from the UI."
            
        parts = query.strip().split(maxsplit=1)
        action = parts[0].lower() if parts else "channels"
        arg = parts[1] if len(parts) > 1 else ""

        dispatch = {
            "channels": self._list_channels,
            "messages": self._read_messages,
            "search": self._search_messages,
            "post": self._post_message,
        }

        handler = dispatch.get(action, self._list_channels)
        return await handler(arg)

    # ── helpers ───────────────────────────────────────────
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json; charset=utf-8",
        }

    async def _api(
        self, method: str, endpoint: str, params: Optional[dict] = None, json_body: Optional[dict] = None
    ) -> dict:
        async with httpx.AsyncClient() as client:
            if method == "GET":
                resp = await client.get(
                    f"{SLACK_API}/{endpoint}",
                    headers=self._headers(),
                    params=params or {},
                    timeout=15,
                )
            else:
                resp = await client.post(
                    f"{SLACK_API}/{endpoint}",
                    headers=self._headers(),
                    json=json_body or {},
                    timeout=15,
                )
            return resp.json()

    # ── actions ───────────────────────────────────────────
    async def _list_channels(self, _: str = "") -> str:
        """List channels the bot has access to."""
        try:
            data = await self._api("GET", "conversations.list", {
                "types": "public_channel,private_channel",
                "limit": 20,
            })
            if not data.get("ok"):
                return f"Slack error: {data.get('error', 'unknown')}"
            channels = data.get("channels", [])
            lines = []
            for ch in channels:
                members = ch.get("num_members", "?")
                lines.append(
                    f"• #{ch['name']} ({members} members) "
                    f"{'🔒' if ch.get('is_private') else '🌐'}"
                )
            return "\n".join(lines) or "No channels found."
        except Exception as e:
            return f"Slack API error: {e}"

    async def _read_messages(self, channel_ref: str) -> str:
        """Read recent messages from a channel. Accepts #channel-name or channel ID."""
        channel_id = channel_ref.strip().lstrip("#")

        # Resolve channel name → ID if needed
        if not channel_id.startswith("C"):
            resolved = await self._resolve_channel(channel_id)
            if not resolved:
                return f"Could not find channel '{channel_ref}'."
            channel_id = resolved

        try:
            data = await self._api("GET", "conversations.history", {
                "channel": channel_id,
                "limit": 15,
            })
            if not data.get("ok"):
                return f"Slack error: {data.get('error', 'unknown')}"

            messages = data.get("messages", [])
            lines = []
            for msg in messages:
                user = msg.get("user", "bot")
                text = msg.get("text", "")[:120]
                lines.append(f"• [{user}] {text}")
            return "\n".join(lines) or "No messages."
        except Exception as e:
            return f"Slack API error: {e}"

    async def _search_messages(self, query: str) -> str:
        """Search messages across the workspace."""
        if not query:
            return "Please provide a search query."
        try:
            data = await self._api("GET", "search.messages", {
                "query": query,
                "count": 10,
                "sort": "timestamp",
            })
            if not data.get("ok"):
                return f"Slack error: {data.get('error', 'unknown')}"

            matches = data.get("messages", {}).get("matches", [])
            lines = []
            for m in matches:
                ch = m.get("channel", {}).get("name", "?")
                user = m.get("username", "?")
                text = m.get("text", "")[:100]
                lines.append(f"• #{ch} [{user}]: {text}")
            return "\n".join(lines) or "No matches found."
        except Exception as e:
            return f"Slack API error: {e}"

    async def _post_message(self, args: str) -> str:
        """Post a message. Format: '#channel message text'."""
        parts = args.split(maxsplit=1)
        if len(parts) < 2:
            return "Provide '#channel message'."
        channel_ref, text = parts
        channel_id = channel_ref.strip().lstrip("#")

        if not channel_id.startswith("C"):
            resolved = await self._resolve_channel(channel_id)
            if not resolved:
                return f"Could not find channel '{channel_ref}'."
            channel_id = resolved

        try:
            data = await self._api("POST", "chat.postMessage", json_body={
                "channel": channel_id,
                "text": text,
            })
            if not data.get("ok"):
                return f"Slack error: {data.get('error', 'unknown')}"
            return f"✅ Message posted to <#{channel_id}>."
        except Exception as e:
            return f"Slack API error: {e}"

    async def _resolve_channel(self, name: str) -> Optional[str]:
        """Resolve a channel name to its ID."""
        try:
            data = await self._api("GET", "conversations.list", {
                "types": "public_channel,private_channel",
                "limit": 200,
            })
            for ch in data.get("channels", []):
                if ch["name"] == name:
                    return ch["id"]
        except Exception:
            pass
        return None
