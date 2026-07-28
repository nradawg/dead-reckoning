"""Seed The Coroner's evidence corpus into HydraDB via the app_knowledge ingest path.

Every timestamp is computed as an offset from NOW, so the time spread stays correct
no matter when this is re-run. Four projects, four providers, one deliberate verdict each:

  atlas-migration     DECEASED  Linear says In Progress. Nothing has moved in ~6 weeks.
  payments-v2         ZOMBIE    Linear says In Progress. Recent Slack, but it is all
                                content-free status-chasing with no replies. False life sign.
  search-rewrite      ALIVE     In Progress and genuinely moving.
  onboarding-redesign FRESH     Started this week. Control case.

Usage:
    python seed/seed_corpus.py --create     # create db WITH metadata schema (do this FIRST, once)
    python seed/seed_corpus.py --smoke      # ingest ONE record, prove timestamp round-trips
    python seed/seed_corpus.py              # ingest the full corpus
    python seed/seed_corpus.py --verify     # run the two demo queries + the verdict math
"""
import argparse
import datetime as dt
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

DATABASE = os.environ.get("HYDRA_DB_DATABASE", "coroner")
client = HydraDB(token=API_KEY)

PROVIDERS = ["slack", "github", "linear", "gmail"]

# Verdict threshold lives here so it can be changed live on stage.
DEAD_AFTER_DAYS = 30


def ago(days, hours=0):
    """ISO-8601 UTC timestamp `days` in the past. Never hardcode a literal date."""
    t = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days, hours=hours)
    return t.strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------
# Cast. Consistent human names across all four surfaces, otherwise the
# cross-tool correlation looks like one person talking to themselves.
# --------------------------------------------------------------------------
CAST = {
    "priya": ("Priya Raman", "priya.raman@northgate.io"),
    "marcus": ("Marcus Webb", "marcus.webb@northgate.io"),
    "dana": ("Dana Cho", "dana.cho@northgate.io"),
    "tomas": ("Tomas Ruiz", "tomas.ruiz@northgate.io"),
    "nick": ("Nick Raddon", "nick@northgate.io"),
}

