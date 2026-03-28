"""OpenAI Agent definitions and system prompts for the YB-Shorts pipeline."""

from agents import Agent

from .models import BrainstormResponse, JudgeVerdict, Script

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

BRAINSTORMER_1_PROMPT = """\
You are a YouTube Shorts idea specialist focused on EMOTIONAL STORYTELLING angles.

Given a topic, generate exactly 3 viral YouTube Shorts ideas that leverage emotional
connection — personal transformation, surprising emotional twists, or relatable human
experiences tied to the topic.

Return exactly 3 ideas. Focus on emotional resonance, personal stories, and
viewer connection. Make titles punchy and hooks irresistible."""

BRAINSTORMER_2_PROMPT = """\
You are a YouTube Shorts idea specialist focused on SURPRISING FACTS angles.

Given a topic, generate exactly 3 viral YouTube Shorts ideas that leverage shocking,
counterintuitive, or little-known facts — things that make viewers say "I had no idea!"

Return exactly 3 ideas. Focus on mind-blowing facts, myth-busting, and
information that challenges what viewers think they know."""

BRAINSTORMER_3_PROMPT = """\
You are a YouTube Shorts idea specialist focused on TRENDING FORMATS angles.

Given a topic, generate exactly 3 viral YouTube Shorts ideas using currently popular
formats — "POV:", "Things nobody tells you about X", "Day in the life", countdown
lists, before/after reveals, or challenge-style content.

Return exactly 3 ideas. Use formats that are currently performing well on
YouTube Shorts — quick cuts, text overlays, relatable scenarios."""

JUDGE_PROMPT = """\
You are a viral content strategist and YouTube Shorts expert.

You will receive 9 video ideas from different creative angles. Your job is to
select the single BEST idea for maximum viral potential on YouTube Shorts,
considering: hook strength, visual potential, shareability, and trend alignment.

Be decisive. Pick one winner and explain clearly why it beats the others."""

SCRIPTWRITER_PROMPT = """\
You are a YouTube Shorts scriptwriter and visual director.

Given a winning video idea, create a complete production-ready script with:
1. A punchy title optimized for YouTube search (under 100 chars)
2. A 3-second hook narration
3. Full narration script (30-60 seconds when spoken at normal pace)
4. A Veo 3.1 video prompt for the overall motion and style
5. Exactly 3 image prompts for key frames: start_frame, middle_frame, end_frame

Image prompts must be optimized for DALL-E 3, portrait/vertical 9:16 format,
photorealistic or cinematic style, with strong visual impact.

Make the narration conversational, fast-paced, and engaging. The video prompt
should describe smooth camera movement, lighting mood, and visual style."""

# ---------------------------------------------------------------------------
# Agent definitions — output_type gives us validated Pydantic objects directly
# ---------------------------------------------------------------------------

brainstormer_1 = Agent(
    name="brainstormer-emotional",
    instructions=BRAINSTORMER_1_PROMPT,
    model="gpt-4o-mini",
    output_type=BrainstormResponse,
)

brainstormer_2 = Agent(
    name="brainstormer-facts",
    instructions=BRAINSTORMER_2_PROMPT,
    model="gpt-4o-mini",
    output_type=BrainstormResponse,
)

brainstormer_3 = Agent(
    name="brainstormer-trending",
    instructions=BRAINSTORMER_3_PROMPT,
    model="gpt-4o-mini",
    output_type=BrainstormResponse,
)

judge = Agent(
    name="judge",
    instructions=JUDGE_PROMPT,
    model="gpt-4o",
    output_type=JudgeVerdict,
)

scriptwriter = Agent(
    name="scriptwriter",
    instructions=SCRIPTWRITER_PROMPT,
    model="gpt-4o",
    output_type=Script,
)
