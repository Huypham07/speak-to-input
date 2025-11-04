from __future__ import annotations

from datetime import datetime
from typing import List

from api.dependencies import get_account_repository
from api.dependencies import get_contact_repository
from api.dependencies import get_transaction_repository
from api.helpers.dependencies import get_current_user
from api.helpers.jwt_auth import TokenData
from api.schemas import TransferRequest
from api.schemas import TransferResponse
from application.use_cases import execute_plugin
from domain.value_objects.intent_type import IntentType
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from infra.db.repositories import AccountRepository
from infra.db.repositories import ContactRepository
from infra.db.repositories import TransactionRepository

router = APIRouter(prefix='/transfers', tags=['Money Transfers'])


@router.post('', response_model=TransferResponse)
async def create_transfer(
    request: TransferRequest,
    current_user: TokenData = Depends(get_current_user),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
    account_repo: AccountRepository = Depends(get_account_repository),
    contact_repo: ContactRepository = Depends(get_contact_repository),
):
    """
    Create a money transfer using SendMoneyPlugin.
    Requires authentication.
    """
    try:
        # Execute transfer via plugin
        result = await execute_plugin.execute(
            intent_type=IntentType.SEND_MONEY.value,
            parameters={
                'amount': request.amount,
                'recipient_account_number': request.recipient_account_number,
                'message': request.message or '',
            },
            context={
                'user_id': int(current_user.user_id),
                'transaction_repository': transaction_repo,
                'account_repository': account_repo,
                'contact_repository': contact_repo,
            },
        )

        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message,
            )

        # Extract transaction data from result
        transaction_id = result.data.get('transaction_id')
        if not transaction_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Transfer succeeded but transaction ID not returned',
            )

        # Get transaction details
        transaction = await transaction_repo.read_by_id(transaction_id)
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail='Transfer succeeded but transaction not found',
            )

        return TransferResponse(
            id=transaction.id,
            from_account_id=transaction.from_account_id or 0,
            to_account_number=transaction.recipient_account_number or '',
            amount=float(transaction.amount),
            message=transaction.message or '',
            status=transaction.status,
            created_at=transaction.created_at.isoformat() if transaction.created_at else datetime.now().isoformat(),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Transfer failed: {str(e)}',
        )


@router.get('', response_model=List[TransferResponse])
async def list_transfers(
    current_user: TokenData = Depends(get_current_user),
    limit: int = 50,
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
):
    """
    List transfer history (Traditional API).
    Requires authentication.
    """
    try:
        # Get all transactions for the user
        transactions = await transaction_repo.get_by_user_id(current_user.user_id)

        # Filter for transfers only and limit results
        transfers = [
            TransferResponse(
                id=txn.id,
                from_account_id=txn.from_account_id,
                to_account_number=txn.recipient_account_number or '',
                amount=float(txn.amount),
                message=txn.message,
                status=txn.status,
                created_at=txn.created_at.isoformat() if txn.created_at else datetime.now().isoformat(),
            )
            for txn in transactions
            if txn.transaction_type == 'transfer'
        ][:limit]

        return transfers

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to list transfers: {str(e)}',
        )


@router.get('/{transaction_id}', response_model=TransferResponse)
async def get_transfer(
    transaction_id: int,
    current_user: TokenData = Depends(get_current_user),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
):
    """
    Get transfer details (Traditional API).
    Requires authentication.
    """
    try:
        # Get all user transactions
        transactions = await transaction_repo.get_by_user_id(current_user.user_id)

        # Find the specific transfer
        for txn in transactions:
            if txn.id == transaction_id and txn.transaction_type == 'transfer':
                return TransferResponse(
                    id=txn.id,
                    from_account_id=txn.from_account_id,
                    to_account_number=txn.recipient_account_number or '',
                    amount=float(txn.amount),
                    message=txn.message,
                    status=txn.status,
                    created_at=txn.created_at.isoformat() if txn.created_at else datetime.now().isoformat(),
                )

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Transfer not found',
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to get transfer: {str(e)}',
        )
