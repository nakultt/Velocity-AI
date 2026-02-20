"""
Velocity AI - Configuration
Loads environment variables via pydantic-settings.
"""

import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings loaded from .env"""

    # App
    app_name: str = "Velocity AI"
    debug: str | bool = True

    # Gemini AI
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")

    # MongoDB
    mongodb_uri: str = os.getenv("MONGODB_URI", "mongodb://localhost:27017/velocity")

    # Neo4j
    neo4j_uri: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_user: str = os.getenv("NEO4J_USER", "neo4j")
    neo4j_password: str = os.getenv("NEO4J_PASSWORD", "")

    # Google OAuth
    google_client_id: str = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    google_redirect_uri: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/google/callback")

    # GitHub
    github_token: str = os.getenv("GITHUB_TOKEN", "")

    # Slack
    slack_bot_token: str = os.getenv("SLACK_BOT_TOKEN", "")

    # Notion
    notion_api_key: str = os.getenv("NOTION_API_KEY", "")

    # Jira
    jira_api_token: str = os.getenv("JIRA_API_TOKEN", "")
    jira_email: str = os.getenv("JIRA_EMAIL", "")
    jira_cloud_url: str = os.getenv("JIRA_CLOUD_URL", "")

    # Frontend
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")

    class Config:
        env_file = ".env"
        extra = "allow"


settings = Settings()
