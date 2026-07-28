"""InsForge storage: the morgue.

Every run writes a certificate row. The UI reads only from here, which is what
makes the on-stage kill-shot toggle a database read rather than a live inference.
"""
import json
import os

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

BASE = os.environ["INSFORGE_BASE_URL"].rstrip("/")
ANON = os.environ["INSFORGE_ANON_KEY"]
ADMIN = os.environ.get("INSFORGE_API_KEY")

TABLE = "certificates"
AUTH = {"Authorization": f"Bearer {ANON}"}


def ensure_table():
    """Create the certificates table. Idempotent enough for a hackathon."""
    r = requests.post(
        f"{BASE}/api/database/tables",
        headers={"X-API-Key": ADMIN, "Content-Type": "application/json"},
        json={
            "tableName": TABLE,
            "rlsEnabled": False,
            # InsForge wants columnName/isNullable/isUnique, not name/nullable.
            "columns": [
                {"columnName": c, "type": t, "isNullable": n, "isUnique": False}
                for c, t, n in [
                    ("project", "string", False),
                    ("scope", "string", False),
                    ("verdict", "string", True),
                    ("confidence", "float", True),
                    ("time_of_death", "string", True),
                    ("cause", "string", True),
                    ("survived_by", "string", True),
                    ("recommendation", "string", True),
                    ("alternative", "string", True),
                    ("evidence", "json", True),
                    ("evidence_count", "integer", True),
                ]
            ],
        },
        timeout=30,
    )
    return r.status_code, r.text[:300]


def save(cert):
    """Write one certificate. `scope` is 'all' or the single connector name."""
    row = dict(cert)
    if isinstance(row.get("evidence"), (list, dict)):
        row["evidence"] = json.dumps(row["evidence"])
    r = requests.post(
        f"{BASE}/api/database/records/{TABLE}",
        headers={**AUTH, "Content-Type": "application/json",
                 "Prefer": "return=representation"},
        json=[row],
        timeout=30,
    )
    r.raise_for_status()
    return r.json()


def latest(project, scope):
    """Read back the most recent certificate for a project at a given scope."""
    r = requests.get(
        f"{BASE}/api/database/records/{TABLE}"
        f"?project=eq.{project}&scope=eq.{scope}&limit=1",
        headers=AUTH,
        timeout=30,
    )
    r.raise_for_status()
    rows = r.json()
    return rows[0] if rows else None


if __name__ == "__main__":
    print("ensure_table:", ensure_table())
    print("save:", save({
        "project": "smoke-test", "scope": "all", "verdict": "DECEASED",
        "confidence": 0.9, "cause": "smoke test", "evidence": [], "evidence_count": 0,
    }))
    print("latest:", latest("smoke-test", "all"))


def recent(project="", limit=20):
    """Recent certificates, optionally for one project. Powers the memory tool."""
    q = f"?limit={limit}&order=created_at.desc"
    if project:
        q += f"&project=eq.{project}"
    r = requests.get(f"{BASE}/api/database/records/{TABLE}{q}",
                     headers=AUTH, timeout=30)
    r.raise_for_status()
    return r.json()
