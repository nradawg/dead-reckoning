# The Coroner

**An agent that pronounces your zombie projects dead, and tells you what to do about it.**

Built at Agents You Love 2 — Frontier Tower, San Francisco, July 28 2026.

## The question

> "Project X says In Progress. Is it actually alive?"

A status field is only as true as the last person who bothered to update it, and
updating it is nobody's job. Linear holds the company's **claim**. Slack, GitHub,
and Gmail hold its **behavior**. The gap between the two is where dead projects
hide, and no single tool can see that gap.

## What it returns

**1. The certificate.** The diagnosis: time of death, cause of death, survived by,
every field carrying a citation from the connector it came from.

**2. The verdict.** Revive, replace, or bury — with reasoning tied to the evidence.
*"Revive: this was two review comments from done and the only blocker left the team."*

**3. The alternative.** Fires only on a `replace` verdict. What already exists that
solves what the dead project was solving, internally or off the shelf.

Then you can ask it follow-up questions. Every certificate and its evidence live in
InsForge, so "why review starvation?" or "who should own reviving this?" is a
grounded call against stored evidence, not a fresh guess.

## The kill shot

Same agent, same question, scoped to Linear only.

Linear's sole evidence is `status: In Progress`. Nothing contradicts it, because
the contradiction lives in the other three systems. So the answer does not get
vaguer — it gets **confidently wrong**. The death certificate is replaced by a
smiling green In Progress badge.

| | All sources | Linear only |
|---|---|---|
| Verdict | DECEASED | In Progress |
| Evidence items | many, across 4 connectors | 1 |
| Time of death | exact | unknown |
| Cause | diagnosed | undetermined |

Both runs are computed by the deployed pipeline and written to InsForge, so the
on-stage toggle is a database read. Nothing is inferred live during the flip.

## Who it's for

Engineering leaders and founders carrying projects nobody has admitted are dead:
headcount on abandoned work, customers waiting on features that will never ship,
roadmaps that are partly fiction. It works identically for a solo builder with
fifteen side projects.

## Stack

| Tool | Role |
|---|---|
| **HydraDB** | The federated evidence query across connectors. Its source-scoping parameter *is* the kill shot. |
| **Pipeshift** | Cause-of-death classifier (structured) and the medical examiner's voice. |
| **RocketRide Cloud** | The deployed pipeline: webhook → Investigator → Coroner → Registrar → response. |
| **InsForge** | The morgue. Stores every certificate, evidence trail, and both scoped runs. The UI reads only from here. |

## Setup

```bash
cp .env.example .env   # paste keys
pip install -r requirements.txt
python smoke/test_hydradb.py
python smoke/test_pipeshift.py
python smoke/test_insforge.py
python smoke/rocketride_hello.py
```
