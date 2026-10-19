

from __future__ import annotations
import json
import asyncio
import os
import time
import uuid
from typing import Any, AsyncGenerator
import os
from dotenv import load_dotenv

load_dotenv()

   # or llama3.2, mistral, etc.
NEO4J_URI    = os.getenv("NEO4J_URI",    "bolt://localhost:7687")

#NEO4J_URI    = os.getenv("NEO4J_URI",    "neo4j://host.docker.internal:7687")
NEO4J_USER   = os.getenv("NEO4J_USER",   "neo4j")
NEO4J_PASS   = os.getenv("NEO4J_PASS", "password1234")
API_TIMEOUT  = 120

try:
    from neo4j import GraphDatabase

    _neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    NEO4J_AVAILABLE = True
except Exception:
    _neo4j_driver  = None
    NEO4J_AVAILABLE = False


def run_neo4j(query: str, params: dict = {}) -> list[dict]:
    if not NEO4J_AVAILABLE or _neo4j_driver is None:
        return []
    try:
        with _neo4j_driver.session() as s:
            return [r.data() for r in s.run(query, params)]
    except Exception as e:
        print(f"Neo4j error: {e}")
        return []
