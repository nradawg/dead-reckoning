"""The Coroner — dashboard.

Serves the UI and two endpoints. Every autopsy is written to InsForge and the
UI reads certificates back from there, so the on-stage scope toggle is a
database read, not a live inference gamble.
"""
import os
import sys

from flask import Flask, jsonify, render_template, request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import coroner, morgue  # noqa: E402
from agents.coroner import CORPUS  # noqa: E402

app = Flask(__name__)


@app.route("/")
def index():
    projects = [{"slug": s, "display": p["display"]} for s, p in CORPUS.items()]
    return render_template("index.html", projects=projects,
                           threshold=coroner.DEAD_AFTER_DAYS)


@app.route("/api/autopsy")
def autopsy():
    slug = request.args.get("project")
    scope = request.args.get("scope", "all")
    sources = None if scope == "all" else scope.split(",")

    cert = coroner.autopsy(slug, sources)

    try:
        morgue.save({
            "project": cert["project"], "scope": cert["scope"],
            "verdict": cert["verdict"], "confidence": cert["confidence"],
            "time_of_death": cert.get("time_of_death"), "cause": cert.get("cause"),
            "survived_by": cert.get("survived_by"),
            "recommendation": cert.get("recommendation"),
            "alternative": cert.get("alternative"),
            "evidence": cert["evidence"], "evidence_count": cert["evidence_count"],
        })
        cert["stored"] = True
    except Exception as e:
        cert["stored"] = False
        cert["store_error"] = str(e)[:200]

    return jsonify(cert)


@app.route("/api/ask", methods=["POST"])
def ask():
    """Follow-up questions, grounded in the stored evidence."""
    body = request.get_json(force=True)
    question = body.get("question", "")
    ev = body.get("evidence", [])
    project = body.get("project", "")

    lines = [f"[{e.get('provider')}] {e.get('timestamp')}: {e.get('text')}"
             for e in ev[:12]]
    prompt = (
        f"You are the medical examiner who just autopsied '{project}' at Northgate.\n"
        f"Evidence you gathered:\n" + "\n".join(lines) +
        f"\n\nAnswer this question in 2 sentences, grounded only in that evidence. "
        f"If the evidence does not support an answer, say so plainly.\n\n"
        f"Question: {question}"
    )
    resp = coroner._ps.chat.completions.create(
        model=coroner.MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1200, temperature=0.5,
    )
    return jsonify({"answer": (resp.choices[0].message.content or "").strip()})


if __name__ == "__main__":
    app.run(port=5001, debug=False)
