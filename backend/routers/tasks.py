"""
Velocity AI - Tasks Router
Daily prioritized tasks and daily summary.
"""

from fastapi import APIRouter
from models.schemas import Task, DailySummary

router = APIRouter()


# Mock task data
MOCK_TASKS: list[Task] = [
    Task(
        id="t1",
        title="Study Linear Algebra — Chapter 7",
        description="Review eigenvalues and eigenvectors. High weight on final exam.",
        priority="critical",
        category="academic",
        due_date="2026-02-20",
        estimated_hours=2.5,
        completed=False,
        source="ai_generated",
    ),
    Task(
        id="t2",
        title="Fix Login Bug (#47)",
        description="Auth token not refreshing on mobile. Affects 23% of users.",
        priority="high",
        category="startup",
        due_date="2026-02-21",
        estimated_hours=2.0,
        completed=False,
        source="ai_generated",
    ),
    Task(
        id="t3",
        title="Review PR #52 — Payment Flow",
        description="Aarav submitted the Stripe integration. Needs code review.",
        priority="high",
        category="startup",
        due_date="2026-02-20",
        estimated_hours=1.0,
        completed=False,
        source="ai_generated",
    ),
    Task(
        id="t4",
        title="Data Structures Assignment",
        description="Binary tree traversal problems. Due by midnight.",
        priority="medium",
        category="academic",
        due_date="2026-02-20",
        estimated_hours=1.5,
        completed=False,
        source="ai_generated",
    ),
    Task(
        id="t5",
        title="Prepare Pitch Deck Slide 3-5",
        description="Add market size data and competitive analysis for investor meeting.",
        priority="medium",
        category="startup",
        due_date="2026-02-22",
        estimated_hours=2.0,
        completed=False,
        source="ai_generated",
    ),
]


@router.get("/tasks")
async def get_tasks() -> list[Task]:
    """Get all prioritized tasks."""
    return MOCK_TASKS


@router.get("/tasks/summary")
async def get_daily_summary() -> DailySummary:
    """Get the daily summary card with top priorities and schedule breakdown."""
    return DailySummary(
        date="2026-02-20",
        greeting="Good afternoon! You have 5 tasks today — let's crush it 🚀",
        tasks=MOCK_TASKS[:3],  # Top 3 priorities
        study_hours=4.0,
        coding_hours=3.0,
        insights=[
            "📊 Your Linear Algebra exam is in 2 days — I've front-loaded study time.",
            "🐛 The login bug is trending on your error tracker. Prioritized for tonight.",
            "💡 Market research found 2 competitor launches this week — check Workspace mode.",
        ],
    )
