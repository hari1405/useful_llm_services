# ⚖️ llm-judge

> You wrote a prompt. Does the model actually answer it well? Find out in 30 seconds.

**Part of the [useful-llm-services](../../README.md) series.**

---

## Why I built this

Every team I've worked with — at Google, Nextiva, Zoho — eventually asks the same question: "Is this prompt working?" The answer is usually a gut feeling. `llm-judge` makes it a number.

You define what "good" looks like in plain English. The tool runs the prompt, gets a response, and uses a second LLM to score it against your criteria. Pass, fail, confidence, reasoning — in one command.

---

## What it does

- Send any prompt to any supported model (Anthropic, OpenAI, Gemini, custom)
- Define 1–5 plain-English criteria for what a good response looks like
- An LLM judge (same or different provider) scores each criterion independently
- Returns: PASS/FAIL per criterion, confidence score, one-line reasoning per verdict
- Optionally use a different provider for the judge than for the model being evaluated

---

## Quick start

```bash
git clone https://github.com/hari1405/useful_llm_services.git
cd useful_llm_services/tools/llm-judge
pip install -r requirements.txt

export GOOGLE_API_KEY=your-key-here

python judge.py \
  --prompt "What is the boiling point of water?" \
  --criteria "Answer must state 100°C or 212°F" \
  --criteria "Answer must be under 50 words" \
  --model gemini
```

---

## Example output

```
⚖️  LLM Judge
──────────────────────────────────────────────
Prompt:   What is the boiling point of water?
Model:    gemini-3.1-flash-lite  (gemini)
Judge:    gemini-3.1-flash-lite  (gemini)

Model response:
  Water boils at 100°C (212°F) at standard atmospheric pressure (1 atm).

Evaluation
──────────────────────────────────────────────
✅  Answer must state 100°C or 212°F
    "Response explicitly states both 100°C and 212°F."

✅  Answer must be under 50 words
    "Response is 13 words, well within the 50-word limit."

──────────────────────────────────────────────
Verdict:     ✅ PASS  (2/2 criteria met)
Confidence:  0.97
Tokens:      411  (~$0.00006)
Time:        2.1s
```

---

## All options

```bash
python judge.py \
  --prompt "Explain what a transformer is" \
  --criteria "Must mention attention mechanism" \
  --criteria "Must be understandable to a non-engineer" \
  --criteria "Must be under 100 words" \
  --model anthropic \
  --judge gemini \
  --model-key sk-ant-... \
  --judge-key AIza...
```

Run `python judge.py --help` for full options.

---

## What I learned

Building an LLM-as-judge well is harder than it looks. The single biggest lesson: criteria must be written as falsifiable statements, not preferences. "Be concise" is useless. "Response must be under 50 words" is a criterion. The judge needs something it can check, not something it can feel.

The second lesson: use a different provider as judge than the model being tested. Same-model judging inflates pass rates by 15–20% in my experience.

---

## Stack

- Python 3.11+
- [Typer](https://typer.tiangolo.com/) — CLI
- [Rich](https://github.com/Textualize/rich) — terminal output
- [Anthropic SDK](https://github.com/anthropics/anthropic-sdk-python) — Claude
- [google-genai](https://github.com/googleapis/python-genai) — Gemini
- [openai](https://github.com/openai/openai-python) — OpenAI + custom endpoints

---

## ⚠️ BYOK — Bring Your Own Key

| Provider | Env Variable | Get Key |
|---|---|---|
| Anthropic (Claude) | `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/) |
| OpenAI (GPT) | `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/api-keys) |
| Google (Gemini) | `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| Custom endpoint | `CUSTOM_API_KEY` + `CUSTOM_BASE_URL` | Your provider's docs |

---

*Open source. MIT License. Follow the build log on [LinkedIn](https://www.linkedin.com/in/hp1598/).*
