"""
Velocity AI – Notion LangChain Tool
Access Notion databases, pages, and search via the Notion API.
"""

from __future__ import annotations

import os
from typing import Optional

import httpx
from langchain_core.tools import BaseTool
from pydantic import Field


NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"


class NotionTool(BaseTool):
    """
    LangChain tool for the Notion API.

    Capabilities:
    - List databases
    - Query a database
    - Read a page
    - Search across workspace

    Used by: IngestorNode, ResearcherNode
    """

    name: str = "notion"
    description: str = (
        "Access Notion workspace: list databases, query database, read page, search. "
        "Use action='databases' to list, 'query DB_ID' to query, "
        "'read PAGE_ID' to read, 'search query' to find."
    )
    api_key: str = Field(default="")

    def _run(self, query: str) -> str:
        import asyncio
        return asyncio.run(self._arun(query))

    async def _arun(self, query: str) -> str:
        from services.db_service import mongodb
        t = await mongodb.get_token("notion")
        if t:
            self.api_key = t.get("token", "")
            
        if not self.api_key:
            return "Notion not configured. Please connect from the UI."

        parts = query.strip().split(maxsplit=1)
        action = parts[0].lower() if parts else "databases"
        arg = parts[1] if len(parts) > 1 else ""

        dispatch = {
            "databases": self._list_databases,
            "query": self._query_database,
            "read": self._read_page,
            "search": self._search,
        }

        handler = dispatch.get(action, self._list_databases)
        return await handler(arg)

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        }

    async def _list_databases(self, _: str = "") -> str:
        """List all databases the integration has access to."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{NOTION_API}/search",
                    headers=self._headers(),
                    json={"filter": {"value": "database", "property": "object"}},
                    timeout=15,
                )
                data = resp.json()
                results = data.get("results", [])
                lines = []
                for db in results:
                    title_parts = db.get("title", [])
                    title = title_parts[0]["plain_text"] if title_parts else "Untitled"
                    lines.append(f"• {title} (ID: {db['id']})")
                return "\n".join(lines) or "No databases found."
        except Exception as e:
            return f"Notion API error: {e}"

    async def _query_database(self, db_id: str) -> str:
        """Query a Notion database."""
        if not db_id:
            return "Provide a database ID."
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{NOTION_API}/databases/{db_id}/query",
                    headers=self._headers(),
                    json={"page_size": 10},
                    timeout=15,
                )
                data = resp.json()
                results = data.get("results", [])
                lines = []
                for page in results:
                    props = page.get("properties", {})
                    # Try to get title from first title property
                    title = "Untitled"
                    for prop in props.values():
                        if prop.get("type") == "title":
                            title_arr = prop.get("title", [])
                            if title_arr:
                                title = title_arr[0].get("plain_text", "Untitled")
                            break
                    lines.append(f"• {title} (ID: {page['id'][:8]}...)")
                return "\n".join(lines) or "Database is empty."
        except Exception as e:
            return f"Notion API error: {e}"

    async def _read_page(self, page_id: str) -> str:
        """Read a Notion page's content."""
        if not page_id:
            return "Provide a page ID."
        try:
            async with httpx.AsyncClient() as client:
                # Get page blocks
                resp = await client.get(
                    f"{NOTION_API}/blocks/{page_id}/children",
                    headers=self._headers(),
                    params={"page_size": 50},
                    timeout=15,
                )
                data = resp.json()
                blocks = data.get("results", [])
                text_parts = []
                for block in blocks:
                    block_type = block.get("type", "")
                    content = block.get(block_type, {})
                    rich_text = content.get("rich_text", [])
                    for rt in rich_text:
                        text_parts.append(rt.get("plain_text", ""))
                return "\n".join(text_parts)[:3000] or "Page is empty."
        except Exception as e:
            return f"Notion API error: {e}"

    async def _search(self, query: str) -> str:
        """Search across the Notion workspace."""
        if not query:
            return "Provide a search query."
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"{NOTION_API}/search",
                    headers=self._headers(),
                    json={"query": query, "page_size": 10},
                    timeout=15,
                )
                data = resp.json()
                results = data.get("results", [])
                lines = []
                for item in results:
                    obj_type = item.get("object", "?")
                    if obj_type == "page":
                        props = item.get("properties", {})
                        title = "Untitled"
                        for prop in props.values():
                            if prop.get("type") == "title":
                                title_arr = prop.get("title", [])
                                if title_arr:
                                    title = title_arr[0].get("plain_text", "Untitled")
                                break
                        lines.append(f"• 📄 {title}")
                    elif obj_type == "database":
                        title_parts = item.get("title", [])
                        title = title_parts[0]["plain_text"] if title_parts else "Untitled"
                        lines.append(f"• 🗃️ {title}")
                return "\n".join(lines) or f"No results for '{query}'."
        except Exception as e:
            return f"Notion API error: {e}"
