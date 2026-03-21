# 🏛️ decision-council

> **Stress-test your decisions before the room does.**

Send any proposal to a panel of 8 AI critics — CFO, skeptical engineer, PM devil's advocate, compliance lead, and more. Get back a **Battle Brief**: the hardest questions you'll face, the biggest assumption you need to prove, and exactly how to prep.

Built for PMs, AI strategists, and anyone who needs to walk into a meeting battle-hardened.

**Part of the [useful-llm-services](../README.md) series.**

---

## ⚠️ BYOK — Bring Your Own Key

This tool supports four LLM providers. You need **one** API key to run it.

| Provider | Env Variable | Get Key |
|---|---|---|
| Anthropic (Claude) | `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com/) |
| OpenAI (GPT) | `OPENAI_API_KEY` | [platform.openai.com](https://platform.openai.com/api-keys) |
| Google (Gemini) | `GOOGLE_API_KEY` | [aistudio.google.com](https://aistudio.google.com/app/apikey) |
| Custom endpoint | `CUSTOM_API_KEY` + `CUSTOM_BASE_URL` | Your provider's docs |

Set your key and go:

```bash
export ANTHROPIC_API_KEY=sk-ant-your-key-here
# or
export OPENAI_API_KEY=sk-your-key-here
# or
export GOOGLE_API_KEY=AI-your-key-here
```

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/hariprasadrengarajan/useful-llm-services.git
cd useful-llm-services/decision-council

# 2. Install
pip install -r requirements.txt

# 3. Set your API key (pick one)
export ANTHROPIC_API_KEY=sk-ant-...

# 4. Run — interactive mode walks you through everything
python -m council
```

Runs in under 10 minutes from clone to first output.

---

## Usage

### Interactive (recommended for first run)
```bash
python -m council
```
Walks you through entering your proposal, optional context, and picking council members. Auto-detects your provider from whichever env var is set.

### With flags
```bash
python -m council run \
  --proposal "I want to automate our compliance review with a multi-agent system." \
  --context "Team of 3 engineers, 6-month timeline, Python stack." \
  --all
```

### Pick your LLM provider
```bash
# Use OpenAI
python -m council run --provider openai --proposal "..."

# Use Gemini
python -m council run --provider gemini --proposal "..."

# Use a custom OpenAI-compatible endpoint (e.g. Ollama, Together AI)
python -m council run \
  --provider custom \
  --api-key your-key \
  --base-url https://api.together.xyz/v1 \
  --model mistralai/Mixtral-8x7B-Instruct-v0.1 \
  --proposal "..."

# List all supported providers
python -m council providers
```

### Select specific personas
```bash
python -m council run \
  --proposal "..." \
  --persona "The CFO" \
  --persona "The Skeptical Eng" \
  --persona "The Compliance Lead"
```

### Save report to Markdown
```bash
python -m council run --proposal "..." --all --output report.md
```

### List all available personas
```bash
python -m council list
```

---

## The Council

| Persona | Role | What They'll Challenge |
|---|---|---|
| 💰 The CFO | Chief Financial Officer | ROI, cost assumptions, payback period |
| ⚙️ The Skeptical Eng | Principal Engineer | Scalability, failure modes, evals, tech debt |
| 🔪 The PM Devil | Product Skeptic | User evidence, MVP scope, what you're not building |
| 🔒 The Compliance Lead | Legal / Security | Data privacy, AI liability, auditability |
| 🥊 The Competitor | Your Smartest Rival's CPO | Moat, time-to-copy, strategic differentiation |
| 🔬 The Researcher | AI Research Scientist | Model capabilities vs. reality, eval gaps |
| 🙋 The End User | Actual Human Stakeholder | Trust, workflow disruption, adoption friction |
| 📊 The Exec Sponsor | VP Presenting Upward | Narrative clarity, board-room kill questions |

---

## Output Example

```
╭─────────────────── 💰 The CFO — Chief Financial Officer ────────────────────╮
│                                                                               │
│ You've claimed $2.5M in savings — but have you modelled the total cost of    │
│ ownership? API costs at scale, engineer maintenance, and retraining when the  │
│ model updates are not zero.                                                   │
│                                                                               │
│ What's the payback period if this takes 9 months instead of 6?               │
╰──────────────────────── 1/8 · 2.1s · 847 tokens ────────────────────────────╯

━━━━━━━━━━━━━━━━━━━━ 🧠 Battle Brief ━━━━━━━━━━━━━━━━━━━━

**Top 3 Hardest Questions You Will Face**
1. What happens when the AI makes a wrong compliance call and we get fined?
2. Have you run this on real regulatory documents yet, or just demos?
3. What does the human review step actually look like?

**Biggest Assumption to Prove**
That 4 hours of AI review + 2 hours of human validation is sufficient for legal sign-off.

**Recommended Prep Actions**
- Run a pilot on 2–3 historical compliance changes and compare to analyst decisions
- Get legal to define what human sign-off requires to be legally defensible
- Model API costs at current volume + 3x growth
```

---

## Run Tests

```bash
pip install pytest
pytest tests/ -v
```

All tests are mocked — **no API key required** to run the test suite.

---

## Extend with Custom Personas

```python
from council import DecisionCouncil, build_custom_persona

my_persona = build_custom_persona(
    name="The Board Member",
    role="Independent Board Director",
    emoji="🎩",
    focus="Governance, fiduciary duty, long-term shareholder value",
    extra_context="You've seen three IPOs and two acquisitions go sideways.",
)

council = DecisionCouncil(provider="anthropic", api_key="sk-ant-...")
session = council.run(
    proposal="We are proposing a $5M investment in AI infrastructure...",
    personas=[my_persona],
)
print(session.synthesis)
```

---

## Project Structure

```
decision-council/
├── council/
│   ├── __init__.py       # Public API
│   ├── __main__.py       # python -m council entry point
│   ├── council.py        # Core orchestration logic
│   ├── main.py           # Typer CLI + Rich terminal UI
│   ├── personas.py       # 8 default personas
│   └── providers.py      # LLM provider abstraction
├── tests/
│   ├── test_council.py   # 39 tests — all mocked
│   └── test_personas.py  # Persona validation
├── examples/
│   └── sample_proposal.txt
├── requirements.txt
├── setup.py
├── LICENSE
└── README.md
```

---

## Built By

[Hariprasad Rengarajan](https://linkedin.com/in/hariprasad-rengarajan) — AI Strategist at Google.

Part of a weekly series: one focused, runnable AI tool, every week. Follow along on [LinkedIn](https://linkedin.com/in/hariprasad-rengarajan) for the build log.

---

*Open source. MIT License. BYOK.*
