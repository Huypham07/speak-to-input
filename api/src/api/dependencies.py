from __future__ import annotations

from api.helpers.audio_stream_accumulator import AudioStreamAccumulator
from application.services import IntentUnderstandingService
from application.services import VoiceService
from application.services.orchestration_service import OrchestrationService
from domain.plugins.registry import get_plugin_registry
from fastapi import Depends
from fastapi import Request
from fastapi import WebSocket
from infra.db.repositories import AccountRepository
from infra.db.repositories import BillRepository
from infra.db.repositories import ContactRepository
from infra.db.repositories import SavingsFundRepository
from infra.db.repositories import TransactionRepository
from infra.db.repositories import UserRepository
from infra.infra_manager import InfrastructureManager
from infra.llm.llm_service import LLMService
from shared.settings import Settings


# ========== Infrastructure Dependencies ==========

def get_infra_manager(request: Request) -> InfrastructureManager:
    """Get infrastructure manager from app state"""
    return request.app.state.infra_manager


def get_infra_manager_ws(websocket: WebSocket) -> InfrastructureManager:
    """Get infrastructure manager from app state for WebSocket connections"""
    return websocket.app.state.infra_manager


def get_settings(request: Request) -> Settings:
    """Get settings from app state"""
    return request.app.state.settings


def get_settings_ws(websocket: WebSocket) -> Settings:
    """Get settings from app state for WebSocket connections"""
    return websocket.app.state.settings


# ========== Repository Dependencies ==========


def get_user_repository(
    infra_manager: InfrastructureManager = Depends(get_infra_manager),
) -> UserRepository:
    """Get User Repository"""
    return infra_manager.user_repository


def get_user_repository_ws(
    infra_manager: InfrastructureManager = Depends(get_infra_manager_ws),
) -> UserRepository:
    """Get User Repository for WebSocket"""
    return infra_manager.user_repository


def get_account_repository(
    infra_manager: InfrastructureManager = Depends(get_infra_manager),
) -> AccountRepository:
    """Get Account Repository"""
    return infra_manager.account_repository


def get_account_repository_ws(
    infra_manager: InfrastructureManager = Depends(get_infra_manager_ws),
) -> AccountRepository:
    """Get Account Repository for WebSocket"""
    return infra_manager.account_repository


def get_contact_repository(
    infra_manager: InfrastructureManager = Depends(get_infra_manager),
) -> ContactRepository:
    """Get Contact Repository"""
    return infra_manager.contact_repository


def get_contact_repository_ws(
    infra_manager: InfrastructureManager = Depends(get_infra_manager_ws),
) -> ContactRepository:
    """Get Contact Repository for WebSocket"""
    return infra_manager.contact_repository


def get_transaction_repository(
    infra_manager: InfrastructureManager = Depends(get_infra_manager),
) -> TransactionRepository:
    """Get Transaction Repository"""
    return infra_manager.transaction_repository


def get_transaction_repository_ws(
    infra_manager: InfrastructureManager = Depends(get_infra_manager_ws),
) -> TransactionRepository:
    """Get Transaction Repository for WebSocket"""
    return infra_manager.transaction_repository


def get_bill_repository(
    infra_manager: InfrastructureManager = Depends(get_infra_manager),
) -> BillRepository:
    """Get Bill Repository"""
    return infra_manager.bill_repository


def get_bill_repository_ws(
    infra_manager: InfrastructureManager = Depends(get_infra_manager_ws),
) -> BillRepository:
    """Get Bill Repository for WebSocket"""
    return infra_manager.bill_repository


def get_fund_repository(
    infra_manager: InfrastructureManager = Depends(get_infra_manager),
) -> SavingsFundRepository:
    """Get Savings Fund Repository"""
    return infra_manager.fund_repository


def get_fund_repository_ws(
    infra_manager: InfrastructureManager = Depends(get_infra_manager_ws),
) -> SavingsFundRepository:
    """Get Savings Fund Repository for WebSocket"""
    return infra_manager.fund_repository


# ========== Service Dependencies ==========

