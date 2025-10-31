from __future__ import annotations

from datetime import timedelta

from api.dependencies import get_user_repository
from api.helpers.dependencies import get_current_user
from api.helpers.jwt_auth import ACCESS_TOKEN_EXPIRE_MINUTES
from api.helpers.jwt_auth import create_access_token
from api.helpers.jwt_auth import get_password_hash
from api.helpers.jwt_auth import Token
from api.helpers.jwt_auth import TokenData
from api.helpers.jwt_auth import verify_password
from api.schemas import LoginRequest
from api.schemas import RegisterRequest
from api.schemas import UserResponse
from domain.entities import User
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from infra.db.repositories import UserRepository

router = APIRouter(prefix='/auth', tags=['Authentication'])


@router.post('/login', response_model=Token)
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

    return Token(access_token=access_token, token_type='bearer')


@router.post('/register', response_model=UserResponse)
async def register(
    request: RegisterRequest,
    user_repo: UserRepository = Depends(get_user_repository),
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


@router.post('/refresh', response_model=Token)
async def refresh_token(current_user: TokenData = Depends(get_current_user)):

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={'sub': current_user.username, 'user_id': current_user.user_id},
        expires_delta=access_token_expires,
    )

    return Token(access_token=access_token, token_type='bearer')
