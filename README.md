# YB-Shorts: YouTube Viral Shorts Video Generator

Automatically generates viral YouTube Shorts from a topic. A multi-agent pipeline brainstorms ideas, picks the best one, writes a script with visual direction, generates image frames via DALL-E 3, then stitches them into a video with Veo 3.1.

**Output:** A ready-to-upload `output/output.mp4` (720p, 9:16, ~8s).

---

## How It Works

```
Topic → Brainstorm (3 agents in parallel) → Judge → Script → DALL-E 3 frames → Veo 3.1 video
```

| Agent | Model | Role |
|-------|-------|------|
| brainstormer-1 | gpt-4o-mini | Emotional storytelling → 3 ideas |
| brainstormer-2 | gpt-4o-mini | Surprising facts → 3 ideas |
| brainstormer-3 | gpt-4o-mini | Trending formats → 3 ideas |
| judge | gpt-4o | Picks best from 9 ideas |
| scriptwriter | gpt-4o | Full script + image prompts |

---

## Prerequisites

- Python 3.11+
- API keys for OpenAI and Google

---

## Setup

### 1. Clone and install dependencies

```bash
git clone <repo-url>
cd yb-shorts
pip install -e .
```

Or with `uv`:

```bash
uv sync
```

### 2. Configure API keys

```bash
cp .env.example .env
```

Edit `.env` and fill in your keys:

```bash
OPENAI_API_KEY=sk-...          # OpenAI Agents SDK + DALL-E 3 — get from platform.openai.com
GOOGLE_API_KEY=AIza...         # Veo 3.1 — get from aistudio.google.com
SHORTS_TOPIC=surprising science facts  # Optional default topic
```

---

## Running

### Full pipeline (agents + images + video)

```bash
python main.py
```

With a custom topic:

```bash
SHORTS_TOPIC="one weird trick to fall asleep fast" python main.py
```

Or pass the topic as an argument:

```bash
python main.py "why cats knock things off tables"
```

**Expected output:** `output/output.mp4`
**Expected time:** ~3–5 minutes (agents ~30s, DALL-E ~30s/frame, Veo ~2–4 min)

---

### Test agents only (no images or video)

```bash
python -c "
import asyncio
from src.yb_shorts.orchestrator import run_orchestration

async def t():
    script = await run_orchestration('coffee facts')
    print(script.model_dump_json(indent=2))

asyncio.run(t())
"
```

---

## Project Structure

```
yb-shorts/
├── main.py                     # CLI entry point
├── pyproject.toml              # Dependencies
├── .env.example                # API key template
├── src/
│   └── yb_shorts/
│       ├── models.py           # Pydantic data models
│       ├── agents.py           # Agent definitions + system prompts
│       ├── orchestrator.py     # Claude Agent SDK pipeline
│       ├── image_gen.py        # DALL-E 3 frame generation
│       ├── video_gen.py        # Veo 3.1 video generation
│       └── utils.py            # JSON extraction helper
└── output/                     # Generated files saved here
```

---

## Troubleshooting

**`ModuleNotFoundError: No module named 'claude_agent_sdk'`**
Install dependencies: `pip install -e .`

**Veo model 404 error**
The code automatically tries fallback model names. If all fail, verify your Google API key has Veo access at [aistudio.google.com](https://aistudio.google.com).

**DALL-E rate limit**
Tier 1 OpenAI accounts are limited to 7 HD images/minute. With 2–3 frames this is fine; the pipeline will raise an error if hit. Wait 60 seconds and retry.

**Agents run sequentially instead of in parallel**
The orchestrator system prompt instructs Claude to call all three brainstormers simultaneously. If they run sequentially, the pipeline still works — just takes a bit longer.
