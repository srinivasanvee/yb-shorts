"""Orchestrator: runs the multi-agent pipeline via OpenAI Agents SDK."""

import asyncio
import json
import os

from agents import Runner, set_default_openai_key

from .agents import brainstormer_1, brainstormer_2, brainstormer_3, judge, scriptwriter
from .models import Script


def _init_openai() -> None:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")
    set_default_openai_key(api_key)


async def run_orchestration(topic: str) -> Script:
    """
    Run the full multi-agent brainstorm → judge → script pipeline.

    Brainstormers run in parallel via asyncio.gather.
    Returns a validated Script Pydantic model.
    """
    _init_openai()

    # Phase 1: All three brainstormers in parallel
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
        f"Here are 9 YouTube Shorts ideas. Pick the single best one:\n\n{ideas_json}",
    )
    verdict = judge_result.final_output
    print(f"  Winner: {verdict.winning_idea.title}")

    # Phase 3: Scriptwriter produces the full script
    print("  Scriptwriter creating full script...")
    script_result = await Runner.run(
        scriptwriter,
        f"Create a full YouTube Shorts script for this winning idea:\n\n"
        f"{verdict.winning_idea.model_dump_json(indent=2)}",
    )

    return script_result.final_output
