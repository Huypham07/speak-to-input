from __future__ import annotations

from contextlib import asynccontextmanager

import uvicorn
from api.routers import api_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from infra import InfrastructureManager
from shared.logging import get_logger
from shared.logging import setup_logging
from shared.utils import get_settings

setup_logging(json_logs=False, log_level='INFO')
logger = get_logger('api')


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for the FastAPI application."""
    logger.info('Initializing Speak To Input Service...')

    # Initialize settings
    settings = get_settings()

    # Initialize infrastructure manager
    infra_manager = InfrastructureManager(settings)

    try:
        # Initialize all infrastructure connections
        await infra_manager.initialize()

        # Store infrastructure manager in app state for access in routes
        app.state.infrastructure = infra_manager
        app.state.settings = settings

        logger.info('Speak To Input Service initialized successfully')

    except Exception as e:
        logger.error(f'Failed to initialize infrastructure: {e}')
        await infra_manager.cleanup()
        raise

    yield

    # Cleanup on shutdown
    logger.info('Shutting down Speak To Input Service...')

    # Then cleanup infrastructure
    await infra_manager.cleanup()
    logger.info('Speak To Input Service shutdown completed')


app = FastAPI(
    title='Speak To Input Service',
    description='Service for processing and managing speak to input workflows.',
    version='1.0.0',
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

# Include API routers
app.include_router(api_router)


@app.get('/')
def root():
    return {
        'status': 'running',
        'service': 'Speak To Input Service',
        'description': 'Service for processing and managing speak to input workflows.',
        'version': '1.0.0',
    }


if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        host='0.0.0.0',
        port=8000,
        reload=True,
    )
