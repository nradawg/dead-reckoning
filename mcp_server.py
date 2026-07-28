"""Dead Reckoning as an MCP server.

The dashboard is the proof. This is the product: any agent (Claude, Codex,
whatever you run) connects and can ask about the health of your work across
every tool you've synced into HydraDB.

Run:
    python mcp_server.py

Register with Claude Code:
    claude mcp add dead-reckoning -- /path/to/.venv/bin/python /path/to/mcp_server.py
"""
import json
import sys

from mcp.server.fastmcp import FastMCP

from agents import coroner, morgue

mcp = FastMCP("dead-reckoning")


@mcp.tool()
def list_projects() -> str:
    """List every project Dead Reckoning knows about, with its slug."""
    return json.dumps([
        {"slug": s, "name": m["display"]} for s, m in coroner.CORPUS.items()
    ])


@mcp.tool()
def check_project(project: str, sources: str = "") -> str:
    """Is this project actually alive?

    Cross-references what the tracker CLAIMS against what the team actually
    did across every synced connector, and returns a verdict with evidence.

    project: the project slug (see list_projects)
    sources: optional comma-separated connectors to limit the check to
             (e.g. "linear"). Leave empty to use every source, which is
             the only way to get a trustworthy answer.
    """
    scope = [s.strip() for s in sources.split(",") if s.strip()] or None
    cert = coroner.autopsy(project, scope)
    return json.dumps({
        "project": cert["project"],
        "verdict": cert["verdict"],
        "confidence": cert["confidence"],
        "finding": cert["reason"],
        "days_since_activity_by_source": cert["days_by_source"],
        "time_of_death": cert.get("time_of_death"),
        "cause": cert.get("cause"),
        "survived_by": cert.get("survived_by"),
        "recommendation": cert.get("recommendation"),
        "alternative": cert.get("alternative"),
        "evidence_count": cert["evidence_count"],
        "evidence": cert["evidence"][:6],
        "caveat": ("Scoped to a single source: this verdict is based only on "
                   "what that tool claims and may be confidently wrong."
                   if scope else None),
    }, default=str)


@mcp.tool()
def triage_all() -> str:
    """Check every project at once. Use this for a standup or a Monday review.

    Returns the dead and zombie projects first, since those are the ones
    costing money nobody has noticed.
    """
    out = []
    for slug, meta in coroner.CORPUS.items():
        days, _ = coroner.vitals(slug)
        v = coroner.verdict(days)
        out.append({
            "project": meta["display"], "slug": slug,
            "verdict": v["verdict"], "finding": v["reason"],
            "days_by_source": days,
        })
    rank = {"DECEASED": 0, "ZOMBIE": 1, "ALIVE": 2}
    out.sort(key=lambda r: rank.get(r["verdict"], 3))
    return json.dumps(out)


@mcp.tool()
def past_certificates(project: str = "") -> str:
    """Read previously issued certificates from InsForge.

    This is the memory: what did we conclude about this project last time,
    and has the verdict changed since?
    """
    try:
        rows = morgue.recent(project) if hasattr(morgue, "recent") else []
        return json.dumps(rows, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)[:200]})


if __name__ == "__main__":
    print("dead-reckoning MCP server starting", file=sys.stderr)
    mcp.run()
