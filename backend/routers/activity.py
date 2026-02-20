"""
Velocity AI - Activity Log Router
Logs real AI-driven actions from integrations.
No seed data — populated by append_activity() calls from other routers.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class ActivityLogEntry(BaseModel):
    id: str
    timestamp: str
    action: str
    source: str
    mode: str
    project: Optional[str] = None
    details: Optional[str] = None


# Real activity log — populated by integration calls
_activity_log: list[dict] = []


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
    """Called by routers/tools to log real AI actions."""
    _activity_log.insert(0, {
        "id": f"act-{len(_activity_log) + 1}",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "action": action,
        "source": source,
        "mode": mode,
        "project": project,
        "details": details,
    })
    # Keep max 200 entries
    if len(_activity_log) > 200:
        _activity_log.pop()
