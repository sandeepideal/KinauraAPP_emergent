"""
Authentication routes
"""
from fastapi import APIRouter, HTTPException, Depends, status, Response, Request
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
import aiohttp
import json
import base64
import hmac
import hashlib
from datetime import datetime, timedelta
import uuid
from ..deps import get_db, create_access_token
from typing import Optional

router = APIRouter(prefix="/auth", tags=["authentication"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Models
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    phone: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class SocialLogin(BaseModel):
    provider: str  # apple, google, facebook
    access_token: str
    full_name: str
    email: EmailStr

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

@router.post("/register")
async def register_user(user_data: UserCreate, db = Depends(get_db)):
    """Register a new user"""
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user_id = str(uuid.uuid4())
    hashed_password = get_password_hash(user_data.password)
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "full_name": user_data.full_name,
        "phone": user_data.phone,
        "password_hash": hashed_password,
        "role": "member",
        "membership_tier": "not_member",
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    await db.users.insert_one(user_doc)
    
    # Create access token
    access_token = create_access_token(data={"sub": user_id})
    
    # Remove password hash from response
    user_doc.pop("password_hash", None)
    user_doc.pop("_id", None)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_doc
    }

@router.post("/login")
async def login_user(login_data: UserLogin, response: Response, db = Depends(get_db)):
    """Login user with email/password"""
    user = await db.users.find_one({"email": login_data.email})
    
    if not user or not verify_password(login_data.password, user.get("password_hash", "")):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.get("is_active", True):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is disabled"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user["id"]})
    
    # Set HTTP-only cookie for web clients
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=1800  # 30 minutes
    )
    
    # Remove sensitive data from response
    user.pop("password_hash", None)
    user.pop("_id", None)
    
    return {
        "access_token": access_token,
        "token_type": "bearer", 
        "user": user
    }

@router.post("/social-login")
async def social_login(social_data: SocialLogin, response: Response, db = Depends(get_db)):
    """Login/register with social provider"""
    # Check if user exists
    user = await db.users.find_one({"email": social_data.email})
    
    if not user:
        # Create new user
        user_id = str(uuid.uuid4())
        user_doc = {
            "id": user_id,
            "email": social_data.email,
            "full_name": social_data.full_name,
            "role": "member",
            "membership_tier": "not_member",
            "created_at": datetime.utcnow(),
            "is_active": True,
            "social_provider": social_data.provider
        }
        await db.users.insert_one(user_doc)
        user = user_doc
    
    # Create access token
    access_token = create_access_token(data={"sub": user["id"]})
    
    # Set HTTP-only cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
        max_age=1800
    )
    
    # Clean user data
    user.pop("password_hash", None)
    user.pop("_id", None)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }

@router.post("/refresh")
async def refresh_token(request: Request, response: Response, db = Depends(get_db)):
    """Refresh access token from cookie"""
    token = request.cookies.get("access_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token found"
        )
    
    try:
        import jwt
        payload = jwt.decode(token, create_access_token.__globals__['SECRET_KEY'], algorithms=["HS256"])
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        
        # Generate new token
        new_token = create_access_token(data={"sub": user_id})
        
        # Set new cookie
        response.set_cookie(
            key="access_token",
            value=new_token,
            httponly=True,
            secure=True,
            samesite="lax", 
            path="/",
            max_age=1800
        )
        
        return {"access_token": new_token, "token_type": "bearer"}
        
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate token"
        )

@router.post("/logout")
async def logout(response: Response):
    """Logout user by clearing cookie"""
    response.delete_cookie("access_token", path="/")
    return {"message": "Successfully logged out"}

