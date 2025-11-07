from __future__ import annotations

from pydantic import Field
from shared.base import BaseModel


class LoginRequest(BaseModel):
    """Login request"""
    username: str = Field(..., description='Username or Email')
    password: str = Field(..., description='Password')


class RegisterRequest(BaseModel):
    """Registration request"""
    username: str = Field(..., min_length=3, max_length=50)
    email: str
    password: str = Field(..., min_length=6)
    full_name: str


class UserResponse(BaseModel):
    """User response"""
    id: int
    username: str
    email: str
    full_name: str
    is_active: bool
    is_verified: bool
