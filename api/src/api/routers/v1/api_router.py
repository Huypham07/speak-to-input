from __future__ import annotations

from fastapi import APIRouter

from .endpoints.accounts import router as accounts_router
from .endpoints.auth import router as auth_router
from .endpoints.bills import router as bills_router
from .endpoints.funds import router as funds_router
from .endpoints.transfers import router as transfers_router

api_router = APIRouter(prefix='/api/v1')

# Authentication
api_router.include_router(auth_router)

# Traditional API endpoints
api_router.include_router(accounts_router)
api_router.include_router(transfers_router)
api_router.include_router(bills_router)
api_router.include_router(funds_router)
