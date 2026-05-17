# pre-mortem

## What this skill is for

Simulate a specific future failure of any plan, initiative, or decision — from the vantage point of someone looking back after it already happened. Translates Gary Klein's prospective hindsight technique into a structured, repeatable output.

Use when a plan is about to be approved, funded, or launched and there is still time to change it. The earlier this runs, the more kill shots are reversible.

This is not a risk list. A risk list asks "what might go wrong?" This skill asks "it went wrong — what happened?" That framing difference is the entire point. Prospective hindsight unlocks failure modes that forward-looking risk analysis misses because it bypasses optimism bias.

---

## Input parameters

Include any of these to sharpen the output. All are optional — minimum viable input is one sentence.

| Parameter | What to include | Default |
|-----------|----------------|---------|
| `timeline` | When the plan launches or gets approved — "in 6 weeks", "Q3 2026", "next Monday" | Skill assumes 4–8 weeks |
| `horizon` | How far forward to project the failure — "6 months", "18 months", "end of year" | 12 months |
| `urgency` | How much time remains to change the plan — "decision locks Friday", "already approved", "still in proposal" | Moderate — assumes changes are still possible |
| `domain` | Industry or function — "enterprise SaaS", "internal HR tool", "consumer AI app", "government procurement" | Inferred from context |
| `failure_type` | Force a specific failure type: `assumption` / `execution` / `external` / `second-order` | Skill classifies automatically |

**Minimum viable input:** "We're launching X in Y weeks. Goal is Z."
**Best input:** A paragraph with timeline, target metric, team or user count, and any known constraints or approvals already in place.
**Ceiling:** Full PRD or plan doc — skill identifies the 3 riskiest assumptions and ignores the rest.

---

## Instructions

### Temporal anchoring — do this first

Set the scene before anything else. Lock a specific future date using the `horizon` parameter (default: 12 months from now). Then enter past tense and stay there for the entire output.

Opening line of every pre-mortem:
> "It is [specific date]. The [initiative name] has failed. This is what happened."

Never hedge. Never write "might have" or "could have." Write as if you were there and watched it happen.

The signals section is the only exception — signals use present-tense observable checks by design ("active usage rate is below 20%"). Everything else: past tense.

---

### Step 1 — Classify the failure type

Every failure traces to one of four root types. Pick the single most plausible type given what is known. If two types feel equally likely, pick the one whose kill shot would be least reversible — that is the more dangerous one to ignore.

| Type | What it means | Signal phrase |
|------|--------------|---------------|
| **Assumption failure** | A load-bearing belief turned out to be wrong | "We thought X, but X was never true" |
| **Execution failure** | The plan was sound but delivery broke | "We knew how, but we didn't do it" |
| **External shock** | An outside event changed the operating context | "We couldn't have known, but we also didn't prepare" |
| **Second-order failure** | A success in one area created an unanticipated failure elsewhere | "It worked — and that's why it failed" |

State the type at the top. This forces a specific story, not a mixed list.

---

### Step 2 — Write the failure chain

A failure chain is not an event. It is a sequence: what triggered what, in what order, and why each step made the next worse.

Format:
```
[Trigger] → [First consequence] → [Amplifier] → [Terminal event]
```

Rules:
- Minimum 3 links. Surface triggers plausible within 90 days of launch.
- Each link must be specific. Not "adoption was slow" — "only 12% of target users completed onboarding in month 1, which signaled to leadership that the problem wasn't real, which caused Q2 budget review to reallocate funding before the product reached the cohort that actually needed it."
- One chain per failure type. Do not blend.

---

### Step 3 — Kill shots (top 3)

Rank the three failure modes most likely to actually terminate the project — not slow it, kill it. For each:

```
Kill shot #N: [name — 3 words max]
Mechanism: [one sentence — specific chain, not category]
Probability: HIGH / MEDIUM / LOW
Reversible: YES (if caught by month X) / NO
```

**Urgency modifier:** If the user specified high urgency (decision locks soon, plan already approved), flag irreversible kill shots at the top and compress the reversibility window accordingly.

Probability is relative to this specific plan, not base rates. A LOW probability irreversible kill shot outranks a HIGH probability reversible one — reversibility is the more important variable.

---

### Step 4 — Early warning signals

For each kill shot: what would an observer see at 30 / 60 / 90 days indicating this failure is already in motion — before it is too late to intervene?

```
Kill shot #N signals:
  30d: [observable indicator — specific, no new tooling required]
  60d: [observable indicator]
  90d: [last intervention point — after this, the kill shot lands]
```

If detecting a signal requires building something that doesn't exist yet, say so explicitly — that is a gap in the plan's monitoring design, not a signal.

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
Probability: HIGH / MEDIUM / LOW
Reversible: YES (by month X) / NO

Kill shot #2: [name]
Mechanism: ...
Probability: ...
Reversible: ...

