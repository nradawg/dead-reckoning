"""The Coroner: verdict engine.

Split deliberately:
  - Vitals and verdict are DETERMINISTIC (timestamp arithmetic). An LLM never
    decides whether something is dead. That's why the demo can't hallucinate.
  - Pipeshift writes the cause, the recommendation, and the alternative — the
    parts that are genuinely judgment, grounded in evidence we already pulled.
"""
import datetime as dt
import json
import os
import sys
import time

import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from agents.hydra_rest import client  # noqa: E402

DATABASE = os.environ.get("HYDRA_DB_DATABASE", "hackathon")

# Slug -> display name. Slugs match additional_metadata.project in the corpus.
CORPUS = {
    "atlas-migration": {"display": "Atlas Migration"},
    "payments-v2": {"display": "Payments V2"},
    "search-rewrite": {"display": "Search Rewrite"},
    "onboarding-redesign": {"display": "Onboarding Redesign"},
}

DEAD_AFTER_DAYS = int(os.environ.get("DEAD_AFTER_DAYS", "30"))
WORK_SOURCES = ("github", "gmail")
ALL_SOURCES = ["slack", "github", "linear", "gmail"]

# The OpenAI SDK constructor takes minutes in this environment (same pathology
# as the HydraDB SDK). Pipeshift is OpenAI-compatible REST, so just call it.
PIPESHIFT_URL = "https://api.pipeshift.com/api/v0/chat/completions"
MODEL = os.environ.get("PIPESHIFT_MODEL", "deepseek-ai/DeepSeek-V4-Flash")


def chat(prompt, max_tokens=1500, temperature=0.4):
    """One Pipeshift completion. Retries: 80 people share this endpoint today."""
    body = {"model": MODEL, "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens, "temperature": temperature}
    h = {"Authorization": f"Bearer {os.environ['PIPESHIFT_API_KEY']}",
         "Content-Type": "application/json"}
    last = None
    for attempt in range(3):
        try:
            r = requests.post(PIPESHIFT_URL, headers=h, json=body, timeout=120)
            if r.status_code < 400:
                return (r.json()["choices"][0]["message"].get("content") or "").strip()
            last = f"{r.status_code} {r.text[:200]}"
        except Exception as e:
            last = str(e)[:200]
        time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"pipeshift failed: {last}")


def _days_since(ts, now):
    return (now - dt.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
            .replace(tzinfo=dt.timezone.utc)).days


def _chunks(project, sources, limit=60):
    """Raw evidence chunks for a project, scoped to `sources` via collections.

    Scoping MUST be `collections` — it's a real vector-store pre-filter.
    metadata_filters compares arrays by set-equality and fails silently, which
    would return everything and make the kill shot a lie.
    """
    r = client.query(
        database=DATABASE, type="knowledge",
        query=f"{project} status update progress work review",
        collections=list(sources or ALL_SOURCES),
        query_apps=True, recency_bias=0, max_results=limit,
    )
    out = []
    for c in r._payload["data"].get("chunks", []):
        am = c.get("additional_metadata") or {}
        if am.get("project") != project:
            continue
        out.append(c)
    return out


def vitals(project, sources=None):
    """Last activity per source, in days.

    Timestamps come from additional_metadata.timestamp, NOT source_upload_time:
    HydraDB stamps upload time as today, so using it would make every project
    look alive regardless of the real history.
    """
    now = dt.datetime.now(dt.timezone.utc)
    per = {}
    for c in _chunks(project, sources):
        am = c.get("additional_metadata") or {}
        ts = am.get("timestamp")
        prov = am.get("provider")
        if ts and prov:
            per[prov] = max(per.get(prov, ""), ts)
    return {k: _days_since(v, now) for k, v in per.items()}, per


def verdict(days_by_source):
    """DECEASED / ZOMBIE / ALIVE / UNKNOWN. Pure arithmetic, no model."""
    human = {k: v for k, v in days_by_source.items() if k != "linear"}
    if not human:
        # Only Linear in scope: the status field is the sole witness, and it
        # says In Progress. This is the kill shot — confidently wrong.
        return {
            "verdict": "In Progress",
            "confidence": 0.71,
            "reason": "No contradicting evidence available in this scope.",
            "talk_days": None, "work_days": None, "degraded": True,
        }

    talk = min(human.values())
    work = min([d for k, d in human.items() if k in WORK_SOURCES] or [talk])

    if work > DEAD_AFTER_DAYS and talk > DEAD_AFTER_DAYS:
        v, conf = "DECEASED", 0.93
        reason = f"No human signal in {talk} days; no work in {work} days."
    elif work > DEAD_AFTER_DAYS:
        v, conf = "ZOMBIE", 0.88
        reason = (f"People are still talking ({talk}d ago) but no actual work "
                  f"has happened in {work} days.")
    else:
        v, conf = "ALIVE", 0.90
        reason = f"Active work {work} days ago."

    return {"verdict": v, "confidence": conf, "reason": reason,
            "talk_days": talk, "work_days": work, "degraded": False}


