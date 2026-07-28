"""Smoke test: InsForge — create a table (admin key), insert + read a record (anon key)."""
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

BASE = os.environ.get("INSFORGE_BASE_URL", "").rstrip("/")
ANON = os.environ.get("INSFORGE_ANON_KEY")
ADMIN = os.environ.get("INSFORGE_API_KEY")
if not (BASE and ANON):
    sys.exit(
        "FAIL: need INSFORGE_BASE_URL (https://<your-app>.insforge.app) and "
        "INSFORGE_ANON_KEY in .env (npx @insforge/cli secrets get ANON_KEY)"
    )

TABLE = "kept_smoke"

if ADMIN:
    r = requests.post(
        f"{BASE}/api/database/tables",
        headers={"X-API-Key": ADMIN, "Content-Type": "application/json"},
        json={
            "tableName": TABLE,
            "columns": [{"name": "note", "type": "string", "nullable": False}],
            "rlsEnabled": False,
        },
    )
    print("create table:", r.status_code, r.text[:200])
else:
    print("no INSFORGE_API_KEY — assuming table exists (create it in dashboard)")

H = {"Authorization": f"Bearer {ANON}"}
r = requests.post(
    f"{BASE}/api/database/records/{TABLE}",
    headers={**H, "Content-Type": "application/json", "Prefer": "return=representation"},
    json=[{"note": "KEPT smoke: promise stored"}],
)
print("insert:", r.status_code, r.text[:200])
if r.status_code >= 300:
    sys.exit("FAIL: insert failed")

r = requests.get(f"{BASE}/api/database/records/{TABLE}?limit=5", headers=H)
print("read:", r.status_code, r.text[:300])
if r.status_code >= 300 or not r.json():
    sys.exit("FAIL: read failed or empty")
print("PASS: InsForge table + insert + read all work")
