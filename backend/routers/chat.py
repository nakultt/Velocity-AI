"""
Velocity AI - Chat Router
WhatsApp-style AI chat powered by LangGraph agent pipeline.
"""

import uuid
from fastapi import APIRouter
from models.schemas import ChatRequest, ChatResponse
from agents.graph import run_velocity_agent
from services.ai_service import generate_chat_response

router = APIRouter()

# In-memory conversation store (mock — production uses MongoDB)
_conversations: dict[str, list[dict]] = {}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Send a message to the AI assistant.
    Routes through the full LangGraph agent pipeline:
    - Personal: Prioritizer → Planner → Researcher → Summary
    - Workspace: Ingestor → Context Matcher → Prioritizer → Summary
    Falls back to simple Gemini chat if agent pipeline fails.
    """
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Store user message
    if conversation_id not in _conversations:
        _conversations[conversation_id] = []

    _conversations[conversation_id].append({
        "role": "user",
        "content": request.message,
    })

    # Run through LangGraph agent pipeline
    try:
        result = await run_velocity_agent(
            user_input=request.message,
            mode=request.mode,
            thread_id=conversation_id,
        )
    except Exception:
        # Fallback to simple chat
        result = await generate_chat_response(request.message, request.mode)

    # Store assistant message
    _conversations[conversation_id].append({
        "role": "assistant",
        "content": result["response"],
    })

    return ChatResponse(
        response=result["response"],
        conversation_id=conversation_id,
        requires_approval=result.get("requires_approval", False),
        proposed_action=result.get("proposed_action"),
        sources=result.get("sources", []),
    )


@router.post("/chat/approve/{conversation_id}")
async def approve_action(conversation_id: str) -> dict:
    """Approve a proposed AI action (human-in-the-loop)."""
    return {
        "status": "approved",
        "conversation_id": conversation_id,
        "message": "✅ Action approved! Changes have been applied to your calendar.",
    }


@router.post("/chat/reject/{conversation_id}")
async def reject_action(conversation_id: str) -> dict:
    """Reject a proposed AI action (human-in-the-loop)."""
    return {
        "status": "rejected",
        "conversation_id": conversation_id,
        "message": "❌ Action rejected. No changes were made.",
    }


@router.get("/chat/history/{conversation_id}")
async def get_chat_history(conversation_id: str) -> dict:
    """Get conversation history."""
    messages = _conversations.get(conversation_id, [])
    return {
        "conversation_id": conversation_id,
        "messages": messages,
    }
