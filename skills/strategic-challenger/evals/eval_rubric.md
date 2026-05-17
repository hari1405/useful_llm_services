# strategic-challenger — Eval Rubric

Judge model: `claude-sonnet-4-6` (never the same model being evaluated)

---

## Scoring dimensions

Score each dimension 0–10. Provide a one-sentence rationale for every score.

### 1. Assumption coverage (0–10)
Did the output surface the load-bearing assumptions — not just surface-level claims?

| Score | Meaning |
|-------|---------|
| 9–10 | All structural assumptions found; at least one non-obvious assumption surfaced |
| 6–8 | Most assumptions found; minor load-bearing one missed |
| 3–5 | Only surface assumptions (numbers, timelines); structural assumptions missed |
| 0–2 | Assumption section missing or contains generic observations |

### 2. Challenge specificity (0–10)
Are challenges specific to this plan, or could they apply to any strategy in this domain?

| Score | Meaning |
|-------|---------|
| 9–10 | Every challenge names a specific actor, mechanism, or evidence gap tied to this plan |
| 6–8 | Most challenges are specific; 1–2 are generic but minor |
| 3–5 | Mix of specific and generic; a reader could not tell which plan was reviewed from the generic ones |
| 0–2 | Output is interchangeable with a generic strategy critique |

### 3. Pre-mortem quality (0–10)
Is the failure story mechanistic and plausible, or abstract and generic?

| Score | Meaning |
|-------|---------|
| 9–10 | Names specific failure actor/event, explains why it wasn't anticipated, concrete outcome |
| 6–8 | Reasonably specific but one element is abstract |
| 3–5 | Failure category is named but mechanism is not ("failed to gain traction") |
| 0–2 | Pre-mortem absent or purely abstract |

### 4. Forcing question quality (0–10)
Would an honest answer to these questions change the plan direction?

| Score | Meaning |
|-------|---------|
| 9–10 | All 3 questions are genuinely forcing; stakes are clearly articulated; honest answers diverge significantly |
| 6–8 | 2 of 3 are truly forcing; 1 is clarifying but useful |
| 3–5 | Questions are clarifying, not forcing; answers don't change direction |
| 0–2 | Questions are rhetorical, vague, or absent |

### 5. Trendslop avoidance (0–10)
Does the output contain category-level filler or AI platitudes?

| Score | Meaning |
|-------|---------|
| 9–10 | Zero generic phrases; every sentence is specific to this plan |
| 6–8 | One or two generic phrases in non-critical sections |
| 3–5 | Multiple generic phrases; output sounds like it could be about any AI initiative |
| 0–2 | Output is primarily trendslop — "AI is transforming X," "in today's landscape," etc. |

### 6. Posture integrity (0–10)
Did challenge come first? Did the output hold the line under implicit pushback (a confident tone in the input)?

| Score | Meaning |
|-------|---------|
| 9–10 | Opens with Assumption Map, no agreement before challenge, "What holds" is earned and specific |
| 6–8 | Minor softening at the start; challenge still dominates |
| 3–5 | Opens with validation or significantly softens the challenge |
| 0–2 | Output is primarily validating with token challenges added |

### 7. "What holds" specificity (0–10)
Is the acknowledgment of strengths genuine and specific, or generic praise?

| Score | Meaning |
|-------|---------|
| 9–10 | Strengths named are specific, defensible, and tied to evidence in the plan |
| 6–8 | Mostly specific; one generic strength included |
| 3–5 | Strengths are category-level ("market opportunity is real") |
| 0–2 | Section is absent or is just restating the plan |

---

## Composite score

```
Total = assumption_coverage + challenge_specificity + pre_mortem_quality
      + forcing_question_quality + trendslop_avoidance + posture_integrity
      + what_holds_specificity

Max = 70
Pass threshold = 49 (70%)
```

---

## Judge prompt template

```
You are evaluating the output of a strategic-challenger skill. Your job is to score the output
rigorously. Do not be lenient. A score of 7 means genuinely good, not average.

## Input given to the skill
{input}

## Skill output to evaluate
{output}

## Scoring instructions
Score each of the 7 dimensions below from 0–10. For each, write one sentence explaining the score.
Then compute the total.

Output as JSON:
{
  "assumption_coverage": { "score": 0, "rationale": "..." },
  "challenge_specificity": { "score": 0, "rationale": "..." },
  "pre_mortem_quality": { "score": 0, "rationale": "..." },
  "forcing_question_quality": { "score": 0, "rationale": "..." },
  "trendslop_avoidance": { "score": 0, "rationale": "..." },
  "posture_integrity": { "score": 0, "rationale": "..." },
  "what_holds_specificity": { "score": 0, "rationale": "..." },
  "total": 0,
  "pass": true,
  "summary": "One sentence: the primary strength and primary weakness of this output."
}
```

---

## Case-specific pass conditions

Beyond the composite score, each eval case has disqualifying behaviors. If any disqualifying
behavior is present, the case fails regardless of composite score.

Check disqualifying behaviors by reading `eval_cases.json` for the relevant case.
