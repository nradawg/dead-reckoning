# Dead Reckoning

**Find the projects your company thinks are alive but are actually dead.**

Your tracker says "In Progress." Nobody has touched it in six weeks. Updating
that status is nobody's job, so the roadmap quietly becomes fiction.

Dead Reckoning reads what your team actually *did* across Slack, GitHub, Linear
and Gmail, and issues a death certificate when the work stopped.

```
DECEASED   Atlas Migration      github 74d, slack 44d, gmail 52d
ZOMBIE     Payments V2          github 61d, slack 4d     <- talking, not working
ALIVE      Search Rewrite       github 2d,  slack 1d
```

---

## Quickstart

```bash
git clone https://github.com/nradawg/dead-reckoning
cd dead-reckoning
./setup.sh
```

Then fill in `.env` (about 10 minutes of signups, all have free tiers):

| Service | What you need | Where |
|---|---|---|
| **HydraDB** | API key, a database, and at least one connector | [app.hydradb.com](https://app.hydradb.com) |
| **Pipeshift** | API key and one "Serverless API" model | [dashboard.pipeshift.com](https://dashboard.pipeshift.com) |
| **InsForge** | Base URL and keys | [insforge.dev](https://insforge.dev) |
| RocketRide *(optional)* | Token, only for the hosted pipeline | [cloud.rocketride.ai](https://cloud.rocketride.ai) |

Verify everything works before you build on it:

```bash
./.venv/bin/python check.py
```

It tells you exactly which service is misconfigured and why. Then:

```bash
./.venv/bin/python agents/discover.py
```

**Using Claude Code or Codex?** Just say *"set this up"* — `CLAUDE.md` tells your
agent the whole procedure including the four non obvious gotchas that would
otherwise cost it an hour.

---

## Connecting your own tools

In the HydraDB dashboard, go to **Connectors** and add whatever you use. Slack,
GitHub, Linear, Gmail, Notion, Asana and about 50 others.

**Connect at least two, and make them different kinds.** The entire idea is
comparing a *claim* in one tool against *behavior* in another. One tool can only
ever tell you what it already believes.

The strongest pair is an issue tracker plus a code host: the tracker holds the
optimism, the repo holds the truth.

No connectors yet and just want to see it work?

```bash
./.venv/bin/python seed/seed_corpus.py    # generates a fake company
```

---

## How it works

1. **Discover** — the model reads a sample of your data and names your ongoing projects. Nothing is hardcoded.
2. **Vitals** — last real human signal per source, per project.
3. **Verdict** — pure timestamp arithmetic. A model never decides whether something is dead, which is why this cannot hallucinate a verdict.
4. **Diagnose** — Pipeshift writes the cause of death and whether to revive, replace, or bury it.

### Four verdicts

| | |
|---|---|
| **ALIVE** | Recent work confirmed |
| **DECEASED** | No signal and no work past the threshold |
| **ZOMBIE** | People still talking, nobody working. The interesting one. |
| **In Progress** | What you get when you only ask one tool |

That last row is the point. Scope the same question to your tracker alone and
the answer does not get vaguer, it gets **confidently wrong**.

---

## Two ways to use it

**As an agent tool (recommended).** Register the MCP server and just ask, in
whatever agent you already use:

```bash
claude mcp add dead-reckoning -- $(pwd)/.venv/bin/python $(pwd)/mcp_server.py
```

> "Which of my projects are dead?"

Tools: `list_projects`, `check_project`, `triage_all`, and `past_certificates`,
which reads stored verdicts so the agent can tell you a project was alive in
June and is dead now.

**As a dashboard.**

```bash
./.venv/bin/python app.py     # localhost:5001
```

---

## Tuning

`DEAD_AFTER_DAYS` in `.env` sets the threshold. 30 is a reasonable default. A
team shipping daily might use 14; one on quarterly cycles, 60.

---

## Notes

Built at Agents You Love 2, Frontier Tower, San Francisco, July 2026.

The verdict is deliberately deterministic. Models are used to name projects and
explain causes, never to decide liveness, because a hallucinated verdict about
whether your project is dead is worse than no verdict at all.
