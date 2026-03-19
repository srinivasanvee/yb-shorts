"""JSON extraction utility for parsing agent outputs."""

import json
import re


def extract_json(text: str) -> dict:
    """
    Extract JSON from agent output, stripping markdown code fences if present.
    Agents often wrap JSON in ```json ... ``` blocks despite instructions.
    """
    if not text:
        raise ValueError("Empty text provided to extract_json")

    # Strip markdown code fences (```json ... ``` or ``` ... ```)
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(fence_pattern, text)
    if match:
        text = match.group(1).strip()

    # Try direct parse first
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object or array in the text
    for pattern in [r"\{[\s\S]*\}", r"\[[\s\S]*\]"]:
        match = re.search(pattern, text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                continue

    raise ValueError(f"Could not extract valid JSON from text: {text[:200]}...")
