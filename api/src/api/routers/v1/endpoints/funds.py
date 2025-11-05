from __future__ import annotations

from datetime import datetime
from typing import Any
from typing import Dict
from typing import List

from api.dependencies import get_account_repository
from api.dependencies import get_fund_repository
from api.dependencies import get_transaction_repository
from api.helpers.dependencies import get_current_user
from api.helpers.jwt_auth import TokenData
from api.schemas import CreateFundRequest
from api.schemas import FundDepositRequest
from api.schemas import FundResponse
from api.schemas import FundWithdrawRequest
from application.use_cases import execute_plugin
from domain.value_objects import IntentType
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from infra.db.repositories import AccountRepository
from infra.db.repositories import SavingsFundRepository
from infra.db.repositories import TransactionRepository

router = APIRouter(prefix='/funds', tags=['Savings Funds'])


@router.post('', response_model=FundResponse, status_code=status.HTTP_201_CREATED)
async def create_fund(
    request: CreateFundRequest,
    current_user: TokenData = Depends(get_current_user),
    fund_repo: SavingsFundRepository = Depends(get_fund_repository),
    account_repo: AccountRepository = Depends(get_account_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
):
    """
    Create a new savings fund (Traditional API).
    Requires authentication.
    """
    try:
        # Execute via plugin (same logic as speech)
        result = await execute_plugin.execute(
            intent_type=IntentType.CREATE_FUND.value,
            parameters={
                'fund_name': request.fund_name,
                'target_amount': float(request.target_amount),
                'target_date': request.target_date,
                'initial_amount': float(request.initial_amount),
                'monthly_contribution': float(request.monthly_contribution),
                'category': request.category or 'other',
                'auto_transfer': request.auto_transfer,
                'notes': request.notes or '',
            },
            context={
                'user_id': int(current_user.user_id),
                'fund_repository': fund_repo,
                'account_repository': account_repo,
                'transaction_repository': transaction_repo,
            },
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message,
            )

        # Extract fund data from result
        # Plugin returns 'fund_id' in data, but model uses 'id'
        fund_id = result.data.get('fund_id') or result.data.get('id')
        if not fund_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Fund creation succeeded but fund ID not returned',
            )

        # Get fund details
        fund = await fund_repo.read_by_id(fund_id)
        if not fund:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Fund creation succeeded but fund not found',
            )

        # Calculate progress
        progress_percentage = (
            float(fund.current_amount / fund.target_amount * 100)
            if fund.target_amount > 0
            else 0
        )

        return FundResponse(
            id=fund.id,
            fund_name=fund.fund_name,
            target_amount=float(fund.target_amount),
            current_amount=float(fund.current_amount),
            target_date=fund.target_date.isoformat() if fund.target_date else request.target_date,
            category=fund.category,
            monthly_contribution=float(fund.monthly_contribution),
            progress_percentage=round(progress_percentage, 2),
            status=fund.status,
            created_at=fund.created_at.isoformat() if fund.created_at else datetime.now().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Fund creation failed: {str(e)}',
        )


@router.get('', response_model=List[FundResponse])
async def list_funds(
    current_user: TokenData = Depends(get_current_user),
    status_filter: str | None = None,
    fund_repo: SavingsFundRepository = Depends(get_fund_repository),
):
    """
    List all savings funds for current user (Traditional API).
    Requires authentication.
    """
    try:
        funds = await fund_repo.get_by_user_id(
            user_id=int(current_user.user_id),
            status=status_filter,
        )

        return [
            FundResponse(
                id=fund.id,
                fund_name=fund.fund_name,
                target_amount=float(fund.target_amount),
                current_amount=float(fund.current_amount),
                target_date=fund.target_date.isoformat() if fund.target_date else '',
                category=fund.category,
                monthly_contribution=float(fund.monthly_contribution),
                progress_percentage=round(
                    float(fund.current_amount / fund.target_amount * 100) if fund.target_amount > 0 else 0,
                    2,
                ),
                status=fund.status,
                created_at=fund.created_at.isoformat() if fund.created_at else datetime.now().isoformat(),
            )
            for fund in funds
        ]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to list funds: {str(e)}',
        )


