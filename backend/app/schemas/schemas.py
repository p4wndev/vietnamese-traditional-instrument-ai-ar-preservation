from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Instrument ────────────────────────────────────────────────────────────────

class InstrumentOut(BaseModel):
    name: str
    description: str


# ── Image detection ───────────────────────────────────────────────────────────

class ImageDetectOut(BaseModel):
    output: List[str] = Field(description="Relative paths to cropped prediction images")
    classifications: List[str] = Field(description="Predicted class for each cropped image")


# ── Ontology ──────────────────────────────────────────────────────────────────

class OntologyInfoOut(BaseModel):
    ontology_info: Dict[str, Any]
    videos: List[Dict[str, Any]]


# ── RAG chatbot ───────────────────────────────────────────────────────────────

class RAGRequest(BaseModel):
    question: str = Field(min_length=1, description="User question in Vietnamese or English")


class RAGOut(BaseModel):
    answer: str
    sources: List[str]


# ── Video detection ───────────────────────────────────────────────────────────

class TimeDetection(BaseModel):
    time_second: float
    detected_instruments: List[str]


class SimilarVideo(BaseModel):
    video_id: str
    video_url: str
    similarity: float
    common_instruments: List[str]
    all_instruments: List[str]
    music_description: Optional[str] = None


class VideoDetectOut(BaseModel):
    video_url: str
    time_detections: List[TimeDetection]
    music_description: str
    similar_videos: List[SimilarVideo]
