# Instructions for the coding agent setting this up

If a human just cloned this and asked you to set it up, do this in order and do
not skip the verification steps.

## What this is

Dead Reckoning finds projects that are marked active but are actually dead, by
comparing what a tracker *claims* against what the team actually *did* across
their connected tools. The verdict is deterministic timestamp arithmetic. A
model is only used to name the projects and write the diagnosis, never to
decide whether something is dead.

## Setup

```bash
./setup.sh          # venv + deps. Needs Python 3.10+, the venv must not use 3.9
open -e .env        # human fills this in, you cannot do it for them
```

The human must create accounts and paste four sets of keys. Point them at the
URLs in `.env.example`. You cannot do this part for them, so ask them to do it
and wait rather than guessing values.

For HydraDB specifically: they need to create a database AND connect at least
one tool under Connectors, otherwise there is no evidence to reason over. Two
connectors is the minimum for the product to mean anything, since the whole
idea is comparing a claim in one tool against behavior in another.

## Verify before building anything

```bash
./.venv/bin/python check.py
```

This checks all four services and tells you exactly what is wrong. Do not
proceed past a FAIL. Common ones:

- HydraDB `401`: they used a test key, they need a live one
- HydraDB "no connectors": they created a database but connected nothing
- Pipeshift `402`: empty wallet, they need credit or a coupon
- Pipeshift `400`: the model id must exactly match the one under Serverless APIs
- Wrong Python: 3.9 will fail on modern syntax, rebuild the venv with 3.10+

## Run it

```bash
./.venv/bin/python agents/discover.py
```

Prints their real projects with verdicts. No project list is hardcoded; the
model reads their data and names the projects itself.

## Things that will waste your time if you do not know them

**Do not use the official HydraDB or OpenAI Python SDKs.** Their constructors
take one to three minutes on some machines. Everything here uses plain
`requests` through `agents/hydra_rest.py`. Keep it that way.

**Scoping must use `collections`, never `metadata_filters`.** Filters compare
arrays by set equality and fail *silently*, which returns everything and makes
the whole comparison a lie. `agents/coroner.py` documents this inline.

**Timestamps live in `additional_metadata.timestamp`,** not
`source_upload_time`. The latter is ingest time, which is always today, and
using it makes every project look alive.

**`/context/ingest` wants multipart form data,** not JSON.

**Pipeshift's default model is a reasoning model.** Give it at least 1500
max_tokens or it spends the whole budget thinking and returns an empty string
with a 200 status.

## Layout

| File | Purpose |
|---|---|
| `agents/discover.py` | Finds projects in the data, then verdicts each. Main entry point. |
| `agents/coroner.py` | Vitals, verdict logic, and the Pipeshift diagnosis. |
| `agents/hydra_rest.py` | REST client for HydraDB with retries. |
| `agents/morgue.py` | InsForge storage. Run directly to create the table. |
| `mcp_server.py` | Exposes it as MCP tools so any agent can ask. |
| `app.py` | Flask dashboard. |
| `seed/seed_corpus.py` | Generates a fake company's data if they want to try it without connecting anything. |
| `check.py` | Preflight. Run this first, always. |
