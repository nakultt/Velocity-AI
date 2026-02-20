"""
Velocity AI - Background Polling Service
Polls integrations every minute for new activity and feeds to AI.
"""

import asyncio
from datetime import datetime
from routers.projects import get_updates
from agents.graph import run_velocity_agent
from routers.activity import append_activity

# Keep track of seen update IDs to only process new ones
_seen_updates: set[str] = set()

async def poll_integrations():
    """Background task to poll for new activity every minute."""
    print("🔄 Background polling started. Checking for new activity every minute...")
    while True:
        try:
            # 1. Fetch latest updates from all connected integrations
            # (get_updates already aggregates Gmail, Slack, GitHub)
            updates = await get_updates()
            
            # 2. Filter for new updates we haven't seen yet
            new_updates = []
            for u in updates:
                if u.id not in _seen_updates:
                    new_updates.append(u)
            
            # 3. If there's new activity, have the AI analyze it
            if new_updates:
                print(f"📥 Found {len(new_updates)} new updates. Sending to AI for analysis...")
                
                # Format updates for the AI prompt
                update_text = "\n".join([f"- [{u.source}] {u.message} ({u.timestamp})" for u in new_updates])
                prompt = (
                    f"Here is some new activity from my connected applications:\n{update_text}\n"
                    "Analyze these updates. If anything is urgent or requires action, highlight it. "
                    "Keep your summary concise."
                )
                
                # Pass to Workspace mode agent
                try:
                    result = await run_velocity_agent(
                        user_input=prompt,
                        mode="workspace",
                        thread_id="system_polling"
                    )
                    ai_response = result.get("response", "Activity analyzed.")
                except Exception as ai_err:
                    print(f"⚠️ AI analysis failed (rate limit?): {ai_err}")
                    ai_response = "Rate limit reached. Activity logged without AI summary."
                
                # 4. Log the AI's response so it appears in the Activity Log or as a notification
                append_activity(
                    action=f"Found {len(new_updates)} new updates across integrations",
                    source="system",
                    mode="workspace",
                    details=ai_response[:200]
                )
                
                # 5. Only mark as seen AFTER successfully processing/logging them
                for u in new_updates:
                    _seen_updates.add(u.id)
                    
                print("✅ Processing of background updates complete.")
                
        except Exception as e:
            print(f"⚠️ Polling error: {e}")
            
        # Wait 60 seconds before next poll
        await asyncio.sleep(60)
