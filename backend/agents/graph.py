"""
Velocity AI – LangGraph Agent Orchestrator
=============================================

Two state graphs matching the architecture diagrams:

PERSONAL MODE:
  Input → Brain (Prioritizer) → Planner (Timetable) → Researcher → Summary
                                    ↕ (Human-in-the-loop approval)

WORKSPACE MODE:
  Ingestor (Apps Analyzer) → Context Matcher → Prioritizer → Summary
      ↕ GitHub, Slack, Gmail, Docs            ↕ Neo4j GraphRAG

Each node is a proper LangGraph node using Gemini 2.5 Flash via LangChain.
"""

from __future__ import annotations

import os
import json
from typing import TypedDict, Annotated, Literal
from datetime import datetime

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from tools.github_tool import GitHubTool
from tools.slack_tool import SlackTool
from tools.google_workspace_tool import GmailTool, GoogleCalendarTool, GoogleDocsTool
from tools.neo4j_tool import Neo4jMemoryTool


# ═══════════════════════════════════════════════════════════
# Shared State
# ═══════════════════════════════════════════════════════════

class VelocityState(TypedDict):
    """Shared state flowing through the LangGraph."""
    messages: Annotated[list, add_messages]
    user_input: str
    mode: str  # "personal" | "workspace"
    # Data collected by agents
    raw_data: dict           # ingested data from tools
    prioritized_tasks: list  # output of prioritizer
    schedule_proposals: list # planner output
    research_findings: list  # researcher output
    context: str             # Neo4j RAG context
    # Human-in-the-loop
    requires_approval: bool
    proposed_action: dict | None
    approval_status: str     # "pending" | "approved" | "rejected" | "none"
    # Final
    summary: str
    sources: list[str]


# ═══════════════════════════════════════════════════════════
# LLM + Tools
# ═══════════════════════════════════════════════════════════

def _get_llm() -> ChatGroq:
    """Get Groq LLM instance."""
    return ChatGroq(
        model="llama-3.3-70b-versatile",
        api_key=os.getenv("GROQ_API_KEY", ""),
        temperature=0.7,
        max_tokens=2048,
    )


def _get_tools() -> dict:
    """Instantiate all LangChain tools."""
    return {
        "github": GitHubTool(),
        "slack": SlackTool(),
        "gmail": GmailTool(),
        "calendar": GoogleCalendarTool(),
        "docs": GoogleDocsTool(),
        "neo4j": Neo4jMemoryTool(),
    }


# ═══════════════════════════════════════════════════════════
# NODE: Ingestor (Apps Analyzer Agent)
# ═══════════════════════════════════════════════════════════

async def ingestor_node(state: VelocityState) -> VelocityState:
    """
    Step 1 – Data Ingestion (Workspace Mode).
    Continuously monitors GitHub, Slack, Gmail for the latest signals.
    Collects raw data for downstream processing.
    """
    tools = _get_tools()
    raw_data: dict = {}

    # Pull from GitHub
    try:
        repos = await tools["github"]._arun("repos")
        raw_data["github_repos"] = repos
    except Exception as e:
        raw_data["github_repos"] = f"Error: {e}"

    # Pull from Slack
    try:
        channels = await tools["slack"]._arun("channels")
        raw_data["slack_channels"] = channels
    except Exception as e:
        raw_data["slack_channels"] = f"Error: {e}"

    # Pull from Gmail
    try:
        inbox = await tools["gmail"]._arun("inbox")
        raw_data["gmail_inbox"] = inbox
    except Exception as e:
        raw_data["gmail_inbox"] = f"Error: {e}"

    # Pull from Google Docs
    try:
        docs = await tools["docs"]._arun("list")
        raw_data["google_docs"] = docs
    except Exception as e:
        raw_data["google_docs"] = f"Error: {e}"

    state["raw_data"] = raw_data
    state["sources"] = ["github", "slack", "gmail", "google_docs"]
    state["messages"].append(
        AIMessage(content=f"[Ingestor] Collected data from {len(raw_data)} sources.")
    )
    return state


# ═══════════════════════════════════════════════════════════
# NODE: Context Matcher (Pending Tasks Analyzer)
# ═══════════════════════════════════════════════════════════

