"""Preflight. Tells you exactly which service is not configured, and why.

Run this before anything else. It fails loudly and specifically instead of
letting you discover a bad key twenty minutes later.
"""
import os
import sys

import requests
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))

OK, BAD = "  OK   ", "  FAIL "
problems = []


def need(*names):
    missing = [n for n in names if not os.environ.get(n)]
    return missing


def check_hydra():
    missing = need("HYDRA_DB_API_KEY", "HYDRA_DB_DATABASE")
    if missing:
        return False, f"missing in .env: {', '.join(missing)}"
    h = {"Authorization": f"Bearer {os.environ['HYDRA_DB_API_KEY']}",
         "API-Version": "2"}
    r = requests.get("https://api.hydradb.com/databases", headers=h, timeout=30)
    if r.status_code == 401:
        return False, "key rejected. Get a LIVE key at app.hydradb.com"
    if r.status_code >= 400:
        return False, f"HTTP {r.status_code} {r.text[:80]}"
    dbs = r.json().get("data", {}).get("databases", [])
    want = os.environ["HYDRA_DB_DATABASE"]
    if want not in dbs:
        return False, (f"database '{want}' not found. Yours: {dbs or 'none yet'}. "
                       f"Create one at app.hydradb.com then set HYDRA_DB_DATABASE")

    c = requests.get("https://api.hydradb.com/connectors", headers=h, timeout=30)
    n = len(c.json().get("connectors", [])) if c.status_code < 400 else 0
    if n == 0:
        return True, (f"connected, database '{want}' exists, but NO CONNECTORS. "
                      f"Add Slack/GitHub/Gmail at app.hydradb.com > Connectors, "
                      f"or run: python seed/seed_corpus.py for demo data")
    return True, f"database '{want}', {n} connector(s) synced"


def check_pipeshift():
    if need("PIPESHIFT_API_KEY"):
        return False, "missing PIPESHIFT_API_KEY"
    model = os.environ.get("PIPESHIFT_MODEL", "deepseek-ai/DeepSeek-V4-Flash")
    r = requests.post(
        "https://api.pipeshift.com/api/v0/chat/completions",
        headers={"Authorization": f"Bearer {os.environ['PIPESHIFT_API_KEY']}",
                 "Content-Type": "application/json"},
        json={"model": model, "messages": [{"role": "user", "content": "hi"}],
              "max_tokens": 8},
        timeout=60)
    if r.status_code == 402:
        return False, "wallet empty. Add credit or redeem a coupon in Settings > Billing"
    if r.status_code == 403:
        return False, "key rejected"
    if r.status_code >= 400:
        return False, (f"HTTP {r.status_code}. Is '{model}' added under Serverless "
                       f"APIs? Copy the exact id from its View endpoint panel")
    return True, f"model {model} responding"


def check_insforge():
    missing = need("INSFORGE_BASE_URL", "INSFORGE_ANON_KEY")
    if missing:
        return False, f"missing in .env: {', '.join(missing)}"
    base = os.environ["INSFORGE_BASE_URL"].rstrip("/")
    r = requests.get(f"{base}/api/database/records/certificates?limit=1",
                     headers={"Authorization":
                              f"Bearer {os.environ['INSFORGE_ANON_KEY']}"},
                     timeout=30)
    if r.status_code == 404:
        return True, "reachable, but no 'certificates' table yet. Run: python agents/morgue.py"
    if r.status_code >= 400:
        return False, f"HTTP {r.status_code} {r.text[:80]}"
    return True, "certificates table reachable"


def check_rocketride():
    if need("ROCKETRIDE_AUTH"):
        return None, "not set (optional, only needed for the hosted pipeline)"
    return True, "token present"


if __name__ == "__main__":
    print(f"python {sys.version.split()[0]}")
    if sys.version_info < (3, 10):
        print(f"{BAD} python 3.10+ required. Re-run ./setup.sh")
        sys.exit(1)

    for name, fn in (("HydraDB", check_hydra), ("Pipeshift", check_pipeshift),
                     ("InsForge", check_insforge), ("RocketRide", check_rocketride)):
        try:
            ok, msg = fn()
        except Exception as e:
            ok, msg = False, f"{type(e).__name__}: {str(e)[:100]}"
        tag = "  SKIP " if ok is None else (OK if ok else BAD)
        print(f"{tag} {name:<12} {msg}")
        if ok is False:
            problems.append(name)

    print()
    if problems:
        print(f"Fix these first: {', '.join(problems)}")
        sys.exit(1)
    print("All good. Now run:  ./.venv/bin/python agents/discover.py")
