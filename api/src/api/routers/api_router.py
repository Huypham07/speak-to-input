from __future__ import annotations

from fastapi import APIRouter

from .endpoints.health_check import router as health_check_router

api_router = APIRouter()

api_router.include_router(health_check_router)
