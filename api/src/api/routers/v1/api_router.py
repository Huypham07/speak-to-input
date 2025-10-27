from __future__ import annotations

from fastapi import APIRouter

from .endpoints.voice import voice_router

api_router = APIRouter(prefix='/api/v1')

api_router.include_router(voice_router)
