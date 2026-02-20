"""
Velocity AI - Integrations Router
Handles connected service status and OAuth flows (pattern from nakultt/locus).
"""

import os
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse

from config import settings
from models.schemas import IntegrationStatus

router = APIRouter()

# ──────────────────────────────────────
# Google OAuth
# ──────────────────────────────────────

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

GOOGLE_SCOPES = {
    "gmail": [
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",
    ],
    "calendar": [
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/calendar.events",
    ],
    "docs": [
        "https://www.googleapis.com/auth/documents",
    ],
    "sheets": [
        "https://www.googleapis.com/auth/spreadsheets",
    ],
    "drive": [
        "https://www.googleapis.com/auth/drive",
    ],
}

# In-memory state storage (in production, use Redis or database)
_oauth_states: dict[str, dict] = {}
_connected_services: dict[str, dict] = {}


def _get_all_google_scopes() -> list[str]:
    """Get all Google scopes combined."""
    all_scopes = []
    for scopes in GOOGLE_SCOPES.values():
        all_scopes.extend(scopes)
    all_scopes.extend([
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
    ])
    return list(set(all_scopes))


@router.get("/google/connect")
async def google_oauth_start(
    service: str = Query("google", description="Service to connect: gmail, calendar, docs, etc.")
):
    """
    Start Google OAuth flow (locus pattern).
    Redirects to Google consent screen.
    """
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET."
        )

    state = secrets.token_urlsafe(32)
    _oauth_states[state] = {
        "service": service,
        "created_at": datetime.utcnow().isoformat(),
    }

    scopes = _get_all_google_scopes() if service == "google" else GOOGLE_SCOPES.get(service, [])
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }

    return RedirectResponse(url=f"{GOOGLE_AUTH_URL}?{urlencode(params)}")


@router.get("/google/callback")
async def google_oauth_callback(
    code: str = Query(None),
    state: str = Query(None),
    error: str = Query(None),
):
    """Handle Google OAuth callback (locus pattern)."""
    if error:
        return RedirectResponse(url=f"{settings.frontend_url}/settings?error={error}")

    if not code or not state or state not in _oauth_states:
        return RedirectResponse(url=f"{settings.frontend_url}/settings?error=invalid_request")

    state_data = _oauth_states.pop(state)

    # In production: exchange code for tokens via httpx
    # For demo, mark as connected
    service = state_data["service"]
    services = ["gmail", "calendar", "docs", "sheets", "drive"] if service == "google" else [service]
    for svc in services:
        _connected_services[svc] = {
            "connected": True,
            "connected_at": datetime.utcnow().isoformat(),
        }

    return RedirectResponse(
        url=f"{settings.frontend_url}/settings?success=google_connected&service={service}"
    )


# ──────────────────────────────────────
# Integration Status
# ──────────────────────────────────────

@router.get("/status")
async def get_integration_status() -> list[IntegrationStatus]:
    """Get connection status for all supported integrations."""
    services = [
        ("gmail", "Google Gmail"),
        ("calendar", "Google Calendar"),
        ("slack", "Slack"),
        ("notion", "Notion"),
        ("github", "GitHub"),
        ("jira", "Jira"),
    ]

    result = []
    for service_id, _ in services:
        connected_info = _connected_services.get(service_id, {})
        result.append(IntegrationStatus(
            service=service_id,
            connected=connected_info.get("connected", False),
            last_synced=connected_info.get("connected_at"),
        ))

    return result
