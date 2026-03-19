"""Orchestrator: runs the multi-agent pipeline via Claude Agent SDK."""

import json

from claude_agent_sdk import ClaudeAgentOptions, ResultMessage, query

from .agents import AGENT_DEFINITIONS, ORCHESTRATOR_SYSTEM_PROMPT
from .models import Script
from .utils import extract_json


async def run_orchestration(topic: str) -> Script:
    """
    Run the full multi-agent brainstorm → judge → script pipeline.

    Calls brainstormers in parallel, judges all ideas, writes the script,
    and returns a validated Script model.
    """
    prompt = (
        f"Create a viral YouTube Short about this topic: {topic}\n\n"
        f"Follow your instructions: call brainstormer-1, brainstormer-2, and "
        f"brainstormer-3 SIMULTANEOUSLY, then judge, then scriptwriter."
    )

    result_text: str | None = None

    async for message in query(
        prompt=prompt,
        options=ClaudeAgentOptions(
            allowed_tools=["Agent"],
            agents=AGENT_DEFINITIONS,
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
            model="claude-opus-4-6",
            max_turns=20,
        ),
    ):
        if isinstance(message, ResultMessage):
            result_text = message.result

    if not result_text:
        raise RuntimeError("Orchestrator returned no result")

    raw = extract_json(result_text)
    return Script.model_validate(raw)


def format_ideas_for_judge(brainstorm_results: list[dict]) -> str:
    """Format multiple brainstorm results into a single JSON string for the judge."""
    all_ideas = []
    for result in brainstorm_results:
        ideas = result.get("ideas", [])
        all_ideas.extend(ideas)
    return json.dumps({"all_ideas": all_ideas}, indent=2)
