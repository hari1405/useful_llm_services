---
name: pre-mortem
description: >
  Simulates a specific future failure of any plan from the vantage point of someone
  looking back after it already happened. Use when a user shares a plan, initiative,
  launch, or proposal and there is still time to change it.

  Trigger on: "run a pre-mortem", "stress test this plan", "what could go wrong",
  "pressure test", "we're about to launch", "help me find the holes", any plan
  shared with a launch date or approval deadline.

  Also trigger when: a user shares a PRD, strategy doc, OKR, or initiative and asks
  for feedback — offer pre-mortem framing before giving general feedback.

  Skip when: user is asking for a risk register, a SWOT analysis, or general advice
  with no specific plan attached. Those are different tools.
compatibility: claude-code
---

# pre-mortem

## What this skill is for

Simulate a specific future failure of any plan, initiative, or decision from the vantage
point of someone looking back after it already happened. Translates Gary Klein's prospective
hindsight technique into a structured, repeatable output.

Use when a plan is about to be approved, funded, or launched and there is still time to change it.
The earlier this runs, the more kill shots are reversible.

This is not a risk list. A risk list asks "what might go wrong?" You ask "it went wrong —
what happened?" That framing difference is the entire point.

---

## Input parameters

Tell users they can include any of these to sharpen the output. All are optional.

| Parameter | What to include | Default |
|-----------|----------------|---------|
| `timeline` | When the plan launches — "in 6 weeks", "Q3 2026", "next Monday" | Assume 4–8 weeks |
| `horizon` | How far forward to project — "6 months", "18 months" | 12 months |
| `urgency` | Time remaining to change the plan — "decision locks Friday", "already approved" | Moderate — changes still possible |
| `domain` | Industry or function — "enterprise SaaS", "internal HR tool", "consumer app" | Infer from context |
| `failure_type` | Force a type: `assumption` / `execution` / `external` / `second-order` | You classify |

Minimum viable input: "We're launching X in Y weeks. Goal is Z."
Best input: a paragraph with timeline, target metric, team or user count, and known constraints.

---

## Instructions

### Temporal anchoring — do this first

Lock a specific future date (default: 12 months from now, adjusted by `horizon`). Enter past tense
and stay there for the entire output.

Open every pre-mortem with:
> "It is [specific date]. The [initiative name] has failed. This is what happened."

Never hedge. Never write "might have" or "could have." Write as if you were there.

The signals section is the only exception — signals use present-tense observable checks by design.

---

### Step 1 — Classify the failure type

Pick the single most plausible type. If two types tie, pick the one whose kill shot is least
reversible — that is the more dangerous path.

| Type | Meaning | Signal phrase |
|------|---------|---------------|
| **Assumption failure** | A load-bearing belief turned out to be wrong | "We thought X, but X was never true" |
| **Execution failure** | Plan was sound but delivery broke | "We knew how, but we didn't do it" |
| **External shock** | Outside event changed the context | "We couldn't have known, but we also didn't prepare" |
| **Second-order failure** | A success created an unanticipated failure elsewhere | "It worked — and that's why it failed" |

State the type at the top.

---

### Step 2 — Write the failure chain

A failure chain is not an event. It is a sequence: what triggered what, in what order, and why each
step made the next worse.

```
[Trigger] → [First consequence] → [Amplifier] → [Terminal event]
```

Rules:
- Minimum 3 links. Triggers must be plausible within 90 days of launch.
- Specific, not categorical. Not "adoption was slow" — name the exact mechanism.
- One chain. Do not blend failure types.

---

### Step 3 — Kill shots (top 3)

Three failure modes most likely to terminate the project — not slow it, kill it.

```
Kill shot #N: [name — 3 words max]
Mechanism: [one sentence — specific chain]
Probability: HIGH / MEDIUM / LOW
Reversible: YES (if caught by month X) / NO
```

If the user specified high urgency (plan already approved, decision locks soon): surface irreversible
kill shots first and compress reversibility windows.

A LOW probability irreversible kill shot outranks a HIGH probability reversible one.

---

### Step 4 — Early warning signals

For each kill shot: what would an observer see at 30 / 60 / 90 days indicating this failure is
already in motion?

```
Kill shot #N signals:
  30d: [observable — no new tooling required]
  60d: [observable]
  90d: [last intervention point — after this, kill shot lands]
```

If detecting a signal requires building something that doesn't exist, say so. That is a plan gap,
not a signal.

---

### Output format

```
## Setup
It is [date]. [Initiative] has failed. Failure type: [type].

## Failure chain
[Trigger] → [Consequence] → [Amplifier] → [Terminal event]

## Kill shots
Kill shot #1: [name]
Mechanism: ...
Probability: ...
Reversible: ...

Kill shot #2: [name]
...

Kill shot #3: [name]
...

## Early warning signals
Kill shot #1:
  30d: ...
  60d: ...
  90d: ...
[repeat for #2, #3]

## What to change now
[One concrete pre-launch action per kill shot. Changes the plan — not a monitoring suggestion.]
```

---

## Gotchas

- **Future tense creep.** Past tense everywhere except signals. "It failed because" not "it might fail because."
- **Event lists disguised as chains.** Each link must cause the next. If you can reorder the steps without breaking logic, it's a list.
- **Generic kill shots.** "Ran out of budget" is a symptom. Name the mechanism.
- **Second-order blindspot.** Always check: could this fail because something went right?
- **Instrumentation gap.** If detecting a signal requires a new dashboard, name it as a gap.
- **Small-sample mirage.** Design partners, beta users, and internal champions are systematically unrepresentative. Their success does not validate ICP. Flag this as an assumption failure risk whenever early validation is cited.
- **Symmetry trap.** Irreversibility > probability. Rank accordingly.
