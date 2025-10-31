from __future__ import annotations

from fastapi import APIRouter

from .auth import router as auth_router
from .bills import router as bills_router
from .endpoints.voice import voice_router
from .funds import router as funds_router
from .speech import router as speech_router
from .transfers import router as transfers_router

api_router = APIRouter(prefix='/api/v1')

# Authentication
api_router.include_router(auth_router)

# Speech-to-Input (Orchestration)
api_router.include_router(speech_router)

# Traditional API endpoints
api_router.include_router(transfers_router)
api_router.include_router(bills_router)
api_router.include_router(funds_router)

# Voice processing (ASR)
api_router.include_router(voice_router)