# (provider, days_ago, hours_ago, author_key, payload)
# payload shape depends on provider:
#   slack  -> (channel, text)
#   github -> (repo, kind, title, body)   kind in {commit, pr_comment, review}
#   linear -> (identifier, title, status, description)   only ONE per project
#   gmail  -> (subject, body, to_key)
CORPUS = {
    "atlas-migration": {
        "display": "Atlas Migration",
        "channel": "#proj-atlas",
        "repo": "northgate/atlas-migration",
        "linear": ("ATL-114", "Migrate auth service off legacy Atlas cluster",
                   "In Progress", 96,
                   "Cut over the auth service from the Atlas cluster to the new "
                   "managed Postgres. Blocked on the token refresh path until the "
                   "dual-write shim lands."),
        "events": [
            ("slack", 94, 2, "marcus", "Kicking off Atlas. First target is the auth service, everything else waits on that cutover."),
            ("slack", 91, 5, "priya", "Dual-write shim spec is up. Rough plan is 3 weeks of dual-write then flip reads."),
            ("gmail", 90, 3, "priya", ("Atlas migration plan for review",
                                       "Attaching the cutover plan. Main risk is the token refresh path, we do not have a clean rollback if reads flip early. Marcus is driving.", "nick")),
            ("github", 88, 1, "marcus", ("commit", "add dual-write shim scaffold", "Adds the shim behind ATLAS_DUAL_WRITE flag, no traffic yet.")),
            ("slack", 86, 4, "dana", "Shim is behind a flag on staging. No traffic on it yet, just want the wiring reviewed."),
            ("github", 84, 6, "priya", ("review", "PR #212 dual-write shim", "Looks right structurally. One concern: the refresh path still reads from Atlas directly, that needs to move before we flip anything.")),
            ("slack", 82, 2, "marcus", "Good catch on the refresh path. Adding it to scope, that is probably another week."),
            ("github", 74, 3, "marcus", ("commit", "wip: route refresh reads through shim", "Partial. Session invalidation still hits Atlas.")),
            ("gmail", 70, 4, "marcus", ("Re: Atlas migration plan for review",
                                        "Slipping the cutover date by two weeks. The refresh path is more tangled than the plan assumed, session invalidation still reaches into Atlas in three places.", "nick")),
            ("slack", 66, 1, "dana", "Is anyone else blocked on Atlas? I have the billing work queued behind the cutover."),
            ("slack", 64, 7, "marcus", "Not blocked yet but I would not queue anything behind it. Refresh path is a mess."),
            ("github", 61, 2, "marcus", ("commit", "wip: session invalidation adapter", "Still failing two integration tests.")),
            ("slack", 58, 3, "priya", "Marcus, do you want to pair on the invalidation adapter this week?"),
            ("gmail", 52, 5, "marcus", ("Handover notes",
                                        "My last day is Friday. Atlas is the big one that needs an owner. The dual-write shim works, the refresh path does not, and the session invalidation adapter has two failing tests that I think are the adapter's fault and not the tests'. Notes are in the PR.", "nick")),
            ("slack", 51, 2, "priya", "Marcus is out Friday. We need someone to pick up Atlas or we should be honest that it is paused."),
            ("github", 47, 4, "priya", ("pr_comment", "PR #218 session invalidation adapter", "Marcus is gone as of Friday. Leaving this open, someone will need to finish the two failing tests. Not me this sprint.")),
            ("slack", 44, 6, "dana", "Who owns Atlas now? Genuinely asking, I have billing work behind it."),
            ("slack", 41, 3, "priya", "No owner yet. I will raise it in planning."),
            ("github", 38, 5, "priya", ("pr_comment", "PR #218 session invalidation adapter", "Still unowned. Marking draft so it stops showing up in the review queue.")),
        ],
    },
    "payments-v2": {
        "display": "Payments V2",
        "channel": "#proj-payments-v2",
        "repo": "northgate/payments-v2",
        "linear": ("PAY-58", "Payments V2 provider abstraction", "In Progress", 70,
                   "Abstract the payment provider behind an interface so we can add "
                   "a second processor. Stripe adapter done, second processor not started."),
        "events": [
            ("slack", 69, 2, "tomas", "Starting Payments V2. Goal is one interface, two processors, no provider names in the call sites."),
            ("github", 67, 1, "tomas", ("commit", "extract PaymentProvider interface", "Pulls the Stripe calls behind an interface. No behavior change.")),
            ("slack", 66, 5, "dana", "Interface looks clean. Do we have a signed contract with the second processor yet?"),
            ("slack", 65, 3, "tomas", "Not yet. Legal has it. I can build against their sandbox in the meantime."),
            ("gmail", 64, 6, "dana", ("Second processor contract status",
                                      "Checking on where the processor agreement sits with legal. Tomas is building against sandbox but we cannot ship without it.", "nick")),
            ("github", 62, 2, "tomas", ("commit", "stripe adapter conforms to interface", "All existing tests green.")),
            ("github", 61, 4, "dana", ("review", "PR #77 stripe adapter", "Approved. Nice, this is a straight refactor with no surprises.")),
            ("slack", 60, 1, "tomas", "Stripe adapter merged. Second adapter is blocked on the contract, so I am picking up the search work in the meantime."),
            ("gmail", 45, 3, "nick", ("Re: Second processor contract status",
                                      "Legal came back with redlines, the processor has not responded. No date.", "dana")),
            # The false life sign: recent, but content-free, and nobody answers.
            ("slack", 23, 4, "dana", "Any update on Payments V2?"),
            ("slack", 11, 2, "dana", "Bumping this. Payments V2 still shows In Progress on the board, is that real?"),
            ("slack", 4, 5, "dana", "Third time asking about Payments V2. Should I just move it to blocked?"),
        ],
    },
    "search-rewrite": {
        "display": "Search Rewrite",
        "channel": "#proj-search",
        "repo": "northgate/search-rewrite",
        "linear": ("SRCH-31", "Replace search backend with hybrid retrieval",
                   "In Progress", 30,
                   "Swap the keyword-only search for hybrid dense plus sparse retrieval. "
                   "Ranking is in, reindex pipeline in review."),
        "events": [
            ("slack", 29, 2, "tomas", "Search rewrite starts today. First milestone is the reindex pipeline, then ranking."),
            ("github", 27, 3, "tomas", ("commit", "reindex pipeline skeleton", "Batch reindex with resumable checkpoints.")),
            ("gmail", 21, 4, "tomas", ("Search rewrite: week 1",
                                       "Reindex pipeline runs end to end on the staging corpus in about 40 minutes. Ranking work starts next.", "nick")),
            ("slack", 18, 1, "priya", "Pulled the reindex branch, checkpoint resume works. Nice."),
            ("github", 14, 5, "tomas", ("commit", "hybrid scorer with tunable alpha", "Dense plus BM25, alpha configurable per index.")),
            ("slack", 12, 3, "dana", "Alpha at 0.6 looks better than 0.5 on the eval set. Worth another pass."),
            ("github", 9, 2, "priya", ("review", "PR #91 hybrid scorer", "Two nits on naming, otherwise ship it. The eval numbers speak for themselves.")),
            ("gmail", 4, 6, "tomas", ("Search rewrite: ranking eval results",
                                      "Hybrid beats keyword-only on every slice we measured. Recommending we cut over next sprint.", "nick")),
            ("github", 2, 1, "tomas", ("commit", "address review nits on scorer", "Renames only.")),
            ("slack", 1, 4, "tomas", "Scorer merged. Cutover plan going up tomorrow."),
        ],
    },
    "onboarding-redesign": {
        "display": "Onboarding Redesign",
        "channel": "#proj-onboarding",
        "repo": "northgate/onboarding-redesign",
        "linear": ("ONB-7", "Rebuild first-run onboarding flow", "In Progress", 6,
                   "New three-step onboarding replacing the current six-screen flow."),
        "events": [
            ("slack", 6, 2, "priya", "Onboarding redesign kickoff. Three steps instead of six, that is the whole brief."),
            ("gmail", 5, 3, "priya", ("Onboarding redesign brief",
                                      "Scope is the first-run flow only. Six screens to three. Nothing about billing or invites changes.", "nick")),
            ("github", 4, 1, "dana", ("commit", "scaffold new onboarding routes", "Three routes, no content yet.")),
            ("slack", 2, 5, "dana", "Routes are up on preview. Copy is placeholder, do not read anything into it."),
            ("github", 1, 2, "priya", ("review", "PR #4 onboarding routes", "Structure is right. Let us get real copy in before we test with anyone.")),
            ("slack", 0, 6, "priya", "Copy draft going in this afternoon."),
        ],
    },
}


