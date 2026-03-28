"""YB-Shorts: YouTube Viral Shorts Video Generator — CLI entry point."""

import asyncio
import os
import sys
from pathlib import Path

from dotenv import load_dotenv


async def main() -> None:
    load_dotenv()

    topic = os.getenv("SHORTS_TOPIC", "Lord Shiva grace towards his young happy meditating woman devotee").strip()
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:]).strip()

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
    print(f"  Title:      {script.title}")
    print(f"  Hook:       {script.hook}")
    print(f"  Narration:  {script.narration}")
    print(f"  Duration:   {script.duration_seconds}s")
    print(f"  Video prompt: {script.video_prompt}")
    print(f"  Character:  {script.character}")
    print()

    # --- Resolve ingredient images ---
    # For _devotee characters: ingredient_1 = deity, ingredient_2 = devotee.
    # For deity-only characters: both ingredients are the deity image.
    RESOURCES_DIR = Path(__file__).parent / "resources"
    character = script.character
    if character.endswith("_devotee"):
        deity = character.replace("_devotee", "")
        ingredient_1 = RESOURCES_DIR / f"{deity}.png"
        ingredient_2 = RESOURCES_DIR / f"{character}.png"
    else:
        ingredient_1 = RESOURCES_DIR / f"{character}.png"
        ingredient_2 = ingredient_1

    for img_path in {ingredient_1, ingredient_2}:
        if not img_path.exists():
            raise FileNotFoundError(
                f"Character image not found: {img_path}\n"
                f"Place a PNG for '{img_path.stem}' in the resources/ folder."
            )

    print(f"  Ingredients: {ingredient_1.stem} + {ingredient_2.stem}")
    print()

    # --- Phase 2: Video generation (Veo 3.1) ---
    print("Phase 2: Generating video with Veo 3.1...")
    from src.yb_shorts.video_gen import generate_video

    output_path = generate_video(script.video_prompt, ingredient_1, ingredient_2)
    print()

    print("=" * 60)
    print(f"Done! Video saved to: {output_path}")
    print("=" * 60)
    print()
    print(f"Topic:  {topic}")
    print(f"Title:  {script.title}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    asyncio.run(main())