def evidence(project, sources=None, limit=12):
    """Retrieve the supporting quotes, scoped. This is the HydraDB kill shot."""
    r = client.query(
        database=DATABASE, type="knowledge",
        query=f"What is the current state of {project}? Who last worked on it?",
        collections=list(sources or ALL_SOURCES),
        query_apps=True, recency_bias=0, max_results=limit,
    )
    chunks = json.loads(r.model_dump_json())["data"].get("chunks", [])
    out = []
    for c in chunks:
        meta = (c.get("metadata") or {})
        extra = (c.get("additional_metadata") or meta.get("additional_metadata") or {})
        out.append({
            "text": (c.get("text") or c.get("content") or "")[:400],
            "provider": extra.get("provider") or meta.get("provider") or c.get("type"),
            "timestamp": extra.get("timestamp") or c.get("timestamp"),
            "author": extra.get("author_name"),
            "url": c.get("url"),
        })
    return out


DIAGNOSE_PROMPT = """You are a medical examiner for software projects at Northgate, \
a B2B company. You are given evidence gathered from the company's tools.

Project: {project}
Deterministic finding: {verdict} — {reason}
Evidence:
{evidence}

Return ONLY a JSON object, no prose, with exactly these keys:
  "cause": short clinical cause of death, max 12 words (e.g. "review starvation", \
"silent deprioritization after owner reassignment")
  "survived_by": who or what is still waiting on this, max 20 words. Name real \
people/customers from the evidence if present. If nothing, use "No known survivors."
  "recommendation": exactly one of REVIVE, REPLACE, or BURY
  "reasoning": one sentence justifying the recommendation, citing the evidence
  "alternative": only if recommendation is REPLACE, name what already solves this \
(internal or off-the-shelf). Otherwise empty string.
  "eulogy": one dry, humane sentence marking its passing. Not jokey. No em dashes."""


def diagnose(project_display, v, ev):
    """Pipeshift writes cause, recommendation, alternative."""
    lines = [
        f"[{e['provider']}] {e['timestamp']} {e.get('author') or ''}: {e['text']}"
        for e in ev[:12]
    ]
    prompt = DIAGNOSE_PROMPT.format(
        project=project_display, verdict=v["verdict"], reason=v["reason"],
        evidence="\n".join(lines) or "(no evidence in this scope)",
    )
    # Reasoning model: it spends tokens thinking before it writes. Starve it and
    # content comes back empty with a 200. Give it real headroom.
    raw = chat(prompt, max_tokens=1500, temperature=0.4)
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        return {"cause": "undetermined", "survived_by": "unknown",
                "recommendation": "BURY", "reasoning": "Model returned no JSON.",
                "alternative": "", "eulogy": "", "_raw": raw[:300]}
    try:
        return json.loads(raw[start:end + 1])
    except json.JSONDecodeError:
        return {"cause": "undetermined", "survived_by": "unknown",
                "recommendation": "BURY", "reasoning": "Unparseable model output.",
                "alternative": "", "eulogy": "", "_raw": raw[:300]}


def autopsy(slug, sources=None):
    """Full run for one project at one scope. Returns a certificate dict."""
    display = CORPUS[slug]["display"] if slug in CORPUS else slug
    days, stamps = vitals(slug, sources)
    v = verdict(days)
    ev = evidence(slug, sources)

    cert = {
        "project": display, "slug": slug,
        "scope": "all" if not sources else ",".join(sources),
        "verdict": v["verdict"], "confidence": v["confidence"],
        "reason": v["reason"], "degraded": v["degraded"],
        "days_by_source": days, "last_seen": stamps,
        "evidence": ev, "evidence_count": len(ev),
        "time_of_death": None, "cause": None, "survived_by": None,
        "recommendation": None, "alternative": None, "eulogy": None,
    }

    if v["verdict"] in ("DECEASED", "ZOMBIE"):
        work = [s for s in stamps if s in WORK_SOURCES]
        if work:
            cert["time_of_death"] = max(stamps[s] for s in work)
        d = diagnose(display, v, ev)
        cert.update({
            "cause": d.get("cause"), "survived_by": d.get("survived_by"),
            "recommendation": d.get("recommendation"),
            "reasoning": d.get("reasoning"), "alternative": d.get("alternative"),
            "eulogy": d.get("eulogy"),
        })
    return cert


if __name__ == "__main__":
    slug = sys.argv[1] if len(sys.argv) > 1 else list(CORPUS)[0]
    for scope in (None, ["linear"]):
        c = autopsy(slug, scope)
        print(f"\n=== scope={c['scope']} ===")
        print(f"{c['project']}: {c['verdict']} ({c['confidence']}) "
              f"[{c['evidence_count']} evidence]")
        print(f"  {c['reason']}")
        if c.get("cause"):
            print(f"  cause: {c['cause']}")
            print(f"  survived by: {c['survived_by']}")
            print(f"  -> {c['recommendation']}: {c.get('reasoning')}")
            if c.get("alternative"):
                print(f"  alternative: {c['alternative']}")
