"""Pydantic data models for YB-Shorts pipeline."""

from typing import Literal
from pydantic import BaseModel, Field


class BrainstormIdea(BaseModel):
    title: str = Field(description="Catchy title for the Short")
    hook: str = Field(description="Opening hook line to grab attention in first 3 seconds")
    concept: str = Field(description="Core concept of the video")
    viral_angle: str = Field(description="Why this will go viral")
    estimated_duration_seconds: int = Field(description="Estimated video duration in seconds (30-60)")


class BrainstormResponse(BaseModel):
    ideas: list[BrainstormIdea] = Field(description="List of 3 video ideas")


class JudgeVerdict(BaseModel):
    winning_idea: BrainstormIdea = Field(description="The best idea chosen from all candidates")
    reason: str = Field(description="Why this idea was chosen over the others")


class ImagePrompt(BaseModel):
    role: Literal["start_frame", "middle_frame", "end_frame"] = Field(
        description="Position of this frame in the video"
    )
    prompt: str = Field(description="Detailed DALL-E 3 prompt for generating this frame")


class Script(BaseModel):
    title: str = Field(description="YouTube Shorts title (max 100 chars)")
    hook: str = Field(description="Opening hook narration for first 3 seconds")
    narration: str = Field(description="Full narration script for the video")
    video_prompt: str = Field(description="Veo 3.1 prompt describing the video motion and style")
    image_prompts: list[ImagePrompt] = Field(
        description="2-3 image prompts for key frames (start, middle, end)",
        min_length=2,
        max_length=3,
    )
    duration_seconds: int = Field(description="Target duration in seconds (30-60)")
