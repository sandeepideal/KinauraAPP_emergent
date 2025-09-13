# Enhanced Authentication Service with HttpOnly Cookies and Secure Storage
# Implements secure token management, refresh cycles, and CSRF protection

import os
import uuid
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple

import jwt
from fastapi import HTTPException, Response, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext

from motor.motor_asyncio import AsyncIOMotorClient

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Configuration
SECRET_KEY = os.environ.get("SECRET_KEY", "kinaura-secret-key-2024")
REFRESH_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "kinaura-refresh-secret-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # Short-lived access tokens
REFRESH_TOKEN_EXPIRE_DAYS = 7     # Longer-lived refresh tokens

# Cookie Configuration
ACCESS_COOKIE_NAME = "__Host-kna.sid"
REFRESH_COOKIE_NAME = "__Host-kna.r"
CSRF_COOKIE_NAME = "__Host-kna.csrf"

class SecureAuthService:
    """Enhanced authentication service with secure token management"""
    
    def __init__(self, db_client):
        self.db = db_client
        self.security = HTTPBearer(auto_error=False)
    
    def create_access_token(self, data: dict) -> str:
        """Create short-lived access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        to_encode.update({
            "exp": expire,
            "type": "access",
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())  # JWT ID for blacklisting
        })
        return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create long-lived refresh token"""
        to_encode = {
            "sub": user_id,
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            "iat": datetime.utcnow(),
            "jti": str(uuid.uuid4())
        }
        return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)
    
    def create_csrf_token(self) -> str:
        """Create CSRF token for double-submit protection"""
        return secrets.token_urlsafe(32)
    
    def set_auth_cookies(self, response: Response, user_data: Dict[str, Any], 
                        csrf_token: str) -> Tuple[str, str]:
        """Set secure authentication cookies"""
        
        # Create tokens
        access_token = self.create_access_token({
            "sub": user_data["id"],
            "email": user_data["email"],
            "role": user_data["role"],
            "csrf": csrf_token
        })
        
        refresh_token = self.create_refresh_token(user_data["id"])
        
        # Security flags
        is_production = os.environ.get("ENVIRONMENT", "development") == "production"
        secure_flag = is_production
        domain = None  # Let browser determine domain
        
        # Set access token cookie (short-lived)
        response.set_cookie(
            key=ACCESS_COOKIE_NAME,
            value=access_token,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            expires=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            path="/",
            domain=domain,
            secure=secure_flag,
            httponly=True,
            samesite="lax"  # Allow cross-site for mobile apps
        )
        
        # Set refresh token cookie (long-lived)
        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=refresh_token,
            max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
            expires=datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
            path="/api/auth/refresh",  # Only sent to refresh endpoint
            domain=domain,
            secure=secure_flag,
            httponly=True,
            samesite="strict"  # Strict for refresh token
        )
        
        # Set CSRF token cookie (readable by JavaScript)
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=csrf_token,
            max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            expires=datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
            path="/",
            domain=domain,
            secure=secure_flag,
            httponly=False,  # JavaScript needs to read this
            samesite="lax"
        )
        
        return access_token, refresh_token

# Global auth service instance
auth_service = None

def get_auth_service():
    """Get global auth service instance"""
    global auth_service
    if auth_service is None:
        # Import here to avoid circular imports
        from motor.motor_asyncio import AsyncIOMotorClient
        import os
        
        mongo_url = os.environ['MONGO_URL']
        client = AsyncIOMotorClient(mongo_url)
        db = client[os.environ.get('DB_NAME', 'kinaura_db')]
        
        auth_service = SecureAuthService(db)
    
    return auth_service