# Dead Reckoning — what got built

Agents You Love 2, Frontier Tower SF, July 28 2026. Roughly four hours from
empty folder to live link.

---

## The short version

An agent that finds projects a company thinks are alive but are actually dead,
by comparing what a tracker *claims* against what the team actually *did*
across their connected tools.

Four sponsor tools, all load bearing. A working live demo. A public repo a
stranger can run. And an MCP server so any agent can ask "which of my projects
are dead?"

---

## Deliverables

| Thing | Where | State |
|---|---|---|
| Live dashboard | dead-reckoning-q8sa0cu0l-nick-raddons-projects.vercel.app | Public, HTTP 200 |
| Public repo | github.com/nradawg/dead-reckoning | 28 files, no secrets |
| RocketRide pipeline | `dead-reckoning-coroner` in Pipeline Builder | Saved, credentials validated |
| MCP server | `mcp_server.py` | 4 tools, package installed |
| Presentation brief | `PRESENTATION_BRIEF.md` | For Perplexity |
| Speaking script | `SCRIPT.md` | Timed with click cues |

---

## How the idea got chosen

The organizers wrote the example question into the problem statement: "which
bugs did we complain about in Slack that never became Linear tickets?" Every
team at the venue was going to build that.

So a tournament ran instead: six concepts generated from deliberately different
creative angles, three independent judges scoring novelty, three hour
feasibility, sponsor fit, and demo punch. The Coroner won two of three top picks
and the highest combined score.

The reason it won, in the judges' words: **its failure mode is an inversion, not
a fade.** Every other team scoping to one source would show a vaguer answer.
This shows a confidently *wrong* one. That difference is the whole demo.

---

## What each tool actually does

**HydraDB** is the verdict. A federated query across Slack, GitHub, Linear and
Gmail. Its `collections` scoping parameter *is* the kill shot: the same question
scoped to Linear alone returns 4 evidence items instead of 12.

**Pipeshift** does two jobs. It writes the cause of death and the
revive/replace/bury recommendation, and it powers project discovery by reading
raw records and naming the projects it finds.

**RocketRide Cloud** runs the pipeline. Webhook feeding an OpenAI Compatible
node pointed at Pipeshift. RocketRide validated those credentials live on save.
Pipelines also executed on their Cloud runtime via the Python SDK.

**InsForge** is the morgue. A Postgres table holding every certificate. The
dashboard reads only from there, which is why the on stage scope toggle is
instant and cannot fail mid demo.

---

## The design decision that matters most

**The verdict is deterministic. A model never decides whether a project is dead.**

Vitals and verdict are timestamp arithmetic. Pipeshift only names projects and
writes explanations. This means the demo cannot hallucinate a verdict, and it is
the answer to the sharpest question a judge can ask.

Four verdicts came out of this, not two:

| | |
|---|---|
| ALIVE | Recent work confirmed |
| DECEASED | No signal, no work, past threshold |
| ZOMBIE | People still talking, nobody working |
| In Progress | What you get asking one tool |

ZOMBIE is the proof it reasons. A dead-or-alive tool is a date subtraction.
Payments V2 has Slack activity 4 days old and GitHub silent for 61. Only a
cross source agent calls that correctly.

---

## Bugs found and fixed

**My own scoping bug would have faked the kill shot.** The first version used
`metadata_filters`, which compares arrays by set equality and fails *silently*.
The Linear-only run would have returned everything and looked identical to the
full run, and neither of us would have noticed on stage. Switched to
`collections`, a real vector store pre filter.

**Timestamps were being read from the wrong field.** HydraDB stamps
`source_upload_time` as ingest time, always today. Using it made every project
look alive. The real value lives in `additional_metadata.timestamp`.

**Death fields rendered on living projects.** An ALIVE project was showing
"Time of death: UNKNOWN, Cause: UNDETERMINED" in red. Nonsense. Now those fields
only appear on a corpse.

