"""
Solomon Memory System — Built on Memary Principles
===================================================
Memary (kingjulio8238/memary) principles adapted for Solomon OS:
- Memory Stream: chronological log of all interactions
- Entity Knowledge Store: tracks entities by frequency + recency
- Routing Agent: decides what to remember and when
- ReAct pattern: reasoning + action for memory decisions

This system runs ON TOP of existing brain files — not replacing them.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

MEMORY_DIR = Path("/home/workspace/solomon-vault/brain")
STREAM_FILE = MEMORY_DIR / "memory_stream.jsonl"
ENTITIES_FILE = MEMORY_DIR / "entity_knowledge_store.json"
LESSONS_FILE = MEMORY_DIR / "LESSONS.md"


class MemoryStream:
    """Chronological log — every significant interaction is recorded."""

    def __init__(self, file_path: Path = STREAM_FILE):
        self.file_path = file_path
        self.buffer = []

    def add(self, entities: list[str], summary: str, source: str = "session"):
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "entities": entities,
            "summary": summary,
            "source": source,
        }
        self.buffer.append(entry)
        with open(self.file_path, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_recent(self, n: int = 50) -> list[dict]:
        if not self.file_path.exists():
            return []
        lines = open(self.file_path).readlines()
        return [json.loads(l) for l in lines[-n:]]

    def search(self, query: str) -> list[dict]:
        """Full-text search across memory stream."""
        results = []
        q = query.lower()
        if self.file_path.exists():
            for line in open(self.file_path):
                entry = json.loads(line)
                if q in entry["summary"].lower() or any(q in e.lower() for e in entry["entities"]):
                    results.append(entry)
        return results


class EntityKnowledgeStore:
    """
    Tracks entities (clients, tools, concepts, decisions) by frequency + recency.
    Inspired by Memary's depth-of-knowledge scoring.
    """

    def __init__(self, file_path: Path = ENTITIES_FILE):
        self.file_path = file_path
        self.entities = self._load()

    def _load(self) -> dict:
        if self.file_path.exists():
            return json.loads(open(self.file_path).read())
        return {}

    def _save(self):
        with open(self.file_path, "w") as f:
            json.dump(self.entities, f, indent=2)

    def add(self, entities: list[str], timestamp: str = None):
        ts = timestamp or datetime.utcnow().isoformat() + "Z"
        for entity in entities:
            e = entity.lower().strip()
            if e in self.entities:
                self.entities[e]["count"] += 1
                self.entities[e]["last_seen"] = ts
            else:
                self.entities[e] = {"count": 1, "first_seen": ts, "last_seen": ts}

    def get_top(self, n: int = 20) -> list[tuple]:
        """Return top-N entities by frequency."""
        sorted_e = sorted(self.entities.items(), key=lambda x: x[1]["count"], reverse=True)
        return sorted_e[:n]

    def get_depth(self, entity: str) -> str:
        """Return depth of knowledge for an entity."""
        e = entity.lower().strip()
        if e not in self.entities:
            return "unknown"
        count = self.entities[e]["count"]
        if count >= 10:
            return "expert"
        elif count >= 5:
            return "proficient"
        elif count >= 2:
            return "familiar"
        else:
            return "new"


class SolomonMemory:
    """
    Main memory system — combines Memory Stream + Entity Knowledge Store.
    Call after every significant action.
    """

    def __init__(self):
        self.stream = MemoryStream()
        self.entities = EntityKnowledgeStore()
        os.makedirs(MEMORY_DIR, exist_ok=True)

    def log(self, summary: str, entities: list[str] = None, source: str = "session"):
        """Log a significant event to memory."""
        entities = entities or []
        self.stream.add(entities, summary, source)
        self.entities.add(entities)

    def query(self, question: str) -> str:
        """Query memory for relevant context."""
        results = self.stream.search(question)
        if not results:
            return "No relevant memory found."
        recent = results[-5:]
        lines = [f"[{r['timestamp'][:10]}] {r['summary']}" for r in recent]
        return "\n".join(lines)

    def who(self, entity: str) -> dict:
        """Get everything we know about an entity."""
        e = entity.lower().strip()
        entity_data = self.entities.entities.get(e, {})
        depth = self.entities.get_depth(entity)
        return {"data": entity_data, "depth": depth}

    def status(self) -> dict:
        """Return current memory system status."""
        return {
            "total_entities": len(self.entities.entities),
            "total_memories": len(self.stream.get_recent(9999)),
            "top_entities": self.entities.get_top(10),
        }


# ─────────────────────────────────────────
# SOLOMON OS MEMORY LOGGER — Call in sessions
# ─────────────────────────────────────────

def log_to_memory(summary: str, entities: list[str] = None, source: str = "telegram"):
    """One-line logger for any session."""
    mem = SolomonMemory()
    mem.log(summary, entities, source)


if __name__ == "__main__":
    # Test
    mem = SolomonMemory()
    print("Status:", json.dumps(mem.status(), indent=2))
    mem.log(
        summary="Sherlock Digital Footprint Audit launched as first product",
        entities=["Sherlock", "Digital Footprint", "Stripe", "OSINT", "product launch"],
        source="integration",
    )
    print("After log:", mem.status())
