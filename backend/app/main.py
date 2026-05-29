from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes import detection, instruments, ontology, rag, video
from app.core.config import settings
from app.core.lifespan import load_models
from app.core.logging import setup_logging


setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await load_models()
    yield


app = FastAPI(
    title="ViTIP API",
    description="Vietnamese Traditional Instrument Preservation – AI Backend",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=settings.STATIC_DIR, html=False), name="static")

app.include_router(instruments.router, prefix="/api/instruments", tags=["Instruments"])
app.include_router(detection.router, prefix="/api/detect", tags=["Image Detection"])
app.include_router(ontology.router, prefix="/api/ontology", tags=["Ontology"])
app.include_router(rag.router, prefix="/api/chatbot", tags=["RAG Chatbot"])
app.include_router(video.router, prefix="/api/video", tags=["Video Detection"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "version": app.version}
