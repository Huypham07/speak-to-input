from __future__ import annotations

from typing import Any
from typing import Dict
from typing import List

from api.dependencies import get_account_repository
from api.dependencies import get_bill_repository
from api.dependencies import get_transaction_repository
from api.helpers.dependencies import get_current_user
from api.helpers.jwt_auth import TokenData
from api.schemas import BillResponse
from api.schemas import CreateBillRequest
from application.use_cases import execute_plugin
from domain.value_objects import IntentType
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from infra.db.repositories import AccountRepository
from infra.db.repositories import BillRepository
from infra.db.repositories import TransactionRepository

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
    try:

        result = await execute_plugin.execute(
            intent_type=IntentType.CREATE_BILL.value,
            parameters={
                'bill_name': request.bill_name,
                'amount': request.amount,
                'due_date': request.due_date,
                'category': request.category,
                'recurring': request.recurring,
                'notes': request.notes,
            },
            context={
                'user_id': int(current_user.user_id),
                'bill_repository': bill_repo,
            },
        )
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message,
            )

        return BillResponse(**result.data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Create bill failed: {str(e)}',
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
    from_account_id: int | None = None,
    current_user: TokenData = Depends(get_current_user),
    bill_repo: BillRepository = Depends(get_bill_repository),
    account_repo: AccountRepository = Depends(get_account_repository),
    transaction_repo: TransactionRepository = Depends(get_transaction_repository),
) -> Dict[str, Any]:
    """Mark bill as paid and create transaction (Traditional API)"""

    try:
        # Execute via plugin (same logic as speech)
        result = await execute_plugin.execute(
            intent_type=IntentType.PAY_BILL.value,
            parameters={
                'bill_id': bill_id,
                'from_account_id': from_account_id,
            },
            context={
                'user_id': int(current_user.user_id),
                'bill_repository': bill_repo,
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
            'bill_id': bill_id,
            'success': True,
            'message': 'Bill paid successfully',
            'data': result.data,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f'Pay bill failed: {str(e)}',
        )


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
        'success': True,
        'message': 'Bill deleted successfully',
    }
