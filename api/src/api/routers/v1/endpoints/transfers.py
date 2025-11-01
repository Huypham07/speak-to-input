from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Dict
from typing import List
from typing import Optional

from api.dependencies import get_account_repository
from api.dependencies import get_contact_repository
from api.dependencies import get_transaction_repository
from api.helpers.dependencies import get_current_user
from api.helpers.jwt_auth import TokenData
from api.schemas import TransferRequest
from api.schemas import TransferResponse
from domain.entities.transaction import Transaction
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from infra.db.repositories import AccountRepository
from infra.db.repositories import ContactRepository
from infra.db.repositories import TransactionRepository
from shared.exceptions import NotFoundError

router = APIRouter(prefix='/transfers', tags=['Money Transfers'])


async def _resolve_recipient(
    recipient: str,
    user_id: int,
    contact_repo: ContactRepository,
    account_repo: AccountRepository,
) -> Optional[Dict]:
    """
    Resolve recipient from account number or contact name.
    Returns dict with recipient info or None if not found.
    """
    # Try to find as contact first
    contacts = await contact_repo.get_by_user_id(user_id)
    for contact in contacts:
        if contact.name.lower() == recipient.lower():
            return {
                'account_number': contact.account_number,
                'name': contact.name,
                'bank': contact.bank_name,
                'account_id': None,  # External contact
            }

    # Try to find as account number (internal transfer)
    account = await account_repo.get_by_account_number(recipient)
    if account:
        return {
            'account_number': account.account_number,
            'name': account.account_name,
            'bank': 'Internal',
            'account_id': account.id,
        }

    # Try as account number in contacts
    for contact in contacts:
        if contact.account_number == recipient:
            return {
                'account_number': contact.account_number,
                'name': contact.name,
                'bank': contact.bank_name,
                'account_id': None,  # External contact
            }

    return None


@router.post('', response_model=TransferResponse)
async def create_transfer(
    request: TransferRequest,
    current_user: TokenData = Depends(get_current_user),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
    account_repo: AccountRepository = Depends(get_account_repository),
    contact_repo: ContactRepository = Depends(get_contact_repository),
):
    """
    Create a money transfer (Traditional API).
    Requires authentication.
    """
    try:
        # Get user's accounts
        user_accounts = await account_repo.get_by_user_id(current_user.user_id)
        if not user_accounts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='User has no accounts',
            )

        # Use specified account or default to first account
        from_account_id = request.from_account_id or user_accounts[0].id
        from_account = None
        for account in user_accounts:
            if account.id == from_account_id:
                from_account = account
                break

        if not from_account:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Invalid source account',
            )

        amount = Decimal(str(request.amount))

        # Check balance
        if Decimal(str(from_account.balance)) < amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Insufficient balance',
            )

        # Resolve recipient
        recipient_info = await _resolve_recipient(
            recipient=request.recipient_account_number,
            user_id=current_user.user_id,
            contact_repo=contact_repo,
            account_repo=account_repo,
        )

        if not recipient_info:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f'Recipient not found: {request.recipient_account_number}',
            )

        # Perform transfer
        if recipient_info.get('account_id'):
            # Internal transfer
            to_account_id = recipient_info['account_id']
            updated_from, updated_to = await account_repo.transfer(
                from_account_id=from_account_id,
                to_account_id=to_account_id,
                amount=amount,
            )

            # Create transaction record
            transaction = Transaction(
                user_id=current_user.user_id,
                from_account_id=from_account_id,
                to_account_id=to_account_id,
                transaction_type='transfer',
                amount=amount,
                currency='VND',
                message=request.message,
                status='completed',
            )

            created_txn = await transaction_repo.create(transaction)
            await transaction_repo.update_status(created_txn.id, 'completed')

            return TransferResponse(
                id=created_txn.id,
                from_account_id=from_account_id,
                to_account_number=recipient_info.get('account_number', ''),
                amount=float(amount),
                message=request.message,
                status='completed',
                created_at=created_txn.created_at.isoformat() if created_txn.created_at else datetime.now().isoformat(),
            )
        else:
            # External transfer
            await account_repo.update_balance(
                account_id=from_account_id,
                amount=amount,
                operation='subtract',
            )

            # Create transaction record
            transaction = Transaction(
                user_id=current_user.user_id,
                from_account_id=from_account_id,
                to_account_id=None,
                transaction_type='transfer',
                amount=amount,
                currency='VND',
                recipient_account_number=recipient_info.get('account_number'),
                recipient_name=recipient_info.get('name'),
                recipient_bank=recipient_info.get('bank'),
                message=request.message,
                status='completed',
            )

            created_txn = await transaction_repo.create(transaction)
            await transaction_repo.update_status(created_txn.id, 'completed')

            return TransferResponse(
                id=created_txn.id,
                from_account_id=from_account_id,
                to_account_number=recipient_info.get('account_number', ''),
                amount=float(amount),
                message=request.message,
                status='completed',
                created_at=created_txn.created_at.isoformat() if created_txn.created_at else datetime.now().isoformat(),
            )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
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
