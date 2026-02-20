"""
Velocity AI - Database Service
Mock connectors for MongoDB (state checkpoints) and Neo4j (GraphRAG).
In production, these would connect to real instances.
"""

import motor.motor_asyncio
from config import settings


# ──────────────────────────────────────
# MongoDB (State Checkpoints & Tokens)
# ──────────────────────────────────────

class MongoDBService:
    """Real MongoDB service for conversation state, checkpoints, and integration tokens."""

    def __init__(self):
        self.connected = False
        self.client = None
        self.db = None
        
        # Fallback memory just in case
        self._conversations: dict[str, list] = {}
        self._checkpoints: dict[str, dict] = {}

    async def connect(self):
        """Connect to MongoDB."""
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(settings.mongodb_uri)
            self.db = self.client["velocity"]
            # Ping db
            await self.client.admin.command('ping')
            self.connected = True
            print("📦 MongoDB connected")
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            self.connected = False

    async def save_conversation(self, conversation_id: str, messages: list):
        if self.connected:
            await self.db.conversations.update_one(
                {"conversation_id": conversation_id},
                {"$set": {"messages": messages}},
                upsert=True
            )
        else:
            self._conversations[conversation_id] = messages

    async def get_conversation(self, conversation_id: str) -> list:
        if self.connected:
            doc = await self.db.conversations.find_one({"conversation_id": conversation_id})
            return doc["messages"] if doc else []
        return self._conversations.get(conversation_id, [])

    async def save_checkpoint(self, agent_id: str, state: dict):
        if self.connected:
            await self.db.checkpoints.update_one(
                {"agent_id": agent_id},
                {"$set": {"state": state}},
                upsert=True
            )
        else:
            self._checkpoints[agent_id] = state

    async def get_checkpoint(self, agent_id: str) -> dict | None:
        if self.connected:
            doc = await self.db.checkpoints.find_one({"agent_id": agent_id})
            return doc["state"] if doc else None
        return self._checkpoints.get(agent_id)

    # ==== Integration Tokens ====
    
    async def get_token(self, service: str) -> dict | None:
        """Get auth info for a service."""
        if self.connected:
            return await self.db.integrations.find_one({"service": service}, {"_id": 0})
        return None

    async def save_token(self, service: str, auth_info: dict):
        """Save auth info for a service."""
        if self.connected:
            await self.db.integrations.update_one(
                {"service": service},
                {"$set": auth_info},
                upsert=True
            )

    async def delete_token(self, service: str):
        """Delete auth info for a service."""
        if self.connected:
            await self.db.integrations.delete_many({"service": service})


# ──────────────────────────────────────
# Neo4j Mock (GraphRAG)
# ──────────────────────────────────────

class Neo4jService:
    """Mock Neo4j service for knowledge graph and GraphRAG."""

    def __init__(self):
        self.connected = False
        self._nodes: list[dict] = []
        self._relationships: list[dict] = []

    async def connect(self):
        """Connect to Neo4j (mock)."""
        # TODO: Replace with real neo4j driver
        # driver = neo4j.GraphDatabase.driver(
        #     settings.neo4j_uri,
        #     auth=(settings.neo4j_user, settings.neo4j_password)
        # )
        self.connected = True
        print("🔗 Neo4j mock connected")

    async def add_knowledge_node(self, label: str, properties: dict):
        """Add a node to the knowledge graph (mock)."""
        self._nodes.append({"label": label, **properties})

    async def query_related(self, topic: str) -> list[dict]:
        """Query related knowledge from the graph (mock)."""
        return [
            node for node in self._nodes
            if topic.lower() in str(node).lower()
        ]

    async def get_context_for_rag(self, query: str) -> str:
        """Get contextual information for RAG pipeline (mock)."""
        related = await self.query_related(query)
        if related:
            return f"Related context: {related}"
        return "No additional context available."


# Singleton instances
mongodb = MongoDBService()
neo4j_service = Neo4jService()
