from __future__ import annotations

from application.services import IntentUnderstandingService
from application.services import StateMachineService
from application.services import VoiceService
from application.use_cases import ProcessVoiceUseCase
from fastapi import Depends
from fastapi import Request
from infra.infra_manager import InfrastructureManager
from shared.settings import Settings


# ========== Infrastructure Dependencies ==========

def get_infra_manager(request: Request) -> InfrastructureManager:
    """Get infrastructure manager from app state"""
    return request.app.state.infra_manager


def get_settings(request: Request) -> Settings:
    """Get settings from app state"""
    return request.app.state.settings


# ========== Service Dependencies (Per-Request) ==========

def get_voice_service(
    settings: Settings = Depends(get_settings),
) -> VoiceService:
    """
    Create VoiceService instance.
    """
    return VoiceService(settings)


def get_intent_service(
    settings: Settings = Depends(get_settings),
) -> IntentUnderstandingService:
    """
    Create IntentUnderstandingService instance.
    """
    return IntentUnderstandingService(settings)


def get_state_machine_service(
    settings: Settings = Depends(get_settings),
) -> StateMachineService:
    """
    Create StateMachineService instance.
    """
    return StateMachineService(settings)


# ========== Use Case Dependencies ==========

def get_process_voice_use_case(
    settings: Settings = Depends(get_settings),
    voice_service: VoiceService = Depends(get_voice_service),
    intent_service: IntentUnderstandingService = Depends(get_intent_service),
    state_machine_service: StateMachineService = Depends(get_state_machine_service),
) -> ProcessVoiceUseCase:
    """
    Create ProcessVoiceUseCase instance.
    """
    return ProcessVoiceUseCase(
        settings=settings,
        voice_service=voice_service,
        intent_service=intent_service,
        state_machine_service=state_machine_service,
    )
