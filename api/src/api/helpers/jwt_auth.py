from __future__ import annotations

from datetime import datetime
from datetime import timedelta
from typing import Optional

from jose import jwt
from jose import JWTError
from passlib.context import CryptContext
from pydantic import BaseModel
from shared.utils import get_settings

settings = get_settings()

# JWT settings
SECRET_KEY = settings.secret_key
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7  # Refresh token lasts 7 days

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')


class Token(BaseModel):
    """JWT Token response"""
    access_token: str
    token_type: str = 'bearer'


class TokenData(BaseModel):
    """Data stored in JWT token"""
    username: Optional[str] = None
    user_id: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Data to encode in the token (should include 'sub' for user identifier)
        expires_delta: Token expiration time delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token.

    Args:
        data: Data to encode in the token (should include 'sub' for user identifier)
        expires_delta: Token expiration time delta

    Returns:
        Encoded JWT refresh token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({'exp': expire, 'type': 'refresh'})  # Mark as refresh token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def decode_access_token(token: str) -> Optional[TokenData]:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token string

    Returns:
        TokenData if valid, None otherwise
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: str = payload.get('user_id')

        if username is None:
            return None

        return TokenData(username=username, user_id=user_id)

    except JWTError:
        return None


def verify_token(token: str) -> TokenData:
    """
    Verify JWT token and return TokenData.
    Raises exception if token is invalid.

    Args:
        token: JWT token string

    Returns:
        TokenData if valid

    Raises:
        ValueError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: str = payload.get('user_id')

        if username is None or user_id is None:
            raise ValueError('Invalid token payload')

        return TokenData(username=username, user_id=user_id)

    except JWTError as e:
        raise ValueError(f'Invalid or expired token: {str(e)}')
