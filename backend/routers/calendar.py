"""
Velocity AI - Calendar Router
Grade-aware smart calendar with study and coding blocks.
"""

from fastapi import APIRouter
from models.schemas import CalendarBlock

router = APIRouter()

# Mock calendar blocks - a student founder's day
MOCK_CALENDAR: list[CalendarBlock] = [
    CalendarBlock(
        id="c1",
        title="☀️ Morning Review",
        start="2026-02-20T08:00:00",
        end="2026-02-20T08:30:00",
        category="study",
        color="#6366f1",
        description="Quick review of yesterday's notes",
    ),
    CalendarBlock(
        id="c2",
        title="📐 Linear Algebra Lecture",
        start="2026-02-20T09:00:00",
        end="2026-02-20T10:30:00",
        category="study",
        color="#6366f1",
        description="Chapter 7: Eigenvalues & Eigenvectors",
        grade_impact="high",
    ),
    CalendarBlock(
        id="c3",
        title="💻 Sprint Work — Auth Module",
        start="2026-02-20T11:00:00",
        end="2026-02-20T13:00:00",
        category="coding",
        color="#10b981",
        description="Fix login bug (#47) and review Aarav's PR",
    ),
    CalendarBlock(
        id="c4",
        title="🍽️ Lunch Break",
        start="2026-02-20T13:00:00",
        end="2026-02-20T14:00:00",
        category="break",
        color="#94a3b8",
        description="Recharge!",
    ),
    CalendarBlock(
        id="c5",
        title="🌳 Data Structures Class",
        start="2026-02-20T14:00:00",
        end="2026-02-20T15:30:00",
        category="study",
        color="#6366f1",
        description="Binary tree traversal",
        grade_impact="medium",
    ),
    CalendarBlock(
        id="c6",
        title="📚 Exam Prep — Linear Algebra",
        start="2026-02-20T16:00:00",
        end="2026-02-20T18:00:00",
        category="study",
        color="#f59e0b",
        description="Practice problems for Friday exam",
        grade_impact="high",
    ),
    CalendarBlock(
        id="c7",
        title="💻 Startup — Landing Page",
        start="2026-02-20T19:00:00",
        end="2026-02-20T21:00:00",
        category="coding",
        color="#10b981",
        description="Implement hero section and CTA",
    ),
    CalendarBlock(
        id="c8",
        title="📝 Daily Reflection & Planning",
        start="2026-02-20T21:30:00",
        end="2026-02-20T22:00:00",
        category="study",
        color="#8b5cf6",
        description="Review day, prep tomorrow",
    ),
]


@router.get("/calendar")
async def get_calendar_blocks() -> list[CalendarBlock]:
    """Get all calendar blocks for the grade-aware smart calendar."""
    return MOCK_CALENDAR


@router.get("/calendar/today")
async def get_today_blocks() -> dict:
    """Get today's calendar summary."""
    study_blocks = [b for b in MOCK_CALENDAR if b.category == "study"]
    coding_blocks = [b for b in MOCK_CALENDAR if b.category == "coding"]

    return {
        "date": "2026-02-20",
        "total_blocks": len(MOCK_CALENDAR),
        "study_hours": sum(2.0 for _ in study_blocks),  # simplified
        "coding_hours": sum(2.0 for _ in coding_blocks),
        "blocks": MOCK_CALENDAR,
        "high_impact_exams": [
            b.dict() for b in MOCK_CALENDAR if b.grade_impact == "high"
        ],
    }