@router.post("/emergent-auth")
async def emergent_auth(request: Request, response: Response, db = Depends(get_db)):
    """Handle Emergent authentication callback"""
    import aiohttp
    import json
    
    # Get session ID from headers
    session_id = request.headers.get("X-Session-ID")
    
    if not session_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session ID required in X-Session-ID header"
        )
    
    # Call Emergent auth API to get user data
    try:
        async with aiohttp.ClientSession() as session:
            headers = {"X-Session-ID": session_id}
            async with session.get(
                "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
                headers=headers
            ) as resp:
                if resp.status != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid session"
                    )
                
                user_data = await resp.json()
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to validate session: {str(e)}"
        )
    
    # Extract user info from response
    user_id = user_data.get("id")
    email = user_data.get("email")
    name = user_data.get("name")
    picture = user_data.get("picture")
    session_token = user_data.get("session_token")
    
    if not all([user_id, email, session_token]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incomplete user data from Emergent"
        )
    
    # Check if user exists in our database
    existing_user = await db.users.find_one({"email": email})
    
    if existing_user:
        # Update session token but don't update user data
        user = existing_user
        user_db_id = user["user_id"]
    else:
        # Create new user
        user_db_id = str(uuid.uuid4())
        user = {
            "user_id": user_db_id,
            "email": email,
            "full_name": name,
            "profile_picture": picture,
            "auth_provider": "emergent",
            "emergent_user_id": user_id,
            "role": "patient",
            "membership_tier": "basic",
            "created_at": datetime.utcnow(),
            "last_login": datetime.utcnow(),
            "is_active": True
        }
        
        # Save new user to database
        await db.users.insert_one(user)
    
    # Save session token in sessions table
    session_data = {
        "session_id": str(uuid.uuid4()),
        "user_id": user_db_id,
        "session_token": session_token,
        "expires_at": datetime.utcnow() + timedelta(days=7),  # 7 days expiry
        "created_at": datetime.utcnow()
    }
    
    await db.sessions.insert_one(session_data)
    
    # Set HttpOnly cookie with session token
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",  # Required for cross-origin
        path="/",
        max_age=7 * 24 * 60 * 60  # 7 days in seconds
    )
    
    # Also create a JWT token for compatibility with existing system
    access_token = create_access_token(data={"sub": user_db_id})
    
    # Clean user data for response
    user.pop("_id", None)
    user.pop("password_hash", None)
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user,
        "session_token": session_token
    }

@router.post("/apple")
async def apple_login(request: Request, db = Depends(get_db)):
    """Handle Apple Sign In authentication"""
    from jose import jwt, JWTError
    import os
    
    try:
        body = await request.json()
        identity_token = body.get("identity_token")
        user_data = body.get("user", {})
        
        if not identity_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Identity token required"
            )
        
        # For demo purposes, decode without signature verification
        # In production, implement proper Apple key verification
        try:
            decoded_token = jwt.decode(
                identity_token, 
                options={"verify_signature": False, "verify_exp": False, "verify_aud": False}
            )
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Apple token: {str(e)}"
            )
        
        # Extract user information
        provider_id = decoded_token.get("sub")
        email = decoded_token.get("email")
        email_verified = decoded_token.get("email_verified", False)
        
        # Extract name from user_data if available (only on first login)
        name = None
        if user_data and "name" in user_data:
            first_name = user_data["name"].get("firstName", "")
            last_name = user_data["name"].get("lastName", "")
            name = f"{first_name} {last_name}".strip()
        
        if not provider_id or not email:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incomplete user data from Apple"
            )
        
        # Check if user exists
        existing_user = await db.users.find_one({
            "$or": [
                {"email": email},
                {"provider_id": provider_id, "auth_provider": "apple"}
            ]
        })
        
        if existing_user:
            # Update existing user
            user_db_id = existing_user["user_id"]
            update_data = {
                "last_login": datetime.utcnow(),
                "email_verified": email_verified or existing_user.get("email_verified", False)
            }
            
            # Update name if not set or if new name is provided
            if name and not existing_user.get("full_name"):
                update_data["full_name"] = name
            
            await db.users.update_one(
                {"user_id": user_db_id},
                {"$set": update_data}
            )
            
            user = {**existing_user, **update_data}
        else:
            # Create new user
            user_db_id = str(uuid.uuid4())
            user = {
                "user_id": user_db_id,
                "email": email,
                "full_name": name,
                "auth_provider": "apple",
                "provider_id": provider_id,
                "email_verified": email_verified,
                "role": "patient",
                "membership_tier": "basic",
                "created_at": datetime.utcnow(),
                "last_login": datetime.utcnow(),
                "is_active": True
            }
            
            await db.users.insert_one(user)
        
        # Create JWT token
        access_token = create_access_token(data={"sub": user_db_id})
        
        # Clean user data for response
        user_response = user.copy()
        user_response.pop("_id", None)
        user_response.pop("password_hash", None)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_info": user_response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during Apple authentication: {str(e)}"
        )

