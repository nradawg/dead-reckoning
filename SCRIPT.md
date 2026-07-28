# Dead Reckoning — speaking script

**Open first:** https://dead-reckoning-q8sa0cu0l-nick-raddons-projects.vercel.app
**Have ready:** nothing else. Do not switch tabs mid demo.

---

## 0:00 — the hook (say this before you touch anything)

> "Every company has projects that are dead but still marked In Progress.
> Look at this list. Every single one of these says In Progress."

*Let them look at the sidebar for one beat.*

---

## 0:15 — click Atlas Migration

> "This one is Atlas Migration. Watch what the agent says."

*Certificate renders. Point at it.*

> "Deceased. Confidence 0.93. Time of death June 20th.
> Cause: silent abandonment after extended inactivity.
> Twelve pieces of evidence, pulled from four different tools."

---

## 0:45 — THE KILL SHOT. Click the scope button.

*Say this WHILE you click:*

> "Same agent. Same question. One source instead of four."

*It flips to a green In Progress badge.*

**STOP TALKING. Count to two in your head.**

> "That green badge is what your dashboard shows you every morning."

---

## 1:10 — click Payments V2

> "This one is worse. It is a zombie.
> Three people are still actively discussing it in Slack.
> Nobody has written a line of code in weeks.
> Talk without work. A dead or alive tool calls this healthy."

---

## 1:25 — the honesty line (volunteer it, do not wait to be asked)

> "The data is seeded through HydraDB's own ingest API, the same path the
> connectors write through, because Slack physically cannot backdate messages.
> The retrieval and the scoping are untouched. Change the threshold and I will
> re run it right now."

---

## 1:40 — close

> "HydraDB does the query and its scoping is the whole trick.
> Pipeshift writes the diagnosis. RocketRide runs the pipeline.
> InsForge stores every certificate.
>
> And it is an MCP server, so I can just ask Claude which of my projects are dead."

---

# IF THEY ASK

**"Is this real data?"**
> Real pipeline, real query, real inference. The corpus is seeded so a dead
> project exists to find. Change any date and re run it.

**"Why not let the model decide if it is dead?"**
> Because then it could hallucinate a verdict. The verdict is timestamp math.
> The model only writes the diagnosis. That is why the demo cannot break.

**"What if a project is just slow, not dead?"**
> That is the zombie verdict. Talk recent, work stale. It is the interesting case.

**"How would my company use this?"**
> Connect Slack, GitHub, Linear and Gmail in the HydraDB dashboard, point one
> environment variable at that database. The engine only reads provider,
> timestamp and text.

**"What is the business?"**
> Every engineering org over about thirty people has this problem and no one
> owns it. It runs every Monday morning and tells you where your headcount is
> going and which customers are waiting on something that will never ship.

---

# IF SOMETHING BREAKS

- Live link dead? Local backup: `http://127.0.0.1:8899/demo.html`
- Page blank? Hit "Reload from InsForge"
- Everything down? Talk through the numbers: DECEASED 0.93 with 12 evidence
  items becomes In Progress 0.71 with 4. That contrast IS the pitch.

---

# THE ONE LINE THAT MATTERS

> "That green badge is what your dashboard shows you every morning."

If you only land one sentence, land that one.
