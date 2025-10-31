from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List

from api.dependencies import get_bill_repository
from api.helpers.dependencies import get_current_user
from api.helpers.jwt_auth import TokenData
from api.schemas import BillResponse
from api.schemas import CreateBillRequest
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from infra.db.repositories import BillRepository

router = APIRouter(prefix='/bills', tags=['Bills'])


@router.post('', response_model=BillResponse, status_code=status.HTTP_201_CREATED)
async def create_bill(
    request: CreateBillRequest,
    current_user: TokenData = Depends(get_current_user),
    bill_repo: BillRepository = Depends(get_bill_repository),
):
    """
    Create a new bill (Traditional API).
    Uses the SAME business logic as speech-to-input.
    """

    # Execute via plugin (same logic as speech)
    # TODO: Implement
    # return mock response for now

    return BillResponse(
        bill_id=123,
        bill_name=request.title,
        amount=request.amount,
        due_date=request.due_date,
        category=request.category,
        status='pending',
    )


@router.get('', response_model=List[BillResponse])
async def list_bills(
    current_user: TokenData = Depends(get_current_user),
    status_filter: str | None = None,
    bill_repo: BillRepository = Depends(get_bill_repository),
):
    """
    List all bills for current user (Traditional API).
    """

    bills = await bill_repo.get_by_user_id(
        user_id=int(current_user.user_id),
        status=status_filter,
    )

    return [
        BillResponse.model_validate(bill)
        for bill in bills
    ]


@router.get('/{bill_id}', response_model=BillResponse)
async def get_bill(
    bill_id: int,
    current_user: TokenData = Depends(get_current_user),
    bill_repo: BillRepository = Depends(get_bill_repository),
):
    """Get bill details (Traditional API)"""

    bill = await bill_repo.read_by_id(bill_id)

    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Bill not found',
        )

    # Check ownership
    if bill.user_id != int(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Access denied',
        )

    return BillResponse.model_validate(bill)


@router.post('/{bill_id}/pay')
async def pay_bill(
    bill_id: int,
    current_user: TokenData = Depends(get_current_user),
    bill_repo: BillRepository = Depends(get_bill_repository),
) -> Dict[str, Any]:
    """Mark bill as paid (Traditional API)"""

    bill = await bill_repo.read_by_id(bill_id)

    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Bill not found',
        )

    # Check ownership
    if bill.user_id != int(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Access denied',
        )

    # Mark as paid
    updated_bill = await bill_repo.mark_as_paid(bill_id)

    return {
        'bill_id': updated_bill.bill_id,
        'status': updated_bill.status,
        'paid_at': updated_bill.paid_at.isoformat() if updated_bill.paid_at else None,
        'message': f'Đã đánh dấu hóa đơn "{updated_bill.bill_name}" đã thanh toán',
    }


@router.delete('/{bill_id}')
async def delete_bill(
    bill_id: int,
    current_user: TokenData = Depends(get_current_user),
    bill_repo: BillRepository = Depends(get_bill_repository),
) -> Dict[str, Any]:
    """Delete bill (Traditional API)"""

    bill = await bill_repo.read_by_id(bill_id)

    if not bill:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Bill not found',
        )

    # Check ownership
    if bill.user_id != int(current_user.user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail='Access denied',
        )

    # Delete
    await bill_repo.delete_by_id(bill_id)

    return {
        'bill_id': bill_id,
        'deleted': True,
        'message': 'Bill deleted successfully',
    }
