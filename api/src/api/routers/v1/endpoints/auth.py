from __future__ import annotations

from datetime import timedelta

from api.dependencies import get_account_repository
from api.dependencies import get_user_repository
from api.helpers.dependencies import get_current_user
from api.helpers.jwt_auth import ACCESS_TOKEN_EXPIRE_MINUTES
from api.helpers.jwt_auth import create_access_token
from api.helpers.jwt_auth import create_refresh_token
from api.helpers.jwt_auth import decode_access_token
from api.helpers.jwt_auth import get_password_hash
from api.helpers.jwt_auth import REFRESH_TOKEN_EXPIRE_DAYS
from api.helpers.jwt_auth import TokenData
from api.helpers.jwt_auth import verify_password
from api.schemas import LoginRequest
from api.schemas import RegisterRequest
from api.schemas import UserResponse
from domain.entities import Account
from domain.entities import User
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.responses import JSONResponse
from infra.db.repositories import AccountRepository
from infra.db.repositories import UserRepository
from shared.utils import generate_account_number

router = APIRouter(prefix='/auth', tags=['Authentication'])


@router.post('/login')
async def login(
    request: LoginRequest,
    user_repo: UserRepository = Depends(get_user_repository),
):
    # Try to get user by username first, then by email
    user = await user_repo.get_by_username(request.username)

    # If not found by username, try email
    if not user:
        user_entity = await user_repo.get_by_email(request.username)
        if user_entity:
            # Get the model again for password verification
            user = await user_repo.get_by_username(user_entity.username)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username/email or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    # Verify password
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username/email or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Inactive user',
        )

    # Update last login timestamp
    await user_repo.update_last_login(user.id)

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub': user.username, 'user_id': str(user.id)},
        expires_delta=access_token_expires,
    )

    # Create refresh token
    refresh_token_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_refresh_token(
        data={'sub': user.username, 'user_id': str(user.id)},
        expires_delta=refresh_token_expires,
    )

    # Create response with httpOnly cookie
    response = JSONResponse(
        content={
            'access_token': access_token,
            'token_type': 'bearer',
        },
    )

    # Set httpOnly cookie for access token
    response.set_cookie(
        key='access_token',
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        path='/',
        samesite='lax',  # Allows cookie to be sent with top-level navigations
    )

    # Set httpOnly cookie for refresh token
    response.set_cookie(
        key='refresh_token',
        value=refresh_token,
        httponly=True,
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,  # Convert to seconds
        path='/',
        samesite='lax',
    )

    return response


@router.post('/register', response_model=UserResponse)
async def register(
    request: RegisterRequest,
    user_repo: UserRepository = Depends(get_user_repository),
    account_repo: AccountRepository = Depends(get_account_repository),
):
    # Check if username already exists
    existing_user = await user_repo.get_by_username(request.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Username already registered',
        )

    # Check if email already exists
    existing_email = await user_repo.get_by_email(request.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='Email already registered',
        )

    # Hash password
    hashed_password = get_password_hash(request.password)

    # Create user entity
    new_user = User(
        username=request.username,
        email=request.email,
        hashed_password=hashed_password,
        full_name=request.full_name,
        is_active=True,
        is_verified=False,  # Email verification can be added later
    )

    # Save to database
    created_user = await user_repo.create(new_user)

    # Auto-create default account for new user
    # Generate unique account number based on user_id
    # Sequence = 1 for first account
    account_number = generate_account_number(created_user.id, sequence=1)

    default_account = Account(
        user_id=created_user.id,
        account_number=account_number,
        account_name=f'Tài khoản chính - {request.full_name}',
        balance=0.0,
        currency='VND',
        account_type='checking',
        is_active=True,
    )

    await account_repo.create(default_account)

    return UserResponse.model_validate(created_user)


@router.get('/me', response_model=UserResponse)
async def get_current_user_info(
    current_user: TokenData = Depends(get_current_user),
    user_repo: UserRepository = Depends(get_user_repository),
):

    # Get full user info from database
    user = await user_repo.read_by_id(int(current_user.user_id))

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='User not found',
        )

    return UserResponse.model_validate(user)


@router.post('/refresh')
async def refresh_token(request: Request):
    """
    Refresh access token using refresh token from httpOnly cookie.
    Does NOT require valid access token - only refresh token.
    """
    # Get refresh token from cookie
    refresh_token = request.cookies.get('refresh_token')

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Refresh token not found',
        )

    # Decode and validate refresh token
    token_data = decode_access_token(refresh_token)

    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Invalid refresh token',
        )

    # Create new access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub': token_data.username, 'user_id': token_data.user_id},
        expires_delta=access_token_expires,
    )

    # Create response with new access token
    response = JSONResponse(
        content={
            'access_token': access_token,
            'token_type': 'bearer',
        },
    )

    # Update httpOnly cookie with new access token
    response.set_cookie(
        key='access_token',
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path='/',
        samesite='lax',
    )

    return response


@router.post('/logout')
async def logout():
    """
    Logout endpoint - clears both access and refresh token httpOnly cookies.
    """
    response = JSONResponse(content={'message': 'Logged out successfully'})
    response.delete_cookie(key='access_token', path='/')
    response.delete_cookie(key='refresh_token', path='/')
    return response
