"""
Velocity AI – Google Workspace LangChain Tools
Gmail, Google Calendar, and Google Docs access via Google APIs.
OAuth tokens are managed by the integrations router (locus pattern).
"""

from __future__ import annotations

import os
from typing import Optional

import httpx
from langchain_core.tools import BaseTool
from pydantic import Field, BaseModel


class QueryInput(BaseModel):
    query: str = Field(description="The action and arguments to perform.")


# ═══════════════════════════════════════════════════════════
# Gmail Tool
# ═══════════════════════════════════════════════════════════

class GmailTool(BaseTool):
    """
    LangChain tool for Gmail API.

    Capabilities:
    - List recent emails (inbox, sent)
    - Read a specific email
    - Search emails by query
    - Send an email (draft or send)

    Used by: IngestorNode, ContextMatcherNode
    """

    name: str = "gmail"
    description: str = (
        "Access Gmail: list recent emails, read an email, search, or send. "
        "Use action='inbox' for recent emails, 'read MSG_ID' to read, "
        "'search query' to search, 'send to@email.com|subject|body' to send."
    )
    args_schema: type[BaseModel] = QueryInput
    access_token: str = Field(default="")

    def _run(self, query: str) -> str:
        import asyncio
        return asyncio.run(self._arun(query))

    async def _arun(self, query: str) -> str:
        from services.db_service import mongodb
        t = await mongodb.get_token("gmail")
        if t:
            self.access_token = t.get("access_token", "")
            
        if not self.access_token:
            return "Gmail not configured. Please connect from the UI."

        parts = query.strip().split(maxsplit=1)
        action = parts[0].lower() if parts else "inbox"
        arg = parts[1] if len(parts) > 1 else ""

        dispatch = {
            "inbox": self._list_inbox,
            "read": self._read_email,
            "search": self._search_emails,
            "send": self._send_email,
        }

        handler = dispatch.get(action, self._list_inbox)
        return await handler(arg)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"}

    async def _list_inbox(self, _: str = "") -> str:
        """List recent inbox emails."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                    headers=self._headers(),
                    params={"maxResults": 10, "labelIds": "INBOX"},
                    timeout=15,
                )
                data = resp.json()
                messages = data.get("messages", [])

                results = []
                for msg_ref in messages[:5]:
                    msg_resp = await client.get(
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_ref['id']}",
                        headers=self._headers(),
                        params={"format": "metadata", "metadataHeaders": ["From", "Subject", "Date"]},
                        timeout=15,
                    )
                    msg = msg_resp.json()
                    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
                    results.append(
                        f"• From: {headers.get('From', '?')} | "
                        f"Subject: {headers.get('Subject', 'No subject')} | "
                        f"{headers.get('Date', '')}"
                    )
                return "\n".join(results) or "Inbox is empty."
        except Exception as e:
            return f"Gmail API error: {e}"

    async def _read_email(self, msg_id: str) -> str:
        """Read a specific email by ID."""
        if not msg_id:
            return "Provide a message ID."
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
                    headers=self._headers(),
                    params={"format": "full"},
                    timeout=15,
                )
                msg = resp.json()
                snippet = msg.get("snippet", "")
                headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
                return (
                    f"From: {headers.get('From', '?')}\n"
                    f"Subject: {headers.get('Subject', 'No subject')}\n"
                    f"Date: {headers.get('Date', '?')}\n\n"
                    f"{snippet}"
                )
        except Exception as e:
            return f"Gmail API error: {e}"

    async def _search_emails(self, query: str) -> str:
        """Search emails."""
        if not query:
            return "Provide a search query."
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                    headers=self._headers(),
                    params={"q": query, "maxResults": 10},
                    timeout=15,
                )
                data = resp.json()
                messages = data.get("messages", [])
                return f"Found {len(messages)} emails matching '{query}'." if messages else "No emails found."
        except Exception as e:
            return f"Gmail API error: {e}"

    async def _send_email(self, args: str) -> str:
        """Send email. Format: 'to@email.com|subject|body'"""
        parts = args.split("|", 2)
        if len(parts) < 3:
            return "Format: 'to@email.com|subject|body'"

        import base64
        to, subject, body = parts
        raw = f"To: {to}\nSubject: {subject}\n\n{body}"
        encoded = base64.urlsafe_b64encode(raw.encode()).decode()

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                    headers=self._headers(),
                    json={"raw": encoded},
                    timeout=15,
                )
                if resp.status_code == 200:
                    return f"✅ Email sent to {to}."
                return f"Failed to send: {resp.text}"
        except Exception as e:
            return f"Gmail API error: {e}"


# ═══════════════════════════════════════════════════════════
# Google Calendar Tool
# ═══════════════════════════════════════════════════════════

class GoogleCalendarTool(BaseTool):
    """
    LangChain tool for Google Calendar API.

    Capabilities:
    - List upcoming events
    - Create a new event (schedule study/coding blocks)
    - Delete / update an event

    Used by: PlannerNode (schedule creation), SummaryNode
    """

    name: str = "google_calendar"
    description: str = (
        "Access Google Calendar: list upcoming events, create events, delete events. "
        "Use action='events' for upcoming, "
        "'create title|start_iso|end_iso|description' to create, "
        "'delete EVENT_ID' to remove."
    )
    args_schema: type[BaseModel] = QueryInput
    access_token: str = Field(default="")
    calendar_id: str = Field(default="primary")

    def _run(self, query: str) -> str:
        import asyncio
        return asyncio.run(self._arun(query))

    async def _arun(self, query: str) -> str:
        from services.db_service import mongodb
        t = await mongodb.get_token("calendar")
        if t:
            self.access_token = t.get("access_token", "")
            
        if not self.access_token:
            return "Google Calendar not configured. Please connect from the UI."

        parts = query.strip().split(maxsplit=1)
        action = parts[0].lower() if parts else "events"
        arg = parts[1] if len(parts) > 1 else ""

        dispatch = {
            "events": self._list_events,
            "create": self._create_event,
            "delete": self._delete_event,
        }

        handler = dispatch.get(action, self._list_events)
        return await handler(arg)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"}

    async def _list_events(self, _: str = "") -> str:
        """List upcoming calendar events."""
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://www.googleapis.com/calendar/v3/calendars/{self.calendar_id}/events",
                    headers=self._headers(),
                    params={
                        "timeMin": now,
                        "maxResults": 10,
                        "singleEvents": True,
                        "orderBy": "startTime",
                    },
                    timeout=15,
                )
                data = resp.json()
                events = data.get("items", [])
                lines = []
                for ev in events:
                    start = ev.get("start", {}).get("dateTime", ev.get("start", {}).get("date", "?"))
                    lines.append(f"• {ev.get('summary', 'No title')} @ {start}")
                return "\n".join(lines) or "No upcoming events."
        except Exception as e:
            return f"Calendar API error: {e}"

    async def _create_event(self, args: str) -> str:
        """Create a calendar event. Format: 'title|start_iso|end_iso|description'"""
        parts = args.split("|", 3)
        if len(parts) < 3:
            return "Format: 'title|2026-02-20T10:00:00|2026-02-20T11:00:00|description'"
        title, start, end = parts[0], parts[1], parts[2]
        desc = parts[3] if len(parts) > 3 else ""

        event_body = {
            "summary": title,
            "description": desc,
            "start": {"dateTime": start, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end, "timeZone": "Asia/Kolkata"},
        }

        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    f"https://www.googleapis.com/calendar/v3/calendars/{self.calendar_id}/events",
                    headers=self._headers(),
                    json=event_body,
                    timeout=15,
                )
                if resp.status_code in (200, 201):
                    return f"✅ Event '{title}' created."
                return f"Failed: {resp.text}"
        except Exception as e:
            return f"Calendar API error: {e}"

    async def _delete_event(self, event_id: str) -> str:
        """Delete a calendar event by ID."""
        if not event_id:
            return "Provide an event ID."
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.delete(
                    f"https://www.googleapis.com/calendar/v3/calendars/{self.calendar_id}/events/{event_id}",
                    headers=self._headers(),
                    timeout=15,
                )
                if resp.status_code in (200, 204):
                    return f"✅ Event {event_id} deleted."
                return f"Failed: {resp.text}"
        except Exception as e:
            return f"Calendar API error: {e}"


# ═══════════════════════════════════════════════════════════
# Google Docs Tool
# ═══════════════════════════════════════════════════════════

class GoogleDocsTool(BaseTool):
    """
    LangChain tool for Google Docs / Drive API.

    Capabilities:
    - List recent documents
    - Read document content
    - Search documents

    Used by: IngestorNode, ResearcherNode
    """

    name: str = "google_docs"
    description: str = (
        "Access Google Docs/Drive: list recent docs, read content, search. "
        "Use action='list' for recent docs, 'read DOC_ID' to read, 'search query' to find."
    )
    args_schema: type[BaseModel] = QueryInput
    access_token: str = Field(default="")

    def _run(self, query: str) -> str:
        import asyncio
        return asyncio.run(self._arun(query))

    async def _arun(self, query: str) -> str:
        from services.db_service import mongodb
        t = await mongodb.get_token("docs")
        if t:
            self.access_token = t.get("access_token", "")
            
        if not self.access_token:
            return "Google Docs not configured. Please connect from the UI."

        parts = query.strip().split(maxsplit=1)
        action = parts[0].lower() if parts else "list"
        arg = parts[1] if len(parts) > 1 else ""

        dispatch = {
            "list": self._list_docs,
            "read": self._read_doc,
            "search": self._search_docs,
        }

        handler = dispatch.get(action, self._list_docs)
        return await handler(arg)

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"}

    async def _list_docs(self, _: str = "") -> str:
        """List recent Google Docs."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://www.googleapis.com/drive/v3/files",
                    headers=self._headers(),
                    params={
                        "q": "mimeType='application/vnd.google-apps.document'",
                        "pageSize": 10,
                        "orderBy": "modifiedTime desc",
                        "fields": "files(id,name,modifiedTime)",
                    },
                    timeout=15,
                )
                data = resp.json()
                files = data.get("files", [])
                lines = [f"• {f['name']} (modified: {f.get('modifiedTime', '?')})" for f in files]
                return "\n".join(lines) or "No documents found."
        except Exception as e:
            return f"Drive API error: {e}"

    async def _read_doc(self, doc_id: str) -> str:
        """Read a Google Doc's content."""
        if not doc_id:
            return "Provide a document ID."
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"https://docs.googleapis.com/v1/documents/{doc_id}",
                    headers=self._headers(),
                    timeout=15,
                )
                data = resp.json()
                title = data.get("title", "Untitled")
                # Extract text from body content
                body = data.get("body", {}).get("content", [])
                text_parts = []
                for element in body:
                    paragraph = element.get("paragraph", {})
                    for el in paragraph.get("elements", []):
                        text_run = el.get("textRun", {})
                        if text_run.get("content"):
                            text_parts.append(text_run["content"])
                return f"📄 {title}\n\n{''.join(text_parts)[:2000]}"
        except Exception as e:
            return f"Docs API error: {e}"

    async def _search_docs(self, query: str) -> str:
        """Search Google Drive for documents."""
        if not query:
            return "Provide a search query."
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://www.googleapis.com/drive/v3/files",
                    headers=self._headers(),
                    params={
                        "q": f"fullText contains '{query}' and mimeType='application/vnd.google-apps.document'",
                        "pageSize": 10,
                        "fields": "files(id,name,modifiedTime)",
                    },
                    timeout=15,
                )
                data = resp.json()
                files = data.get("files", [])
                lines = [f"• {f['name']} (ID: {f['id']})" for f in files]
                return "\n".join(lines) or f"No docs matching '{query}'."
        except Exception as e:
            return f"Drive API error: {e}"
