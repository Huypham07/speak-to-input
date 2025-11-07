from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import List

from api.dependencies import get_account_repository
from api.dependencies import get_transaction_repository
from api.helpers.dependencies import get_current_user
from api.helpers.jwt_auth import TokenData
from api.schemas import AccountResponse
from api.schemas import DepositRequest
from api.schemas import OtherUserAccountResponse
from api.schemas import TransactionResponse
from api.schemas import WithdrawRequest
from domain.entities import Account
from domain.entities.transaction import Transaction
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from infra.db.repositories import AccountRepository
from infra.db.repositories import TransactionRepository
from pydantic import BaseModel
from pydantic import Field
from shared.utils import generate_account_number

router = APIRouter(prefix='/accounts', tags=['Accounts'])


class CreateAccountRequest(BaseModel):
    """Request to create a new account"""
    account_name: str = Field(..., min_length=1, max_length=255, description='Account name/label')
    account_type: str = Field('checking', description='Account type: checking, savings')
    currency: str = Field('VND', description='Currency code')


@router.post('', response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(
    request: CreateAccountRequest,
    current_user: TokenData = Depends(get_current_user),
    account_repo: AccountRepository = Depends(get_account_repository),
):
    """
    Create a new account for current user.
    Account number will be auto-generated.
    """
    user_id = int(current_user.user_id)

    # Count existing accounts to get next sequence number
    existing_count = await account_repo.count_by_user_id(user_id)
    next_sequence = existing_count + 1

    # Generate account number
    account_number = generate_account_number(user_id, next_sequence)

    # Create account entity
    new_account = Account(
        user_id=user_id,
        account_number=account_number,
        account_name=request.account_name,
        balance=0.0,
        currency=request.currency,
        account_type=request.account_type,
        is_active=True,
    )

    # Save to database
    created_account = await account_repo.create(new_account)

    return AccountResponse.model_validate(created_account)


@router.get('', response_model=List[AccountResponse])
async def list_accounts(
    current_user: TokenData = Depends(get_current_user),
    account_repo: AccountRepository = Depends(get_account_repository),
):
    """
    List all accounts for current user.
    """
    accounts = await account_repo.get_by_user_id(int(current_user.user_id))

    return [
        AccountResponse.model_validate(acc)
        for acc in accounts
    ]


@router.get('/others', response_model=List[OtherUserAccountResponse])
async def list_other_users_accounts(
    current_user: TokenData = Depends(get_current_user),
    account_repo: AccountRepository = Depends(get_account_repository),
):
    """
    List all accounts from other users (excluding current user).
    Useful for transfer form to show available recipients.
    """
    try:
        accounts_with_users = await account_repo.get_other_users_accounts(
            exclude_user_id=int(current_user.user_id),
        )

        return [
            OtherUserAccountResponse(
                id=account.id,
                account_number=account.account_number,
                account_name=account.account_name,
                balance=float(account.balance),
                currency=account.currency,
                account_type=account.account_type,
                is_active=account.is_active,
                user_id=user.id,
                user_full_name=user.full_name,
                user_username=user.username,
            )
            for account, user in accounts_with_users
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to fetch other users accounts: {str(e)}',
        )


@router.get('/transactions', response_model=List[TransactionResponse])
async def get_transactions(
    current_user: TokenData = Depends(get_current_user),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
    limit: int = 50,
):
    """
    Get transaction history for the current user.
    """
    try:
        transactions = await transaction_repo.get_by_user_id(int(current_user.user_id))

        # Convert to response format
        return [
            TransactionResponse(
                id=txn.id,
                user_id=txn.user_id,
                from_account_id=txn.from_account_id,
                to_account_id=txn.to_account_id,
                transaction_type=txn.transaction_type,
                amount=float(txn.amount),
                currency=txn.currency,
                status=txn.status,
                message=txn.message,
                recipient_account_number=txn.recipient_account_number,
                recipient_name=txn.recipient_name,
                recipient_bank=txn.recipient_bank,
                created_at=txn.created_at.isoformat() if txn.created_at else datetime.now().isoformat(),
                updated_at=txn.updated_at.isoformat() if txn.updated_at else None,
            )
            for txn in transactions[:limit]
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Failed to fetch transactions: {str(e)}',
        )


@router.get('/{account_id}', response_model=AccountResponse)
async def get_account(
    account_id: int,
    current_user: TokenData = Depends(get_current_user),
    account_repo: AccountRepository = Depends(get_account_repository),
):
    """
    Get account details.
    """
    account = await account_repo.read_by_id(account_id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Account not found',
        )

    # Check ownership
    if account.user_id != int(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Access denied',
        )

    return AccountResponse.model_validate(account)


@router.post('/{account_id}/deposit', response_model=TransactionResponse)
async def deposit_to_account(
    account_id: int,
    request: DepositRequest,
    current_user: TokenData = Depends(get_current_user),
    account_repo: AccountRepository = Depends(get_account_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
):
    """
    Deposit money to account (Nạp tiền).
    """
    account = await account_repo.read_by_id(account_id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Account not found',
        )

    # Check ownership
    if account.user_id != int(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Access denied',
        )

    # Update balance
    try:
        await account_repo.update_balance(
            int(account_id),
            Decimal(str(request.amount)),
            operation='add',
        )

        # Create transaction record
        transaction = Transaction(
            user_id=int(current_user.user_id),
            from_account_id=None,  # No source for deposit
            to_account_id=int(account_id),
            transaction_type='deposit',
            amount=Decimal(str(request.amount)),
            currency='VND',
            message=request.note,
            status='completed',
        )
        created_txn = await transaction_repo.create(transaction)

        return TransactionResponse(
            id=created_txn.id,
            user_id=int(current_user.user_id),
            from_account_id=None,
            to_account_id=int(account_id),
            transaction_type='deposit',
            amount=float(request.amount),
            currency='VND',
            status='completed',
            message=request.note,
            recipient_account_number=None,
            recipient_name=None,
            recipient_bank=None,
            created_at=created_txn.created_at.isoformat() if created_txn.created_at else datetime.now().isoformat(),
            updated_at=created_txn.updated_at.isoformat() if created_txn.updated_at else None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post('/{account_id}/withdraw', response_model=TransactionResponse)
async def withdraw_from_account(
    account_id: int,
    request: WithdrawRequest,
    current_user: TokenData = Depends(get_current_user),
    account_repo: AccountRepository = Depends(get_account_repository),
):
    """
    Withdraw money from account (Rút tiền).
    Requires authentication.
    """
    account = await account_repo.read_by_id(account_id)

    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Account not found',
        )

    # Check ownership
    if account.user_id != int(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Access denied',
        )

    # Check balance
    if account.balance < Decimal(str(request.amount)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Insufficient balance',
        )

    # Update balance
    try:
        await account_repo.update_balance(
            int(account_id),
            Decimal(str(request.amount)),
            operation='subtract',
        )

        # Create transaction record
        transaction_repo = TransactionRepository(account_repo.session)
        transaction = Transaction(
            user_id=int(current_user.user_id),
            from_account_id=int(account_id),
            to_account_id=None,  # No destination for withdrawal
            transaction_type='withdraw',
            amount=Decimal(str(request.amount)),
            currency='VND',
            message=request.note,
            status='completed',
        )
        created_txn = await transaction_repo.create(transaction)

        return TransactionResponse(
            id=created_txn.id,
            user_id=int(current_user.user_id),
            from_account_id=int(account_id),
            to_account_id=None,
            transaction_type='withdraw',
            amount=float(request.amount),
            currency='VND',
            status='completed',
            message=request.note,
            recipient_account_number=None,
            recipient_name=None,
            recipient_bank=None,
            created_at=created_txn.created_at.isoformat() if created_txn.created_at else datetime.now().isoformat(),
            updated_at=created_txn.updated_at.isoformat() if created_txn.updated_at else None,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
