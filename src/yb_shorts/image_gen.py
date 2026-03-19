"""DALL-E 3 image generation for YouTube Shorts frames."""

import asyncio
import os
from pathlib import Path

import httpx
from openai import AsyncOpenAI

from .models import ImagePrompt

OUTPUT_DIR = Path("output")

# DALL-E 3 settings for 9:16 portrait (native Shorts format)
IMAGE_SIZE = "1024x1792"
IMAGE_QUALITY = "hd"


async def generate_image(
    client: AsyncOpenAI,
    image_prompt: ImagePrompt,
    index: int,
) -> Path | None:
    """Generate a single frame image via DALL-E 3 and save to output dir.

    Returns None if the request is blocked by content policy.
    """
    from openai import BadRequestError

    print(f"  Generating {image_prompt.role} (frame {index + 1})...")

    try:
        response = await client.images.generate(
            model="dall-e-3",
            prompt=image_prompt.prompt,
            size=IMAGE_SIZE,
            quality=IMAGE_QUALITY,
            n=1,
        )
    except BadRequestError as e:
        if "content_policy_violation" in str(e) or e.code == "content_policy_violation":
            print(f"  WARNING: {image_prompt.role} blocked by content policy — skipping")
            return None
        raise

    image_url = response.data[0].url
    if not image_url:
        raise RuntimeError(f"DALL-E 3 returned no URL for {image_prompt.role}")

    # Download the image
    async with httpx.AsyncClient() as http_client:
        img_response = await http_client.get(image_url, timeout=60.0)
        img_response.raise_for_status()

    # Save to output directory
    filename = f"frame_{index:02d}_{image_prompt.role}.png"
    output_path = OUTPUT_DIR / filename
    output_path.write_bytes(img_response.content)

    print(f"  Saved {image_prompt.role} → {output_path}")
    return output_path


async def generate_all_images(image_prompts: list[ImagePrompt]) -> list[Path]:
    """
    Generate all frame images concurrently via DALL-E 3.

    Skips frames blocked by content policy. Raises if no frames succeed.
    Returns list of successfully generated paths.
    """
    OUTPUT_DIR.mkdir(exist_ok=True)

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable not set")

    client = AsyncOpenAI(api_key=api_key)

    print(f"Generating {len(image_prompts)} frames with DALL-E 3...")
    tasks = [
        generate_image(client, prompt, i)
        for i, prompt in enumerate(image_prompts)
    ]

    results = await asyncio.gather(*tasks)
    paths = [p for p in results if p is not None]

    if not paths:
        raise RuntimeError("All DALL-E 3 frames were blocked by content policy")

    skipped = len(results) - len(paths)
    if skipped:
        print(f"  {skipped} frame(s) skipped due to content policy.")
    print(f"{len(paths)} frame(s) generated successfully.")
    return paths
