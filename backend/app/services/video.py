"""
Video detection service.

Processes an uploaded video frame-by-frame using YOLO, annotates frames,
re-attaches original audio, generates a music description via OpenAI,
and persists results to MongoDB.
"""

import logging
import os
import uuid
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np

from app.core.config import settings
from app.services.ml import INSTRUMENT_DISPLAY_NAMES, generate_color_for_class

logger = logging.getLogger(__name__)


# ── Public entry point ────────────────────────────────────────────────────────

def process_video_file(
    input_path: str,
    interval: int = 1,
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Run YOLO detection on every frame, annotate, merge audio.

    Returns
    -------
    final_video_path : absolute path to processed video
    time_detections  : list of {time_second, detected_instruments}
    """
    from app.core.lifespan import state

    yolo = state.get("yolo")
    if yolo is None:
        raise RuntimeError("YOLO model is not loaded")

    predict_dir: Path = settings.PREDICT_DIR
    predict_dir.mkdir(parents=True, exist_ok=True)

    output_path = str(predict_dir / f"output_{uuid.uuid4().hex}.mp4")
    output_path, time_detections = _run_detection(yolo, input_path, output_path, interval)
    final_path = _merge_audio(input_path, output_path)
    return final_path, time_detections


def generate_music_description(time_detections: List[Dict[str, Any]]) -> str:
    """Call OpenAI to produce a 3-5 sentence description of the detected music."""
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        return "Music description unavailable (OpenAI API key not configured)"

    if not time_detections:
        return "No instruments detected in video"

    from openai import OpenAI

    client = OpenAI(api_key=api_key)

    lines = ["I have data on instruments appearing in the video over time:"]
    for entry in time_detections:
        t = entry["time_second"]
        raw = entry["detected_instruments"]
        display = [INSTRUMENT_DISPLAY_NAMES.get(code, code) for code in raw]
        if len(display) == 1:
            instr_text = display[0]
        elif len(display) == 2:
            instr_text = f"{display[0]} và {display[1]}"
        else:
            instr_text = ", ".join(display[:-1]) + " và " + display[-1]
        lines.append(f"- At second {t}: {instr_text}")

    lines.append(
        "Please write a short description (3-5 sentences) about the music style in this video based on the instruments detected."
    )
    prompt = "\n".join(lines)

    try:
        response = client.chat.completions.create(
            model=settings.LLM_MODEL,
            messages=[
                {"role": "system", "content": "You are a Vietnamese music expert."},
                {"role": "user", "content": prompt},
            ],
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=500,
        )
        return response.choices[0].message.content.strip()
    except Exception as exc:
        logger.error("LLM description error: %s", exc)
        return "Unable to generate music description"


# ── Internal helpers ──────────────────────────────────────────────────────────

def _run_detection(
    yolo,
    input_path: str,
    output_path: str,
    interval: int,
) -> Tuple[str, List[Dict[str, Any]]]:
    cap = cv2.VideoCapture(input_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {input_path}")

    fw = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    fh = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(output_path, fourcc, fps, (fw, fh))
    if not writer.isOpened():
        raise RuntimeError("Cannot open VideoWriter")

    results_map: Dict[float, List[str]] = {}
    next_time = 0.0
    frame_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        current_time = frame_count / fps

        try:
            detection = yolo.predict(source=frame)[0]
        except Exception as exc:
            logger.warning("YOLO prediction error on frame %d: %s", frame_count, exc)
            detection = None

        if current_time >= next_time and detection and detection.boxes is not None:
            class_names = list({yolo.names[int(b.cls[0])] for b in detection.boxes})
            if class_names:
                results_map[next_time] = class_names
            next_time += interval

        annotated = _annotate_frame(frame.copy(), detection) if detection else frame
        writer.write(annotated)
        frame_count += 1

        if frame_count % 100 == 0:
            logger.info("Processed %d/%d frames (%.1f%%)", frame_count, total, frame_count / total * 100)

    cap.release()
    writer.release()

    time_detections = [
        {"time_second": t, "detected_instruments": sorted(instruments)}
        for t, instruments in sorted(results_map.items())
    ]
    return output_path, time_detections


def _annotate_frame(frame: np.ndarray, results) -> np.ndarray:
    if results.boxes is None or results.masks is None:
        return frame

    boxes = results.boxes.xyxy.cpu().numpy()
    confs = results.boxes.conf.cpu().numpy()
    class_ids = results.boxes.cls.cpu().numpy().astype(int)
    masks = results.masks.data.cpu().numpy()
    class_names = results.names

    overlay = frame.copy()
    alpha = 0.5

    for box, conf, cls_id, mask in zip(boxes, confs, class_ids, masks):
        mask_resized = cv2.resize(mask, (frame.shape[1], frame.shape[0]))
        binary_mask = (mask_resized > 0.5).astype(np.uint8)
        color = generate_color_for_class(cls_id)

        colored = np.zeros_like(frame)
        colored[:] = color
        overlay[binary_mask == 1] = colored[binary_mask == 1]

        x1, y1, x2, y2 = map(int, box)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)

        label = f"{class_names[cls_id]} {conf:.2f}"
        (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 1)
        cv2.rectangle(frame, (x1, y1 - lh - 10), (x1 + lw, y1), color, -1)
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 0), 1)

    frame = cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0)
    return frame


def _merge_audio(original_path: str, processed_path: str) -> str:
    """Mux audio from *original_path* into *processed_path*."""
    try:
        from moviepy import AudioFileClip, VideoFileClip

        final_path = processed_path.replace(".mp4", f"_{uuid.uuid4().hex}_audio.mp4")
        audio = AudioFileClip(original_path)
        video = VideoFileClip(processed_path)
        final = video.with_audio(audio)
        final.write_videofile(final_path, codec="libx264", audio_codec="aac", fps=video.fps)
        audio.close()
        video.close()
        final.close()
        os.remove(processed_path)
        return final_path
    except Exception as exc:
        logger.warning("Audio merge failed (%s) – returning video without audio", exc)
        return processed_path
