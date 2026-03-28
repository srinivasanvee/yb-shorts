"""Pydantic data models for YB-Shorts pipeline."""

from pydantic import BaseModel, Field, field_validator

_VALID_CHARACTERS = {
    "buddha", "buddha_devotee",
    "krishna", "krishna_devotee",
    "muruga", "muruga_devotee",
    "shiva", "shiva_devotee",
    "vishnu", "vishnu_devotee",
}


class BrainstormIdea(BaseModel):
    title: str = Field(description="Catchy title for the Short")
    hook: str = Field(description="Opening hook line to grab attention in first 3 seconds")
    concept: str = Field(description="Core concept of the video")
    viral_angle: str = Field(description="Why this will go viral")
    estimated_duration_seconds: int = Field(description="Video duration in seconds — must be 8")


class BrainstormResponse(BaseModel):
    ideas: list[BrainstormIdea] = Field(description="List of 3 video ideas")


class JudgeVerdict(BaseModel):
    winning_idea: BrainstormIdea = Field(description="The best idea chosen from all candidates")
    reason: str = Field(description="Why this idea was chosen over the others")


class Script(BaseModel):
    title: str = Field(description="YouTube Shorts title (max 100 chars)")
    hook: str = Field(description="Opening hook narration for first 3 seconds")
    narration: str = Field(description="Full narration script for the video")
    video_prompt: str = Field(description="Veo 3.1 prompt describing the video motion and style")
    character: str = Field(
        description=(
            "Character image to use, must be exactly one of: "
            "buddha, buddha_devotee, krishna, krishna_devotee, "
            "muruga, muruga_devotee, shiva, shiva_devotee, vishnu, vishnu_devotee"
        )
    )
    duration_seconds: int = Field(description="Target duration in seconds — must be 8")

    @field_validator("character")
    @classmethod
    def validate_character(cls, v: str) -> str:
        normalized = v.lower().strip()
        if normalized not in _VALID_CHARACTERS:
            raise ValueError(
                f"character must be one of {sorted(_VALID_CHARACTERS)}, got {v!r}"
            )
        return normalized
