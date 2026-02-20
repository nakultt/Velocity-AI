"""
Velocity AI - FastAPI Backend Entry Point
Dual-mode autonomous OS for student founders.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routers import chat, tasks, calendar, projects, metrics, integrations, conversations, activity
from services.db_service import mongodb, neo4j_service

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    print(f"🚀 {settings.app_name} API starting...")
    import asyncio
    from services.polling import poll_integrations
    
    # Initialize Databases
    await mongodb.connect()
    await neo4j_service.connect()
    
    # Start polling loop
    polling_task = asyncio.create_task(poll_integrations())
    
    yield
    print(f"👋 {settings.app_name} API shutting down...")
    polling_task.cancel()


app = FastAPI(
    title="Velocity AI",
    description="Dual-mode autonomous operating system for student founders",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS - locus-style configuration
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    settings.frontend_url,
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers

app.include_router(chat.router, prefix="/api", tags=["Chat"])
app.include_router(tasks.router, prefix="/api", tags=["Tasks"])
app.include_router(calendar.router, prefix="/api", tags=["Calendar"])
app.include_router(projects.router, prefix="/api", tags=["Projects & Workspace"])
app.include_router(metrics.router, prefix="/api", tags=["Metrics"])
app.include_router(integrations.router, prefix="/api/integrations", tags=["Integrations"])
app.include_router(conversations.router, prefix="/api", tags=["Conversations"])
app.include_router(activity.router, prefix="/api", tags=["Activity Log"])


@app.get("/", tags=["Health"])
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "Velocity AI API"}


@app.get("/health", tags=["Health"])
async def detailed_health() -> dict[str, str]:
    """Detailed health check for Render deployment."""
    return {
        "status": "healthy",
        "service": "Velocity AI API",
        "ai_model": "llama-3.3-70b-versatile",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