**Project discovery matched everything.** When discovery was added, the model
returned "northgate.io" and people's names as project identifiers. That domain
is in every email address in the corpus, so every project inherited the newest
activity and all four read ALIVE. Fixed with a stricter prompt plus automatic
detection: any term appearing in more than a third of records gets dropped
regardless of what the model claims.

**Stale data on the live site.** The deployed snapshot predated the diagnosis
fix and showed "UNDETERMINED" as Atlas's cause. Caught during the final check
and regenerated from InsForge.

---

## Environment problems that cost real time

These were the machine and the vendors, not the code, and they are all
documented in `CLAUDE.md` so nobody repeats them.

**`import requests` takes 57 seconds on this Mac.** Almost certainly security
software scanning the venv. Every process paid it three times over.

**The HydraDB SDK takes 150 seconds inside its constructor.** The OpenAI SDK
has the same pathology. Both were replaced with plain `requests`, which does the
same calls in under half a second.

**Slack cannot backdate messages, at all.** No timestamp parameter on
`chat.postMessage`, and `chat.scheduleMessage` is future only. This single fact
determined the entire data strategy, because a workspace seeded today would show
every project as healthy and there would be no corpse to find.

**Vendor docs were ahead of their APIs.** InsForge wants
`columnName`/`isNullable`, not the `name`/`nullable` their docs show.
RocketRide's documented `rrext_deploy_add` returns "Invalid command" on Cloud.
HydraDB's ingest rejects JSON and wants multipart form data.

---

## What is real and what is seeded

**Real:** the retrieval, the scoping, the verdict logic, the inference, the
storage, the pipeline, the deployment.

**Seeded:** the corpus itself, through HydraDB's ingest API, which is the same
contract the OAuth connectors write through.

Why: the verdict is timestamp math, and Slack cannot backdate. A workspace
seeded this afternoon would have no dead project in it.

This is worth volunteering before anyone asks, along with the offer to change
the threshold and re run live.

---

## The part that makes it actually yours

Discovery was added late and it is the difference between a demo and a product.

The original version had four hardcoded project slugs. Now the model reads a
sample of whatever data exists and names the projects itself. Proven on the
demo corpus: it correctly identified all four projects with zero hints, and the
verdicts matched the hardcoded version exactly.

```
DECEASED   Atlas migration      github 74d, slack 44d, gmail 52d
ZOMBIE     Payments V2          github 61d, slack 4d
ALIVE      Search rewrite       github 2d,  slack 1d
ALIVE      Onboarding redesign  github 1d,  slack 6d
```

Point it at your own Gmail and GitHub and it does the same thing to your work.

---

## Making it usable by strangers

The repo would have failed for anyone else. Fixed:

- `setup.sh` — one command, finds a Python 3.10+ interpreter
- `check.py` — preflight that tests all four services and says exactly what is
  wrong in plain language ("wallet empty, redeem a coupon", "you created a
  database but connected no tools")
- `CLAUDE.md` — so someone using Claude Code can say "set this up" and their
  agent already knows the four gotchas
- Cleaned `requirements.txt`, fixed `.env.example`, deleted three dead files

Realistic time for a stranger: about 15 minutes, mostly account signups.

---

## Security

The InsForge anon key was briefly in the published page with row level security
off, meaning anyone could have written to the certificates table. Fixed by
splitting the build: the local demo reads live from InsForge with credentials
that never leave the laptop, the published page reads an exported snapshot and
contains no key at all.

The old key is still in git history, so it should be rotated.

---

## What is not finished

**No live OAuth connectors.** Everything is ready for them, and discovery works
on whatever syncs, but no real account is attached yet.

**The RocketRide pipeline has no response node.** Webhook and LLM are wired and
validated. Their UI names the output node something other than "response" and
hunting for it was not worth the last minutes before submission.

**Row level security is still off** on the InsForge table.
