"""
Velocity AI - Metrics Router
Team velocity metrics for workspace mode.
"""

from fastapi import APIRouter
from models.schemas import TeamMetrics

router = APIRouter()


@router.get("/metrics")
async def get_team_metrics() -> TeamMetrics:
    """Get team velocity metrics for the workspace dashboard."""
    return TeamMetrics(
        hours_saved=127.5,
        hours_saved_trend=12.3,
        market_alerts=8,
        market_alerts_new=3,
        active_leads=24,
        active_leads_conversion=18.7,
        sprint_velocity=89.2,
        team_mood="great",
    )
