"""
Velocity AI - Conversations Router
In-memory CRUD for conversation management.
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

# In-memory conversation store
_conversations: dict[int, dict] = {}
_messages: dict[int, list[dict]] = {}
_next_id = 1


class CreateConversationRequest(BaseModel):
    user_id: int
    title: str | None = None


class UpdateConversationRequest(BaseModel):
    title: str


class ConversationResponse(BaseModel):
    id: int
    title: str
    owner_id: int
    created_at: str
    updated_at: str | None = None


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    created_at: str


@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation."""
    global _next_id

    conversation = {
        "id": _next_id,
        "title": request.title or "New Chat",
        "owner_id": request.user_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": None,
    }

    _conversations[_next_id] = conversation
    _messages[_next_id] = []
    _next_id += 1

    return ConversationResponse(**conversation)


@router.get("/conversations/{user_id}")
async def get_user_conversations(user_id: int):
    """Get all conversations for a user."""
    user_convos = [
        c for c in _conversations.values()
        if c["owner_id"] == user_id
    ]

    # Sort by created_at descending (newest first)
    user_convos.sort(key=lambda x: x["created_at"], reverse=True)

    return {
        "conversations": user_convos,
        "total": len(user_convos),
    }


@router.get("/conversations/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: int):
    """Get all messages in a conversation."""
    if conversation_id not in _conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return _messages.get(conversation_id, [])


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(conversation_id: int, request: UpdateConversationRequest):
    """Update conversation title."""
    if conversation_id not in _conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    _conversations[conversation_id]["title"] = request.title
    _conversations[conversation_id]["updated_at"] = datetime.utcnow().isoformat()

    return ConversationResponse(**_conversations[conversation_id])


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(conversation_id: int):
    """Delete a conversation."""
    if conversation_id not in _conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")

    del _conversations[conversation_id]
    _messages.pop(conversation_id, None)

    return {"status": "deleted"}