async def context_matcher_node(state: VelocityState) -> VelocityState:
    """
    Step 2 – Cross-references updates across platforms.
    Example: Reads Slack "UI is finished", checks GitHub to verify commit exists.
    Uses Neo4j to find related context from the knowledge graph.
    """
    llm = _get_llm()
    tools = _get_tools()

    # Get context from Neo4j knowledge graph
    try:
        context = await tools["neo4j"]._arun(f"query {state['user_input']}")
        state["context"] = context
    except Exception:
        state["context"] = "No graph context available."

    # Use Gemini to cross-reference the raw data
    raw_summary = json.dumps(state.get("raw_data", {}), default=str)[:3000]

    messages = [
        SystemMessage(content=(
            "You are the Context Matcher agent in Velocity AI. "
            "Your job is to cross-reference updates from different platforms "
            "(GitHub, Slack, Gmail, Docs) and identify:\n"
            "1. Verified completions (e.g., Slack says 'done' + GitHub has the commit)\n"
            "2. Conflicting signals (e.g., Slack says 'done' but no commit found)\n"
            "3. New information that changes priorities\n"
            "4. Related context from the knowledge graph\n\n"
            f"Knowledge Graph Context:\n{state['context']}\n\n"
            "Respond with a structured JSON with keys: "
            "'verified_updates', 'conflicts', 'new_signals', 'context_links'"
        )),
        HumanMessage(content=f"Raw data from all sources:\n{raw_summary}"),
    ]

    try:
        response = await llm.ainvoke(messages)
        state["messages"].append(
            AIMessage(content=f"[Context Matcher] {response.content[:500]}")
        )
    except Exception as e:
        state["messages"].append(
            AIMessage(content=f"[Context Matcher] Analysis skipped: {e}")
        )

    return state


# ═══════════════════════════════════════════════════════════
# NODE: Prioritizer (The Brain)
# ═══════════════════════════════════════════════════════════

async def prioritizer_node(state: VelocityState) -> VelocityState:
    """
    Step 2/3 – The Brain (works in both modes).
    Analyzes pending tasks and assigns priorities using:
    - Grade impact (Personal Mode)
    - Revenue/launch impact (Workspace Mode)
    - Deadline urgency
    - Neo4j context for historical patterns
    """
    llm = _get_llm()
    tools = _get_tools()

    # Pull context from Neo4j
    try:
        graph_context = await tools["neo4j"]._arun(f"query {state['user_input']}")
    except Exception:
        graph_context = ""

    mode = state.get("mode", "personal")

    if mode == "personal":
        system = (
            "You are the Prioritizer (The Brain) in Velocity AI Personal Mode.\n"
            "Given the user's input, analyze and prioritize their tasks.\n"
            "Consider:\n"
            "- Academic deadlines and grade weight (exams > homework > reading)\n"
            "- Startup urgency (bugs affecting users > feature work > nice-to-haves)\n"
            "- Energy levels (hard tasks when fresh, light tasks when tired)\n"
            "- Historical context from the knowledge graph\n\n"
            f"Knowledge Graph:\n{graph_context}\n\n"
            "Respond with JSON array of tasks, each with: "
            "title, priority (critical/high/medium/low), category (academic/startup/personal), "
            "estimated_hours, reasoning"
        )
    else:
        system = (
            "You are the Prioritizer (Task Sorting Agent) in Velocity AI Workspace Mode.\n"
            "Re-evaluate what the team needs to do next based on:\n"
            "- Latest updates from all platforms\n"
            "- Market signals and competitor moves\n"
            "- Sprint velocity and team capacity\n"
            "- Blocker resolution urgency\n\n"
            f"Context:\n{state.get('context', '')}\n\n"
            "Respond with JSON array of priorities, each with: "
            "title, urgency (critical/high/medium/low), project, assigned_to, ai_reasoning"
        )

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=state["user_input"]),
    ]

    try:
        response = await llm.ainvoke(messages)
        state["prioritized_tasks"] = [response.content]
        state["messages"].append(
            AIMessage(content=f"[Prioritizer] {response.content[:500]}")
        )

        # Store priorities in Neo4j for future context
        try:
            await tools["neo4j"]._arun(
                f"store PrioritySnapshot|date:{datetime.now().isoformat()},tasks:{response.content[:200]}"
            )
        except Exception:
            pass

    except Exception as e:
        state["messages"].append(
            AIMessage(content=f"[Prioritizer] Error: {e}")
        )
        state["prioritized_tasks"] = []

    return state