def build_items():
    """Flatten CORPUS into HydraDB app_knowledge items, one list per provider."""
    by_provider = {p: [] for p in PROVIDERS}

    for slug, proj in CORPUS.items():
        display = proj["display"]
        channel = proj["channel"]
        repo = proj["repo"]

        def base(provider, seq, days, hours, author_key, title, url):
            name, email = CAST[author_key]
            ts = ago(days, hours)
            return {
                # NOTE: no commas in id — /context/status?ids= splits on comma.
                "id": f"{provider}_{slug}_{seq:03d}",
                "database": DATABASE,
                "collection": provider,          # provider == collection: the hard scope
                "title": title,
                "type": provider,
                "provider": provider,
                "url": url,
                "timestamp": ts,                 # <-- the whole ballgame
                "metadata": {                    # declared in schema, hard pre-filterable
                    "provider": provider,
                    "project": slug,
                    "author": author_key,
                },
                "additional_metadata": {         # mirrored, needs no schema declaration
                    "provider": provider,
                    "project": slug,
                    "project_name": display,
                    "author_name": name,
                    "author_email": email,
                    "timestamp": ts,
                },
            }, ts, name, email

        # ---- Linear: exactly one ticket per project, the CLAIM ----
        ident, title, status, created_days, description = proj["linear"]
        item, ts, name, email = base(
            "linear", 1, created_days, 0, "priya", f"{ident} {title}",
            f"https://linear.app/northgate/issue/{ident}",
        )
        item["kind"] = "ticket"
        item["external_id"] = ident
        item["fields"] = {
            "kind": "ticket",
            "title": f"{ident}: {title}",
            "description": description,
            "status": status,
            "priority": "High",
            "assignee": name,
            "reporter": name,
            "created_at": ts,
            "updated_at": ts,
            "url": f"https://linear.app/northgate/issue/{ident}",
        }
        by_provider["linear"].append(item)

        counters = {p: 1 for p in PROVIDERS}
        for provider, days, hours, author_key, payload in proj["events"]:
            counters[provider] += 1
            seq = counters[provider]

            if provider == "slack":
                text = payload
                item, ts, name, email = base(
                    "slack", seq, days, hours, author_key,
                    f"{channel} — {text[:60]}",
                    f"https://northgate.slack.com/archives/{slug}/p{seq:06d}",
                )
                item["kind"] = "message"
                item["external_id"] = f"{slug}.{seq:06d}"
                item["fields"] = {
                    "kind": "message", "body": text, "author": name,
                    "thread_id": f"{slug}.thread", "created_at": ts,
                    "url": item["url"],
                }
                item["additional_metadata"]["channel"] = channel
                by_provider["slack"].append(item)

            elif provider == "github":
                gkind, gtitle, gbody = payload
                item, ts, name, email = base(
                    "github", seq, days, hours, author_key,
                    f"{repo} — {gtitle}",
                    f"https://github.com/{repo}",
                )
                item["kind"] = "comment"
                item["external_id"] = f"{slug}-gh-{seq:03d}"
                item["fields"] = {
                    "kind": "comment",
                    "body": f"[{gkind}] {gtitle}\n\n{gbody}",
                    "author": name, "created_at": ts, "updated_at": ts,
                }
                item["additional_metadata"]["repo"] = repo
                item["additional_metadata"]["github_kind"] = gkind
                by_provider["github"].append(item)

            elif provider == "gmail":
                subject, body, to_key = payload
                to_name, to_email = CAST[to_key]
                item, ts, name, email = base(
                    "gmail", seq, days, hours, author_key, subject,
                    f"https://mail.google.com/mail/u/0/#inbox/{slug}-{seq:03d}",
                )
                item["kind"] = "email"
                item["external_id"] = f"{slug}-mail-{seq:03d}"
                item["fields"] = {
                    "kind": "email", "subject": subject, "body": body,
                    "from": f"{name} <{email}>", "to": [f"{to_name} <{to_email}>"],
                    "thread_id": f"{slug}-mail-thread", "created_at": ts,
                    "url": item["url"],
                }
                by_provider["gmail"].append(item)

    return by_provider


