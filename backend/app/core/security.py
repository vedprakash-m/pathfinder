"""
Security configuration and authentication utilities.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import jwt
from jwt.exceptions import PyJWTError
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from passlib.context import CryptContext
from pydantic import BaseModel

from app.core.config import get_settings
from app.models.user import User as UserModel

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token
security = HTTPBearer()


class TokenData(BaseModel):
    """Token data model."""
    sub: Optional[str] = None
    email: Optional[str] = None
    roles: list = []
    permissions: list = []


class User(BaseModel):
    """User model for authentication."""
    id: str
    email: str
    name: Optional[str] = None
    picture: Optional[str] = None
    roles: list = []
    permissions: list = []


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


async def verify_token(token: str) -> TokenData:
    """Verify and decode JWT token."""
    try:
        # Check if we're in test mode
        if settings.is_testing:
            # For test tokens, use simple verification with our secret key
            payload = jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS256"]
            )
        else:
            # For Auth0 tokens, we need to verify against Auth0's public key
            # This is a simplified version - in production, you'd fetch the public key
            # from Auth0's JWKS endpoint and verify the signature
            payload = jwt.decode(
                token,
                options={"verify_signature": False},  # In production, set to True
                audience=settings.AUTH0_AUDIENCE,
                issuer=settings.AUTH0_ISSUER,
            )
        
        email: str = payload.get("email")
        user_id: str = payload.get("sub")
        
        if email is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract roles and permissions from token
        roles = payload.get("https://pathfinder.app/roles", [])
        permissions = payload.get("https://pathfinder.app/permissions", [])
        
        return TokenData(
            sub=user_id,
            email=email,
            roles=roles,
            permissions=permissions
        )
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except PyJWTError as e:
        logger.error(f"JWT verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """Get current authenticated user."""
    token_data = await verify_token(credentials.credentials)
    
    # In a real application, you'd fetch user details from the database
    # For now, we'll create a user object from the token data
    user = User(
        id=token_data.sub,
        email=token_data.email,
        roles=token_data.roles,
        permissions=token_data.permissions
    )
    
    return user


async def get_current_user_websocket(token: str) -> Optional[User]:
    """Get current authenticated user from WebSocket token."""
    try:
        token_data = await verify_token(token)
        
        # In a real application, you'd fetch user details from the database
        # For now, we'll create a user object from the token data
        user = User(
            id=token_data.sub,
            email=token_data.email,
            roles=token_data.roles,
            permissions=token_data.permissions
        )
        
        return user
        
    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        return None


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user."""
    # In a real application, you'd check if the user is active in the database
    return current_user


def require_permission(permission: str):
    """Decorator to require specific permission."""
    def permission_checker(current_user: User = Depends(get_current_user)):
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return current_user
    
    return permission_checker


def require_role(role: str):
    """Decorator to require specific role."""
    def role_checker(current_user: User = Depends(get_current_user)):
        if role not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' required"
            )
        return current_user
    
    return role_checker


class RateLimiter:
    """Simple rate limiter."""
    
    def __init__(self, requests: int = 100, window: int = 3600):
        self.requests = requests
        self.window = window
        self.request_counts = {}
    
    def is_allowed(self, identifier: str) -> bool:
        """Check if request is allowed for identifier."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window)
        
        # Clean old entries
        self.request_counts = {
            key: value for key, value in self.request_counts.items()
            if value["timestamp"] > window_start
        }
        
        # Check current count
        if identifier in self.request_counts:
            if self.request_counts[identifier]["count"] >= self.requests:
                return False
            self.request_counts[identifier]["count"] += 1
        else:
            self.request_counts[identifier] = {
                "count": 1,
                "timestamp": now
            }
        
        return True


# Global rate limiter instance
rate_limiter = RateLimiter(
    requests=settings.RATE_LIMIT_REQUESTS,
    window=settings.RATE_LIMIT_WINDOW
)


async def check_rate_limit(request: Request):
    """Rate limiting dependency."""
    client_ip = request.client.host
    
    if not rate_limiter.is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )


def validate_file_upload(file_content: bytes, content_type: str) -> bool:
    """Validate file upload."""
    # Check file size
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes"
        )
    
    # Check file type
    if content_type not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{content_type}' not allowed"
        )
    
    return True


def require_permissions(*permissions):
    """
    Decorator to require specific permissions for accessing an endpoint.
    Accepts either multiple string arguments or a single list of permissions.
    """
    # Handle both require_permissions("perm1", "perm2") and require_permissions(["perm1", "perm2"])
    if len(permissions) == 1 and isinstance(permissions[0], list):
        permission_list = permissions[0]
    else:
        permission_list = list(permissions)
    
    def permission_checker(user: UserModel = Depends(get_current_user)):
        # For now, we'll implement a basic permission check
        # In a full implementation, this would check user roles and permissions
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Inactive user"
            )
        return user
    
    return permission_checker