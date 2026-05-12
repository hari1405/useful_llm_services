# useful-llm-services

> Small, sharp AI tools and skills for PMs and builders — clone it, run it, ship it.

Built by [Hariprasad Rengarajan](https://www.linkedin.com/in/hp1598/) — AI Strategist at Google (AI Garage, PeopleOps). MS CS, Georgia Tech.

This repo has two tracks. Both grow as long as there are real problems worth solving.

---

## Track 1 — Tools

Runnable Python tools. Each one solves a single, specific problem. Clone, `pip install -r requirements.txt`, and you have output in under 5 minutes.

Every tool:
- Runs from one command
- Supports Anthropic, OpenAI, Gemini, and any custom OpenAI-compatible endpoint
- Ships with a full mocked test suite — no API key needed to run tests
- Costs roughly what a coffee costs to use

| Tool | What it does | Status |
|------|-------------|--------|
| [🏛️ decision-council](./tools/decision-council/) | Send any proposal to 8 AI critics. Get a Battle Brief: hardest questions, biggest assumption, how to prep. | ✅ Live |
| [⚖️ llm-judge](./tools/llm-judge/) | Eval harness for LLM outputs. Plain-English criteria. Pass/fail with reasoning. Batch mode. | 🚧 Coming soon |
| [🧪 persona-lab](./tools/persona-lab/) | Synthetic user interview simulator. 10 conversations in 2 minutes. Synthesised brief included. | 🚧 Coming soon |

---

## Track 2 — Skills

Model-agnostic instruction sets that make Claude and Gemini better at specific recurring tasks — evals, PRDs, RAG review, agent design. Copy a folder, and it works immediately.

| Skill | What it encodes | Status |
|-------|----------------|--------|
| `ai-pm-spec` | Write PRDs the way an experienced AI PM would — with eval criteria, fallback states, and measurable success metrics | 🚧 Coming soon |
| `llm-eval-design` | Design eval suites from scratch — right eval type, LLM-as-judge rubrics, regression detection | 🚧 Coming soon |
| `rag-reviewer` | Review any RAG pipeline — diagnose chunking vs retrieval vs generation failures | 🚧 Coming soon |
| `agent-design-review` | Checklist for multi-agent systems — tool scope, failure modes, cost runaway, observability | 🚧 Coming soon |
| `voice-to-structure` | Extract structured information from messy spoken transcripts | 🚧 Coming soon |

---

## Quick Start

```bash
git clone https://github.com/hari1405/useful_llm_services.git
cd useful_llm_services/tools/decision-council
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # or OPENAI_API_KEY or GOOGLE_API_KEY
python -m council
```

---

## BYOK — Bring Your Own Key

All tools read keys from environment variables. No config files, no accounts, no data leaving your machine except the API call you make.

| Provider | Env var | Get key |
|---|---|---|
| Anthropic (Claude) | `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/) |
| OpenAI (GPT) | `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/api-keys) |
| Google (Gemini) | `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| Custom endpoint | `CUSTOM_API_KEY` + `CUSTOM_BASE_URL` | Your provider's docs |

---

## What makes this different

Every tool here was built by someone who has shipped AI products at Google, Nextiva, and Zoho — not someone learning AI for the first time. The design choices reflect that: no framework abstractions, honest error messages, observable pipelines, and tests that run without an API key.

A tool that exists to pad a portfolio is worse than no tool at all. This repo grows only when there is a real problem worth solving.

---

*Open source. MIT License. Follow the build log on [LinkedIn](https://www.linkedin.com/in/hp1598/).*
