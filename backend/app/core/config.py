import os
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # ── General ──────────────────────────────────────────────────────────────
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: List[str] = [
        "http://localhost:3001",
        "https://vietnamese-traditional-instrument-a.vercel.app",
    ]

    # ── Paths ─────────────────────────────────────────────────────────────────
    MODEL_DIR: Path = BASE_DIR / "models"
    STATIC_DIR: str = str(BASE_DIR / "static")
    UPLOAD_DIR: Path = BASE_DIR / "static" / "uploads"
    PREDICT_DIR: Path = BASE_DIR / "static" / "predict"

    # ── ML model files ────────────────────────────────────────────────────────
    YOLO_MODEL_PATH: Path = BASE_DIR / "models" / "model_yolo" / "best.pt"
    LENET_WEIGHTS_PATH: Path = BASE_DIR / "models" / "model_lenet" / "lenet5_model_300.h5"
    ONTOLOGY_PATH: Path = BASE_DIR / "models" / "ontology" / "nhaccu.owl"
    FAISS_DB_PATH: Path = BASE_DIR / "models" / "RAG" / "vectorstores" / "db_faiss_pdf"

    # ── External services ─────────────────────────────────────────────────────
    OPENAI_API_KEY: str = ""
    MONGODB_URI: str = "mongodb://localhost:27017/"
    MONGODB_DB_NAME: str = "instrument_detection_db"

    # ── LLM settings ──────────────────────────────────────────────────────────
    LLM_MODEL: str = "gpt-3.5-turbo"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 512

    # ── Embedding model ───────────────────────────────────────────────────────
    EMBEDDING_MODEL_NAME: str = "BAAI/bge-m3"

    # ── LeNet / YOLO ──────────────────────────────────────────────────────────
    LENET_INPUT_SIZE: int = 64
    LENET_NUM_CLASSES: int = 14


settings = Settings()

# Ensure directories exist at import time
for _path in (settings.STATIC_DIR, settings.UPLOAD_DIR, settings.PREDICT_DIR):
    Path(_path).mkdir(parents=True, exist_ok=True)
