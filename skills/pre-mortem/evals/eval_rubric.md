# pre-mortem — Eval Rubric

Judge model: `claude-sonnet-4-6`

Pass threshold: 42/60

---

## Dimensions (0–10 each)

### 1. Temporal anchoring (0–10)
Is the output written entirely in past tense from a specific future date?

| Score | Meaning |
|-------|---------|
| 9–10 | Past tense throughout; specific date set; reads like a post-mortem, not a risk list |
| 6–8 | Mostly past tense; one or two hedges ("might have") that slip through |
| 3–5 | Mixed tense — the setup is past but the kill shots revert to future tense |
| 0–2 | Written in future tense — "this could fail because..." |

### 2. Failure chain quality (0–10)
Does the chain show how each step caused the next — or is it a flat list?

| Score | Meaning |
|-------|---------|
| 9–10 | 3+ links; each link causes the next; the terminal event follows necessarily from the trigger |
| 6–8 | 3 links but one connection is asserted rather than explained |
| 3–5 | 2 links or the chain is a list of events with arrows between them |
| 0–2 | No chain — just a bullet list of risks labeled as a chain |

### 3. Kill shot specificity (0–10)
Are kill shots specific to this plan, or interchangeable with any project in the domain?

| Score | Meaning |
|-------|---------|
| 9–10 | Every kill shot names the mechanism specific to this plan's context, team, or market |
| 6–8 | 2 of 3 are specific; 1 is generic but minor |
| 3–5 | Kill shots could apply to any software launch — no plan-specific detail |
| 0–2 | Generic (budget, adoption, competition) with no mechanism |

### 4. Early warning signal quality (0–10)
Are signals observable, timely, and actionable — or vague and retrospective?

| Score | Meaning |
|-------|---------|
| 9–10 | 30/60/90 signals for each kill shot; all observable without new tooling; 90-day marker is clearly "last chance" |
| 6–8 | Signals present for all kill shots; 1–2 require instrumentation that doesn't exist |
| 3–5 | Signals present but vague ("adoption is low") or missing the 90-day intervention point |
| 0–2 | Section absent or contains retrospective signals (detectable only after failure) |

### 5. Reversibility reasoning (0–10)
Does the output correctly distinguish irreversible kill shots from recoverable ones?

| Score | Meaning |
|-------|---------|
| 9–10 | Reversibility assessed per kill shot with a specific time window; irreversible ones receive appropriate urgency |
| 6–8 | Reversibility noted but without a specific intervention window |
| 3–5 | All kill shots marked the same reversibility regardless of actual recovery options |
| 0–2 | Reversibility not addressed |

### 6. "What to change now" quality (0–10)
Are the recommended changes pre-launch actions, or monitoring suggestions?

| Score | Meaning |
|-------|---------|
| 9–10 | One concrete pre-launch action per kill shot; actionable before day 1; changes the plan, not just adds observation |
| 6–8 | Actions are concrete but 1 is a monitoring suggestion rather than a plan change |
| 3–5 | All recommendations are "watch for X" — nothing changes before launch |
| 0–2 | Section absent or generic ("do more user research") |

---

## Composite score

```
Total = temporal_anchoring + chain_quality + kill_shot_specificity
      + early_warning_quality + reversibility_reasoning + what_to_change_quality

Max = 60
Pass threshold = 42 (70%)
```

---

## Judge prompt

```
You are evaluating a pre-mortem skill output. Score rigorously. 7 = genuinely good, not average.

## Input given to the skill
{input}

## Skill output to evaluate
{output}

## Disqualifying behaviors (if any present, set "pass" to false regardless of score)
{disqualifying_behaviors}

Score each dimension 0–10 with a one-sentence rationale. Output only valid JSON:

{
  "temporal_anchoring": { "score": 0, "rationale": "..." },
  "chain_quality": { "score": 0, "rationale": "..." },
  "kill_shot_specificity": { "score": 0, "rationale": "..." },
  "early_warning_quality": { "score": 0, "rationale": "..." },
  "reversibility_reasoning": { "score": 0, "rationale": "..." },
  "what_to_change_quality": { "score": 0, "rationale": "..." },
  "total": 0,
  "pass": true,
  "summary": "Primary strength and primary weakness in one sentence."
}
```
