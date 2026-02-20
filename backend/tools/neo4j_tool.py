"""
Velocity AI – Neo4j LangChain Tool
Knowledge graph memory for GraphRAG: stores tasks, relationships,
context, and enables semantic retrieval across conversations.
"""

from __future__ import annotations

import os
from typing import Optional

from langchain_core.tools import BaseTool
from pydantic import Field


class Neo4jMemoryTool(BaseTool):
    """
    LangChain tool for Neo4j-backed knowledge graph (GraphRAG).

    Capabilities:
    - Store knowledge nodes (tasks, people, projects, concepts)
    - Create relationships between nodes
    - Query related context for RAG augmentation
    - Get full subgraph around a topic

    Used by: PrioritizerNode, ResearcherNode, SummaryNode
    """

    name: str = "neo4j_memory"
    description: str = (
        "Access the knowledge graph for storing and retrieving context. "
        "Use action='store label|prop1:val1,prop2:val2' to add a node, "
        "'relate from_label:from_name|relation|to_label:to_name' for relationships, "
        "'query topic' for context retrieval, 'subgraph topic' for full graph."
    )

    uri: str = Field(default_factory=lambda: os.getenv("NEO4J_URI", "bolt://localhost:7687"))
    user: str = Field(default_factory=lambda: os.getenv("NEO4J_USER", "neo4j"))
    password: str = Field(default_factory=lambda: os.getenv("NEO4J_PASSWORD", ""))

    # In-memory fallback when Neo4j is not available
    _memory_nodes: list = []
    _memory_edges: list = []
    _driver: object = None

    class Config:
        arbitrary_types_allowed = True

    def _get_driver(self):
        """Lazy-init Neo4j driver."""
        if self._driver is None and self.password:
            try:
                from neo4j import GraphDatabase
                self._driver = GraphDatabase.driver(
                    self.uri, auth=(self.user, self.password)
                )
            except Exception as e:
                print(f"Neo4j connection failed ({e}), using in-memory fallback.")
        return self._driver

    def _run(self, query: str) -> str:
        import asyncio
        return asyncio.run(self._arun(query))

    async def _arun(self, query: str) -> str:
        parts = query.strip().split(maxsplit=1)
        action = parts[0].lower() if parts else "query"
        arg = parts[1] if len(parts) > 1 else ""

        dispatch = {
            "store": self._store_node,
            "relate": self._create_relationship,
            "query": self._query_context,
            "subgraph": self._get_subgraph,
            "tasks": self._get_all_tasks,
        }

        handler = dispatch.get(action, self._query_context)
        return await handler(arg)

    # ── Store a knowledge node ────────────────────────────
    async def _store_node(self, args: str) -> str:
        """Store a node. Format: 'Label|key1:val1,key2:val2'"""
        parts = args.split("|", 1)
        if len(parts) < 2:
            return "Format: 'Task|title:Fix login bug,priority:high'"

        label = parts[0].strip()
        props = {}
        for pair in parts[1].split(","):
            if ":" in pair:
                k, v = pair.split(":", 1)
                props[k.strip()] = v.strip()

        driver = self._get_driver()
        if driver:
            try:
                with driver.session() as session:
                    prop_str = ", ".join(f"n.{k} = ${k}" for k in props)
                    cypher = f"CREATE (n:{label}) SET {prop_str} RETURN n"
                    session.run(cypher, **props)
                return f"✅ Node [{label}] stored in Neo4j: {props}"
            except Exception as e:
                return f"Neo4j error: {e}"
        else:
            # In-memory fallback
            node = {"label": label, **props}
            self._memory_nodes.append(node)
            return f"✅ Node [{label}] stored in memory: {props}"

    # ── Create a relationship ─────────────────────────────
    async def _create_relationship(self, args: str) -> str:
        """Create a relationship. Format: 'FromLabel:from_name|RELATION|ToLabel:to_name'"""
        parts = args.split("|")
        if len(parts) < 3:
            return "Format: 'Person:Nakul|WORKS_ON|Project:Auth Module'"

        from_parts = parts[0].split(":", 1)
        relation = parts[1].strip()
        to_parts = parts[2].split(":", 1)

        if len(from_parts) < 2 or len(to_parts) < 2:
            return "Use 'Label:name' format for both nodes."

        from_label, from_name = from_parts[0].strip(), from_parts[1].strip()
        to_label, to_name = to_parts[0].strip(), to_parts[1].strip()

        driver = self._get_driver()
        if driver:
            try:
                with driver.session() as session:
                    cypher = (
                        f"MATCH (a:{from_label} {{name: $from_name}}), "
                        f"(b:{to_label} {{name: $to_name}}) "
                        f"CREATE (a)-[r:{relation}]->(b) RETURN r"
                    )
                    session.run(cypher, from_name=from_name, to_name=to_name)
                return f"✅ Relationship: ({from_label}:{from_name})-[{relation}]->({to_label}:{to_name})"
            except Exception as e:
                return f"Neo4j error: {e}"
        else:
            edge = {
                "from": f"{from_label}:{from_name}",
                "relation": relation,
                "to": f"{to_label}:{to_name}",
            }
            self._memory_edges.append(edge)
            return f"✅ Relationship stored in memory: {edge}"

    # ── Query context (for RAG) ───────────────────────────
    async def _query_context(self, topic: str) -> str:
        """Query knowledge graph for context related to a topic."""
        if not topic:
            return "Provide a topic to query."

        driver = self._get_driver()
        if driver:
            try:
                with driver.session() as session:
                    # Full-text-like search across all node properties
                    cypher = """
                    MATCH (n)
                    WHERE any(key IN keys(n) WHERE toString(n[key]) CONTAINS $topic)
                    OPTIONAL MATCH (n)-[r]-(m)
                    RETURN n, type(r) as rel, m
                    LIMIT 20
                    """
                    result = session.run(cypher, topic=topic)
                    lines = []
                    for record in result:
                        node = dict(record["n"])
                        lines.append(f"• {list(record['n'].labels)[0]}: {node}")
                        if record["rel"] and record["m"]:
                            related = dict(record["m"])
                            lines.append(f"  └─ [{record['rel']}] → {related}")
                    return "\n".join(lines) or f"No context found for '{topic}'."
            except Exception as e:
                return f"Neo4j error: {e}"
        else:
            # Search in-memory nodes
            matches = [
                n for n in self._memory_nodes
                if topic.lower() in str(n).lower()
            ]
            if matches:
                lines = [f"• {m.get('label', '?')}: {m}" for m in matches]
                return "\n".join(lines)
            return f"No context found for '{topic}'."

    # ── Get subgraph ──────────────────────────────────────
    async def _get_subgraph(self, topic: str) -> str:
        """Get full subgraph around a topic (2-hop neighbourhood)."""
        if not topic:
            return "Provide a topic."

        driver = self._get_driver()
        if driver:
            try:
                with driver.session() as session:
                    cypher = """
                    MATCH path = (n)-[*1..2]-(m)
                    WHERE any(key IN keys(n) WHERE toString(n[key]) CONTAINS $topic)
                    RETURN path
                    LIMIT 50
                    """
                    result = session.run(cypher, topic=topic)
                    paths = list(result)
                    return f"Found {len(paths)} paths in the subgraph around '{topic}'."
            except Exception as e:
                return f"Neo4j error: {e}"
        else:
            return f"Subgraph for '{topic}': {len(self._memory_nodes)} nodes, {len(self._memory_edges)} edges in memory."

    # ── Get all tasks ─────────────────────────────────────
    async def _get_all_tasks(self, _: str = "") -> str:
        """Retrieve all Task nodes from the knowledge graph."""
        driver = self._get_driver()
        if driver:
            try:
                with driver.session() as session:
                    result = session.run("MATCH (t:Task) RETURN t ORDER BY t.priority")
                    tasks = [dict(record["t"]) for record in result]
                    if tasks:
                        lines = [f"• {t.get('title', '?')} [{t.get('priority', '?')}]" for t in tasks]
                        return "\n".join(lines)
                    return "No tasks in the knowledge graph."
            except Exception as e:
                return f"Neo4j error: {e}"
        else:
            tasks = [n for n in self._memory_nodes if n.get("label") == "Task"]
            if tasks:
                lines = [f"• {t.get('title', '?')} [{t.get('priority', '?')}]" for t in tasks]
                return "\n".join(lines)
            return "No tasks stored yet."