@router.post("/facebook")
async def facebook_login(request: Request, db = Depends(get_db)):
    """Handle Facebook Login authentication"""
    import os
    
    try:
        body = await request.json()
        access_token = body.get("access_token")
        user_data = body.get("user_data", {})
        
        if not access_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Access token required"
            )
        
        # Verify Facebook access token
        async with aiohttp.ClientSession() as session:
            # Get user information from Facebook
            fb_url = "https://graph.facebook.com/me"
            fb_params = {
                "access_token": access_token,
                "fields": "id,name,email,verified,picture"
            }
            
            async with session.get(fb_url, params=fb_params) as resp:
                if resp.status != 200:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Invalid Facebook token"
                    )
                
                fb_user_data = await resp.json()
            
            # Verify token belongs to our app (optional but recommended)
            app_id = os.getenv("FACEBOOK_APP_ID")
            if app_id:
                debug_url = "https://graph.facebook.com/debug_token"
                debug_params = {
                    "input_token": access_token,
                    "access_token": f"{app_id}|{os.getenv('FACEBOOK_APP_SECRET', '')}"
                }
                
                async with session.get(debug_url, params=debug_params) as debug_resp:
                    if debug_resp.status == 200:
                        debug_data = await debug_resp.json()
                        token_data = debug_data.get("data", {})
                        if not token_data.get("is_valid", False):
                            raise HTTPException(
                                status_code=status.HTTP_401_UNAUTHORIZED,
                                detail="Invalid Facebook token"
                            )
        
        # Extract user information
        provider_id = fb_user_data.get("id")
        email = fb_user_data.get("email")
        name = fb_user_data.get("name")
        verified = fb_user_data.get("verified", False)
        picture = fb_user_data.get("picture", {}).get("data", {}).get("url")
        
        if not provider_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incomplete user data from Facebook"
            )
        
        # Check if user exists
        existing_user = await db.users.find_one({
            "$or": [
                {"email": email} if email else {"provider_id": provider_id},
                {"provider_id": provider_id, "auth_provider": "facebook"}
            ]
        })
        
        if existing_user:
            # Update existing user
            user_db_id = existing_user["user_id"]
            update_data = {
                "last_login": datetime.utcnow(),
                "email_verified": verified or existing_user.get("email_verified", False)
            }
            
            # Update profile info
            if name:
                update_data["full_name"] = name
            if picture:
                update_data["profile_picture"] = picture
            
            await db.users.update_one(
                {"user_id": user_db_id},
                {"$set": update_data}
            )
            
            user = {**existing_user, **update_data}
        else:
            # Create new user
            user_db_id = str(uuid.uuid4())
            user = {
                "user_id": user_db_id,
                "email": email or f"facebook_{provider_id}@temp.com",
                "full_name": name,
                "auth_provider": "facebook",
                "provider_id": provider_id,
                "email_verified": verified,
                "profile_picture": picture,
                "role": "patient",
                "membership_tier": "basic",
                "created_at": datetime.utcnow(),
                "last_login": datetime.utcnow(),
                "is_active": True
            }
            
            await db.users.insert_one(user)
        
        # Create JWT token
        access_token = create_access_token(data={"sub": user_db_id})
        
        # Clean user data for response
        user_response = user.copy()
        user_response.pop("_id", None)
        user_response.pop("password_hash", None)
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user_info": user_response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during Facebook authentication: {str(e)}"
        )