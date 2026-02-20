"""
Velocity AI - Integrations Router
Real OAuth flows and token-based connections for all services.
"""

import os
import secrets
from datetime import datetime, timedelta
from urllib.parse import urlencode
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Query, Body
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from config import settings
from models.schemas import IntegrationStatus
from services.db_service import mongodb

router = APIRouter()

# ──────────────────────────────────────
# Token Storage (MongoDB)
# ──────────────────────────────────────

_oauth_states: dict[str, dict] = {}


async def get_token(service: str) -> Optional[str]:
    """Get access token for a service. Used by tools and routers."""
    info = await mongodb.get_token(service)
    if not info:
        return None
    # Auto-refresh Google tokens if expired
    if info.get("expires_at") and datetime.utcnow().isoformat() > info["expires_at"]:
        if info.get("refresh_token"):
            await _refresh_google_token(service)
            info = await mongodb.get_token(service)
    return info.get("access_token") or info.get("token")


async def is_connected(service: str) -> bool:
    """Check if a service has stored credentials."""
    info = await mongodb.get_token(service)
    return bool(info)

# No more _init_env_tokens() — UI only


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
    "forms": [
        "https://www.googleapis.com/auth/forms.body",
        "https://www.googleapis.com/auth/forms.responses.readonly",
    ],
}


def _get_all_google_scopes() -> list[str]:
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
    service: str = Query("google", description="Service: gmail, calendar, docs, or google for all")
):
    """Start Google OAuth flow — redirects to Google consent screen."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=500, detail="Google OAuth not configured.")

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
    """Handle Google OAuth callback — exchange code for real tokens."""
    if error:
        return RedirectResponse(url=f"{settings.frontend_url}/integrations?error={error}")

    if not code or not state or state not in _oauth_states:
        return RedirectResponse(url=f"{settings.frontend_url}/integrations?error=invalid_request")

    state_data = _oauth_states.pop(state)

    # Exchange authorization code for tokens
    async with httpx.AsyncClient() as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data={
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.google_redirect_uri,
        })

        if resp.status_code != 200:
            return RedirectResponse(
                url=f"{settings.frontend_url}/integrations?error=token_exchange_failed"
            )

        token_data = resp.json()

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)
    expires_at = (datetime.utcnow() + timedelta(seconds=expires_in)).isoformat()

    # Store tokens for each Google service
    service = state_data["service"]
    services = ["gmail", "calendar", "docs", "sheets", "drive", "forms"] if service == "google" else [service]
    for svc in services:
        await mongodb.save_token(svc, {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
            "connected_at": datetime.utcnow().isoformat(),
            "source": "oauth",
        })

    return RedirectResponse(
        url=f"{settings.frontend_url}/integrations?success=google_connected&service={service}"
    )


async def _refresh_google_token(service: str):
    """Refresh Google OAuth token using refresh_token."""
    info = await mongodb.get_token(service)
    if not info or not info.get("refresh_token"):
        return

    async with httpx.AsyncClient() as client:
        resp = await client.post(GOOGLE_TOKEN_URL, data={
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "refresh_token": info["refresh_token"],
            "grant_type": "refresh_token",
        })
        if resp.status_code == 200:
            data = resp.json()
            expires_at = (datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600))).isoformat()
            # Update all Google services with new token
            for svc in ["gmail", "calendar", "docs", "sheets", "drive", "forms"]:
                svc_info = await mongodb.get_token(svc)
                if svc_info and svc_info.get("source") == "oauth":
                    svc_info["access_token"] = data["access_token"]
                    svc_info["expires_at"] = expires_at
                    await mongodb.save_token(svc, svc_info)


# ──────────────────────────────────────
# Token Connect (for GitHub, Slack, Notion, Jira)
# ──────────────────────────────────────

class TokenConnect(BaseModel):
    token: str
    email: str | None = None
    cloud_url: str | None = None


@router.post("/connect/{service}")
async def connect_service(service: str, body: TokenConnect):
    """Connect a service by providing its API token."""
    if service == "github":
        # Verify the token works
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {body.token}", "Accept": "application/vnd.github+json"},
                timeout=10,
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid GitHub token")
        await mongodb.save_token("github", {"token": body.token, "source": "manual"})

    elif service == "slack":
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://slack.com/api/auth.test",
                headers={"Authorization": f"Bearer {body.token}"},
                timeout=10,
            )
            data = resp.json()
            if not data.get("ok"):
                raise HTTPException(status_code=400, detail=f"Invalid Slack token: {data.get('error')}")
        await mongodb.save_token("slack", {"token": body.token, "source": "manual"})

    elif service == "notion":
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.notion.com/v1/users/me",
                headers={
                    "Authorization": f"Bearer {body.token}",
                    "Notion-Version": "2022-06-28",
                },
                timeout=10,
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid Notion API key")
        await mongodb.save_token("notion", {"token": body.token, "source": "manual"})

    elif service == "jira":
        if not body.email or not body.cloud_url:
            raise HTTPException(status_code=400, detail="Jira requires email and cloud_url")
        import base64
        auth_str = base64.b64encode(f"{body.email}:{body.token}".encode()).decode()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{body.cloud_url.rstrip('/')}/rest/api/3/myself",
                headers={"Authorization": f"Basic {auth_str}", "Accept": "application/json"},
                timeout=10,
            )
            if resp.status_code != 200:
                raise HTTPException(status_code=400, detail="Invalid Jira credentials")
        await mongodb.save_token("jira", {
            "token": body.token,
            "email": body.email,
            "cloud_url": body.cloud_url,
            "source": "manual",
            "connected_at": datetime.utcnow().isoformat()
        })
    else:
        raise HTTPException(status_code=400, detail=f"Unknown service: {service}")

    return {"status": "connected", "service": service}


@router.post("/disconnect/{service}")
async def disconnect_service(service: str):
    """Disconnect a service by removing its tokens."""
    await mongodb.delete_token(service)
    return {"status": "disconnected", "service": service}


# ──────────────────────────────────────
# Token Retrieval (used by tools/routers)
# ──────────────────────────────────────

@router.get("/token/{service}")
async def get_service_token(service: str) -> dict:
    """Get access token for a service (internal use)."""
    token = await get_token(service)
    if not token:
        raise HTTPException(status_code=404, detail=f"{service} not connected")
    return {"service": service, "token": token}


# ──────────────────────────────────────
# Integration Status — Real Checks
# ──────────────────────────────────────

@router.get("/status")
async def get_integration_status() -> list[IntegrationStatus]:
    """Get real connection status for all integrations."""
    services = [
        ("gmail", "Google Gmail"),
        ("calendar", "Google Calendar"),
        ("docs", "Google Docs"),
        ("sheets", "Google Sheets"),
        ("drive", "Google Drive"),
        ("forms", "Google Forms"),
        ("github", "GitHub"),
        ("slack", "Slack"),
        ("notion", "Notion"),
        ("jira", "Jira"),
    ]

    result = []
    for service_id, _ in services:
        connected = await is_connected(service_id)
        last_synced = None
        if connected:
            info = await mongodb.get_token(service_id)
            if info:
                last_synced = info.get("connected_at")
        result.append(IntegrationStatus(
            service=service_id,
            connected=connected,
            last_synced=last_synced,
        ))

    return result
