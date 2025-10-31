from __future__ import annotations

from typing import List

from api.helpers.dependencies import get_current_user
from api.helpers.jwt_auth import TokenData
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from pydantic import BaseModel
from pydantic import Field

router = APIRouter(prefix='/transfers', tags=['Money Transfers'])


class TransferRequest(BaseModel):
    """Request to transfer money"""
    from_account_id: str | None = None  # If None, use default account
    recipient_account_number: str = Field(..., description='Recipient account number')
    recipient_name: str | None = None
    amount: float = Field(..., gt=0)
    message: str | None = None


class TransferResponse(BaseModel):
    """Transfer response"""
    transaction_id: str
    from_account: str
    to_account: str
    amount: float
    message: str | None
    status: str
    created_at: str


@router.post('', response_model=TransferResponse)
async def create_transfer(
    request: TransferRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Create a money transfer (Traditional API).
    Requires authentication.
    """

    # TODO: Implement transfer
    # - Get user's accounts
    # - Validate balance
    # - Resolve recipient
    # - Create transaction
    # - Update balances

    # Mock response
    return TransferResponse(
        transaction_id='txn_123',
        from_account='1234567890',
        to_account=request.recipient_account_number,
        amount=request.amount,
        message=request.message,
        status='completed',
        created_at='2025-10-30T00:00:00Z',
    )


@router.get('', response_model=List[TransferResponse])
async def list_transfers(
    current_user: TokenData = Depends(get_current_user),
    limit: int = 50,
):
    """
    List transfer history (Traditional API).
    Requires authentication.
    """

    # TODO: Implement transfer listing
    return []


@router.get('/{transaction_id}', response_model=TransferResponse)
async def get_transfer(
    transaction_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get transfer details (Traditional API).
    Requires authentication.
    """

    # TODO: Implement transfer retrieval
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Transfer not found',
    )
