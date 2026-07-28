# KEPT

**The agent that makes sure your team keeps its word.**

Built at Agents You Love 2 — Frontier Tower, San Francisco, July 28 2026.

## The impossible question

> "What did we promise people in email and Slack, and did the code ever actually ship?"

Promises live in **Gmail** and **Slack**. Proof lives in **GitHub** and **Linear**.
No single tool can answer it. KEPT can, because HydraDB resolves entities across
all four connectors before we ever ask.

## How it works

1. **Extractor agent** (Pipeshift, specialized model) — finds commitments in
   Gmail/Slack messages: who promised what, to whom, by when.
2. **Resolver agent** (HydraDB) — cross-references each promise against GitHub
   PRs and Linear tickets to verdict it: KEPT / BROKEN / PENDING, with receipts.
3. **Drafter agent** (Pipeshift) — drafts the honest follow-up ("this shipped,
   here's the PR" or "we owe you an update").

The whole loop runs as a multi-agent pipeline deployed on **RocketRide Cloud**.
**InsForge** holds the agent intent profile and the promise ledger (db + auth).

## The kill shot (demo)

Run the full query → promise ledger with verdicts and receipts.
Re-run scoped to Gmail only → every verdict collapses to UNKNOWN.
The truth lives *between* your apps.

## Setup

```bash
cp .env.example .env   # paste your keys
pip install -r requirements.txt
python smoke/test_hydradb.py
python smoke/test_pipeshift.py
python smoke/test_insforge.py
python smoke/rocketride_hello.py
```

All four smoke tests must pass before any feature work.
