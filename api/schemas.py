"""
Pydantic models and schemas for API requests and responses.
"""

from typing import List, Optional
from pydantic import BaseModel


class SpeakerSegment(BaseModel):
    """Model for a speaker segment with timing information."""
    speaker: str
    start_time: float
    end_time: float
    text: str


class TranscriptionResponse(BaseModel):
    """Response model for transcription."""
    transcription: str
    speaker_segments: List[SpeakerSegment]
    language_code: Optional[str] = None
    duration: Optional[float] = None

