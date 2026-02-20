"""
Velocity AI - AI Service
Uses Gemini 2.5 Flash via google-genai for chat and orchestration.
LangGraph orchestration is scaffolded for future agentic workflows.
"""

import os
from groq import AsyncGroq
from config import settings


# Initialize Groq client
client = None
if settings.groq_api_key:
    client = AsyncGroq(api_key=settings.groq_api_key)

MODEL = "llama-3.3-70b-versatile"

# System prompts for different modes
PERSONAL_SYSTEM_PROMPT = """You are Velocity AI, a personal productivity assistant for student founders.
You help balance academic commitments with startup work. You can:
- Prioritize tasks based on deadlines and grade impact
- Schedule study sessions and coding blocks
- Identify when something needs human approval before scheduling
- Provide daily summaries and actionable insights

When a user mentions deadlines, exams, or scheduling conflicts, propose a plan and ask for approval.
Always be concise, actionable, and supportive. Use emojis sparingly for friendliness."""

WORKSPACE_SYSTEM_PROMPT = """You are Velocity AI, a workspace intelligence assistant for startup teams.
You help monitor and synthesize information across team tools. You can:
- Summarize project status across Slack, GitHub, Notion, and email
- Re-prioritize backlog items based on new information
- Identify blockers and suggest resolutions
- Track market intelligence and competitive signals

Be data-driven, concise, and actionable. Reference sources when synthesizing updates."""


async def generate_chat_response(message: str, mode: str = "personal") -> dict:
    """
    Generate a chat response using Gemini 2.5 Flash.
    Falls back to mock response if no API key configured.
    """
    system_prompt = PERSONAL_SYSTEM_PROMPT if mode == "personal" else WORKSPACE_SYSTEM_PROMPT

    if client:
        try:
            response = await client.chat.completions.create(
                model=MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            response_text = response.choices[0].message.content

            # Detect if AI suggests scheduling or priority changes → trigger approval
            requires_approval = any(
                keyword in response_text.lower()
                for keyword in ["schedule", "reschedule", "block time", "move your", "i'll set up", "let me arrange"]
            )

            proposed_action = None
            if requires_approval:
                proposed_action = {
                    "type": "schedule",
                    "description": "AI wants to modify your schedule based on this conversation.",
                    "status": "pending_approval",
                }

            return {
                "response": response_text,
                "requires_approval": requires_approval,
                "proposed_action": proposed_action,
                "sources": [],
            }

        except Exception as e:
            print(f"Groq API error: {e}")
            # Fall through to mock

    # Mock response when no API key
    return _get_mock_response(message, mode)


def _get_mock_response(message: str, mode: str) -> dict:
    """Generate mock AI responses for demo purposes."""

    message_lower = message.lower()

    if mode == "personal":
        if "exam" in message_lower or "test" in message_lower:
            return {
                "response": "📚 I see you have an exam coming up! I've analyzed your schedule and here's what I recommend:\n\n**Proposed Study Plan:**\n• Today 4-6 PM: Review Chapter 5-7 (high-weight topics)\n• Tomorrow 10 AM-12 PM: Practice problems\n• Day before exam: Light review + rest\n\nI'll also push your sprint tasks to after the exam. **Should I lock this into your calendar?**",
                "requires_approval": True,
                "proposed_action": {
                    "type": "schedule",
                    "description": "Block study sessions and defer startup tasks until after exam",
                    "status": "pending_approval",
                },
                "sources": ["Google Calendar", "Course Syllabus"],
            }
        elif "bug" in message_lower or "fix" in message_lower:
            return {
                "response": "🐛 Got it — I've flagged the login bug as **high priority** in your startup backlog.\n\n**Quick triage:**\n• Estimated fix time: ~2 hours\n• Best slot today: 7-9 PM (after your study block)\n• Related PR: #47 on GitHub\n\nWant me to **schedule a focused coding block** for this tonight?",
                "requires_approval": True,
                "proposed_action": {
                    "type": "schedule",
                    "description": "Schedule 2-hour coding block tonight for bug fix",
                    "status": "pending_approval",
                },
                "sources": ["GitHub Issues", "Sprint Board"],
            }
        else:
            return {
                "response": "👋 Hey! I'm Velocity AI, your personal productivity co-pilot. I can help you:\n\n• 📅 Schedule study + coding sessions\n• 🎯 Prioritize tasks by grade impact\n• 🔄 Rebalance your week when things change\n\nTry telling me something like *\"I have a Math exam on Friday and need to fix the login bug\"* and I'll create an optimized plan!",
                "requires_approval": False,
                "proposed_action": None,
                "sources": [],
            }
    else:  # workspace mode
        if "status" in message_lower or "update" in message_lower:
            return {
                "response": "📊 **Project Pulse Summary:**\n\n🟢 **Auth Module** — On track (92% complete)\n↳ Latest: Login flow merged [GitHub], Design approved [Slack]\n\n🟡 **Payment Integration** — Needs attention\n↳ Stripe webhook failing intermittently. 3 related Slack threads.\n\n🔴 **Landing Page** — Blocked\n↳ Waiting on copy from marketing. Deadline: Thursday.\n\n**AI Recommendation:** Unblock the landing page first — it's on the critical path for launch.",
                "requires_approval": False,
                "proposed_action": None,
                "sources": ["Slack", "GitHub", "Notion"],
            }
        else:
            return {
                "response": "🏢 Welcome to Workspace Mode! I'm monitoring your team's tools and can help with:\n\n• 📋 Real-time project status across all platforms\n• 🔄 Smart priority re-ranking based on new signals\n• 📈 Market intelligence alerts\n• 👥 Team velocity tracking\n\nAsk me anything about your projects, or check the Dashboard for the full overview!",
                "requires_approval": False,
                "proposed_action": None,
                "sources": [],
            }


# ──────────────────────────────────────
# LangGraph Orchestration Scaffold
# ──────────────────────────────────────

async def run_agent_workflow(user_input: str, mode: str = "personal") -> dict:
    """
    Placeholder for the full LangGraph agentic workflow.
    In production, this would orchestrate:
    - To-Do Planner Agent → Brain (Prioritizer) → Timetable Planner → Summary Agent
    For now, it delegates to the simple Gemini chat.
    """
    # TODO: Implement full LangGraph StateGraph with:
    # - PrioritizerNode: Analyzes tasks with grade/deadline context
    # - SchedulerNode: Blocks calendar slots
    # - ResearcherNode: Searches for relevant opportunities
    # - SummaryNode: Compiles daily output
    return await generate_chat_response(user_input, mode)
