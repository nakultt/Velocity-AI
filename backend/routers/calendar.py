"""
Velocity AI - Calendar Router
Real calendar data from Google Calendar API.
"""

from datetime import datetime, timezone

import httpx
from fastapi import APIRouter

from models.schemas import CalendarBlock

router = APIRouter()


def _get_google_token() -> str | None:
    """Get Google Calendar OAuth token."""
    try:
        from routers.integrations import get_token
        return get_token("calendar")
    except Exception:
        return None


@router.get("/calendar")
async def get_calendar_blocks() -> list[CalendarBlock]:
    """Get real calendar events from Google Calendar."""
    token = _get_google_token()
    if not token:
        return []

    try:
        now = datetime.now(timezone.utc).isoformat()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://www.googleapis.com/calendar/v3/calendars/primary/events",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "timeMin": now,
                    "maxResults": 20,
                    "singleEvents": True,
                    "orderBy": "startTime",
                },
                timeout=15,
            )
            if resp.status_code != 200:
                return []

            data = resp.json()
            blocks = []
            for ev in data.get("items", []):
                start = ev.get("start", {}).get("dateTime") or ev.get("start", {}).get("date", "")
                end = ev.get("end", {}).get("dateTime") or ev.get("end", {}).get("date", "")
                summary = ev.get("summary", "Untitled Event")

                # Auto-categorize by keywords
                lower = summary.lower()
                if any(w in lower for w in ["study", "exam", "lecture", "class", "assignment", "hw"]):
                    category = "study"
                    color = "#6366f1"
                elif any(w in lower for w in ["code", "sprint", "pr", "build", "deploy", "dev"]):
                    category = "coding"
                    color = "#10b981"
                elif any(w in lower for w in ["lunch", "break", "gym", "walk"]):
                    category = "break"
                    color = "#94a3b8"
                else:
                    category = "other"
                    color = "#8b5cf6"

                blocks.append(CalendarBlock(
                    id=ev.get("id", ""),
                    title=summary,
                    start=start,
                    end=end,
                    category=category,
                    color=color,
                    description=ev.get("description", ""),
                    grade_impact=None,
                ))

            # Log activity
            try:
                from routers.activity import append_activity
                append_activity(
                    action=f"Fetched {len(blocks)} calendar events",
                    source="calendar",
                    mode="personal",
                )
            except Exception:
                pass

            return blocks

    except Exception as e:
        print(f"Calendar error: {e}")
        return []


@router.get("/calendar/today")
async def get_today_blocks() -> dict:
    """Get today's calendar summary."""
    blocks = await get_calendar_blocks()
    now = datetime.now(timezone.utc)

    # Filter to today's events
    today_blocks = []
    for b in blocks:
        try:
            block_date = datetime.fromisoformat(b.start.replace("Z", "+00:00"))
            if block_date.date() == now.date():
                today_blocks.append(b)
        except Exception:
            today_blocks.append(b)  # include if can't parse

    study_blocks = [b for b in today_blocks if b.category == "study"]
    coding_blocks = [b for b in today_blocks if b.category == "coding"]

    return {
        "date": now.strftime("%Y-%m-%d"),
        "total_blocks": len(today_blocks),
        "study_hours": len(study_blocks) * 1.5,
        "coding_hours": len(coding_blocks) * 2.0,
        "blocks": today_blocks,
        "high_impact_exams": [
            b.dict() for b in today_blocks if b.grade_impact == "high"
        ],
    }
