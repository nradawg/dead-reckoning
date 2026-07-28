"""HydraDB retrieval layer for The Coroner.

Everything routes through query(), which takes an optional `sources` scope.
That scope parameter IS the kill shot: same question, fewer connectors.
"""
import os

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

BASE = "https://api.hydradb.com"
KEY = os.environ["HYDRA_DB_API_KEY"]
DATABASE = os.environ.get("HYDRA_DB_DATABASE", "default-tenant")

HEADERS = {
    "Authorization": f"Bearer {KEY}",
    "API-Version": "2",
    "Content-Type": "application/json",
}

# The four connectors the verdict depends on.
ALL_SOURCES = ["slack", "github", "linear", "gmail"]


def list_connectors():
    r = requests.get(f"{BASE}/connectors", headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json().get("connectors", [])


def query(question, sources=None, database=None, limit=25):
    """Query the context graph, optionally scoped to specific connectors.

    sources=None searches every synced connector.
    sources=["linear"] is the demo's single-source run.
    """
    body = {
        "database": database or DATABASE,
        "type": "all",
        "query": question,
        "query_apps": True,
        "limit": limit,
    }
    if sources:
        body["metadata_filters"] = {
            "additional_metadata": {"provider": list(sources)}
        }

    r = requests.post(f"{BASE}/query", headers=HEADERS, json=body, timeout=60)
    r.raise_for_status()
    payload = r.json()
    if not payload.get("success"):
        raise RuntimeError(payload.get("error"))
    return payload["data"]


def evidence(question, sources=None):
    """Return flat evidence items: text, provider, timestamp, url."""
    data = query(question, sources=sources)
    items = []
    for chunk in data.get("chunks", []):
        meta = chunk.get("metadata") or {}
        extra = meta.get("additional_metadata") or {}
        items.append(
            {
                "text": chunk.get("text") or chunk.get("content", ""),
                "provider": extra.get("provider") or meta.get("provider") or "unknown",
                "timestamp": extra.get("timestamp") or meta.get("created_at"),
                "url": extra.get("url") or meta.get("url"),
                "score": chunk.get("score"),
            }
        )
    return items


if __name__ == "__main__":
    conns = list_connectors()
    print(f"connectors synced: {len(conns)}")
    for c in conns:
        print(" ", c.get("provider"), c.get("id"), c.get("status"))
    if not conns:
        print("\n>>> NO CONNECTORS. Need the hackathon's pre-synced database.")
