"""
Velocity AI – Jira LangChain Tool
Access Jira projects, issues, and sprints via Jira REST API.
"""

from __future__ import annotations

import base64
import os
from typing import Optional

import httpx
from langchain_core.tools import BaseTool
from pydantic import Field


class JiraTool(BaseTool):
    """
    LangChain tool that wraps the Jira REST API.

    Capabilities:
    - List projects
    - Get board issues
    - Get sprint status
    - Search issues via JQL

    Used by: IngestorNode, PrioritizerNode
    """

    name: str = "jira"
    description: str = (
        "Access Jira: list projects, get issues, search with JQL. "
        "Use action='projects' for all projects, 'issues PROJECT_KEY' for issues, "
        "'search JQL_QUERY' to search."
    )
    api_token: str = Field(default="")
    email: str = Field(default="")
    cloud_url: str = Field(default="")

    def _run(self, query: str) -> str:
        import asyncio
        return asyncio.run(self._arun(query))

    async def _arun(self, query: str) -> str:
        from services.db_service import mongodb
        j = await mongodb.get_token("jira")
        if j:
            self.api_token = j.get("token", "")
            self.email = j.get("email", "")
            self.cloud_url = j.get("cloud_url", "")
            
        if not self.api_token or not self.email or not self.cloud_url:
            return "Jira not configured. Please connect from the UI."

        parts = query.strip().split(maxsplit=1)
        action = parts[0].lower() if parts else "projects"
        arg = parts[1] if len(parts) > 1 else ""

        dispatch = {
            "projects": self._list_projects,
            "issues": self._list_issues,
            "search": self._search_issues,
        }

        handler = dispatch.get(action, self._list_projects)
        return await handler(arg)

    def _headers(self) -> dict:
        auth = base64.b64encode(f"{self.email}:{self.api_token}".encode()).decode()
        return {
            "Authorization": f"Basic {auth}",
            "Accept": "application/json",
        }

    async def _get(self, path: str, params: Optional[dict] = None) -> dict:
        url = f"{self.cloud_url.rstrip('/')}/rest/api/3{path}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self._headers(), params=params or {}, timeout=15)
            resp.raise_for_status()
            return resp.json()

    async def _list_projects(self, _: str = "") -> str:
        """List all Jira projects."""
        try:
            data = await self._get("/project", {"maxResults": 20})
            lines = []
            for p in data if isinstance(data, list) else data.get("values", []):
                lines.append(f"• {p['key']}: {p['name']} ({p.get('projectTypeKey', '?')})")
            return "\n".join(lines) or "No projects found."
        except Exception as e:
            return f"Jira API error: {e}"

    async def _list_issues(self, project_key: str) -> str:
        """List open issues for a project."""
        if not project_key:
            return "Provide a project key."
        try:
            data = await self._get("/search", {
                "jql": f"project={project_key} AND status!=Done ORDER BY updated DESC",
                "maxResults": 15,
                "fields": "summary,status,assignee,priority",
            })
            issues = data.get("issues", [])
            lines = []
            for issue in issues:
                key = issue["key"]
                fields = issue["fields"]
                summary = fields.get("summary", "?")
                status = fields.get("status", {}).get("name", "?")
                assignee = fields.get("assignee", {})
                assignee_name = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"
                priority = fields.get("priority", {}).get("name", "?")
                lines.append(f"• {key} [{priority}] {summary} — {status} ({assignee_name})")
            return "\n".join(lines) or f"No open issues in {project_key}."
        except Exception as e:
            return f"Jira API error: {e}"

    async def _search_issues(self, jql: str) -> str:
        """Search issues using JQL."""
        if not jql:
            return "Provide a JQL query."
        try:
            data = await self._get("/search", {
                "jql": jql,
                "maxResults": 10,
                "fields": "summary,status,assignee",
            })
            issues = data.get("issues", [])
            lines = []
            for issue in issues:
                key = issue["key"]
                summary = issue["fields"].get("summary", "?")
                status = issue["fields"].get("status", {}).get("name", "?")
                lines.append(f"• {key} {summary} — {status}")
            return "\n".join(lines) or "No issues match."
        except Exception as e:
            return f"Jira API error: {e}"
