"""
Velocity AI – GitHub LangChain Tool
Accesses repos, issues, PRs, and commits via GitHub REST API.
Used by the Workspace Dashboard Ingestor for real-time project status.
"""

from __future__ import annotations

import os
from typing import Optional

import httpx
from langchain_core.tools import BaseTool
from pydantic import Field


GITHUB_API = "https://api.github.com"


class GitHubTool(BaseTool):
    """
    LangChain tool that wraps the GitHub REST API.

    Capabilities:
    - List repos for the authenticated user / org
    - Fetch open issues and pull requests
    - Get recent commits on a branch
    - Summarise PR review status

    Used by: IngestorNode, ContextMatcherNode
    """

    name: str = "github"
    description: str = (
        "Access GitHub repositories, issues, pull requests, and commits. "
        "Use action='repos' to list repos, 'issues' for open issues, "
        "'pulls' for open PRs, 'commits' for recent commits."
    )
    token: str = Field(default="")

    # ── public entry-point ────────────────────────────────
    def _run(self, query: str) -> str:
        """Synchronous fallback (LangChain requirement)."""
        import asyncio
        return asyncio.run(self._arun(query))

    async def _arun(self, query: str) -> str:
        """Parse the query and dispatch to the right GitHub endpoint."""
        from services.db_service import mongodb
        t = await mongodb.get_token("github")
        if t:
            self.token = t.get("token", "")
            
        if not self.token:
            return "GitHub not configured. Please connect from the UI."
            
        parts = query.strip().split(maxsplit=1)
        action = parts[0].lower() if parts else "repos"
        arg = parts[1] if len(parts) > 1 else ""

        dispatch = {
            "repos": self._list_repos,
            "issues": self._list_issues,
            "pulls": self._list_pulls,
            "commits": self._list_commits,
            "pr_status": self._pr_review_status,
        }

        handler = dispatch.get(action, self._list_repos)
        return await handler(arg)

    # ── helpers ───────────────────────────────────────────
    def _headers(self) -> dict:
        h = {"Accept": "application/vnd.github+json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    async def _get(self, path: str, params: Optional[dict] = None) -> list | dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GITHUB_API}{path}",
                headers=self._headers(),
                params=params or {},
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()

    # ── actions ───────────────────────────────────────────
    async def _list_repos(self, org: str = "") -> str:
        """List repos for authenticated user or organisation."""
        path = f"/orgs/{org}/repos" if org else "/user/repos"
        try:
            repos = await self._get(path, {"sort": "updated", "per_page": 10})
            lines = []
            for r in repos:
                stars = r.get("stargazers_count", 0)
                lang = r.get("language", "N/A")
                lines.append(
                    f"• {r['full_name']} ⭐{stars} [{lang}] – {r.get('description', 'No description')}"
                )
            return "\n".join(lines) or "No repositories found."
        except Exception as e:
            return f"GitHub API error: {e}"

    async def _list_issues(self, repo: str) -> str:
        """List open issues for a repo (owner/repo)."""
        if not repo:
            return "Please provide a repo in 'owner/repo' format."
        try:
            issues = await self._get(f"/repos/{repo}/issues", {
                "state": "open", "per_page": 15, "sort": "updated",
            })
            lines = []
            for i in issues:
                if i.get("pull_request"):
                    continue  # skip PRs
                labels = ", ".join(l["name"] for l in i.get("labels", []))
                lines.append(
                    f"• #{i['number']} {i['title']} [{labels or 'no labels'}] "
                    f"by {i['user']['login']}"
                )
            return "\n".join(lines) or "No open issues."
        except Exception as e:
            return f"GitHub API error: {e}"

    async def _list_pulls(self, repo: str) -> str:
        """List open pull requests for a repo."""
        if not repo:
            return "Please provide a repo in 'owner/repo' format."
        try:
            prs = await self._get(f"/repos/{repo}/pulls", {
                "state": "open", "per_page": 10, "sort": "updated",
            })
            lines = []
            for pr in prs:
                reviews_ready = "✅" if pr.get("draft") is False else "📝 Draft"
                lines.append(
                    f"• PR #{pr['number']} {pr['title']} by {pr['user']['login']} "
                    f"→ {pr['base']['ref']} {reviews_ready}"
                )
            return "\n".join(lines) or "No open pull requests."
        except Exception as e:
            return f"GitHub API error: {e}"

    async def _list_commits(self, repo: str) -> str:
        """List recent commits on the default branch."""
        if not repo:
            return "Please provide a repo in 'owner/repo' format."
        try:
            commits = await self._get(f"/repos/{repo}/commits", {"per_page": 10})
            lines = []
            for c in commits:
                sha = c["sha"][:7]
                msg = c["commit"]["message"].split("\n")[0][:80]
                author = c["commit"]["author"]["name"]
                lines.append(f"• {sha} {msg} — {author}")
            return "\n".join(lines) or "No commits found."
        except Exception as e:
            return f"GitHub API error: {e}"

    async def _pr_review_status(self, repo_and_pr: str) -> str:
        """Check review status of a PR. Format: 'owner/repo 42'"""
        parts = repo_and_pr.split()
        if len(parts) < 2:
            return "Provide 'owner/repo PR_NUMBER'."
        repo, pr_num = parts[0], parts[1]
        try:
            reviews = await self._get(f"/repos/{repo}/pulls/{pr_num}/reviews")
            if not reviews:
                return f"PR #{pr_num}: No reviews yet."
            states: dict[str, list] = {}
            for r in reviews:
                states.setdefault(r["state"], []).append(r["user"]["login"])
            lines = [f"PR #{pr_num} review summary:"]
            for state, users in states.items():
                lines.append(f"  {state}: {', '.join(users)}")
            return "\n".join(lines)
        except Exception as e:
            return f"GitHub API error: {e}"
