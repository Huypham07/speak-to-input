from __future__ import annotations

from application.services import IntentUnderstandingService
from application.services import VoiceService
from application.services.orchestration_service import OrchestrationService
from domain.plugins.registry import get_plugin_registry
from fastapi import Depends
from fastapi import Request
from infra.db.repositories import AccountRepository
from infra.db.repositories import BillRepository
from infra.db.repositories import ContactRepository
from infra.db.repositories import SavingsFundRepository
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
    """Create Intent Understanding Service with plugin registry"""
    plugin_registry = get_plugin_registry()
    return IntentUnderstandingService(
        settings=settings,
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
