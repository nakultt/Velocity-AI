"""
Velocity AI - Projects Router (Workspace Mode)
Project Pulse Dashboard: current projects, updates feed, priorities.
"""

from fastapi import APIRouter
from models.schemas import Project, UpdateFeedItem, Priority

router = APIRouter()

# ──────────────────────────────────────
# Mock Data — Workspace Mode
# ──────────────────────────────────────

MOCK_PROJECTS: list[Project] = [
    Project(
        id="p1",
        name="Auth & Onboarding",
        status="active",
        progress=87,
        description="User authentication with OAuth, email verification, and onboarding wizard.",
        team_members=["Nakul", "Aarav", "Priya"],
        last_updated="2 hours ago",
        tech_stack=["React", "FastAPI", "PostgreSQL"],
    ),
    Project(
        id="p2",
        name="Payment Integration",
        status="active",
        progress=45,
        description="Stripe payment flow with subscription management and invoicing.",
        team_members=["Aarav", "Riya"],
        last_updated="30 min ago",
        tech_stack=["Stripe API", "Node.js", "MongoDB"],
    ),
    Project(
        id="p3",
        name="Landing Page v2",
        status="paused",
        progress=30,
        description="New landing page with updated branding, testimonials, and pricing.",
        team_members=["Priya"],
        last_updated="1 day ago",
        tech_stack=["Next.js", "Tailwind", "Framer Motion"],
    ),
]

MOCK_UPDATES: list[UpdateFeedItem] = [
    UpdateFeedItem(
        id="u1",
        message="Login flow PR merged and deployed to staging",
        source="github",
        timestamp="30 min ago",
        project="Auth & Onboarding",
        verified=True,
    ),
    UpdateFeedItem(
        id="u2",
        message="Aarav: 'Stripe webhook is intermittently failing on retry'",
        source="slack",
        timestamp="1 hour ago",
        project="Payment Integration",
        verified=False,
    ),
    UpdateFeedItem(
        id="u3",
        message="Competitor 'BuildFast' launched freemium tier — pricing impact TBD",
        source="notion",
        timestamp="2 hours ago",
        project=None,
        verified=True,
    ),
    UpdateFeedItem(
        id="u4",
        message="Design specs updated for onboarding wizard step 3",
        source="notion",
        timestamp="3 hours ago",
        project="Auth & Onboarding",
        verified=True,
    ),
    UpdateFeedItem(
        id="u5",
        message="Weekly investor update email sent successfully",
        source="gmail",
        timestamp="5 hours ago",
        project=None,
        verified=True,
    ),
    UpdateFeedItem(
        id="u6",
        message="CI pipeline passed — 94% test coverage on auth module",
        source="github",
        timestamp="6 hours ago",
        project="Auth & Onboarding",
        verified=True,
    ),
]

MOCK_PRIORITIES: list[Priority] = [
    Priority(
        id="pr1",
        title="Fix Stripe webhook retry logic",
        urgency="critical",
        project="Payment Integration",
        assigned_to="Aarav",
        ai_reasoning="3 failed webhook events in the last hour. Revenue-blocking if not resolved.",
    ),
    Priority(
        id="pr2",
        title="Respond to BuildFast pricing change",
        urgency="high",
        project="Strategy",
        assigned_to="Nakul",
        ai_reasoning="Competitor launched freemium. Need to evaluate pricing before investor call.",
    ),
    Priority(
        id="pr3",
        title="Unblock landing page — get copy from marketing",
        urgency="high",
        project="Landing Page v2",
        assigned_to="Priya",
        ai_reasoning="On critical path for launch. 2 days behind schedule.",
    ),
    Priority(
        id="pr4",
        title="Complete onboarding wizard step 3",
        urgency="medium",
        project="Auth & Onboarding",
        assigned_to="Nakul",
        ai_reasoning="Design specs ready. Can be done in ~3 hours.",
    ),
    Priority(
        id="pr5",
        title="Set up error monitoring dashboard",
        urgency="low",
        project="Infrastructure",
        assigned_to=None,
        ai_reasoning="Good to have before launch, but not blocking anything.",
    ),
]


@router.get("/projects")
async def get_projects() -> list[Project]:
    """Get current active projects for the workspace dashboard."""
    return MOCK_PROJECTS


@router.get("/projects/{project_id}")
async def get_project(project_id: str) -> dict:
    """Get a single project by ID with its activities and priorities."""
    project = next((p for p in MOCK_PROJECTS if p.id == project_id), None)
    if not project:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Project not found")

    # Filter updates and priorities for this project
    activities = [u for u in MOCK_UPDATES if u.project == project.name]
    priorities = [p for p in MOCK_PRIORITIES if p.project == project.name]

    return {
        "project": project,
        "activities": activities,
        "priorities": priorities,
    }


@router.get("/projects/{project_id}/activities")
async def get_project_activities(project_id: str) -> dict:
    """Get activities for a specific project (updates + priorities)."""
    project = next((p for p in MOCK_PROJECTS if p.id == project_id), None)
    if not project:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Project not found")

    activities = [u for u in MOCK_UPDATES if u.project == project.name]
    priorities = [p for p in MOCK_PRIORITIES if p.project == project.name]

    return {
        "project_name": project.name,
        "activities": activities,
        "priorities": priorities,
    }


@router.get("/updates")
async def get_updates_feed() -> list[UpdateFeedItem]:
    """Get the latest updates feed synthesized from all tools."""
    return MOCK_UPDATES


@router.get("/priorities")
async def get_priorities() -> list[Priority]:
    """Get AI-sorted upcoming priorities."""
    return MOCK_PRIORITIES

