from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=['Health'])

# Health check endpoint


@router.get('/health')
async def health_check():
    """Health check endpoint."""
    return {'status': 'healthy', 'service': 'workflow-service'}
