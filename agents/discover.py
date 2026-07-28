"""Project discovery: let the model figure out what you're working on.

The hardcoded CORPUS was scaffolding for the demo. On real connector data
there is no tidy project list, so the agent reads a sample of what actually
synced and names the ongoing efforts itself. Everything downstream (vitals,
verdict, diagnosis) is unchanged.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents import coroner  # noqa: E402
from agents.hydra_rest import client  # noqa: E402

DATABASE = coroner.DATABASE

DISCOVER_PROMPT = """Below is a sample of one person's work data, pulled from \
their email, code repos, chat, and issue tracker.

Identify the ongoing PROJECTS or EFFORTS this person is building. A project is \
something with work happening over time: a product, a client build, a business, \
a side project. Ignore newsletters, promotions, receipts, notifications, and \
one-off conversations.

Return ONLY a JSON array, max 8 items, each like:
{{"name": "human readable name", "keywords": ["distinctive", "identifiers"]}}

CRITICAL: keywords must be DISTINCTIVE to that one project. Good keywords are \
the project name, ticket prefixes (like ATL-114), repo names, product names, \
client names, domains unique to that project, and technical terms used only \
there.

NEVER include: people's names, the company's own email domain, or generic words \
like status, update, launch, build, project. Those appear everywhere and would \
match every project at once.

DATA:
{sample}"""


def sample_content(limit=60):
    """Grab a broad slice of whatever is in the database."""
    seen, out = set(), []
    for probe in ("project update status building launch",
                  "client website business build",
                  "shipped deployed released working on"):
        r = client.query(
            database=DATABASE, type="knowledge", query=probe,
            collections=coroner.ALL_SOURCES, query_apps=True,
            recency_bias=0, max_results=limit,
        )
        for c in r._payload["data"].get("chunks", []):
            key = c.get("id")
            if key in seen:
                continue
            seen.add(key)
            am = c.get("additional_metadata") or {}
            out.append({
                "provider": am.get("provider") or c.get("type"),
                "when": am.get("timestamp"),
                "text": (c.get("chunk_content") or "")[:280],
            })
    return out


def discover(verbose=True):
    """Ask the model what this person is actually building."""
    sample = sample_content()
    if not sample:
        return []
    lines = [f"[{s['provider']}] {s['when']}: {s['text']}" for s in sample[:70]]
    raw = coroner.chat(DISCOVER_PROMPT.format(sample="\n".join(lines)),
                       max_tokens=3000, temperature=0.3)
    start, end = raw.find("["), raw.rfind("]")
    if start == -1:
        if verbose:
            print("model returned no JSON:", raw[:300])
        return []
    try:
        projects = json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        if verbose:
            print("unparseable:", raw[:300])
        return []
    if verbose:
        print(f"discovered {len(projects)} projects from {len(sample)} records")
        for p in projects:
            print(f"  {p.get('name')}  <- {', '.join(p.get('keywords', [])[:4])}")
    return projects


# Terms that show up across every project and would make the filter useless.
# Recomputed per corpus by calling learn_generic(), which catches things the
# model shouldn't have offered (a shared email domain, a teammate's name).
_GENERIC = set()


def learn_generic(threshold=0.35):
    """Any term appearing in more than `threshold` of sampled records is not a
    project identifier, it's background noise. Drop it."""
    global _GENERIC
    sample = sample_content()
    if not sample:
        return _GENERIC
    blobs = [s["text"].lower() for s in sample]
    counts = {}
    for p in discover(verbose=False):
        for kw in [p["name"]] + (p.get("keywords") or []):
            k = kw.lower()
            if k in counts:
                continue
            hits = sum(1 for b in blobs if k in b)
            counts[k] = hits / max(1, len(blobs))
    _GENERIC = {k for k, frac in counts.items() if frac > threshold}
    return _GENERIC


def vitals_for(project, sources=None):
    """Vitals for a discovered project, matched by keyword instead of slug."""
    import datetime as dt
    terms = " ".join(project.get("keywords") or [project["name"]])
    r = client.query(
        database=DATABASE, type="knowledge", query=terms,
        collections=list(sources or coroner.ALL_SOURCES),
        query_apps=True, recency_bias=0, max_results=60,
    )
    now = dt.datetime.now(dt.timezone.utc)

    # Semantic search returns the best matches across the WHOLE database, so a
    # chunk about another project will still come back. Without this filter
    # every project inherits the newest activity in the corpus and they all
    # read ALIVE. Only count a chunk that actually names this project.
    needles = [t.lower() for t in
               ([project["name"]] + (project.get("keywords") or []))
               if len(t) > 3 and t.lower() not in _GENERIC]

    per = {}
    for c in r._payload["data"].get("chunks", []):
        am = c.get("additional_metadata") or {}
        ts = am.get("timestamp")
        prov = am.get("provider") or c.get("type")
        if not (ts and prov):
            continue
        blob = ((c.get("chunk_content") or "") + " " +
                (c.get("source_title") or "")).lower()
        if not any(n in blob for n in needles):
            continue
        per[prov] = max(per.get(prov, ""), ts)
    days = {}
    for k, v in per.items():
        try:
            days[k] = coroner._days_since(v, now)
        except Exception:
            pass
    return days, per


def triage(sources=None):
    """Discover projects, then verdict each one. This is the real entry point."""
    results = []
    learn_generic()
    for p in discover(verbose=False):
        days, _ = vitals_for(p, sources)
        if not days:
            continue
        v = coroner.verdict(days)
        results.append({"project": p["name"], "verdict": v["verdict"],
                        "finding": v["reason"], "days_by_source": days})
    rank = {"DECEASED": 0, "ZOMBIE": 1, "ALIVE": 2}
    results.sort(key=lambda r: rank.get(r["verdict"], 3))
    return results


if __name__ == "__main__":
    print(f"reading database: {DATABASE}\n")
    for r in triage():
        print(f"{r['verdict']:<10} {r['project']:<38} {r['days_by_source']}")