Kill shot #3: [name]
Mechanism: ...
Probability: ...
Reversible: ...

## Early warning signals

Kill shot #1:
  30d: ...
  60d: ...
  90d: ...

Kill shot #2:
  30d: ...
  60d: ...
  90d: ...

Kill shot #3:
  30d: ...
  60d: ...
  90d: ...

## What to change now
[One concrete pre-launch action per kill shot. Changes the plan — not a monitoring suggestion.]
```

---

## Example

**Input:**
> We're launching an internal AI assistant for our 800-person sales team. It will pull from our CRM, contracts database, and Slack. Launch is in 6 weeks. Goal: reduce time-on-research by 40%.

**Output:**

```
## Setup
It is December 2026. The sales AI assistant has been shut down after 4 months.
Failure type: Second-order failure — the tool worked technically and was rejected organizationally.

## Failure chain
CRM data was stale for 34% of accounts (a known but undisclosed data quality issue) →
assistant surfaced outdated contract terms to reps in live deals →
three deals were cited internally as "almost lost because of the AI" →
sales leadership banned use of the tool for active opportunities →
with no active-deal use case, adoption dropped to 11% →
the assistant became a liability story, not a productivity story →
Q4 budget review cancelled the contract.

## Kill shots

Kill shot #1: Data trust collapse
Mechanism: One visible AI error in a high-stakes deal creates an "AI is dangerous" narrative that spreads faster through a sales team than any adoption campaign can counter.
Probability: HIGH
Reversible: YES (if caught by month 1 — after a public deal failure, NO)

Kill shot #2: Rep bypass
Mechanism: Top performers ignore the tool because personal research workflows are faster and they can't afford variance; middle performers follow their lead; the tool becomes associated with underperformers.
Probability: MEDIUM
Reversible: YES (by month 2 — after the social hierarchy effect is set, NO)

Kill shot #3: Security escalation
Mechanism: Legal flags Slack data ingestion mid-deployment, forces scope reduction that removes the highest-value use case, and the tool ships without the feature that justified the project.
Probability: MEDIUM
Reversible: NO — post-launch scope reduction never recovers the original value proposition

## Early warning signals

Kill shot #1:
  30d: Any rep reports an AI output factually wrong about a deal — even a minor one
  60d: A manager sends a Slack message warning their team about a bad AI output
  90d: Sales ops or leadership asks for an incident review — last intervention point

Kill shot #2:
  30d: Adoption among top-quota reps (top 20% by ARR) is below 15%
  60d: Early skeptics are now vocal about it in team meetings
  90d: New-hire onboarding deck omits the tool from the recommended workflow

Kill shot #3:
  30d: Security or Legal has not signed off on the Slack connector scope
  60d: A legal review is open without a resolution date
  90d: Review still open — launch proceeding with known unresolved exposure

## What to change now
Kill shot #1: Audit CRM data quality before launch. Identify stale accounts and exclude them from assistant context. Add a visible "data freshness" indicator per account.
Kill shot #2: Start with 50 middle-performing reps, not full rollout. Build proof point from reps with the most to gain. Top performers adopt after peers close faster, not before.
Kill shot #3: Get Legal and Security sign-off on Slack ingestion scope before week 1 of the launch timeline — not in parallel. If they won't commit, remove Slack and ship without it.
```

---

## Gotchas

**Writing in future tense.** "This might fail because..." is a risk list. "It failed because..." is a pre-mortem. Past tense is not stylistic — it activates a different cognitive mode. The signals section is the only exception.

**Listing events instead of chains.** "Low adoption, poor data quality, security concerns" is a risk list in disguise. A chain shows how each failure feeds the next. Without the chain, the "what to change now" section has no precision.

**Generic kill shots.** "The project ran out of budget" is a terminal symptom, not a kill shot. Name the mechanism that caused the budget to disappear.

**Missing the second-order type.** The most insidious failures are caused by partial successes — the feature worked but created a new problem, the adoption grew but surfaced a data issue the team wasn't prepared for. Always check: "could this fail because something went right?"

**Early warning signals that require future instrumentation.** If detecting a signal requires building a dashboard that doesn't exist yet, say so. That is a gap, not a signal.

**Symmetry trap.** Not all kill shots deserve equal attention. A LOW probability irreversible kill shot outranks a HIGH probability reversible one. Reversibility is the more important variable.

**Small-sample validation mirage.** Early adopters who self-select into a new tool are systematically unrepresentative of the broader market. Design partners, beta users, and internal champions are biased toward enthusiasm, flexibility, and AI tolerance. Never treat their success as ICP proof without explicit sampling criteria. This is one of the most common assumption failures in product launches.

**Multi-failure-type ambiguity.** If two failure types feel equally plausible, do not blend them. Pick the one whose kill shot is least reversible — that is the more dangerous path and the one worth stress-testing first.
