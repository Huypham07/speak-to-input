from __future__ import annotations

from typing import Optional

from fastapi import Depends
from fastapi import HTTPException
from fastapi import Request
from fastapi import status
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer

from .jwt_auth import decode_access_token
from .jwt_auth import TokenData

security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
) -> TokenData:

    token = None

    if 'access_token' in request.cookies:
        token = request.cookies.get('access_token')

    if not token and credentials:
        token = credentials.credentials

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    token_data = decode_access_token(token)

    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate credentials',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    return token_data


async def get_current_user_optional(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
) -> Optional[TokenData]:
    """
    Dependency to get current user if authenticated, None otherwise.
    Useful for endpoints that work for both authenticated and anonymous users.
    Supports both Cookie and Authorization header.

    Args:
        request: FastAPI request object
        credentials: Optional bearer token

    Returns:
        TokenData if authenticated, None otherwise
    """
    token = None

    if 'access_token' in request.cookies:
        token = request.cookies.get('access_token')

    if not token and credentials:
        token = credentials.credentials

    if not token:
        return None

    return decode_access_token(token)