# --------------------------------------------------------------------------
def create_database():
    """Metadata schema is IMMUTABLE after creation. This must run first, once."""
    schema = [
        {"name": "provider", "data_type": "VARCHAR", "enable_match": True},
        {"name": "project", "data_type": "VARCHAR", "enable_match": True},
        {"name": "author", "data_type": "VARCHAR", "enable_match": True},
    ]
    try:
        client.databases.create(database=DATABASE, database_metadata_schema=schema)
        print(f"created database {DATABASE} with metadata schema")
    except Exception as e:
        print(f"create returned: {e}")
        print("If this database already existed WITHOUT the schema, use a new name "
              "(HYDRA_DB_DATABASE in .env). The schema cannot be added later.")
    for _ in range(60):
        if client.databases.status(database=DATABASE).data.infra.ready_for_ingestion:
            print("database ready for ingestion")
            return
        time.sleep(5)
    sys.exit("FAIL: database never became ready")


def ingest(items, collection):
    res = client.context.ingest(
        type="knowledge", database=DATABASE, collection=collection,
        upsert=True, app_knowledge=json.dumps(items),
    )
    return [r.id for r in res.data.results]


def wait(ids, label=""):
    """202 Accepted means QUEUED, not indexed. Never query before this returns."""
    pending = list(ids)
    for _ in range(120):
        statuses = client.context.status(database=DATABASE, ids=pending).data.statuses
        errored = [s for s in statuses if s.indexing_status == "errored"]
        if errored:
            sys.exit(f"FAIL {label}: {errored[0].error_message}")
        pending = [s.id for s in statuses if s.indexing_status != "completed"]
        if not pending:
            print(f"  indexed {len(ids)} {label}")
            return
        time.sleep(2)
    sys.exit(f"FAIL {label}: {len(pending)} never finished indexing")


