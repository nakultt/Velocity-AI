"""
Velocity AI - Pydantic Schemas
Request/Response models for all API endpoints.
"""

from pydantic import BaseModel
from datetime import datetime


# ──────────────────────────────────────
# Chat
# ──────────────────────────────────────
class ChatMessage(BaseModel):
    role: str  # "user" | "assistant" | "system"
    content: str
    timestamp: datetime | None = None
    requires_approval: bool = False
    approval_status: str | None = None  # "pending" | "approved" | "rejected"
    action_type: str | None = None  # "schedule" | "priority" | "delegate"


class ChatRequest(BaseModel):
    message: str
    mode: str = "personal"  # "personal" | "workspace"
    conversation_id: str | None = None


class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    requires_approval: bool = False
    proposed_action: dict | None = None
    sources: list[str] = []


# ──────────────────────────────────────
# Tasks
# ──────────────────────────────────────
class Task(BaseModel):
    id: str
    title: str
    description: str
    priority: str  # "critical" | "high" | "medium" | "low"
    category: str  # "academic" | "startup" | "personal"
    due_date: str | None = None
    estimated_hours: float = 1.0
    completed: bool = False
    source: str | None = None  # "ai_generated" | "manual"


class DailySummary(BaseModel):
    date: str
    greeting: str
    tasks: list[Task]
    study_hours: float
    coding_hours: float
    insights: list[str]


# ──────────────────────────────────────
# Calendar
# ──────────────────────────────────────
class CalendarBlock(BaseModel):
    id: str
    title: str
    start: str
    end: str
    category: str  # "study" | "coding" | "meeting" | "break" | "exam"
    color: str
    description: str | None = None
    grade_impact: str | None = None  # "high" | "medium" | "low"


# ──────────────────────────────────────
# Projects (Workspace Mode)
# ──────────────────────────────────────
class Project(BaseModel):
    id: str
    name: str
    status: str  # "active" | "paused" | "completed"
    progress: int  # 0-100
    description: str
    team_members: list[str]
    last_updated: str
    tech_stack: list[str] = []


class UpdateFeedItem(BaseModel):
    id: str
    message: str
    source: str  # "slack" | "github" | "notion" | "jira" | "gmail"
    timestamp: str
    project: str | None = None
    verified: bool = False


class Priority(BaseModel):
    id: str
    title: str
    urgency: str  # "critical" | "high" | "medium" | "low"
    project: str
    assigned_to: str | None = None
    ai_reasoning: str | None = None


# ──────────────────────────────────────
# Metrics (Workspace Mode)
# ──────────────────────────────────────
class TeamMetrics(BaseModel):
    hours_saved: float
    hours_saved_trend: float  # percentage change
    market_alerts: int
    market_alerts_new: int
    active_leads: int
    active_leads_conversion: float
    sprint_velocity: float
    team_mood: str  # "great" | "good" | "neutral" | "low"


# ──────────────────────────────────────
# Integrations
# ──────────────────────────────────────
class IntegrationStatus(BaseModel):
    service: str
    connected: bool
    last_synced: str | None = None
    scopes: list[str] = []
