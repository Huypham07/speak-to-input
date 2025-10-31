from __future__ import annotations

from typing import List

from api.helpers.dependencies import get_current_user
from api.helpers.jwt_auth import TokenData
from fastapi import APIRouter
from fastapi import Body
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from pydantic import BaseModel
from pydantic import Field

router = APIRouter(prefix='/funds', tags=['Savings Funds'])


class CreateFundRequest(BaseModel):
    """Request to create a savings fund"""
    fund_name: str = Field(..., min_length=1, max_length=100)
    target_amount: float = Field(..., gt=0)
    target_date: str = Field(..., description='Target date in YYYY-MM-DD format')
    initial_amount: float = Field(0, ge=0)
    monthly_contribution: float = Field(0, ge=0)
    category: str | None = None
    auto_transfer: bool = Field(False)
    notes: str | None = None


class FundResponse(BaseModel):
    """Fund response"""
    fund_id: str
    fund_name: str
    target_amount: float
    current_amount: float
    target_date: str
    category: str | None
    monthly_contribution: float
    progress_percentage: float
    status: str
    created_at: str


@router.post('', response_model=FundResponse)
async def create_fund(
    request: CreateFundRequest,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Create a new savings fund (Traditional API).
    Requires authentication.
    """

    # TODO: Implement fund creation
    # - Validate data
    # - Create fund
    # - If initial_amount > 0, create transaction

    # Mock response
    progress = (request.initial_amount / request.target_amount * 100) if request.target_amount > 0 else 0

    return FundResponse(
        fund_id='fund_123',
        fund_name=request.fund_name,
        target_amount=request.target_amount,
        current_amount=request.initial_amount,
        target_date=request.target_date,
        category=request.category,
        monthly_contribution=request.monthly_contribution,
        progress_percentage=progress,
        status='active',
        created_at='2025-10-30T00:00:00Z',
    )


@router.get('', response_model=List[FundResponse])
async def list_funds(
    current_user: TokenData = Depends(get_current_user),
    status: str | None = None,
):
    """
    List all savings funds for current user (Traditional API).
    Requires authentication.
    """

    # TODO: Implement fund listing
    return []


@router.get('/{fund_id}', response_model=FundResponse)
async def get_fund(
    fund_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Get fund details (Traditional API).
    Requires authentication.
    """

    # TODO: Implement fund retrieval
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Fund not found',
    )


@router.post('/{fund_id}/deposit')
async def deposit_to_fund(
    fund_id: str,
    amount: float = Body(..., gt=0, embed=True),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Deposit money to fund (Traditional API).
    Requires authentication.
    """

    # TODO: Implement fund deposit
    # - Check user balance
    # - Create transaction
    # - Update fund amount

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail='Not implemented',
    )


@router.post('/{fund_id}/withdraw')
async def withdraw_from_fund(
    fund_id: str,
    amount: float = Body(..., gt=0, embed=True),
    current_user: TokenData = Depends(get_current_user),
):
    """
    Withdraw money from fund (Traditional API).
    Requires authentication.
    """

    # TODO: Implement fund withdrawal
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail='Not implemented',
    )


@router.delete('/{fund_id}')
async def delete_fund(
    fund_id: str,
    current_user: TokenData = Depends(get_current_user),
):
    """
    Delete fund (Traditional API).
    Requires authentication.
    """

    # TODO: Implement fund deletion
    return {'fund_id': fund_id, 'deleted': True}
