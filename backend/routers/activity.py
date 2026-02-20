"""
Velocity AI - Activity Log Router
Tracks all AI actions (mail reads, Slack fetches, GitHub scans, etc.)
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

# In-memory activity log
_activity_log: list[dict] = [
    {
        "id": "act-1",
        "timestamp": "2026-02-20T11:30:00Z",
        "action": "Scanned 3 GitHub repositories for recent commits",
        "source": "github",
        "mode": "workspace",
        "project": "Auth & Onboarding",
        "details": "Found 2 new PRs merged, 1 issue opened",
    },
    {
        "id": "act-2",
        "timestamp": "2026-02-20T11:25:00Z",
        "action": "Read 5 unread emails from team members",
        "source": "gmail",
        "mode": "workspace",
        "project": "Payment Integration",
        "details": "Stripe webhook failure alert from monitoring",
    },
    {
        "id": "act-3",
        "timestamp": "2026-02-20T11:20:00Z",
        "action": "Fetched latest Slack messages from #dev-updates",
        "source": "slack",
        "mode": "workspace",
        "project": "Auth & Onboarding",
        "details": "Aarav reported login flow PR is ready for review",
    },
    {
        "id": "act-4",
        "timestamp": "2026-02-20T11:15:00Z",
        "action": "Checked Jira board for sprint progress",
        "source": "jira",
        "mode": "workspace",
        "project": "Payment Integration",
        "details": "4 tickets in progress, 2 blocked",
    },
    {
        "id": "act-5",
        "timestamp": "2026-02-20T11:10:00Z",
        "action": "Synced Google Calendar for upcoming deadlines",
        "source": "calendar",
        "mode": "personal",
        "project": None,
        "details": "Found 3 deadlines this week: ML assignment, startup pitch, project review",
    },
    {
        "id": "act-6",
        "timestamp": "2026-02-20T11:05:00Z",
        "action": "Analyzed study schedule from Notion",
        "source": "notion",
        "mode": "personal",
        "project": None,
        "details": "Identified 2 hours gap for deep work between classes",
    },
    {
        "id": "act-7",
        "timestamp": "2026-02-20T11:00:00Z",
        "action": "Scanned GitHub trending repos matching your tech stack",
        "source": "github",
        "mode": "personal",
        "project": None,
        "details": "Found 3 repos related to LangGraph and FastAPI patterns",
    },
    {
        "id": "act-8",
        "timestamp": "2026-02-20T10:55:00Z",
        "action": "Read Slack #general for team announcements",
        "source": "slack",
        "mode": "workspace",
        "project": "Landing Page v2",
        "details": "Design review scheduled for Friday 3pm",
    },
]


class ActivityLogEntry(BaseModel):
    id: str
    timestamp: str
    action: str
    source: str
    mode: str
    project: str | None = None
    details: str | None = None


@router.get("/activity-log")
async def get_activity_log(mode: str | None = None) -> list[ActivityLogEntry]:
    """Get AI activity log, optionally filtered by mode."""
    entries = _activity_log
    if mode:
        entries = [e for e in entries if e["mode"] == mode]
    return [ActivityLogEntry(**e) for e in entries]


def append_activity(
    action: str,
    source: str,
    mode: str = "workspace",
    project: str | None = None,
    details: str | None = None,
):
    """Called by graph nodes to log AI actions."""
    _activity_log.insert(0, {
        "id": f"act-{len(_activity_log) + 1}",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": action,
        "source": source,
        "mode": mode,
        "project": project,
        "details": details,
    })
