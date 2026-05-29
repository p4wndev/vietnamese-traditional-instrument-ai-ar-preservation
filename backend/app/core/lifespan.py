"""
Startup model loading.

All heavy objects (YOLO, LeNet, FAISS, Ontology) are loaded once during
application lifespan and stored in the module-level ``state`` dict so
every request handler can reuse them without re-loading from disk.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Shared state – populated by load_models()
state: Dict[str, Any] = {
    "yolo": None,
    "lenet": None,
    "ontology": None,
    "rag_chain": None,
}


async def load_models() -> None:
    """Load ML models into ``state`` at application startup."""
    from app.core.config import settings

    _load_yolo(settings)
    _load_lenet(settings)
    _load_ontology(settings)
    _load_rag(settings)


# ── Individual loaders ────────────────────────────────────────────────────────

def _load_yolo(settings) -> None:
    path: Path = settings.YOLO_MODEL_PATH
    if not path.exists():
        logger.warning("YOLO model not found at %s – image/video detection disabled", path)
        return
    try:
        from ultralytics import YOLO
        state["yolo"] = YOLO(str(path))
        logger.info("YOLO model loaded from %s", path)
    except Exception as exc:
        logger.error("Failed to load YOLO model: %s", exc)


def _load_lenet(settings) -> None:
    path: Path = settings.LENET_WEIGHTS_PATH
    if not path.exists():
        logger.warning("LeNet weights not found at %s – classification disabled", path)
        return
    try:
        import tensorflow as tf
        from app.services.ml import build_lenet_model

        model = build_lenet_model(
            input_shape=(settings.LENET_INPUT_SIZE, settings.LENET_INPUT_SIZE, 3),
            num_classes=settings.LENET_NUM_CLASSES,
        )
        model.load_weights(str(path))
        state["lenet"] = model
        logger.info("LeNet model loaded from %s", path)
    except Exception as exc:
        logger.error("Failed to load LeNet model: %s", exc)


def _load_ontology(settings) -> None:
    path: Path = settings.ONTOLOGY_PATH
    if not path.exists():
        logger.warning("Ontology file not found at %s – ontology queries disabled", path)
        return
    try:
        from owlready2 import get_ontology

        state["ontology"] = get_ontology(path.as_uri()).load()
        logger.info("Ontology loaded from %s", path)
    except Exception as exc:
        logger.error("Failed to load ontology: %s", exc)


def _load_rag(settings) -> None:
    faiss_path: Path = settings.FAISS_DB_PATH
    if not faiss_path.exists():
        logger.warning("FAISS DB not found at %s – RAG chatbot disabled", faiss_path)
        return
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set – RAG chatbot disabled")
        return
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        from langchain_openai import ChatOpenAI
        from langchain.chains import RetrievalQA
        from langchain.prompts import PromptTemplate
        from langchain_community.vectorstores import FAISS

        embeddings = HuggingFaceEmbeddings(model_name=settings.EMBEDDING_MODEL_NAME)
        db = FAISS.load_local(
            str(faiss_path), embeddings, allow_dangerous_deserialization=True
        )

        template = (
            "<|im_start|>system\n"
            "Use the following information to answer the question in detail.\n"
            "If you do not know the answer, say **unknown**.\n"
            "Format your response clearly with bold headings and bullet points where appropriate.\n"
            "{context}\n"
            "<|im_end|>\n\n"
            "<|im_start|>user\n{question}\n<|im_end|>\n"
            "<|im_start|>assistant\n"
        )
        prompt = PromptTemplate(template=template, input_variables=["context", "question"])

        llm = ChatOpenAI(
            model=settings.LLM_MODEL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            top_p=0.9,
            frequency_penalty=0.5,
            presence_penalty=0.6,
        )

        state["rag_chain"] = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=db.as_retriever(search_kwargs={"k": 5}),
            return_source_documents=True,
            chain_type_kwargs={"prompt": prompt},
        )
        logger.info("RAG chain ready (FAISS + %s)", settings.LLM_MODEL)
    except Exception as exc:
        logger.error("Failed to load RAG chain: %s", exc)
