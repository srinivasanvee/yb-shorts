"""YB-Shorts: YouTube Viral Shorts Video Generator — CLI entry point."""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


async def main() -> None:
    load_dotenv()

    topic = os.getenv("SHORTS_TOPIC", "surprising science facts")
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])

    print("=" * 60)
    print("YB-Shorts: YouTube Viral Shorts Generator")
    print("=" * 60)
    print(f"Topic: {topic}")
    print()

    # --- Phase 1: Agent pipeline (brainstorm → judge → script) ---
    print("Phase 1: Running agent pipeline...")
    from src.yb_shorts.orchestrator import run_orchestration

    script = await run_orchestration(topic)
    print()
    print("Script generated:")
    print(f"  Title:    {script.title}")
    print(f"  Hook:     {script.hook}")
    print(f"  Duration: {script.duration_seconds}s")
    print(f"  Frames:   {len(script.image_prompts)}")
    print()

    # --- Phase 2: Image generation (DALL-E 3, parallel) ---
    print("Phase 2: Generating frames with DALL-E 3...")
    from src.yb_shorts.image_gen import generate_all_images

    image_paths = await generate_all_images(script.image_prompts)
    print()

    # --- Phase 3: Video generation (Veo 3.1) ---
    print("Phase 3: Generating video with Veo 3.1...")
    from src.yb_shorts.video_gen import generate_video

    output_path = generate_video(script.video_prompt, image_paths)
    print()

    print("=" * 60)
    print(f"Done! Video saved to: {output_path}")
    print("=" * 60)
    print()
    print("Script details:")
    print(f"  Title:     {script.title}")
    print(f"  Narration: {script.narration[:100]}...")


if __name__ == "__main__":
    asyncio.run(main())
