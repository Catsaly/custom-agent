"""FastAPI server — main application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from app.api.routes import chat, files, github, images

app = FastAPI(
    title="Milli Yapay Zeka",
    description="Yerli AI Kodlama Platformu — Claude, Gemini & GLM ile güçlendirilmiş",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routes
app.include_router(chat.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(github.router, prefix="/api")
app.include_router(images.router, prefix="/api")

# Static files
static_path = Path(__file__).parent.parent.parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")


@app.get("/")
async def root():
    return {
        "name": "Milli Yapay Zeka",
        "version": "1.0.0",
        "docs": "/docs",
        "models": ["claude", "gemini", "glm"],
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
