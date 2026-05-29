"""
Video database service.

Handles saving detection results and finding similar videos in MongoDB.
"""

import datetime
import logging
from typing import Any, Dict, List, Optional

from bson import ObjectId

from app.core.database import get_collection

logger = logging.getLogger(__name__)

COLLECTION_NAME = "video_detection_results"


def save_video_result(
    video_url: str,
    local_path: str,
    time_detections: List[Dict[str, Any]],
    music_description: str,
) -> Optional[str]:
    """Persist a video detection result; returns inserted document id or None."""
    try:
        collection = get_collection(COLLECTION_NAME)
        doc = {
            "video_url": video_url,
            "local_video_path": local_path,
            "processing_date": datetime.datetime.utcnow(),
            "time_detections": time_detections,
            "music_description": music_description,
        }
        result = collection.insert_one(doc)
        logger.info("Video result saved, id=%s", result.inserted_id)
        return str(result.inserted_id)
    except Exception as exc:
        logger.error("MongoDB save error: %s", exc)
        return None


def find_similar_videos(
    current_detections: List[Dict[str, Any]],
    exclude_id: Optional[str] = None,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """
    Return top-*limit* videos with highest Jaccard similarity to *current_detections*.
    """
    try:
        collection = get_collection(COLLECTION_NAME)

        current_instruments = _extract_instruments(current_detections)

        all_videos = list(
            collection.find({}, {"_id": 1, "video_url": 1, "time_detections": 1, "music_description": 1})
        )

        scored = []
        for video in all_videos:
            if exclude_id and str(video["_id"]) == exclude_id:
                continue
            db_instruments = _extract_instruments(video.get("time_detections", []))
            similarity = _jaccard(current_instruments, db_instruments)
            if similarity <= 0:
                continue
            scored.append(
                {
                    "video_id": str(video["_id"]),
                    "video_url": video.get("video_url", ""),
                    "similarity": similarity,
                    "common_instruments": sorted(current_instruments & db_instruments),
                    "all_instruments": sorted(db_instruments),
                    "music_description": video.get("music_description"),
                }
            )

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:limit]

    except Exception as exc:
        logger.error("Error finding similar videos: %s", exc)
        return []


# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_instruments(detections: List[Dict[str, Any]]) -> set:
    instruments = set()
    for entry in detections:
        instruments.update(entry.get("detected_instruments", []))
    return instruments


def _jaccard(a: set, b: set) -> float:
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)
