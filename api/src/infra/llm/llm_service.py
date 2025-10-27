from __future__ import annotations

from shared.logging import get_logger
from shared.settings import Settings

logger = get_logger(__name__)


class LLMService:
    """Service to interact with LLM"""

    def __init__(self, settings: Settings):
        self.settings = settings
