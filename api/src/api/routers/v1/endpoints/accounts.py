from __future__ import annotations

from decimal import Decimal
from typing import List

from api.dependencies import get_account_repository
from api.helpers.dependencies import get_current_user
from api.helpers.jwt_auth import TokenData
from api.schemas import AccountResponse
from api.schemas import DepositRequest
from api.schemas import TransactionResponse
from api.schemas import WithdrawRequest
from domain.entities import Account
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from infra.db.repositories import AccountRepository
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
    Requires authentication.
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
    Requires authentication.
    """
    accounts = await account_repo.get_by_user_id(int(current_user.user_id))

    return [
        AccountResponse.model_validate(acc)
        for acc in accounts
    ]


@router.get('/{account_id}', response_model=AccountResponse)
async def get_account(
    account_id: int,
    current_user: TokenData = Depends(get_current_user),
    account_repo: AccountRepository = Depends(get_account_repository),
):
    """
    Get account details.
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

    return AccountResponse.model_validate(account)


@router.post('/{account_id}/deposit', response_model=TransactionResponse)
async def deposit_to_account(
    account_id: int,
    request: DepositRequest,
    current_user: TokenData = Depends(get_current_user),
    account_repo: AccountRepository = Depends(get_account_repository),
):
    """
    Deposit money to account (Top-up/Nạp tiền).
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

    # Update balance
    try:
        updated_account = await account_repo.update_balance(
            int(account_id),
            Decimal(str(request.amount)),
            operation='add',
        )

        # TODO: Create transaction record in transaction history

        return TransactionResponse(
            transaction_id=f'txn_{account_id}_{int(updated_account.updated_at.timestamp())}',
            account_id=updated_account.id,
            transaction_type='deposit',
            amount=float(request.amount),
            balance_after=float(updated_account.balance),
            note=request.note,
            created_at=updated_account.updated_at.isoformat(),
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
        updated_account = await account_repo.update_balance(
            int(account_id),
            Decimal(str(request.amount)),
            operation='subtract',
        )

        # TODO: Create transaction record in transaction history

        return TransactionResponse(
            transaction_id=f'txn_{account_id}_{int(updated_account.updated_at.timestamp())}',
            account_id=updated_account.id,
            transaction_type='withdraw',
            amount=float(request.amount),
            balance_after=float(updated_account.balance),
            note=request.note,
            created_at=updated_account.updated_at.isoformat(),
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
