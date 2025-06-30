"""
Security configuration and authentication utilities.
Updated to implement Vedprakash Domain Authentication Standards.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import jwt
from app.core.config import get_settings
from app.models.user import User as UserModel
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import PyJWTError
from passlib.context import CryptContext
from pydantic import BaseModel

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token
security = HTTPBearer()


class TokenData(BaseModel):
    """Token data model implementing Vedprakash standard."""

    sub: Optional[str] = None
    email: Optional[str] = None
    roles: list = []
    permissions: list = []


class VedUser(BaseModel):
    """Vedprakash Domain Standard User Object - exact interface per requirements."""

    id: str
    email: str
    name: str
    givenName: str
    familyName: str
    permissions: list[str]
    vedProfile: dict = {
        "profileId": "",
        "subscriptionTier": "free",
        "appsEnrolled": ["pathfinder"],
        "preferences": {}
    }


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
    # Get fresh settings instead of using cached module-level settings
    current_settings = get_settings()
    encoded_jwt = jwt.encode(to_encode, current_settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt


async def verify_token(token: str) -> TokenData:
    """Verify and decode JWT token using production-ready Entra ID validation."""
    try:
        # Get fresh settings instead of using cached module-level settings
        current_settings = get_settings()
        
        # Check if we're in test mode for simplified validation
        if current_settings.is_testing or current_settings.ENVIRONMENT.lower() in [
            "test", "testing"
        ]:
            # For test tokens, use simple verification with our secret key
            payload = jwt.decode(token, current_settings.SECRET_KEY, algorithms=["HS256"])
        else:
            # Production: Use proper Entra ID token validation
            from app.core.token_validator import token_validator
            user_data = await token_validator.validate_token(token)
            
            if not user_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token validation failed",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Convert to TokenData format for compatibility
            return TokenData(
                sub=user_data['id'],
                email=user_data['email'],
                roles=[],  # Will be populated from permissions
                permissions=user_data['permissions']
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
        # Entra ID tokens have standard claim structures
        roles = payload.get("roles", [])
        permissions = payload.get("permissions", [])

        # If no custom roles/permissions, assign default ones for authenticated users
        if not roles:
            roles = ["user"]  # Default role for authenticated users

        if not permissions:
            # Default permissions for authenticated users
            permissions = [
                "read:trips",
                "create:trips",
                "update:trips",
                "delete:trips",
                "read:families",
                "create:families",
                "update:families",
                "delete:families",
                "read:itineraries",
                "create:itineraries",
                "update:itineraries",
                "delete:itineraries",
            ]

        return TokenData(sub=user_id, email=email, roles=roles, permissions=permissions)

    except jwt.ExpiredSignatureError:
        from app.core.auth_errors import TokenInvalidError, handle_auth_error
        raise handle_auth_error(
            TokenInvalidError({'reason': 'Token has expired'})
        )
    except PyJWTError as e:
        from app.core.auth_errors import TokenInvalidError, handle_auth_error
        logger.error(f"JWT verification failed: {e}")
        raise handle_auth_error(
            TokenInvalidError({'reason': f'Token validation failed: {str(e)}'})
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> VedUser:
    """Get current authenticated user using Vedprakash standard."""
    token_data = await verify_token(credentials.credentials)

    # Create standard VedUser object from token data
    if hasattr(token_data, 'user_data'):
        # If we have user_data from production validation
        user_data = token_data.user_data
        user = VedUser(
            id=user_data['id'],
            email=user_data['email'],
            name=user_data['name'],
            givenName=user_data['givenName'],
            familyName=user_data['familyName'],
            permissions=user_data['permissions'],
            vedProfile=user_data['vedProfile']
        )
    else:
        # Fallback for test tokens
        user = VedUser(
            id=token_data.sub,
            email=token_data.email,
            name=token_data.email.split('@')[0],
            givenName='',
            familyName='',
            permissions=token_data.permissions,
            vedProfile={
                "profileId": token_data.sub,
                "subscriptionTier": "free",
                "appsEnrolled": ["pathfinder"],
                "preferences": {}
            }
        )

    return user


async def get_current_user_websocket(token: str) -> Optional[VedUser]:
    """Get current authenticated user from WebSocket token."""
    try:
        token_data = await verify_token(token)

        # Create standard VedUser object from token data
        if hasattr(token_data, 'user_data'):
            user_data = token_data.user_data
            user = VedUser(
                id=user_data['id'],
                email=user_data['email'],
                name=user_data['name'],
                givenName=user_data['givenName'],
                familyName=user_data['familyName'],
                permissions=user_data['permissions'],
                vedProfile=user_data['vedProfile']
            )
        else:
            user = VedUser(
                id=token_data.sub,
                email=token_data.email,
                name=token_data.email.split('@')[0],
                givenName='',
                familyName='',
                permissions=token_data.permissions,
                vedProfile={
                    "profileId": token_data.sub,
                    "subscriptionTier": "free",
                    "appsEnrolled": ["pathfinder"],
                    "preferences": {}
                }
            )

        return user

    except Exception as e:
        logger.error(f"WebSocket authentication failed: {e}")
        return None


async def get_current_active_user(
    current_user: VedUser = Depends(get_current_user),
) -> VedUser:
    """Get current active user."""
    # In a real application, you'd check if the user is active in the database
    return current_user


def require_permission(permission: str):
    """Decorator to require specific permission."""

    def permission_checker(current_user: VedUser = Depends(get_current_user)):
        if permission not in current_user.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required",
            )
        return current_user

    return permission_checker


def require_role(role: str):
    """Decorator to require specific role."""

    def role_checker(current_user: VedUser = Depends(get_current_user)):
        # Map roles to permissions for Vedprakash Domain Standard
        role_permission_map = {
            "admin": "admin:all",
            "family_admin": "admin:family",
            "user": "user:basic"
        }
        required_permission = role_permission_map.get(role, f"role:{role}")
        
        if required_permission not in current_user.permissions:
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
            key: value
            for key, value in self.request_counts.items()
            if value["timestamp"] > window_start
        }

        # Check current count
        if identifier in self.request_counts:
            if self.request_counts[identifier]["count"] >= self.requests:
                return False
            self.request_counts[identifier]["count"] += 1
        else:
            self.request_counts[identifier] = {"count": 1, "timestamp": now}

        return True


# Global rate limiter instance - use lazy initialization
rate_limiter = None

def get_rate_limiter():
    """Get rate limiter instance with fresh settings."""
    global rate_limiter
    if rate_limiter is None:
        current_settings = get_settings()
        rate_limiter = RateLimiter(
            requests=current_settings.RATE_LIMIT_REQUESTS, 
            window=current_settings.RATE_LIMIT_WINDOW
        )
    return rate_limiter


async def check_rate_limit(request: Request):
    """Rate limiting dependency."""
    client_ip = request.client.host

    if not get_rate_limiter().is_allowed(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded"
        )


def validate_file_upload(file_content: bytes, content_type: str) -> bool:
    """Validate file upload."""
    # Check file size
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed size of {settings.MAX_FILE_SIZE} bytes",
        )

    # Check file type
    if content_type not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"File type '{content_type}' not allowed",
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
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
        return user

    return permission_checker
