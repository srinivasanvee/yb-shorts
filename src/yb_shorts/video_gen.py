"""Veo 3.1 video generation from image frames and a prompt."""

import os
import time
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path("output")

# Veo model to try (fall back if 404)
VEO_MODELS = [
    "veo-3.1-generate-001",
    "veo-3.1-generate-preview",
    "veo-3-generate-preview",
]

POLL_INTERVAL_SECONDS = 15
MAX_POLL_ATTEMPTS = 60  # 15 min max wait


def generate_video(video_prompt: str, ingredient_1: Path, ingredient_2: Path) -> Path:
    """
    Generate a video via Google Veo 3.1 conditioned on two ingredient images.

    ingredient_1 is passed as the primary reference image.
    ingredient_2 is passed as the secondary reference image.
    Both condition the visual style and characters throughout the video.
    Falls back to prompt-only generation if the images are rejected by content policy.
    Polls until the operation completes and saves output to output/output_<timestamp>.mp4.
    """
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY environment variable not set")

    client = genai.Client(api_key=api_key)
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("Generating video with Veo 3.1...")
    print(f"  Ingredient 1: {ingredient_1}")
    print(f"  Ingredient 2: {ingredient_2}")
    print(f"  Prompt:       {video_prompt[:80]}...")

    img_1 = types.Image.from_file(location=str(ingredient_1))
    img_2 = types.Image.from_file(location=str(ingredient_2))

    base_config = types.GenerateVideosConfig(
        aspect_ratio="9:16",
        resolution="720p",
        duration_seconds=8,
    )

    # Two attempts: with ingredient images first, then prompt-only fallback
    attempts = [
        ("with ingredient images", img_1, img_2),
        ("prompt-only (ingredient fallback)", None, None),
    ]

    for attempt_label, primary_img, secondary_img in attempts:
        config = base_config.model_copy()
        config.last_frame = secondary_img

        operation = _submit(client, video_prompt, primary_img, config)
        if operation is None:
            continue  # no model available

        operation = _poll(client, operation)
        veo_response = operation.response or operation.result

        if not veo_response:
            raise RuntimeError("Veo operation completed but returned no response object")

        if veo_response.rai_media_filtered_count:
            reasons = veo_response.rai_media_filtered_reasons or []
            print(f"  Veo filtered ({attempt_label}): {reasons}")
            if attempt_label.startswith("with"):
                print("  Retrying without ingredient images...")
                continue
            raise RuntimeError(f"Veo content policy blocked prompt-only generation: {reasons}")


        generated = veo_response.generated_videos or []
        if not generated:
            raise RuntimeError("Veo returned an empty generated_videos list")

        return _save_video(client, generated[0])

    raise RuntimeError("Veo generation failed on all attempts")


def _submit(client, video_prompt: str, start_image, config):
    """Try each Veo model in order; return the operation or None if all 404."""
    from google.genai import types

    for model_name in VEO_MODELS:
        try:
            print(f"  Trying model: {model_name}")
            op = client.models.generate_videos(
                model=model_name,
                prompt=video_prompt,
                image=start_image,
                config=config,
            )
            print(f"  Using model: {model_name}")
            return op
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                print(f"  Model {model_name} not available, trying next...")
                continue
            raise
    raise RuntimeError(f"No Veo model available from: {VEO_MODELS}")


def _poll(client, operation):
    """Poll until the operation is done."""
    print("Polling for video completion (this may take 2-4 minutes)...")
    for attempt in range(MAX_POLL_ATTEMPTS):
        if operation.done:
            return operation
        elapsed = (attempt + 1) * POLL_INTERVAL_SECONDS
        print(f"  [{attempt + 1}/{MAX_POLL_ATTEMPTS}] Still processing... ({elapsed}s elapsed)")
        time.sleep(POLL_INTERVAL_SECONDS)
        operation = client.operations.get(operation)
    raise TimeoutError("Veo video generation timed out after 15 minutes")


def _save_video(client, gen_video) -> Path:
    """Save the generated video to output/output_YYYYMMDD_HHMMSS.mp4."""
    video_obj = gen_video.video
    if not video_obj:
        raise RuntimeError("GeneratedVideo.video is None")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_path = OUTPUT_DIR / f"output_{timestamp}.mp4"

    if video_obj.video_bytes:
        output_path.write_bytes(video_obj.video_bytes)
    elif video_obj.uri:
        video_bytes = client.files.download(file=video_obj)
        output_path.write_bytes(video_bytes)
    else:
        video_obj.save(str(output_path))

    print(f"Video saved to: {output_path}")
    return output_path