def smoke():
    """Ingest ONE record dated 40 days back and prove the timestamp round-trips.
    This is the highest-value three minutes in the whole plan. Do not skip it."""
    ts = ago(40)
    item = {
        "id": "smoke_backdate_001", "database": DATABASE, "collection": "slack",
        "title": "backdate probe", "type": "slack", "kind": "message",
        "provider": "slack", "external_id": "smoke.000001", "timestamp": ts,
        "url": "https://example.invalid/smoke",
        "fields": {"kind": "message", "body": "Coroner backdate probe. This message "
                                              "is forty days old.", "author": "Probe",
                   "created_at": ts},
        "metadata": {"provider": "slack", "project": "smoke", "author": "probe"},
        "additional_metadata": {"provider": "slack", "project": "smoke",
                                "timestamp": ts},
    }
    print(f"ingesting probe with timestamp {ts}")
    ids = ingest([item], "slack")
    wait(ids, "probe")
    r = client.query(database=DATABASE, type="knowledge", query="backdate probe",
                     collections=["slack"], query_apps=True, recency_bias=0)
    print(json.dumps(json.loads(r.model_dump_json())["data"], indent=2)[:2000])
    print(f"\nEXPECT to see {ts} above, NOT today. If you see today's date, the "
          f"timestamp is not round-tripping and everything downstream is wrong.")


def seed():
    by_provider = build_items()
    total = 0
    for provider in PROVIDERS:
        items = by_provider[provider]
        print(f"ingesting {len(items)} {provider} records")
        ids = ingest(items, provider)
        wait(ids, provider)
        total += len(items)
    print(f"\nseeded {total} records across {len(PROVIDERS)} providers into {DATABASE}")


def last_activity(project):
    """Deterministic verdict input. Do NOT let an LLM eyeball dates.
    There are no range operators server-side, so pull timestamps and max() here."""
    res = client.context.list(
        database=DATABASE, type="knowledge",
        filters={"metadata": {"project": project}},
        include_fields=["id", "title", "type", "timestamp"], page_size=200,
    )
    rows = json.loads(res.model_dump_json())["data"]
    docs = rows.get("documents") or rows.get("items") or rows.get("results") or []
    out = {}
    for d in docs:
        ts, typ = d.get("timestamp"), d.get("type")
        if ts and typ:
            out[typ] = max(out.get(typ, ""), ts)
    return out


def verify():
    now = dt.datetime.now(dt.timezone.utc)
    print(f"threshold: DEAD_AFTER_DAYS = {DEAD_AFTER_DAYS}\n")
    for slug, proj in CORPUS.items():
        per = last_activity(slug)
        human = {k: v for k, v in per.items() if k != "linear"}
        if not human:
            print(f"{proj['display']:<22} no evidence returned — check the metadata "
                  f"schema was declared at database creation")
            continue
        days = {k: (now - dt.datetime.strptime(v, "%Y-%m-%dT%H:%M:%SZ")
                    .replace(tzinfo=dt.timezone.utc)).days
                for k, v in human.items()}
        chatter = min(days.values())
        # WORK is code and mail. Talk is not work: a project where the only recent
        # signal is someone asking "any update?" in Slack is the zombie case.
        work = min([d for k, d in days.items() if k in ("github", "gmail")]
                   or [chatter])
        if work > DEAD_AFTER_DAYS and chatter > DEAD_AFTER_DAYS:
            verdict = "DECEASED"
        elif work > DEAD_AFTER_DAYS:
            verdict = "ZOMBIE (talk without work)"
        else:
            verdict = "ALIVE"
        print(f"{proj['display']:<22} linear=In Progress  last signal {chatter:>3}d  "
              f"last real work {work:>3}d  ->  {verdict}")
        for k in sorted(days):
            print(f"    {k:<8} {days[k]:>3}d")

    print("\n--- kill shot ---")
    q = "What is the current state of the Atlas migration?"
    for scope in (["slack", "github", "linear", "gmail"], ["linear"]):
        r = client.query(database=DATABASE, type="knowledge", query=q,
                         collections=scope, query_apps=True, mode="thinking",
                         recency_bias=0, max_results=10)
        chunks = json.loads(r.model_dump_json())["data"].get("chunks", [])
        print(f"scope={scope} -> {len(chunks)} evidence items")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--create", action="store_true")
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    if a.create:
        create_database()
    elif a.smoke:
        smoke()
    elif a.verify:
        verify()
    else:
        seed()