@router.get('/{fund_id}', response_model=FundResponse)
async def get_fund(
    fund_id: int,
    current_user: TokenData = Depends(get_current_user),
    fund_repo: SavingsFundRepository = Depends(get_fund_repository),
):
    """
    Get fund details (Traditional API).
    Requires authentication.
    """
    try:
        fund = await fund_repo.read_by_id(fund_id)

        if not fund:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Fund not found',
            )

        # Check ownership
        if fund.user_id != int(current_user.user_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail='Access denied',
            )

        # Calculate progress
        progress_percentage = (
            round(float(fund.current_amount / fund.target_amount * 100), 2)
            if fund.target_amount > 0
            else 0
        )

        return FundResponse(
            id=fund.id,
            fund_name=fund.fund_name,
            target_amount=float(fund.target_amount),
            current_amount=float(fund.current_amount),
            target_date=fund.target_date.isoformat() if fund.target_date else '',
            category=fund.category,
            monthly_contribution=float(fund.monthly_contribution),
            progress_percentage=progress_percentage,
            status=fund.status,
            created_at=fund.created_at.isoformat() if fund.created_at else datetime.now().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to get fund: {str(e)}',
        )


@router.post('/{fund_id}/deposit')
async def deposit_to_fund(
    fund_id: int,
    request: FundDepositRequest,
    current_user: TokenData = Depends(get_current_user),
    fund_repo: SavingsFundRepository = Depends(get_fund_repository),
    account_repo: AccountRepository = Depends(get_account_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
):
    """
    Deposit money to fund (Traditional API).
    Requires authentication.
    """
    try:
        # Execute via plugin
        result = await execute_plugin.execute(
            intent_type=IntentType.DEPOSIT_FUND.value,
            parameters={
                'fund_id': fund_id,
                'amount': request.amount,
                'from_account_id': request.from_account_id,
            },
            context={
                'user_id': int(current_user.user_id),
                'fund_repository': fund_repo,
                'account_repository': account_repo,
                'transaction_repository': transaction_repo,
            },
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message,
            )

        # Get updated fund to include fund_name in response
        updated_fund = await fund_repo.read_by_id(fund_id)
        if not updated_fund:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Deposit succeeded but fund not found',
            )

        return {
            'fund_id': result.data.get('fund_id', fund_id),
            'current_amount': result.data.get('current_amount', float(updated_fund.current_amount)),
            'deposit_amount': result.data.get('deposit_amount', request.amount),
            'progress_percentage': result.data.get('progress_percentage', 0),
            'status': result.data.get('status', updated_fund.status),
            'message': result.message,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Deposit failed: {str(e)}',
        )


@router.post('/{fund_id}/withdraw')
async def withdraw_from_fund(
    fund_id: int,
    request: FundWithdrawRequest,
    current_user: TokenData = Depends(get_current_user),
    fund_repo: SavingsFundRepository = Depends(get_fund_repository),
    account_repo: AccountRepository = Depends(get_account_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
):
    """
    Withdraw money from fund (Traditional API).
    Requires authentication.
    """
    try:
        # Execute via plugin
        result = await execute_plugin.execute(
            intent_type=IntentType.WITHDRAW_FUND.value,
            parameters={
                'fund_id': fund_id,
                'amount': request.amount,
                'to_account_id': request.to_account_id,
            },
            context={
                'user_id': int(current_user.user_id),
                'fund_repository': fund_repo,
                'account_repository': account_repo,
                'transaction_repository': transaction_repo,
            },
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message,
            )

        # Get updated fund to include fund_name in response
        updated_fund = await fund_repo.read_by_id(fund_id)
        if not updated_fund:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Withdrawal succeeded but fund not found',
            )

        return {
            'fund_id': result.data.get('fund_id', fund_id),
            'current_amount': result.data.get('current_amount', float(updated_fund.current_amount)),
            'withdraw_amount': result.data.get('withdraw_amount', request.amount),
            'progress_percentage': result.data.get('progress_percentage', 0),
            'status': result.data.get('status', updated_fund.status),
            'message': result.message,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Withdrawal failed: {str(e)}',
        )


@router.delete('/{fund_id}')
async def delete_fund(
    fund_id: int,
    current_user: TokenData = Depends(get_current_user),
    fund_repo: SavingsFundRepository = Depends(get_fund_repository),
    account_repo: AccountRepository = Depends(get_account_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
) -> Dict[str, Any]:
    """
    Delete fund (Traditional API).
    Requires authentication.
    If fund has balance, it will be automatically returned to main account.
    """
    try:
        # Execute via plugin
        result = await execute_plugin.execute(
            intent_type=IntentType.DELETE_FUND.value,
            parameters={
                'fund_id': fund_id,
            },
            context={
                'user_id': int(current_user.user_id),
                'fund_repository': fund_repo,
                'account_repository': account_repo,
                'transaction_repository': transaction_repo,
            },
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message,
            )

        return {
            'fund_id': fund_id,
            'deleted': True,
            'message': result.message,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to delete fund: {str(e)}',
        )
