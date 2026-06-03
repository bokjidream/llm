import logging

from fastapi import FastAPI

from app.config import settings
from app.middleware import LoggingMiddleware
from app.routers import chat_router, health_router, models_router

logging.basicConfig(
    level=settings.app_log_level.upper(),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(
    title="Local LLM API",
    description="OpenAI-compatible API server for local LLM (Ollama / llama.cpp)",
    version="0.1.0",
)

app.add_middleware(LoggingMiddleware)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(models_router)
