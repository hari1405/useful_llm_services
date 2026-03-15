# useful-llm-services

> One focused, runnable AI tool. Every week.

A series of Python terminal apps for PMs, AI builders, and anyone working at the intersection of product and AI engineering. Each tool is self-contained, open source, BYOK, and runnable in under 10 minutes from clone to first output.

All tools support four LLM providers out of the box: **Anthropic, OpenAI, Gemini, and any custom OpenAI-compatible endpoint**.

Built by [Hariprasad Rengarajan](https://linkedin.com/in/hariprasad-rengarajan) — AI Strategist at Google. Follow along on [LinkedIn](https://linkedin.com/in/hariprasad-rengarajan) for the weekly build log.

---

## The Series

| Week | Tool | What It Does | Status |
|------|------|-------------|--------|
| 1 | [🏛️ decision-council](./week-1-decision-council/) | Send any proposal to 8 AI critics. Get a Battle Brief: hardest questions, biggest assumption, how to prep. | ✅ Live |
| 2 | [⚖️ llm-judge](./week-2-llm-judge/) | Eval harness for LLM outputs. Plain-English criteria. Pass/fail with reasoning. Batch CSV mode. | 🚧 Mar 25 |
| 3 | [🧪 persona-lab](./week-3-persona-lab/) | Synthetic user interview simulator. 10 conversations in 2 minutes. Synthesised brief included. | 🚧 Apr 1 |

---

## ⚠️ BYOK — Bring Your Own Key

Every tool in this series requires **your own API key**. We support four providers:

| Provider | Env Variable | Get Key |
|---|---|---|
| Anthropic (Claude) | `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/) |
| OpenAI (GPT) | `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/api-keys) |
| Google (Gemini) | `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| Custom endpoint | `CUSTOM_API_KEY` + `CUSTOM_BASE_URL` | Your provider's docs |

Set whichever key you have and the tool auto-detects it. No config files needed.

---

## Design Principles

Every tool in this series follows the same rules:

- **Python only.** Terminal apps built with Rich + Typer.
- **Open source libraries only.** No proprietary SDKs beyond the LLM providers themselves.
- **BYOK.** You own your keys. We never touch them.
- **Multi-LLM from day one.** Anthropic, OpenAI, Gemini, or custom — your choice.
- **Full test suite included.** All tests are mocked. No API key needed to run them.
- **Under 10 minutes from clone to output.** If it takes longer, it's broken.

---

## Quick Start

Each tool lives in its own directory and is fully self-contained:

```bash
git clone https://github.com/hariprasadrengarajan/useful-llm-services.git

# Week 1 — decision-council
cd useful-llm-services/week-1-decision-council
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...   # or OPENAI_API_KEY, GOOGLE_API_KEY
python -m council
```

See each tool's `README.md` for full usage.

---

*Open source. MIT License.*
