# Dead Reckoning — Presentation Brief

> Feed this whole file to Perplexity and ask it to build a demo-day deck.
> Everything below is verified against a working build. Nothing is aspirational.

---

## THE PRODUCT

**Name:** Dead Reckoning
**Agent:** The Coroner
**One line:** An agent that pronounces your zombie projects dead, and tells you what to do about it.

**Why the name:** Dead reckoning is the navigation technique of determining your
position by inference from evidence rather than direct observation. That is
exactly what the agent does. It never asks a project how it's doing. It infers
the truth from what the team actually did.

---

## THE PROBLEM

Companies pay engineers to work on projects that are already dead, and nobody
notices, because the status field still says "In Progress."

Updating that field is nobody's job. So three things happen:

1. Headcount stays assigned to abandoned work
2. Customers wait on features that will never ship
3. Leadership plans quarters around a roadmap that is partly fiction

Nobody catches it today because catching it means checking four systems at once,
and that is also nobody's job.

---

## THE IMPOSSIBLE QUESTION

> **"This project says In Progress. Is it actually alive?"**

This cannot be answered from any single tool, by construction:

- **Linear** holds what the company *claims* (the status field)
- **Slack, GitHub, Gmail** hold what the company actually *did* (behavior)

Dead projects live in the gap between the claim and the behavior.

---

## HOW IT ANSWERS

Four steps. Only the last one uses a language model.

1. **Pull the footprint** — one HydraDB query per connector for everything tied
   to the project: the Linear ticket, GitHub commits and PR reviews, Slack
   messages, Gmail threads.
2. **Compute vitals** — last genuine human signal per source, with timestamp
   and citation.
3. **Pronounce** — if every behavioral source flatlined more than 30 days ago
   while Linear still claims active, the project is dead. This is timestamp
   arithmetic, not a model guessing, which is why the demo cannot hallucinate.
4. **Diagnose** — Pipeshift classifies the death pattern and writes the
   recommendation.

### Four verdicts, not two

| Verdict | Meaning |
|---|---|
| **ALIVE** | Recent work confirmed across connectors |
| **DECEASED** | No human signal and no work for 30+ days |
| **ZOMBIE** | People still talking, but no work in weeks. Talk without work. |
| **In Progress** | What you get when you only ask one tool (the failure mode) |

**The ZOMBIE verdict is the proof of reasoning.** A dead-or-alive tool is a
date-diff script. Payments V2 has three people actively discussing it and zero
code movement in 61 days. Only a cross-source agent calls that correctly.

---

## THE OUTPUT: three parts

**1. The certificate** — time of death, cause of death, survived by, every field
carrying a citation from the connector it came from.

**2. The verdict** — REVIVE, REPLACE, or BURY, with reasoning tied to evidence.

**3. The alternative** — fires only on REPLACE. What already solves this,
internally or off the shelf.

Then you can ask follow-up questions, grounded in the stored evidence.

---

## THE KILL SHOT (the demo moment)

Same agent, same question, scoped to Linear only.

Linear's only evidence is `status: In Progress`. Nothing contradicts it, because
the contradiction lives in the other three systems. So the answer does not get
vaguer — **it gets confidently wrong.**

### Verified numbers from the live build

| Project | All four sources | Linear only |
|---|---|---|
| **Atlas Migration** | DECEASED, confidence 0.93, 12 evidence items | In Progress, confidence 0.71, 4 items |
| **Payments V2** | ZOMBIE, confidence 0.88, 12 evidence items | In Progress, confidence 0.71, 4 items |
| Search Rewrite | ALIVE | In Progress |
| Onboarding Redesign | ALIVE | In Progress |

Atlas Migration's evidence splits evenly across all four connectors: 3 Slack,
3 GitHub, 3 Linear, 3 Gmail.

**The line to say:** *"That green badge is what your dashboard shows you every morning."*

---

## THE STACK — every tool load-bearing

