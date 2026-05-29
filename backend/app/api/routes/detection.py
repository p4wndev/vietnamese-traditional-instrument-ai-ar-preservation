import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, status

from app.core.config import settings
from app.schemas.schemas import ImageDetectOut
from app.services.detection import detect_and_classify

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/image", response_model=ImageDetectOut, status_code=status.HTTP_200_OK)
async def detect_image(image_input: UploadFile = File(...)):
    """
    Upload an image and receive:
    - ``output`` – relative paths to cropped detected-object images
    - ``classifications`` – predicted instrument class for each crop
    """
    if not image_input.content_type or not image_input.content_type.startswith("image/"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Uploaded file must be an image",
        )

    # Persist upload temporarily
    upload_dir: Path = settings.UPLOAD_DIR
    upload_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(image_input.filename or "upload.jpg").suffix or ".jpg"
    temp_path = upload_dir / f"{uuid.uuid4().hex}{suffix}"

    try:
        contents = await image_input.read()
        temp_path.write_bytes(contents)

        crop_paths, labels = detect_and_classify(str(temp_path))
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    except Exception as exc:
        logger.exception("Detection failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Detection error: {exc}",
        )
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)

    return ImageDetectOut(output=crop_paths, classifications=labels)
