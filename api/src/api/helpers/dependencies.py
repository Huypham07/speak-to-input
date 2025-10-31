from __future__ import annotations

from typing import Optional

from fastapi import Depends
from fastapi import HTTPException
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from .jwt_auth import decode_access_token
from .jwt_auth import TokenData

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> TokenData:
    """
    Dependency to get current authenticated user from JWT token.

    Args:
        credentials: Bearer token from Authorization header

    Returns:
        TokenData with user information

    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials

    token_data = decode_access_token(token)

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    return token_data


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> Optional[TokenData]:
    """
    Dependency to get current user if authenticated, None otherwise.
    Useful for endpoints that work for both authenticated and anonymous users.

    Args:
        credentials: Optional bearer token

    Returns:
        TokenData if authenticated, None otherwise
    """
    if credentials is None:
        return None

    token = credentials.credentials
    return decode_access_token(token)
