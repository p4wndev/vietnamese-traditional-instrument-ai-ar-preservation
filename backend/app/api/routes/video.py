import logging
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query, Request, UploadFile, File, status

from app.core.config import settings
from app.schemas.schemas import VideoDetectOut, TimeDetection, SimilarVideo
from app.services.video import generate_music_description, process_video_file
from app.services.video_db import find_similar_videos, save_video_result

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/detect", response_model=VideoDetectOut, status_code=status.HTTP_200_OK)
async def detect_video(
    request: Request,
    video: UploadFile = File(...),
    interval: int = Query(default=1, ge=1, description="Detection snapshot interval in seconds"),
):
    """
    Upload a video and receive:
    - Annotated video URL (bounding boxes + segmentation masks)
    - Per-second detected instrument list
    - LLM-generated music description
    - Top-3 similar previously-processed videos
    """
    if not video.content_type or not video.content_type.startswith("video/"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file must be a video",
        )

    # Save upload to a temp file
    upload_dir: Path = settings.UPLOAD_DIR
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = upload_dir / f"upload_{uuid.uuid4().hex}.mp4"

    try:
        contents = await video.read()
        temp_path.write_bytes(contents)

        final_video_path, time_detections = process_video_file(str(temp_path), interval=interval)
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        logger.exception("Video processing failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Video processing error: {exc}",
        )
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)

    # Build public URL for the processed video
    relative = Path(final_video_path).relative_to(Path(settings.STATIC_DIR))
    video_url = str(request.base_url) + f"static/{relative.as_posix()}"

    # Generate music description
    music_desc = generate_music_description(time_detections)

    # Persist to MongoDB
    inserted_id = save_video_result(
        video_url=video_url,
        local_path=final_video_path,
        time_detections=time_detections,
        music_description=music_desc,
    )

    # Find similar videos
    raw_similar = find_similar_videos(time_detections, exclude_id=inserted_id)

    similar_videos = [SimilarVideo(**s) for s in raw_similar]
    time_det_out = [TimeDetection(**t) for t in time_detections]

    return VideoDetectOut(
        video_url=video_url,
        time_detections=time_det_out,
        music_description=music_desc,
        similar_videos=similar_videos,
    )
