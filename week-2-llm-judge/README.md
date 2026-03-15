# ⚖️ llm-judge

> **Eval harness for LLM outputs. Plain-English criteria. Pass/fail with reasoning.**

`llm-judge` is a Python terminal app that uses an LLM-as-judge to evaluate the quality of other LLM outputs against plain-English criteria you define. Batch CSV mode for running evals at scale, single-shot terminal mode for quick checks.

**Week 2 of the [useful-llm-services](../README.md) series.**

---

## Status: 🚧 Coming Week of Mar 23, 2026

This package is in active development. Follow along on [LinkedIn](https://linkedin.com/in/hariprasad-rengarajan) for the build log.

---

## What It Will Do

- Give it prompts + LLM responses + plain-English criteria
- Claude-as-judge (or any supported provider) scores each output
- Returns: pass/fail, confidence score (0–1), and reasoning
- Batch CSV mode: run hundreds of evals, get a Markdown/CSV report
- Single-shot mode: test one response in the terminal, see results instantly
- `--threshold` flag: set the pass rate you need (e.g. `--threshold 0.85`)

## Why This Exists

OpenAI's o4-mini hallucinates 48% of the time on structured output tasks. Evals are the #1 unsolved problem in production AI systems. Most teams skip them because building an eval harness from scratch is painful. This makes it a 10-minute setup.

## Why I Built This

I built an eval harness like this at Google from scratch — no playbook existed. `llm-judge` packages what I learned into something anyone can clone and run.

---

## Planned Features

- Rubric DSL: define structured criteria in YAML
- Batch CSV eval with aggregate pass rate
- Markdown + CSV report output
- `--threshold` flag for pass rate requirements
- Multi-LLM support: Anthropic, OpenAI, Gemini, Custom

---

## ⚠️ BYOK — Bring Your Own Key

Will support the same four providers as the rest of this series:

| Provider | Env Variable |
|---|---|
| Anthropic (Claude) | `ANTHROPIC_API_KEY` |
| OpenAI (GPT) | `OPENAI_API_KEY` |
| Google (Gemini) | `GOOGLE_API_KEY` |
| Custom endpoint | `CUSTOM_API_KEY` + `CUSTOM_BASE_URL` |

---

*Open source. MIT License. BYOK.*