# ═══════════════════════════════════════════════════════════
# NODE: Planner (Timetable Planner Agent)
# ═══════════════════════════════════════════════════════════

async def planner_node(state: VelocityState) -> VelocityState:
    """
    Step 3 (Personal Mode) – Timetable Planner.
    Takes prioritized tasks and automatically blocks out time.
    Sets reminders, schedules meetings, adjusts if priorities shift.
    Requests human approval before making changes.
    """
    llm = _get_llm()

    priorities = state.get("prioritized_tasks", [])
    priorities_text = "\n".join(str(p) for p in priorities)

    messages = [
        SystemMessage(content=(
            "You are the Timetable Planner Agent in Velocity AI.\n"
            "Given the prioritized tasks, create an optimal daily schedule.\n"
            "Rules:\n"
            "- Study blocks: 45-90 min with breaks (Pomodoro-friendly)\n"
            "- Coding blocks: 2-3 hour deep work sessions\n"
            "- No scheduling over existing commitments\n"
            "- High-grade-impact items get prime focus hours (morning)\n"
            "- Include breaks and transition time\n\n"
            "Respond with JSON array of schedule_blocks, each with: "
            "title, start_time (HH:MM), end_time (HH:MM), category, reasoning\n\n"
            "Also set 'requires_approval': true since you're proposing schedule changes."
        )),
        HumanMessage(content=f"Prioritized tasks:\n{priorities_text}"),
    ]

    try:
        response = await llm.ainvoke(messages)
        state["schedule_proposals"] = [response.content]
        state["requires_approval"] = True
        state["proposed_action"] = {
            "type": "schedule",
            "description": "AI wants to block time on your calendar for these tasks",
            "status": "pending_approval",
        }
        state["messages"].append(
            AIMessage(content=f"[Planner] {response.content[:500]}")
        )
    except Exception as e:
        state["messages"].append(
            AIMessage(content=f"[Planner] Error: {e}")
        )
        state["schedule_proposals"] = []
        state["requires_approval"] = False

    return state


# ═══════════════════════════════════════════════════════════
# NODE: Researcher (The Hustle)
# ═══════════════════════════════════════════════════════════

async def researcher_node(state: VelocityState) -> VelocityState:
    """
    Step 3 (Personal Mode supplement) – The Hustle.
    While the student studies, this agent autonomously searches for:
    - New business models relevant to their startup
    - Open-source contributions matching their skills
    - Industry news and competitor moves
    """
    llm = _get_llm()
    tools = _get_tools()

    # Search GitHub for relevant repos/opportunities
    try:
        github_data = await tools["github"]._arun("repos")
    except Exception:
        github_data = ""

    # Check Neo4j for user's skill profile
    try:
        skills_context = await tools["neo4j"]._arun("query skills")
    except Exception:
        skills_context = ""

    messages = [
        SystemMessage(content=(
            "You are the Researcher Agent (The Hustle) in Velocity AI.\n"
            "While the user focuses on studying/coding, you proactively find:\n"
            "1. Trending repos relevant to their tech stack\n"
            "2. Open-source contribution opportunities\n"
            "3. Competitor launches or market shifts\n"
            "4. Business model ideas for their startup niche\n\n"
            f"User's GitHub profile:\n{github_data[:500]}\n\n"
            f"Skills context:\n{skills_context[:300]}\n\n"
            "Respond with JSON: research_findings (array of "
            "{title, category, relevance_score, summary, action_item})"
        )),
        HumanMessage(content=state["user_input"]),
    ]

    try:
        response = await llm.ainvoke(messages)
        state["research_findings"] = [response.content]
        state["messages"].append(
            AIMessage(content=f"[Researcher] {response.content[:500]}")
        )

        # Store findings in Neo4j
        try:
            await tools["neo4j"]._arun(
                f"store Research|date:{datetime.now().isoformat()},findings:{response.content[:200]}"
            )
        except Exception:
            pass

    except Exception as e:
        state["messages"].append(
            AIMessage(content=f"[Researcher] Error: {e}")
        )
        state["research_findings"] = []

    return state


