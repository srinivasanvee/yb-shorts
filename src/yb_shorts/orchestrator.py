"""Orchestrator: runs the multi-agent pipeline via OpenAI Agents SDK + Anthropic."""

import asyncio
import json
import os

from agents import Runner, set_default_openai_key

from .agents import SCRIPTWRITER_PROMPT, brainstormer_1, brainstormer_2, brainstormer_3, judge
from .models import Script


def _init_openai() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")
    set_default_openai_key(api_key)


async def _run_scriptwriter(idea_json: str) -> Script:
    """Run the scriptwriter via Claude Opus 4.6 (Anthropic SDK)."""
    import anthropic

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY environment variable not set")

    client = anthropic.AsyncAnthropic(api_key=api_key)
    message = await client.messages.create(
        model="claude-opus-4-6",
        max_tokens=1024,
        system=SCRIPTWRITER_PROMPT + "\n\nRespond with valid JSON only — no markdown fences, no commentary.",
        messages=[{
            "role": "user",
            "content": f"Create a full YouTube Shorts script for this winning idea:\n\n{idea_json}",
        }],
    )

    raw = message.content[0].text.strip()
    # Strip markdown fences if the model adds them despite instructions
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return Script.model_validate(json.loads(raw))


async def run_orchestration(topic: str) -> Script:
    """
    Run the full multi-agent brainstorm → judge → script pipeline.

    Brainstormers run in parallel via asyncio.gather.
    Scriptwriter uses Claude Opus 4.6 via the Anthropic SDK.
    Returns a validated Script Pydantic model.
    """
    _init_openai()

    # Phase 1: All three brainstormers in parallel (2 ideas each = 6 total)
    print("  Running brainstormers in parallel...")
    b1, b2, b3 = await asyncio.gather(
        Runner.run(brainstormer_1, topic),
        Runner.run(brainstormer_2, topic),
        Runner.run(brainstormer_3, topic),
    )

    all_ideas = (
        b1.final_output.ideas
        + b2.final_output.ideas
        + b3.final_output.ideas
    )
    print(f"  Got {len(all_ideas)} ideas total ({len(b1.final_output.ideas)} + "
          f"{len(b2.final_output.ideas)} + {len(b3.final_output.ideas)})")

    # Phase 2: Judge picks the winner
    print("  Judge selecting best idea...")
    ideas_json = json.dumps([idea.model_dump() for idea in all_ideas], indent=2)
    judge_result = await Runner.run(
        judge,
        f"Here are 6 YouTube Shorts ideas. Pick the single best one:\n\n{ideas_json}",
    )
    verdict = judge_result.final_output
    print(f"  Winner: {verdict.winning_idea.title}")

    # Phase 3: Scriptwriter (Claude Opus 4.6) produces the full script
    print("  Scriptwriter (Claude Opus 4.6) creating full script...")
    return await _run_scriptwriter(verdict.winning_idea.model_dump_json(indent=2))
