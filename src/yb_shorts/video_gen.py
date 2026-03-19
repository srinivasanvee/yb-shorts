"""Veo 3.1 video generation from image frames and a prompt."""

import os
import time
from pathlib import Path

OUTPUT_DIR = Path("output")
OUTPUT_VIDEO = OUTPUT_DIR / "output.mp4"

# Veo model to try (fall back if 404)
VEO_MODELS = [
    "veo-3.1-generate-001",
    "veo-3.1-generate-preview",
    "veo-3-generate-preview",
]

POLL_INTERVAL_SECONDS = 15
MAX_POLL_ATTEMPTS = 60  # 15 min max wait


def generate_video(video_prompt: str, image_paths: list[Path]) -> Path:
    """
    Generate a video via Google Veo 3.1 using start/end frames as guidance.

    Polls until the operation completes and saves output to output/output.mp4.
    """
    from google import genai
    from google.genai import types

    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise RuntimeError("GOOGLE_API_KEY environment variable not set")

    client = genai.Client(api_key=api_key)
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Identify start and end frames
    start_frame = _find_frame(image_paths, "start_frame")
    end_frame = _find_frame(image_paths, "end_frame")

    if not start_frame:
        start_frame = image_paths[0]
    if not end_frame:
        end_frame = image_paths[-1]

    print(f"Generating video with Veo 3.1...")
    print(f"  Start frame: {start_frame}")
    print(f"  End frame:   {end_frame}")
    print(f"  Prompt:      {video_prompt[:80]}...")

    start_image = types.Image.from_file(location=str(start_frame))
    end_image = types.Image.from_file(location=str(end_frame))

    config = types.GenerateVideosConfig(
        aspect_ratio="9:16",
        resolution="720p",
        duration_seconds=8,
        last_frame=end_image,
    )

    # Try models in order until one works
    operation = None
    used_model = None
    for model_name in VEO_MODELS:
        try:
            print(f"  Trying model: {model_name}")
            operation = client.models.generate_videos(
                model=model_name,
                prompt=video_prompt,
                image=start_image,
                config=config,
            )
            used_model = model_name
            print(f"  Using model: {used_model}")
            break
        except Exception as e:
            if "404" in str(e) or "not found" in str(e).lower():
                print(f"  Model {model_name} not available, trying next...")
                continue
            raise

    if operation is None:
        raise RuntimeError(f"No Veo model available from: {VEO_MODELS}")

    # Poll until done
    print("Polling for video completion (this may take 2-4 minutes)...")
    for attempt in range(MAX_POLL_ATTEMPTS):
        if operation.done:
            break
        print(f"  [{attempt + 1}/{MAX_POLL_ATTEMPTS}] Still processing... ({(attempt + 1) * POLL_INTERVAL_SECONDS}s elapsed)")
        time.sleep(POLL_INTERVAL_SECONDS)
        operation = client.operations.get(operation)
    else:
        raise TimeoutError("Veo video generation timed out after 15 minutes")

    # Resolve response — Veo may use .response or .result
    veo_response = operation.response or operation.result
    if not veo_response:
        raise RuntimeError("Veo operation completed but returned no response object")

    # Check if content was filtered
    if veo_response.rai_media_filtered_count:
        reasons = veo_response.rai_media_filtered_reasons or []
        raise RuntimeError(
            f"Veo filtered {veo_response.rai_media_filtered_count} video(s) "
            f"due to content policy: {reasons}"
        )

    generated = veo_response.generated_videos or []
    if not generated:
        raise RuntimeError("Veo returned an empty generated_videos list")

    # Save the first generated video
    gen_video = generated[0]
    video_obj = gen_video.video
    if not video_obj:
        raise RuntimeError("GeneratedVideo.video is None")

    if video_obj.video_bytes:
        # Bytes already present — write directly
        OUTPUT_VIDEO.write_bytes(video_obj.video_bytes)
    elif video_obj.uri:
        # Need to download from GCS/signed URL
        video_bytes = client.files.download(file=video_obj)
        OUTPUT_VIDEO.write_bytes(video_bytes)
    else:
        # Use SDK save helper as fallback
        video_obj.save(str(OUTPUT_VIDEO))

    print(f"Video saved to: {OUTPUT_VIDEO}")
    return OUTPUT_VIDEO


def _find_frame(image_paths: list[Path], role: str) -> Path | None:
    """Find a frame by its role name in the filename."""
    for path in image_paths:
        if role in path.name:
            return path
    return None
