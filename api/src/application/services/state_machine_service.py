from __future__ import annotations

from shared.logging import get_logger
from shared.settings import Settings

logger = get_logger(__name__)


class StateMachineService:
    """
    Service for managing business state machine.
    Handles state transitions and context management across multiple requests.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