| Tool | Its actual job | Verified |
|---|---|---|
| **HydraDB** | The entire verdict. Federated query across 4 connectors. Its `collections` scoping parameter *is* the kill shot: a different query returning 12 records vs 4. | 51 records ingested, queries returning in under 1s |
| **Pipeshift** | The diagnosis. Reads evidence, writes cause of death, recommendation, and eulogy. | Produced "silent deprioritization" and named the 3 people still waiting |
| **RocketRide Cloud** | The deployed pipeline `dead-reckoning-coroner`: Webhook → OpenAI-Compatible LLM node → response. The LLM node points at Pipeshift. | Saved in their builder; RocketRide validated the Pipeshift credentials live; pipelines executed on their Cloud runtime |
| **InsForge** | The morgue. Postgres table holding every certificate. The UI reads only from here, which is why the scope toggle is instant. | 9 certificates stored, write and read verified |

---

## TWO SURFACES, ONE ENGINE

**The web dashboard** is the proof. Four projects, click one, see the verdict,
flip the scope toggle.

**The MCP server** is the product. Connect it to Claude, Codex, or any agent and
just ask "which of my projects are dead?" Four tools exposed:
`list_projects`, `check_project`, `triage_all` (Monday review), and
`past_certificates` — which reads InsForge so the agent *remembers* what it
concluded last time and can tell you when a verdict changed.

That memory is the real differentiator. A dashboard tells you today's state. An
agent with memory says *"Atlas was ALIVE when you asked in June. It's DECEASED
now. It died on the 20th."*

---

## HONESTY SLIDE (volunteer this, do not wait to be asked)

The Northgate corpus is seeded through **HydraDB's ingest API**, the same
contract the OAuth connectors write through, rather than through live OAuth.

**Why:** the verdict is timestamp arithmetic, and Slack's API physically cannot
create backdated messages. `chat.postMessage` has no timestamp parameter and
`chat.scheduleMessage` is future-only. A workspace seeded today would show every
project as perfectly healthy and there would be no corpse to find.

**What is not affected:** retrieval, scoping, inference, and storage are all
genuinely running. HydraDB's own docs confirm API-ingested app sources and
connector-synced sources feed the identical retrieval stack.

**The proof offer:** change `DEAD_AFTER_DAYS` on stage and re-run. Nothing is
hardcoded.

Volunteering this reads as engineering judgment. Getting caught not mentioning
it reads as the opposite.

---

## THE 90 SECOND SCRIPT

**0:00** — "Northgate's tracker says Atlas Migration is In Progress. Every
project on this screen says In Progress."

**0:15** — Click Atlas. DECEASED, confidence 0.93, died June 20th, cause: silent
abandonment. Twelve pieces of evidence across four connectors.

**0:45** — Flip the scope toggle to Linear only. Green In Progress badge.
*Pause two seconds.* "Same agent. Same question. One source instead of four."

**1:00** — "That green badge is what your dashboard shows you every morning."

**1:10** — Click Payments V2. "This one's worse. It's a zombie. Three people are
still actively discussing it and no code has moved in weeks. Talk without work.
A dead-or-alive tool calls this healthy."

**1:25** — The honesty line, then: "Change the threshold and I'll re-run it live."

---

## WHO IT'S FOR

**Enterprise:** Engineering leaders and founders carrying projects nobody has
admitted are dead. Runs across the org every Monday morning.

**Solo builders:** Point it at your own accounts and find out which of your
fifteen side projects are actually dead. Identical engine, zero code changes.

**How a company adopts it:** HydraDB dashboard → Connectors → add Slack, GitHub,
Linear, Gmail. Then point one environment variable at that database. The engine
only ever reads provider, timestamp, and text, and connector data has all three.

---

## LINKS

- **Repo:** https://github.com/nradawg/dead-reckoning
- **Live dashboard:** (Vercel URL)
- **RocketRide pipeline:** `dead-reckoning-coroner`

---

## DECK STRUCTURE TO BUILD

1. Title — Dead Reckoning, the agent that pronounces your zombie projects dead
2. The problem — status fields lie, and nobody's job is to check
3. The impossible question — claim vs behavior, why one tool can't answer
4. How it works — 4 steps, only the last uses a model
5. Four verdicts — and why ZOMBIE proves reasoning
6. **The kill shot** — the before/after table, biggest slide in the deck
7. The stack — 4 tools, what each actually does
8. Two surfaces — dashboard as proof, MCP server as product
9. Honesty — the seeding decision and why
10. Who it's for — enterprise and solo, same engine
11. Close — "That green badge is what your dashboard shows you every morning."
