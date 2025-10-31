from __future__ import annotations

from typing import List

from api.helpers.dependencies import get_current_user
from api.helpers.jwt_auth import TokenData
from api.schemas import TransferRequest
from api.schemas import TransferResponse
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status

router = APIRouter(prefix='/transfers', tags=['Money Transfers'])


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
        id=123,
        from_account_id=1,
        to_account_number=request.recipient_account_number,
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
    transaction_id: int,
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
