"""
app/main.py
FastAPI application factory for Nova-AI.
This module creates and configures the FastAPI instance.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import api_router

app = FastAPI(
    title="Nova-AI",
    description="Production-grade multimodal intelligence platform — text, image, voice, and document AI.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount v1 API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "Nova-AI",
        "message": "Nova-AI API is running smoothly",
    }
