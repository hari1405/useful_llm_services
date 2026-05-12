# 🧪 persona-lab

> **Synthetic user interviews at scale. 10 conversations in 2 minutes.**

`persona-lab` is a Python terminal app that simulates user research interviews before you commit to real ones. Give it a persona description, a product scenario, and a number N — get back N diverse interview transcripts and a synthesised brief with themes, objections, blockers, and recommended follow-up questions.

**Part of the [useful-llm-services](../README.md) series.**

---

## Status: 🚧 Coming Week of Mar 30, 2026

This package is in active development. Follow along on [LinkedIn](https://www.linkedin.com/in/hp1598/) for the build log.

---

## What It Will Do

- Input: a persona description + product scenario + N (number of interviews)
- Output: N diverse synthetic interview transcripts + a synthesised brief
- Synthesised brief includes: key themes, objections, blockers, and recommended real interview questions
- Persona diversity engine: randomises seniority, risk tolerance, and domain experience so you don't get 10 identical responses
- JSON + Markdown output modes
- 10 synthetic interviews in under 2 minutes

## Why This Exists

User research is slow and expensive. Before you book 10 real interviews, you should already know what you're going to hear. `persona-lab` pre-qualifies your ideas in minutes so real interview time is spent on genuine surprises.

---

## Planned Features

- Persona diversity engine (randomised seniority, risk tolerance, industry background)
- Scenario modes: feature evaluation, problem discovery, usability testing
- Synthesis brief: themes, objections, blockers, recommended follow-up Qs
- JSON + Markdown output
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