def get_llm_service(
    settings: Settings = Depends(get_settings),
) -> LLMService:
    """Create LLM Service instance"""
    return LLMService(settings)


def get_llm_service_ws(
    settings: Settings = Depends(get_settings_ws),
) -> LLMService:
    """Create LLM Service instance for WebSocket"""
    return LLMService(settings)


def get_voice_service(
    settings: Settings = Depends(get_settings),
    llm_service: LLMService = Depends(get_llm_service),
) -> VoiceService:
    """Create VoiceService instance with LLM dependency"""
    return VoiceService(settings, llm_service)


def get_voice_service_ws(
    settings: Settings = Depends(get_settings_ws),
    llm_service: LLMService = Depends(get_llm_service_ws),
) -> VoiceService:
    """Create VoiceService instance for WebSocket with LLM dependency"""
    return VoiceService(settings, llm_service)


def get_intent_service(
    settings: Settings = Depends(get_settings),
    llm_service: LLMService = Depends(get_llm_service),
) -> IntentUnderstandingService:
    """Create Intent Understanding Service with plugin registry"""
    plugin_registry = get_plugin_registry()
    return IntentUnderstandingService(
        settings=settings,
        llm_service=llm_service,
        plugin_registry=plugin_registry,
    )


def get_intent_service_ws(
    settings: Settings = Depends(get_settings_ws),
    llm_service: LLMService = Depends(get_llm_service_ws),
) -> IntentUnderstandingService:
    """Create Intent Understanding Service with plugin registry for WebSocket"""
    plugin_registry = get_plugin_registry()
    return IntentUnderstandingService(
        settings=settings,
        llm_service=llm_service,
        plugin_registry=plugin_registry,
    )


def get_orchestration_service(
    settings: Settings = Depends(get_settings),
    transaction_repository: TransactionRepository = Depends(get_transaction_repository),
    account_repository: AccountRepository = Depends(get_account_repository),
    contact_repository: ContactRepository = Depends(get_contact_repository),
    bill_repository: BillRepository = Depends(get_bill_repository),
    fund_repository: SavingsFundRepository = Depends(get_fund_repository),
) -> OrchestrationService:
    """Create Orchestration Service with all dependencies"""
    return OrchestrationService(
        settings=settings,
        transaction_repository=transaction_repository,
        account_repository=account_repository,
        contact_repository=contact_repository,
        bill_repository=bill_repository,
        fund_repository=fund_repository,
    )


def get_orchestration_service_ws(
    settings: Settings = Depends(get_settings_ws),
    transaction_repository: TransactionRepository = Depends(get_transaction_repository_ws),
    account_repository: AccountRepository = Depends(get_account_repository_ws),
    contact_repository: ContactRepository = Depends(get_contact_repository_ws),
    bill_repository: BillRepository = Depends(get_bill_repository_ws),
    fund_repository: SavingsFundRepository = Depends(get_fund_repository_ws),
) -> OrchestrationService:
    """Create Orchestration Service with all dependencies for WebSocket"""
    return OrchestrationService(
        settings=settings,
        transaction_repository=transaction_repository,
        account_repository=account_repository,
        contact_repository=contact_repository,
        bill_repository=bill_repository,
        fund_repository=fund_repository,
    )


# ========== Audio Stream Accumulator ==========

def get_audio_stream_accumulator(
    settings: Settings = Depends(get_settings_ws),
    voice_service: VoiceService = Depends(get_voice_service_ws),
) -> AudioStreamAccumulator:
    """
    Create AudioStreamAccumulator instance for WebSocket voice streaming.

    This accumulator handles concurrent audio chunk processing with:
    - Safe buffer management
    - Configurable segment duration and overlap
    - Concurrent task processing with semaphore
    """
    return AudioStreamAccumulator(
        settings=settings,
        voice_service=voice_service,
        target_seconds=10.0,  # Process every 10 seconds of audio
        overlap_seconds=2.0,  # 2 seconds overlap for better continuity
        max_overlap=10,  # Maximum overlap characters for merging
        min_overlap=3,   # Minimum overlap characters for merging
        max_concurrent_tasks=3,  # Limit concurrent transcription tasks
    )
