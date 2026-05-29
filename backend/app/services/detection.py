"""
Image detection service.

Runs YOLO segmentation on an uploaded image, crops each detected object,
then classifies every crop with the LeNet-5 model.
"""

import logging
import os
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

from app.core.config import settings
from app.services.ml import (
    INSTRUMENT_CATEGORIES,
    preprocess_for_lenet,
)

logger = logging.getLogger(__name__)


def detect_and_classify(image_path: str) -> Tuple[List[str], List[str]]:
    """
    Run YOLO + LeNet on *image_path*.

    Returns
    -------
    crop_paths : list of relative URLs  (e.g. "predict/image_000.jpg")
    labels     : class name for each crop
    """
    from app.core.lifespan import state

    yolo = state.get("yolo")
    lenet = state.get("lenet")

    if yolo is None:
        raise RuntimeError("YOLO model is not loaded")

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    orig_h, orig_w = img.shape[:2]
    results = yolo.predict(source=img)[0]

    if results.masks is None:
        logger.info("No masks detected in image")
        return [], []

    masks = results.masks.data.cpu().numpy()
    classes = results.boxes.cls.cpu().numpy().astype(int)

    predict_dir: Path = settings.PREDICT_DIR
    predict_dir.mkdir(parents=True, exist_ok=True)

    crops: List[np.ndarray] = []
    crop_paths: List[str] = []

    for i, (mask, cls_id) in enumerate(zip(masks, classes)):
        mask_resized = cv2.resize(mask, (orig_w, orig_h), interpolation=cv2.INTER_NEAREST)
        binary_mask = (mask_resized * 255).astype(np.uint8)
        masked = cv2.bitwise_and(img, img, mask=binary_mask)

        ys, xs = np.where(binary_mask > 0)
        if len(ys) == 0 or len(xs) == 0:
            continue

        y1, y2 = ys.min(), ys.max()
        x1, x2 = xs.min(), xs.max()
        crop = masked[y1 : y2 + 1, x1 : x2 + 1]

        filename = f"image_{i:03d}.jpg"
        save_path = predict_dir / filename
        cv2.imwrite(str(save_path), crop)

        crops.append(crop)
        crop_paths.append(f"predict/{filename}")

    if lenet is None:
        logger.warning("LeNet not loaded – skipping classification")
        return crop_paths, ["unknown"] * len(crop_paths)

    labels: List[str] = []
    for crop in crops:
        label = _classify_crop(lenet, crop)
        labels.append(label)

    return crop_paths, labels


def _classify_crop(lenet, crop: np.ndarray) -> str:
    batch = preprocess_for_lenet(crop, size=settings.LENET_INPUT_SIZE)
    predictions = lenet.predict(batch)
    class_idx = int(np.argmax(predictions, axis=1)[0])
    return INSTRUMENT_CATEGORIES[class_idx]
