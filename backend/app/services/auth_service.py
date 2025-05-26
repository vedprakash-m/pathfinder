"""
Authentication service for user management and Auth0 integration.

This module handles:
- User authentication with Auth0
- JWT token validation
- User profile management
- Session management
- Password operations (for local development)
"""

import logging
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from urllib.parse import urlencode

import httpx
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User, UserCreate, UserUpdate, UserResponse
from app.core.security import create_access_token

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for handling authentication operations."""
    
    def __init__(self):
        self.auth0_domain = settings.AUTH0_DOMAIN
        self.auth0_client_id = settings.AUTH0_CLIENT_ID
        self.auth0_client_secret = settings.AUTH0_CLIENT_SECRET
        self.auth0_audience = settings.AUTH0_AUDIENCE
        
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash."""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Generate password hash."""
        return pwd_context.hash(password)
    
    async def get_auth0_user_info(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from Auth0."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://{self.auth0_domain}/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"}
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Auth0 userinfo error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting Auth0 user info: {e}")
            return None
    
    def decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Decode and validate JWT token."""
        try:
            # For Auth0 tokens, we need to validate against Auth0's public key
            # For development, we'll use a simpler approach
            if settings.ENVIRONMENT == "development":
                # Skip signature verification in development
                payload = jwt.get_unverified_claims(token)
                return payload
            
            # In production, implement proper JWT validation with Auth0's public key
            # This would involve fetching the JWKS from Auth0 and validating the signature
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                audience=self.auth0_audience
            )
            return payload
            
        except JWTError as e:
            logger.error(f"JWT decode error: {e}")
            return None
    
    def create_user(self, db: Session, user_data: UserCreate) -> User:
        """Create a new user."""
        try:
            # Hash password if provided (for local users)
            hashed_password = None
            if user_data.password:
                hashed_password = self.get_password_hash(user_data.password)
            
            db_user = User(
                email=user_data.email,
                full_name=user_data.full_name,
                hashed_password=hashed_password,
                auth0_user_id=user_data.auth0_user_id,
                profile_picture_url=user_data.profile_picture_url,
                phone_number=user_data.phone_number,
                date_of_birth=user_data.date_of_birth,
                emergency_contact_name=user_data.emergency_contact_name,
                emergency_contact_phone=user_data.emergency_contact_phone,
                preferences=user_data.preferences or {},
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            db.add(db_user)
            db.commit()
            db.refresh(db_user)
            
            logger.info(f"Created user: {db_user.email}")
            return db_user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {e}")
            raise
    
    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_auth0_id(self, db: Session, auth0_user_id: str) -> Optional[User]:
        """Get user by Auth0 user ID."""
        return db.query(User).filter(User.auth0_user_id == auth0_user_id).first()
    
    def update_user(self, db: Session, user_id: str, user_update: UserUpdate) -> Optional[User]:
        """Update user information."""
        try:
            db_user = self.get_user_by_id(db, user_id)
            if not db_user:
                return None
            
            update_data = user_update.model_dump(exclude_unset=True)
            
            # Handle password update
            if "password" in update_data:
                update_data["hashed_password"] = self.get_password_hash(update_data["password"])
                del update_data["password"]
            
            # Update fields
            for field, value in update_data.items():
                if hasattr(db_user, field):
                    setattr(db_user, field, value)
            
            db_user.updated_at = datetime.utcnow()
            
            db.commit()
            db.refresh(db_user)
            
            logger.info(f"Updated user: {db_user.email}")
            return db_user
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating user: {e}")
            raise
    
    def authenticate_user(self, db: Session, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password (for local development)."""
        user = self.get_user_by_email(db, email)
        if not user:
            return None
        
        if not user.hashed_password:
            return None  # User uses OAuth only
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def create_access_token_for_user(self, user: User) -> str:
        """Create access token for user."""
        return create_access_token(
            data={"sub": user.id, "email": user.email}
        )
    
    async def process_auth0_login(
        self, 
        db: Session, 
        access_token: str
    ) -> Optional[tuple[User, str]]:
        """Process Auth0 login and return user with token."""
        try:
            # Get user info from Auth0
            user_info = await self.get_auth0_user_info(access_token)
            if not user_info:
                return None
            
            auth0_user_id = user_info.get("sub")
            email = user_info.get("email")
            
            if not auth0_user_id or not email:
                logger.error("Missing required user info from Auth0")
                return None
            
            # Check if user exists
            user = self.get_user_by_auth0_id(db, auth0_user_id)
            
            if not user:
                # Create new user
                user_data = UserCreate(
                    email=email,
                    full_name=user_info.get("name", ""),
                    auth0_user_id=auth0_user_id,
                    profile_picture_url=user_info.get("picture"),
                    phone_number=user_info.get("phone_number")
                )
                user = self.create_user(db, user_data)
            else:
                # Update existing user with latest Auth0 info
                update_data = UserUpdate(
                    full_name=user_info.get("name", user.full_name),
                    profile_picture_url=user_info.get("picture", user.profile_picture_url),
                    phone_number=user_info.get("phone_number", user.phone_number)
                )
                user = self.update_user(db, user.id, update_data)
            
            if not user:
                return None
            
            # Update last login
            user.last_login_at = datetime.utcnow()
            db.commit()
            
            # Create our own access token
            token = self.create_access_token_for_user(user)
            
            return user, token
            
        except Exception as e:
            logger.error(f"Error processing Auth0 login: {e}")
            return None
    
    def get_current_user(self, db: Session, token: str) -> Optional[User]:
        """Get current user from token."""
        try:
            payload = self.decode_token(token)
            if not payload:
                return None
            
            user_id: str = payload.get("sub")
            if not user_id:
                return None
            
            user = self.get_user_by_id(db, user_id)
            if not user or not user.is_active:
                return None
            
            return user
            
        except Exception as e:
            logger.error(f"Error getting current user: {e}")
            return None
    
    def delete_user(self, db: Session, user_id: str) -> bool:
        """Soft delete user."""
        try:
            user = self.get_user_by_id(db, user_id)
            if not user:
                return False
            
            user.is_active = False
            user.updated_at = datetime.utcnow()
            
            db.commit()
            
            logger.info(f"Deleted user: {user.email}")
            return True
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error deleting user: {e}")
            return False
    
    def get_users(
        self, 
        db: Session, 
        skip: int = 0, 
        limit: int = 100,
        email_filter: Optional[str] = None
    ) -> List[User]:
        """Get list of users with pagination and filtering."""
        query = db.query(User).filter(User.is_active == True)
        
        if email_filter:
            query = query.filter(User.email.ilike(f"%{email_filter}%"))
        
        return query.offset(skip).limit(limit).all()
    
    async def send_password_reset_email(self, email: str) -> bool:
        """Send password reset email via Auth0."""
        try:
            async with httpx.AsyncClient() as client:
                # Get Auth0 management token
                token_response = await client.post(
                    f"https://{self.auth0_domain}/oauth/token",
                    json={
                        "client_id": self.auth0_client_id,
                        "client_secret": self.auth0_client_secret,
                        "audience": f"https://{self.auth0_domain}/api/v2/",
                        "grant_type": "client_credentials"
                    }
                )
                
                if token_response.status_code != 200:
                    logger.error(f"Failed to get Auth0 management token")
                    return False
                
                management_token = token_response.json()["access_token"]
                
                # Send password reset email
                reset_response = await client.post(
                    f"https://{self.auth0_domain}/api/v2/tickets/password-change",
                    headers={"Authorization": f"Bearer {management_token}"},
                    json={
                        "email": email,
                        "connection_id": "Username-Password-Authentication"  # Adjust as needed
                    }
                )
                
                return reset_response.status_code == 201
                
        except Exception as e:
            logger.error(f"Error sending password reset email: {e}")
            return False
    
    def get_auth0_login_url(self, redirect_uri: str) -> str:
        """Generate Auth0 login URL."""
        params = {
            "response_type": "code",
            "client_id": self.auth0_client_id,
            "redirect_uri": redirect_uri,
            "scope": "openid profile email",
            "audience": self.auth0_audience
        }
        
        return f"https://{self.auth0_domain}/authorize?" + urlencode(params)
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Optional[Dict[str, Any]]:
        """Exchange authorization code for access token."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://{self.auth0_domain}/oauth/token",
                    json={
                        "grant_type": "authorization_code",
                        "client_id": self.auth0_client_id,
                        "client_secret": self.auth0_client_secret,
                        "code": code,
                        "redirect_uri": redirect_uri
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Token exchange error: {response.status_code}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            return None


# Global auth service instance
auth_service = AuthService()