# ═══════════════════════════════════════════════════════════
# NODE: Summary (Output Agent)
# ═══════════════════════════════════════════════════════════

async def summary_node(state: VelocityState) -> VelocityState:
    """
    Step 4/5 – Summary Agent.
    Compiles all agent outputs into a clean, actionable response
    for the user's dashboard.
    """
    llm = _get_llm()

    mode = state.get("mode", "personal")
    priorities = "\n".join(str(p) for p in state.get("prioritized_tasks", []))
    schedule = "\n".join(str(s) for s in state.get("schedule_proposals", []))
    research = "\n".join(str(r) for r in state.get("research_findings", []))
    context = state.get("context", "")

    if mode == "personal":
        system = (
            "You are the Summary Agent in Velocity AI Personal Mode.\n"
            "Compile a clean, friendly daily summary for the student's dashboard.\n"
            "Include:\n"
            "1. Top 3 priorities for today (with emojis)\n"
            "2. Proposed schedule (if planner produced one)\n"
            "3. Research highlights (if any)\n"
            "4. One motivational insight\n\n"
            "Be concise, use markdown formatting, be encouraging."
        )
    else:
        system = (
            "You are the Summary Agent in Velocity AI Workspace Mode.\n"
            "Compile a concise project management dashboard update.\n"
            "Include:\n"
            "1. Project status overview (with status emojis 🟢🟡🔴)\n"
            "2. Key updates from all platforms with source attribution\n"
            "3. Re-ranked priorities with AI reasoning\n"
            "4. Action items and blockers\n\n"
            "Be data-driven, cite sources, use markdown."
        )

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=(
            f"User message: {state['user_input']}\n\n"
            f"Priorities:\n{priorities}\n\n"
            f"Schedule:\n{schedule}\n\n"
            f"Research:\n{research}\n\n"
            f"Context:\n{context}"
        )),
    ]

    try:
        response = await llm.ainvoke(messages)
        state["summary"] = response.content
        state["messages"].append(
            AIMessage(content=response.content)
        )
    except Exception as e:
        state["summary"] = f"Summary generation failed: {e}"
        state["messages"].append(
            AIMessage(content=state["summary"])
        )

    return state


# ═══════════════════════════════════════════════════════════
# Routing Logic
# ═══════════════════════════════════════════════════════════

def route_by_mode(state: VelocityState) -> str:
    """Route to the correct first node based on mode."""
    if state.get("mode") == "workspace":
        return "ingestor"
    return "prioritizer"


def route_after_prioritizer(state: VelocityState) -> str:
    """In personal mode, go to planner. In workspace, go to summarizer."""
    if state.get("mode") == "workspace":
        return "summarizer"
    return "planner"


def route_after_planner(state: VelocityState) -> str:
    """After planner, run researcher in parallel (simulated sequentially)."""
    return "researcher"


# ═══════════════════════════════════════════════════════════
# Build the Graphs
# ═══════════════════════════════════════════════════════════

def build_personal_graph() -> StateGraph:
    """
    Personal Mode Graph:
    Input → Prioritizer → Planner → Researcher → Summary
    """
    graph = StateGraph(VelocityState)

    graph.add_node("prioritizer", prioritizer_node)
    graph.add_node("planner", planner_node)
    graph.add_node("researcher", researcher_node)
    graph.add_node("summarizer", summary_node)

    graph.set_entry_point("prioritizer")
    graph.add_edge("prioritizer", "planner")
    graph.add_edge("planner", "researcher")
    graph.add_edge("researcher", "summarizer")
    graph.add_edge("summarizer", END)

    return graph


