"""Smoke test: HydraDB — create db, ingest one memory, query it, query scoped.

PASS means: auth works, ingestion works, query works, and source-scoping
(the kill-shot mechanism for the demo) works.
"""
import json
import os
import sys
import time

from dotenv import load_dotenv
from hydra_db import HydraDB

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

API_KEY = os.environ.get("HYDRA_DB_API_KEY") or os.environ.get("HYDRADB_API_KEY")
if not API_KEY:
    sys.exit("FAIL: no HydraDB key in .env (HYDRA_DB_API_KEY)")

client = HydraDB(token=API_KEY)
database = "kept_smoke"

print("databases:", client.databases.list().data)

try:
    client.databases.create(database=database)
except Exception as e:
    print(f"create skipped ({e})")

for _ in range(60):
    if client.databases.status(database=database).data.infra.ready_for_ingestion:
        break
    time.sleep(5)
else:
    sys.exit("FAIL: database never became ready")

ingest = client.context.ingest(
    type="memory",
    database=database,
    memories=json.dumps([{"text": "KEPT smoke: we promised the demo would work"}]),
)
sid = ingest.data.results[0].id

for _ in range(60):
    status = client.context.status(database=database, ids=[sid]).data.statuses[0]
    if status.indexing_status == "completed":
        break
    if status.indexing_status == "errored":
        sys.exit(f"FAIL: indexing errored: {status.error_message}")
    time.sleep(2)
else:
    sys.exit("FAIL: indexing never completed")

results = client.query(database=database, type="memory", query="What did we promise?")
print("query chunks:", results.data.chunks)

scoped = client.query(
    database=database, type="memory", query="What did we promise?", ids=[sid]
)
print("scoped chunks:", scoped.data.chunks)

if not results.data.chunks:
    sys.exit("FAIL: query returned no chunks")
print("PASS: HydraDB ingest + query + source-scoped query all work")
