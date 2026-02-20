"""
Velocity AI - Database Service
Mock connectors for MongoDB (state checkpoints) and Neo4j (GraphRAG).
In production, these would connect to real instances.
"""

from config import settings


# ──────────────────────────────────────
# MongoDB Mock (State Checkpoints)
# ──────────────────────────────────────

class MongoDBService:
    """Mock MongoDB service for conversation state and checkpoints."""

    def __init__(self):
        self.connected = False
        self._conversations: dict[str, list] = {}
        self._checkpoints: dict[str, dict] = {}

    async def connect(self):
        """Connect to MongoDB (mock)."""
        # TODO: Replace with real pymongo connection
        # client = pymongo.MongoClient(settings.mongodb_uri)
        # self.db = client["velocity"]
        self.connected = True
        print("📦 MongoDB mock connected")

    async def save_conversation(self, conversation_id: str, messages: list):
        """Save conversation messages (mock)."""
        self._conversations[conversation_id] = messages

    async def get_conversation(self, conversation_id: str) -> list:
        """Retrieve conversation messages (mock)."""
        return self._conversations.get(conversation_id, [])

    async def save_checkpoint(self, agent_id: str, state: dict):
        """Save LangGraph agent state checkpoint (mock)."""
        self._checkpoints[agent_id] = state

    async def get_checkpoint(self, agent_id: str) -> dict | None:
        """Retrieve agent state checkpoint (mock)."""
        return self._checkpoints.get(agent_id)


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