def build_workspace_graph() -> StateGraph:
    """
    Workspace Mode Graph:
    Ingestor → Context Matcher → Prioritizer → Summary
    """
    graph = StateGraph(VelocityState)

    graph.add_node("ingestor", ingestor_node)
    graph.add_node("context_matcher", context_matcher_node)
    graph.add_node("prioritizer", prioritizer_node)
    graph.add_node("summarizer", summary_node)

    graph.set_entry_point("ingestor")
    graph.add_edge("ingestor", "context_matcher")
    graph.add_edge("context_matcher", "prioritizer")
    graph.add_edge("prioritizer", "summarizer")
    graph.add_edge("summarizer", END)

    return graph


# ═══════════════════════════════════════════════════════════
# Compiled Graphs (with memory checkpoint)
# ═══════════════════════════════════════════════════════════

# Graphs are now compiled dynamically with AsyncMongoDBSaver in run_velocity_agent


# ═══════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════

async def run_velocity_agent(
    user_input: str,
    mode: str = "personal",
    thread_id: str = "default",
) -> dict:
    """
    Run the full Velocity AI agent pipeline.

    Args:
        user_input: The user's message
        mode: "personal" or "workspace"
        thread_id: Conversation thread for memory persistence

    Returns:
        dict with response, requires_approval, proposed_action, sources
    """
    initial_state: VelocityState = {
        "messages": [HumanMessage(content=user_input)],
        "user_input": user_input,
        "mode": mode,
        "raw_data": {},
        "prioritized_tasks": [],
        "schedule_proposals": [],
        "research_findings": [],
        "context": "",
        "requires_approval": False,
        "proposed_action": None,
        "approval_status": "none",
        "summary": "",
        "sources": [],
    }

    config = {"configurable": {"thread_id": thread_id}}

    # 1. Interactive Chat Mode (User asking chatbot a direct question)
    if thread_id != "system_polling":
        llm = _get_llm()
        tools_dict = _get_tools()
        tools_list = list(tools_dict.values())
        
        system_instruction = (
            "You are Velocity AI, a productivity assistant with access to tools (GitHub, Slack, Calendar, Docs, Notion, Jira). "
            "Use them to answer the user's questions or perform actions on their behalf. "
            "If they ask to see channels, list projects, check emails, etc. you MUST use your tools to find the answer. "
            "Always be concise and helpful."
        )
        if mode == "workspace":
            system_instruction += "\nWorkspace mode: focus on team projects, blockers, and updates."
        else:
            system_instruction += "\nPersonal mode: focus on academics, personal schedule, and study."
            
        chat_agent = create_react_agent(llm, tools=tools_list, checkpointer=MemorySaver())
        
        try:
            chat_result = await chat_agent.ainvoke(
                {"messages": [
                    SystemMessage(content=system_instruction),
                    HumanMessage(content=user_input)
                ]},
                config
            )
            final_msg = chat_result["messages"][-1].content
            return {
                "response": final_msg,
                "requires_approval": False,
                "proposed_action": None,
                "sources": ["Agent Tools"],
                "prioritized_tasks": [],
                "schedule_proposals": [],
                "research_findings": [],
            }
        except Exception as e:
            return {
                "response": f"Chat agent error: {e}",
                "requires_approval": False,
                "proposed_action": None,
                "sources": [],
                "prioritized_tasks": [],
                "schedule_proposals": [],
                "research_findings": [],
            }

    # 2. Daily Summary / Background Polling Mode (Rigid pipeline)
    memory = MemorySaver()
    if mode == "personal":
        graph = build_personal_graph().compile(checkpointer=memory)
    else:
        graph = build_workspace_graph().compile(checkpointer=memory)

    try:
        result = await graph.ainvoke(initial_state, config)
        return {
            "response": result.get("summary", "No summary generated."),
            "requires_approval": result.get("requires_approval", False),
            "proposed_action": result.get("proposed_action"),
            "sources": result.get("sources", []),
            "prioritized_tasks": result.get("prioritized_tasks", []),
            "schedule_proposals": result.get("schedule_proposals", []),
            "research_findings": result.get("research_findings", []),
        }
    except Exception as e:
        # Fallback to simple response if graph fails
        return {
            "response": f"Agent pipeline error: {e}. Falling back to simple mode.",
            "requires_approval": False,
            "proposed_action": None,
            "sources": [],
            "prioritized_tasks": [],
            "schedule_proposals": [],
            "research_findings": [],
        }
