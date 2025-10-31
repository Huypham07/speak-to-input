from __future__ import annotations

from application.services import IntentUnderstandingService
from application.services import StateMachineService
from application.services import VoiceService
from application.services.orchestration_service import OrchestrationService
from fastapi import Depends
from fastapi import Request
from infra.db.repositories import AccountRepository
from infra.db.repositories import BillRepository
from infra.db.repositories import ContactRepository
from infra.db.repositories import SavingsFundRepository
from infra.db.repositories import SessionRepository
from infra.db.repositories import TransactionRepository
from infra.db.repositories import UserRepository
from infra.infra_manager import InfrastructureManager
from shared.settings import Settings


# ========== Infrastructure Dependencies ==========

def get_infra_manager(request: Request) -> InfrastructureManager:
    """Get infrastructure manager from app state"""
    return request.app.state.infra_manager


def get_settings(request: Request) -> Settings:
    """Get settings from app state"""
    return request.app.state.settings


# ========== Repository Dependencies ==========

def get_session_repository(
    infra_manager: InfrastructureManager = Depends(get_infra_manager),
) -> SessionRepository:
    """Get Session Repository"""
    return infra_manager.session_repository


def get_user_repository(
    infra_manager: InfrastructureManager = Depends(get_infra_manager),
) -> UserRepository:
    """Get User Repository"""
    return infra_manager.user_repository


def get_account_repository(
    infra_manager: InfrastructureManager = Depends(get_infra_manager),
) -> AccountRepository:
    """Get Account Repository"""
    return infra_manager.account_repository


def get_contact_repository(
    infra_manager: InfrastructureManager = Depends(get_infra_manager),
) -> ContactRepository:
    """Get Contact Repository"""
    return infra_manager.contact_repository


def get_transaction_repository(
    infra_manager: InfrastructureManager = Depends(get_infra_manager),
) -> TransactionRepository:
    """Get Transaction Repository"""
    return infra_manager.transaction_repository


def get_bill_repository(
    infra_manager: InfrastructureManager = Depends(get_infra_manager),
) -> BillRepository:
    """Get Bill Repository"""
    return infra_manager.bill_repository


def get_fund_repository(
    infra_manager: InfrastructureManager = Depends(get_infra_manager),
) -> SavingsFundRepository:
    """Get Savings Fund Repository"""
    return infra_manager.fund_repository


# ========== Service Dependencies ==========

def get_voice_service(
    settings: Settings = Depends(get_settings),
) -> VoiceService:
    """Create VoiceService instance"""
    return VoiceService(settings)


def get_intent_service(
    settings: Settings = Depends(get_settings),
) -> IntentUnderstandingService:
    """Create Intent Understanding Service"""
    return IntentUnderstandingService(settings)


def get_state_machine_service(
    settings: Settings = Depends(get_settings),
) -> StateMachineService:
    """Create State Machine Service"""
    return StateMachineService(settings)


def get_orchestration_service(
    settings: Settings = Depends(get_settings),
    session_repository: SessionRepository = Depends(get_session_repository),
    intent_service: IntentUnderstandingService = Depends(get_intent_service),
    state_machine_service: StateMachineService = Depends(get_state_machine_service),
    transaction_repository: TransactionRepository = Depends(get_transaction_repository),
    account_repository: AccountRepository = Depends(get_account_repository),
    contact_repository: ContactRepository = Depends(get_contact_repository),
    bill_repository: BillRepository = Depends(get_bill_repository),
    fund_repository: SavingsFundRepository = Depends(get_fund_repository),
) -> OrchestrationService:
    """Create Orchestration Service with all dependencies"""
    return OrchestrationService(
        settings=settings,
        session_repository=session_repository,
        intent_service=intent_service,
        state_machine_service=state_machine_service,
        transaction_repository=transaction_repository,
        account_repository=account_repository,
        contact_repository=contact_repository,
        bill_repository=bill_repository,
        fund_repository=fund_repository,
    )
