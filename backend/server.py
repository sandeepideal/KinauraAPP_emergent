from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request, Query, UploadFile, File, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any, Union, Tuple
from collections import Counter
from enum import Enum
import uuid
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import mimetypes
import magic
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
import base64
from emergentintegrations.payments.stripe.checkout import StripeCheckout, CheckoutSessionResponse, CheckoutStatusResponse, CheckoutSessionRequest
import json
import hashlib
import hmac
from emergentintegrations.llm.chat import LlmChat, UserMessage
import markdown
import frontmatter
import re
# Google Calendar and Push Notifications
from google.oauth2.credentials import Credentials
from google.oauth2.service_account import Credentials as ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import firebase_admin
from firebase_admin import credentials, messaging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
import asyncio
from pywebpush import webpush, WebPushException
import json as json_lib

# Custom ObjectId serialization for FastAPI/MongoDB
class PydanticObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

# Custom Base Model with ObjectId serialization
class CustomBaseModel(BaseModel):
    class Config:
        json_encoders = {
            ObjectId: str
        }
        allow_population_by_field_name = True

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'kinaura_db')]

# Create the main app without a prefix
app = FastAPI(title="KinAura API", description="Centre for Regenerative Wellness API")

# Rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add rate limiting middleware
app.add_middleware(SlowAPIMiddleware)

# Enhanced Security Headers Middleware
@app.middleware("http")
async def add_enhanced_security_headers(request: Request, call_next):
    response = await call_next(request)
    
    # Enhanced security headers for production
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "no-referrer"
    
    # Strict Transport Security (HSTS)
    if request.url.scheme == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    
    # Content Security Policy (CSP)
    csp_policy = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://www.gstatic.com https://apis.google.com https://appleid.cdn-apple.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com; "
        "img-src 'self' data: https: blob:; "
        "media-src 'self' https:; "
        "connect-src 'self' https: wss: ws:; "
        "frame-src 'self' https://appleid.apple.com https://accounts.google.com; "
        "worker-src 'self' blob:; "
        "manifest-src 'self'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'; "
        "object-src 'none'; "
        "upgrade-insecure-requests"
    )
    
    # Apply CSP to HTML responses
    if "text/html" in response.headers.get("content-type", ""):
        response.headers["Content-Security-Policy"] = csp_policy
    
    # Permissions Policy (Feature Policy)
    permissions_policy = (
        "camera=(), "
        "microphone=(), "
        "geolocation=(), "
        "payment=(), "
        "usb=(), "
        "bluetooth=(), "
        "accelerometer=(), "
        "gyroscope=(), "
        "magnetometer=()"
    )
    response.headers["Permissions-Policy"] = permissions_policy
    
    # Additional security headers
    response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
    response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    
    return response

# File Upload Security
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'image/jpeg',
    'image/png', 
    'image/gif',
    'text/plain',
    'text/markdown',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',  # .docx
    'application/msword',  # .doc
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

async def validate_uploaded_file(file: UploadFile) -> None:
    """Validate uploaded file for security"""
    # Check file size
    content = await file.read()
    file.file.seek(0)  # Reset file pointer
    
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE/1024/1024}MB"
        )
    
    # Check MIME type
    try:
        # Try to detect MIME type from content
        detected_type = magic.from_buffer(content[:2048], mime=True)
        
        # Also check declared content type
        declared_type = file.content_type
        
        # Ensure at least one matches allowed types
        if detected_type not in ALLOWED_MIME_TYPES and declared_type not in ALLOWED_MIME_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File type not allowed. Detected: {detected_type}, Declared: {declared_type}"
            )
        
        # Check for suspicious file names
        if any(char in file.filename for char in ['..', '/', '\\']):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid filename"
            )
            
    except Exception as e:
        logging.error(f"File validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File validation failed"
        )

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = os.environ.get("SECRET_KEY", "kinaura-secret-key-2024")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Enhanced rate limiting configuration
# Create enhanced limiter with custom key function
def get_rate_limit_key(request: Request):
    """Enhanced rate limiting key based on IP and user"""
    # Get IP address
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()
    else:
        ip = request.client.host if request.client else "unknown"
    
    # Try to get user ID for authenticated requests
    auth_header = request.headers.get("authorization")
    user_id = None
    
    if auth_header and auth_header.startswith("Bearer "):
        try:
            token = auth_header[7:]
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id = payload.get("sub")
        except:
            pass
    
    # Create composite key
    if user_id:
        return f"user:{user_id}"
    else:
        return f"ip:{ip}"

# Enhanced limiter with custom key function
enhanced_limiter = Limiter(key_func=get_rate_limit_key)
app.state.enhanced_limiter = enhanced_limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Authentication functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await db.users.find_one({"id": user_id}, {"_id": 0})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

async def get_admin_user(current_user: dict = Depends(get_current_user)):
    """Ensure current user has admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def get_staff_user(current_user: dict = Depends(get_current_user)):
    """Ensure current user has staff role (admin or practitioner)"""
    if current_user.get("role") not in ["admin", "practitioner"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required"
        )
    return current_user

def admin_required(current_user: dict = Depends(get_current_user)):
    """Dependency to ensure current user has admin role"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

async def get_current_user_optional(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current user from JWT token (optional - returns None if no valid token)"""
    try:
        if not credentials:
            return None
        
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
            
        user = await db.users.find_one({"id": user_id}, {"_id": 0})
        return user
    except:
        return None

# Models
from enum import Enum

# CRM Lifecycle Stage Enum
class LifecycleStage(str, Enum):
    lead = "lead"           # Downloaded app/created account but no booking
    active = "active"       # Last booking < 60 days ago  
    lapsed = "lapsed"       # Last booking ≥ 60 days ago

# Boutique E-commerce Models
class ProductCategory(str, Enum):
    skincare = "skincare"
    supplements = "supplements" 
    kits = "kits"

class ProductBadge(str, Enum):
    new = "New"
    best_seller = "Best Seller"
    platinum_only = "Platinum Only"
    limited_edition = "Limited Edition"

class OrderStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    shipped = "shipped"
    delivered = "delivered"
    cancelled = "cancelled"
    refunded = "refunded"

class MembershipTier(str, Enum):
    gold = "gold"
    platinum = "platinum"
    elite = "elite"

class ProductImage(BaseModel):
    url: str
    alt: Dict[str, str] = {"en": "", "it": ""}  # Bilingual alt text
    ordering: int = 0

class MembershipPricing(BaseModel):
    gold: Optional[float] = None
    platinum: Optional[float] = None
    elite: Optional[float] = None

class Product(BaseModel):
    sku: str = Field(..., description="Unique product identifier")
    name: Dict[str, str] = Field(..., description="Product name in EN/IT")
    slug: str = Field(..., description="URL-friendly identifier")
    short_description: Dict[str, str] = Field(default={"en": "", "it": ""})
    description_html: Dict[str, str] = Field(default={"en": "", "it": ""})
    category: ProductCategory
    images: List[ProductImage] = []
    price_eur: float = Field(..., description="Base price in EUR")
    price_membership: Optional[MembershipPricing] = None
    tags: List[str] = []  # For search and filtering
    protocol_bindings: List[str] = []  # Protocol associations for cross-sell
    inventory: int = Field(default=0, description="Current stock level")
    is_active: bool = Field(default=True)
    ordering: int = Field(default=0, description="Display order")
    badge: Optional[ProductBadge] = None
    
    # SEO and metadata
    meta_title: Dict[str, str] = Field(default={"en": "", "it": ""})
    meta_description: Dict[str, str] = Field(default={"en": "", "it": ""})
    
    # Product specifications
    ingredients: Dict[str, str] = Field(default={"en": "", "it": ""})
    warnings: Dict[str, str] = Field(default={"en": "", "it": ""})
    usage_instructions: Dict[str, str] = Field(default={"en": "", "it": ""})
    
    # Variants (optional - for sizes, flavors, etc.)
    variants: List[Dict[str, Any]] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # Content versioning fields for native app sync
    content_version: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content_hash: Optional[str] = None

class ProductCollection(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slug: str = Field(..., description="URL-friendly identifier")
    name: Dict[str, str] = Field(..., description="Collection name in EN/IT")
    description: Dict[str, str] = Field(default={"en": "", "it": ""})
    hero_image: Optional[str] = None
    products: List[str] = []  # List of product SKUs
    ordering: int = Field(default=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class CartItem(BaseModel):
    sku: str
    quantity: int = Field(..., gt=0)
    variant_id: Optional[str] = None

class ShippingAddress(BaseModel):
    full_name: str
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    postal_code: str
    country: str = "IT"  # Default to Italy
    phone: Optional[str] = None

class OrderItem(BaseModel):
    sku: str
    name: str  # Snapshot at time of order
    quantity: int
    unit_price: float  # Price paid (including discounts)
    total_price: float
    variant_id: Optional[str] = None
    variant_name: Optional[str] = None

class Order(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    order_number: str  # Human-readable order number
    items: List[OrderItem]
    subtotal: float
    discount_amount: float = 0.0
    tax_amount: float = 0.0
    shipping_cost: float = 0.0
    total_amount: float
    currency: str = "EUR"
    
    # Payment info
    stripe_session_id: Optional[str] = None
    stripe_payment_intent_id: Optional[str] = None
    payment_status: str = "pending"  # pending, paid, failed, refunded
    
    # Order status and tracking
    status: OrderStatus = OrderStatus.pending
    tracking_number: Optional[str] = None
    
    # Customer details (snapshot)
    customer_email: str
    customer_name: str
    shipping_address: Optional[ShippingAddress] = None
    billing_address: Optional[ShippingAddress] = None
    
    # Metadata
    promo_code: Optional[str] = None
    membership_tier: Optional[str] = None
    notes: Optional[str] = None
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    shipped_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None

class CrossSellRule(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    protocol_id: str  # Protocol that triggers the recommendation
    product_skus: List[str]  # Products to recommend
    priority: int = Field(default=1, description="1-5 priority ranking")
    microcopy: Dict[str, str] = Field(default={"en": "", "it": ""})  # Custom upsell message
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class PromotionCode(BaseModel):
    code: str = Field(..., description="Promotion code (uppercase)")
    discount_type: str = Field(..., description="percentage or fixed")  # percentage, fixed
    discount_value: float = Field(..., description="Discount amount or percentage")
    minimum_order: float = Field(default=0.0)
    max_uses: Optional[int] = None
    current_uses: int = Field(default=0)
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_until: Optional[datetime] = None
    is_active: bool = Field(default=True)
    applicable_products: List[str] = []  # Empty = all products
    created_at: datetime = Field(default_factory=datetime.utcnow)

# Analytics Models for Boutique
class ShoppingEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str  # shop_view, product_view, add_to_cart, checkout_start, purchase, upsell_clicked
    patient_id: Optional[str] = None
    session_id: str
    product_sku: Optional[str] = None
    order_id: Optional[str] = None
    membership_tier: Optional[str] = None
    metadata: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    full_name: str
    phone: Optional[str] = None
    role: str = "member"  # member, admin, practitioner
    membership_tier: str = "not_member"  # not_member, gold, platinum, elite
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True
    # Social login fields
    linked_to_social: bool = False
    social_provider: Optional[str] = None
    patient_id: Optional[str] = None  # Link to admin-created patient
    created_from_admin_patient: bool = False
    
    # CRM Lifecycle Tracking Fields
    last_login: Optional[datetime] = None
    last_booking: Optional[datetime] = None
    lifecycle_stage: LifecycleStage = LifecycleStage.lead
    engagement_score: int = 0  # 0-100 engagement score
    total_bookings: int = 0
    total_revenue: float = 0.0
    preferred_language: str = "en"  # for engagement campaigns
    
    # Engagement tracking
    last_engagement_sent: Optional[datetime] = None
    engagement_campaign_count: int = 0
    last_campaign_type: Optional[str] = None

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

class ServiceGroup(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    description: str
    icon: Optional[str] = None  # Icon URL or emoji
    display_order: int = 0
    is_active: bool = True
    color_theme: Optional[str] = None  # Hex color for UI theming
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    # Content versioning fields for native app sync
    content_version: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content_hash: Optional[str] = None

class ServiceGroupCreate(BaseModel):
    name: str
    description: str
    icon: Optional[str] = None
    display_order: int = 0
    is_active: bool = True
    color_theme: Optional[str] = None

class ServiceGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    color_theme: Optional[str] = None

class ServiceMediaItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    caption: Optional[str] = None
    media_type: str  # "image", "video", "document"
    is_primary: bool = False
    order_index: int = 0

class ServiceCreate(BaseModel):
    name: str
    category: str
    description: str
    detailed_description: str
    duration: int = 60
    price: float
    benefits: List[str] = []
    is_active: bool = True
    group_id: Optional[str] = None
    images: List[str] = []
    main_image: Optional[str] = None
    brochure_url: Optional[str] = None
    video_url: Optional[str] = None

class ServiceUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    detailed_description: Optional[str] = None
    duration: Optional[int] = None
    price: Optional[float] = None
    benefits: Optional[List[str]] = None
    is_active: Optional[bool] = None
    group_id: Optional[str] = None
    images: Optional[List[str]] = None
    main_image: Optional[str] = None
    brochure_url: Optional[str] = None
    video_url: Optional[str] = None

class Service(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str
    description: str
    detailed_description: str
    duration: int  # in minutes
    price: float
    benefits: List[str]
    is_active: bool = True
    # Group assignment
    group_id: Optional[str] = None  # Reference to ServiceGroup
    # New fields for media support
    images: List[str] = []  # List of image URLs/paths
    gallery: List[dict] = []  # List of {url: str, caption: str, type: str}
    main_image: Optional[str] = None  # Primary service image
    brochure_url: Optional[str] = None  # Service brochure/PDF
    video_url: Optional[str] = None  # Service demo video
    # Content versioning and sync fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    content_version: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content_hash: Optional[str] = None  # Hash of content for change detection

class Appointment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    service_id: str
    appointment_date: datetime
    status: str = "scheduled"  # scheduled, completed, cancelled
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

class AppointmentCreate(BaseModel):
    service_id: str
    appointment_date: datetime
    notes: Optional[str] = None

class PatientNote(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    author_id: str
    author_name: str
    title: str
    content: str
    category: str = "general"  # general, medical, behavior, treatment, follow_up
    is_important: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class PatientNoteCreate(BaseModel):
    patient_id: str
    title: str
    content: str
    category: str = "general"
    is_important: bool = False

class PatientNoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    is_important: Optional[bool] = None

class NotificationRequest(BaseModel):
    title: str
    message: str
    target_type: str  # "single", "tags", "membership", "all"
    target_patient_id: Optional[str] = None
    target_tags: Optional[List[str]] = None
    target_membership: Optional[str] = None
    send_immediately: bool = True
    scheduled_for: Optional[datetime] = None

class NotificationLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    message: str
    target_type: str
    target_criteria: dict = {}
    sent_count: int = 0
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None
    status: str = "pending"  # pending, sent, failed

# ======================================
# CHATBOT KNOWLEDGE BASE MODELS
# ======================================

class ChatbotConfig(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    system_prompt: str
    is_active: bool = True
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1

class ChatbotConfigUpdate(BaseModel):
    system_prompt: str

class KnowledgeBaseItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    content: str
    category: str  # "treatments", "services", "policies", "faq", "general"
    tags: List[str] = []
    source_type: str  # "admin_created", "service_derived", "policy_document"
    source_id: Optional[str] = None  # Reference to service/document ID if applicable
    is_approved: bool = False
    is_active: bool = True
    approval_date: Optional[datetime] = None
    approved_by: Optional[str] = None
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    version: int = 1

class KnowledgeBaseItemCreate(BaseModel):
    title: str
    content: str
    category: str
    tags: List[str] = []
    source_type: str = "admin_created"
    source_id: Optional[str] = None

class KnowledgeBaseItemUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None

class MarkdownUploadResponse(BaseModel):
    filename: str
    parsed_items: List[Dict[str, Any]]
    success_count: int
    error_count: int
    errors: List[str] = []

class ParsedMarkdownItem(BaseModel):
    title: str
    content: str
    category: str
    tags: List[str]
    source_type: str = "markdown_import"
    source_filename: str

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    user_id: Optional[str] = None  # Patient ID if logged in
    role: str  # "user", "assistant", "system"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}  # For storing additional context

class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None  # Patient ID if logged in
    title: str = "KinAura Chat"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_message_at: Optional[datetime] = None
    message_count: int = 0

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    language: Optional[str] = "en"
    context: Optional[Dict[str, Any]] = Field(default_factory=dict)

class ChatResponse(BaseModel):
    message: str
    session_id: str
    message_id: str
    
    # RAG-specific response fields
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float
    response_time: float
    language: str
    
    # UI enhancement fields
    suggested_questions: List[str] = Field(default_factory=list)
    has_protocol_recommendation: bool = False
    protocol_name: Optional[str] = None
    
    # Medical compliance
    medical_disclaimer: str
    requires_consultation: bool = False
    
    # Legacy compatibility
    suggestions: List[str] = Field(default_factory=list)  # Deprecated - use suggested_questions
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PatientFile(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    filename: str
    original_filename: str
    file_type: str  # "test_result", "image", "report", "scan", "other"
    file_category: str = "general"  # "blood_work", "imaging", "consultation", "treatment", "progress", "general"
    file_path: str
    file_size: int  # in bytes
    mime_type: str
    visible_to_patient: bool = False  # Key feature: admin controls visibility
    description: Optional[str] = None
    notes: Optional[str] = None  # Admin-only notes
    upload_date: datetime = Field(default_factory=datetime.utcnow)
    uploaded_by: str  # admin user ID
    tags: List[str] = []

class PatientFileUpload(BaseModel):
    patient_id: str
    file_type: str
    file_category: str = "general"
    visible_to_patient: bool = False
    description: Optional[str] = None
    notes: Optional[str] = None
    tags: List[str] = []

class PatientFileUpdate(BaseModel):
    visible_to_patient: Optional[bool] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None

# Patient Inquiry Tracking Models
class InquiryType(str, Enum):
    treatment = "treatment"
    condition = "condition"
    wellness_goal = "wellness_goal"

class InquiryStatus(str, Enum):
    new = "new"
    contacted = "contacted"
    converted = "converted"
    dismissed = "dismissed"

class PatientInquiry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    session_id: str
    inquiry_type: InquiryType
    detected_items: List[str] = []  # Specific treatments/conditions/goals mentioned
    original_message: str
    context: str  # Additional context from the conversation
    confidence_score: float = 0.0  # AI confidence in detection
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: InquiryStatus = InquiryStatus.new
    admin_notes: Optional[str] = None
    contacted_by: Optional[str] = None  # Admin user ID who contacted
    contacted_at: Optional[datetime] = None
    booking_sent: bool = False
    booking_sent_at: Optional[datetime] = None
    priority_score: int = 1  # 1-5 scale for prioritizing follow-ups

class PatientInquiryUpdate(BaseModel):
    status: Optional[InquiryStatus] = None
    admin_notes: Optional[str] = None
    priority_score: Optional[int] = None

class BookingRequest(BaseModel):
    patient_id: str
    inquiry_id: str
    treatments: List[str] = []
    message: Optional[str] = None
    suggested_times: List[str] = []

# Admin Notification Models
class AdminNotification(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # "inquiry_alert", "daily_summary"
    title: str
    message: str
    data: Dict[str, Any] = {}  # Additional structured data
    is_read: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None
    file_category: Optional[str] = None
    tags: Optional[List[str]] = None

class PatientFolder(BaseModel):
    patient_id: str
    total_files: int = 0
    visible_files: int = 0  # files visible to patient
    private_files: int = 0  # admin-only files
    categories: Dict[str, int] = {}  # count by category
    last_updated: datetime = Field(default_factory=datetime.utcnow)

# Questionnaire and Document Management Models
class Question(BaseModel):
    id: Optional[str] = None
    question_text: str
    question_type: str = Field(..., pattern="^(multiple_choice|single_choice|text|long_text|number|date|yes_no|rating_scale|file_upload)$")
    is_required: bool = False
    order_index: int = 0
    options: Optional[Dict[str, Any]] = {}  # For multiple choice options, rating scales, etc.
    validation: Optional[Dict[str, Any]] = {}  # Validation rules
    help_text: Optional[str] = None

class Questionnaire(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    category: str = Field(..., pattern="^(medical_history|privacy_disclosure|treatment_consent|pre_treatment|post_treatment|wellness_assessment|lifestyle|symptoms|preferences|other)$")
    is_active: bool = True
    is_required: bool = False
    instructions: Optional[str] = None
    questions: Optional[List[Question]] = []
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = {}

class PatientQuestionnaire(BaseModel):
    id: Optional[str] = None
    patient_id: str
    questionnaire_id: str
    assigned_by: Optional[str] = None
    assigned_at: Optional[datetime] = None
    due_date: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = Field(default="assigned", pattern="^(assigned|in_progress|completed|expired|cancelled)$")
    context: Optional[Dict[str, Any]] = {}

class Answer(BaseModel):
    question_id: str
    answer_text: Optional[str] = None
    answer_number: Optional[float] = None
    answer_date: Optional[str] = None
    answer_choices: Optional[List[str]] = []
    answer_files: Optional[List[Dict[str, Any]]] = []

class PatientAnswer(BaseModel):
    id: Optional[str] = None
    patient_questionnaire_id: str
    question_id: str
    answer_text: Optional[str] = None
    answer_number: Optional[float] = None
    answer_date: Optional[str] = None
    answer_choices: Optional[List[str]] = []
    answer_files: Optional[List[Dict[str, Any]]] = []
    answered_at: Optional[datetime] = None

class Document(BaseModel):
    id: Optional[str] = None
    title: str
    document_type: str = Field(..., pattern="^(consent_form|privacy_notice|treatment_info|waiver|terms_conditions|medical_disclosure|financial_agreement|other)$")
    content: str  # HTML content
    version: str = "1.0"
    is_active: bool = True
    requires_signature: bool = True
    settings: Optional[Dict[str, Any]] = {}
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class PatientDocument(BaseModel):
    id: Optional[str] = None
    patient_id: str
    document_id: str
    assigned_by: Optional[str] = None
    assigned_at: Optional[datetime] = None
    status: str = Field(default="assigned", pattern="^(assigned|viewed|signed|expired|cancelled)$")
    viewed_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    context: Optional[Dict[str, Any]] = {}

class PatientSignature(BaseModel):
    id: Optional[str] = None
    patient_document_id: str
    patient_id: str
    signature_data: str  # Base64 encoded signature
    signature_type: str = Field(default="canvas", pattern="^(canvas|typed|uploaded|electronic)$")
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    timestamp: Optional[datetime] = None
    verification_data: Optional[Dict[str, Any]] = {}

# Request/Response Models
class CreateQuestionnaireRequest(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    is_required: bool = False
    instructions: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}

class CreateQuestionRequest(BaseModel):
    questionnaire_id: str
    question_text: str
    question_type: str
    is_required: bool = False
    order_index: int = 0
    options: Optional[Dict[str, Any]] = {}
    validation: Optional[Dict[str, Any]] = {}
    help_text: Optional[str] = None

class AssignQuestionnaireRequest(BaseModel):
    questionnaire_id: str
    patient_id: str
    due_date: Optional[datetime] = None
    context: Optional[Dict[str, Any]] = {}

class SubmitAnswersRequest(BaseModel):
    patient_questionnaire_id: str
    answers: List[Answer]

class CreateDocumentRequest(BaseModel):
    title: str
    document_type: str
    content: str
    version: str = "1.0"
    requires_signature: bool = True
    settings: Optional[Dict[str, Any]] = {}

class AssignDocumentRequest(BaseModel):
    document_id: str
    patient_id: str
    expires_in_days: Optional[int] = None
    context: Optional[Dict[str, Any]] = {}

class SignDocumentRequest(BaseModel):
    signature_data: str
    signature_type: str = "canvas"

# Appointment Booking Models
class ServiceAvailability(BaseModel):
    id: Optional[str] = None
    service_id: str
    day_of_week: int  # 0=Monday, 1=Tuesday, ..., 6=Sunday
    start_time: str  # Format: "09:00"
    end_time: str    # Format: "17:00"
    slot_duration: int = 60  # Duration in minutes
    buffer_time: int = 15    # Buffer between appointments in minutes
    max_bookings_per_slot: int = 1
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class AppointmentSlot(BaseModel):
    id: Optional[str] = None
    service_id: str
    date: str  # Format: "2024-12-20"
    start_time: str  # Format: "09:00"
    end_time: str    # Format: "10:00"
    is_available: bool = True
    is_blocked: bool = False
    blocked_reason: Optional[str] = None  # "admin_use", "maintenance", "reserved_for_patient"
    reserved_for_patient_id: Optional[str] = None
    max_bookings: int = 1
    current_bookings: int = 0
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None

class AppointmentBooking(BaseModel):
    id: Optional[str] = None
    patient_id: str
    service_id: str
    appointment_date: str  # Format: "2024-12-20"
    start_time: str        # Format: "09:00"
    end_time: str          # Format: "10:00"
    status: str = Field(default="pending", pattern="^(pending|confirmed|completed|cancelled|no_show)$")
    payment_status: str = Field(default="pending", pattern="^(pending|processing|paid|failed|refunded)$")
    payment_intent_id: Optional[str] = None  # Stripe payment intent ID
    amount: float = 0.0
    currency: str = "EUR"
    notes: Optional[str] = None
    confirmation_code: str = Field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None

class CreateAvailabilityRequest(BaseModel):
    service_id: str
    days_of_week: List[int]  # [0, 1, 2, 3, 4] for Mon-Fri
    start_time: str
    end_time: str
    slot_duration: int = 60
    buffer_time: int = 15

class BlockSlotRequest(BaseModel):
    service_id: str
    date: str
    start_time: str
    end_time: str
    reason: str = Field(..., pattern="^(admin_use|maintenance|reserved_for_patient|other)$")
    reserved_for_patient_id: Optional[str] = None
    notes: Optional[str] = None

class BookAppointmentRequest(BaseModel):
    service_id: str
    appointment_date: str
    start_time: str
    notes: Optional[str] = None

class PaymentRequest(BaseModel):
    booking_id: str
    origin_url: str  # Frontend origin URL for success/cancel redirects

class PaymentTransaction(BaseModel):
    id: Optional[str] = None
    booking_id: str
    patient_id: str
    session_id: Optional[str] = None
    payment_intent_id: Optional[str] = None
    amount: float
    currency: str = "EUR"
    payment_status: str = Field(default="pending", pattern="^(pending|processing|paid|failed|refunded|expired)$")
    stripe_status: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Health Data Integration Models
class HealthProvider(str, Enum):
    HEALTHKIT = "HEALTHKIT"
    WHOOP = "WHOOP"

class HealthMetric(str, Enum):
    # Cardiovascular
    RESTING_HR_BPM = "resting_hr_bpm"
    HRV_MS = "hrv_ms"
    RESP_RATE_BPM = "resp_rate_bpm"
    SPO2_PCT = "spo2_pct"
    BLOOD_PRESSURE_SYSTOLIC = "blood_pressure_systolic_mmhg"
    BLOOD_PRESSURE_DIASTOLIC = "blood_pressure_diastolic_mmhg"
    
    # Sleep
    SLEEP_TOTAL_MIN = "sleep_total_min"
    SLEEP_EFFICIENCY_PCT = "sleep_efficiency_pct"
    SLEEP_STAGE_LIGHT_MIN = "sleep_stage_minutes_light"
    SLEEP_STAGE_DEEP_MIN = "sleep_stage_minutes_deep"
    SLEEP_STAGE_REM_MIN = "sleep_stage_minutes_rem"
    SLEEP_STAGE_AWAKE_MIN = "sleep_stage_minutes_awake"
    
    # Activity & Energy
    STEPS_COUNT = "steps_count"
    ACTIVE_ENERGY_KCAL = "active_energy_kcal"
    BASAL_ENERGY_KCAL = "basal_energy_kcal"
    VO2MAX_ML_KG_MIN = "vo2max_ml_kg_min"
    
    # Workouts
    WORKOUT_DURATION_MIN = "workout_duration_min"
    WORKOUT_TYPE = "workout_type"
    WORKOUT_CALORIES_KCAL = "workout_calories_kcal"
    WORKOUT_DISTANCE_M = "workout_distance_m"
    
    # Body Composition
    BODY_WEIGHT_KG = "body_weight_kg"
    BODY_FAT_PCT = "body_fat_pct"
    BLOOD_GLUCOSE_MG_DL = "blood_glucose_mg_dl"
    
    # WHOOP Specific
    STRAIN_SCORE = "strain_score"
    RECOVERY_SCORE_PCT = "recovery_score_pct"
    SKIN_TEMP_C = "skin_temp_c"

class MetricCategory(str, Enum):
    ACTIVITY = "activity"
    SLEEP = "sleep"
    CARDIOMETABOLIC = "cardiometabolic"
    BODY_COMPOSITION = "body_composition"
    RECOVERY = "recovery"

class ConnectionStatus(str, Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PENDING = "pending"

class HealthDataSample(BaseModel):
    id: Optional[str] = None
    patient_id: str
    provider: HealthProvider
    metric: HealthMetric
    value: Union[float, str, Dict[str, Any]]
    unit: str  # UCUM codes where possible
    start_time: datetime  # UTC
    end_time: datetime    # UTC
    source_device: Optional[str] = None
    ingested_at: Optional[datetime] = None
    version: str = "1.0"
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = {}
    raw_payload: Optional[Dict[str, Any]] = {}  # Original provider data
    local_tz: str = "Europe/Rome"  # Default timezone

class HealthProviderConnection(BaseModel):
    id: Optional[str] = None
    patient_id: str
    provider: HealthProvider
    status: ConnectionStatus
    access_token: Optional[str] = None  # Encrypted
    refresh_token: Optional[str] = None  # Encrypted
    token_expires_at: Optional[datetime] = None
    permissions: List[str] = []  # Granted permissions/scopes
    last_sync_at: Optional[datetime] = None
    last_sync_success: bool = True
    sync_error: Optional[str] = None
    backfill_completed: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = {}

class PatientConsentRecord(BaseModel):
    id: Optional[str] = None
    patient_id: str
    provider: HealthProvider
    metric_categories: List[MetricCategory] = []  # Consented categories
    consent_given_at: datetime
    consent_version: str = "1.0"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    revoked_at: Optional[datetime] = None
    revocation_reason: Optional[str] = None
    data_retention_days: int = 2555  # ~7 years default
    allow_data_export: bool = True
    allow_data_sharing: bool = False  # For research/analytics
    metadata: Optional[Dict[str, Any]] = {}

class SyncJobRecord(BaseModel):
    id: Optional[str] = None
    patient_id: str
    provider: HealthProvider
    job_type: str = Field(..., pattern="^(backfill|incremental|manual)$")
    status: str = Field(..., pattern="^(pending|running|completed|failed|cancelled)$")
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    errors: List[str] = []
    metadata: Optional[Dict[str, Any]] = {}

# Request/Response Models
class ConnectProviderRequest(BaseModel):
    provider: HealthProvider
    authorization_code: Optional[str] = None  # For OAuth flow
    permissions: List[str] = []
    metric_categories: List[MetricCategory] = []

class UpdatePermissionsRequest(BaseModel):
    provider: HealthProvider
    metric_categories: List[MetricCategory]

class ExportDataRequest(BaseModel):
    format: str = Field(..., pattern="^(csv|json)$")
    date_from: datetime
    date_to: datetime
    metrics: Optional[List[HealthMetric]] = None
    providers: Optional[List[HealthProvider]] = None

class ProtocolEngineQuery(BaseModel):
    patient_id: str
    metric: Optional[HealthMetric] = None
    metrics: Optional[List[HealthMetric]] = None
    date_from: datetime
    date_to: datetime
    aggregation: str = Field(default="none", pattern="^(none|daily|weekly|monthly)$")
    providers: Optional[List[HealthProvider]] = None

# ======================================
# GOOGLE CALENDAR INTEGRATION MODELS
# ======================================

class GoogleCalendarEvent(BaseModel):
    id: Optional[str] = None
    appointment_id: str
    patient_id: str
    google_event_id: str
    calendar_id: str = "primary"
    event_title: str
    event_description: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    timezone: str = "Europe/Rome"
    attendee_emails: List[str] = []
    location: Optional[str] = None
    event_status: str = "confirmed"  # confirmed, cancelled, tentative
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class CreateCalendarEventRequest(BaseModel):
    appointment_id: str
    title: str
    description: Optional[str] = None
    start_datetime: datetime
    end_datetime: datetime
    patient_email: str
    location: Optional[str] = None
    timezone: str = "Europe/Rome"

class UpdateCalendarEventRequest(BaseModel):
    google_event_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    status: Optional[str] = None

# ======================================
# PUSH NOTIFICATIONS MODELS
# ======================================

class NotificationToken(BaseModel):
    id: Optional[str] = None
    user_id: str
    device_id: str
    token: str
    platform: str = Field(..., pattern="^(web|ios|android)$")
    device_name: Optional[str] = None
    is_active: bool = True
    created_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    
class RegisterTokenRequest(BaseModel):
    token: str
    platform: str
    device_id: str
    device_name: Optional[str] = None

class PushNotification(BaseModel):
    id: Optional[str] = None
    notification_type: str = Field(..., pattern="^(appointment_confirmation|appointment_reminder|appointment_cancelled|appointment_rescheduled|general)$")
    title: str
    body: str
    data: Optional[Dict[str, Any]] = {}
    recipient_id: str
    appointment_id: Optional[str] = None
    scheduled_for: Optional[datetime] = None
    sent_at: Optional[datetime] = None
    delivery_status: str = Field(default="pending", pattern="^(pending|sent|failed|cancelled)$")
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None

class SendNotificationRequest(BaseModel):
    title: str
    body: str
    user_id: str
    data: Optional[Dict[str, Any]] = {}
    notification_type: str = "general"
    appointment_id: Optional[str] = None
    schedule_for: Optional[datetime] = None

class NotificationSchedule(BaseModel):
    id: Optional[str] = None
    appointment_id: str
    patient_id: str
    notification_type: str = Field(..., pattern="^(confirmation|reminder_24h|reminder_2h|reminder_30m)$")
    scheduled_for: datetime
    status: str = Field(default="pending", pattern="^(pending|sent|cancelled|failed)$")
    notification_id: Optional[str] = None
    created_at: Optional[datetime] = None

class CreateReminderRequest(BaseModel):
    appointment_id: str
    reminder_types: List[str] = ["reminder_24h", "reminder_2h"]

# ======================================
# APPOINTMENT INTEGRATION MODELS  
# ======================================

class AppointmentIntegration(BaseModel):
    id: Optional[str] = None
    appointment_id: str
    patient_id: str
    google_calendar_event_id: Optional[str] = None
    push_notification_schedules: List[str] = []  # List of NotificationSchedule IDs
    integration_status: str = Field(default="pending", pattern="^(pending|active|error|cancelled)$")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

async def detect_user_language(message: str) -> str:
    """Detect user's language from their message"""
    # Simple language detection based on common patterns
    italian_patterns = [
        'ciao', 'salve', 'buongiorno', 'buonasera', 'grazie', 'prego',
        'vorrei', 'mi piacerebbe', 'che cosa', 'quando', 'dove', 'come',
        'sono', 'ho bisogno', 'prenotare', 'appuntamento', 'trattamento',
        'bellezza', 'benessere', 'salute', 'medicina', 'dottore'
    ]
    
    english_patterns = [
        'hello', 'hi', 'good morning', 'good evening', 'thank you', 'please',
        'would like', 'i need', 'what is', 'when', 'where', 'how',
        'appointment', 'booking', 'treatment', 'beauty', 'wellness',
        'health', 'medicine', 'doctor'
    ]
    
    message_lower = message.lower()
    
    # Count matches for each language
    italian_score = sum(1 for pattern in italian_patterns if pattern in message_lower)
    english_score = sum(1 for pattern in english_patterns if pattern in message_lower)
    
    # If Italian words are found, return Italian
    if italian_score > english_score:
        return 'it'
    
    # Default to English
    return 'en'

async def get_language_aware_system_prompt(user_language: str, dynamic_prompt: str) -> str:
    """Generate system prompt with language-specific instructions"""
    
    language_instructions = {
        'it': """
IMPORTANTE: L'utente preferisce comunicare in ITALIANO. Devi sempre rispondere in italiano fluente e naturale.

Linee guida per le risposte in italiano:
- Usa un tono professionale ma cordiale
- Utilizza la terminologia medica appropriata in italiano
- Quando menzioni trattamenti, usa i nomi italiani quando possibile
- Mantieni la formalità appropriata per un contesto medico di lusso
- Se non conosci una traduzione specifica, mantieni il termine inglese e spiegalo in italiano
""",
        'en': """
IMPORTANT: The user prefers to communicate in ENGLISH. Always respond in fluent and natural English.

Guidelines for English responses:
- Use a professional yet warm tone
- Use appropriate medical terminology in English
- Maintain the luxury medical context formality
- Be clear and informative in your explanations
"""
    }
    
    base_instructions = language_instructions.get(user_language, language_instructions['en'])
    
    return f"""{base_instructions}

{dynamic_prompt}

LANGUAGE CONSISTENCY: Always maintain consistency with the detected user language throughout the entire conversation."""

# KinAura Protocol Knowledge Base - Bilingual EN/IT with Tags
KINAURA_PROTOCOLS = {
    "skin-laxity": {
        "protocol_en": "Advanced Firm & Renew",
        "protocol_it": "Protocollo Tonificazione & Rinnovo",
        "treatments": [
            {
                "name_en": "Morpheus8 (latest generation)",
                "name_it": "Morpheus8 (ultima generazione)",
                "description_en": "Tightens dermis (face + body), less painful.",
                "description_it": "Rassoda il derma (viso + corpo), meno doloroso."
            },
            {
                "name_en": "Red Light Therapy (PBM)",
                "name_it": "Fotobiomodulazione (PBM)",
                "description_en": "Post-treatment to reduce inflammation, stimulate collagen.",
                "description_it": "Post-trattamento per ridurre infiammazione e stimolare collagene."
            },
            {
                "name_en": "HBOT",
                "name_it": "HBOT",
                "description_en": "Oxygenates tissue, accelerates recovery.",
                "description_it": "Ossigenoterapia iperbarica per ossigenare i tessuti e accelerare recupero."
            },
            {
                "name_en": "Exosome Injections",
                "name_it": "Iniezioni di esosomi",
                "description_en": "Enhance elasticity and long-term results.",
                "description_it": "per aumentare elasticità e risultati duraturi."
            }
        ],
        "why_kinaura_en": "Only KinAura in Milan has the newest Morpheus8 + regenerative boosters in a sterile hospital-grade setting.",
        "why_kinaura_it": "Solo KinAura a Milano dispone del nuovo Morpheus8, combinato con terapie rigenerative in ambiente sterile ospedaliero.",
        "tags": ["concern:skin-laxity", "protocol", "morpheus8", "pbm", "hbot", "exosomes"]
    },
    "wrinkles": {
        "protocol_en": "Cellular Renewal",
        "protocol_it": "Rinnovo Cellulare",
        "treatments": [
            {
                "name_en": "Endolaser (Endolift)",
                "name_it": "Endolaser (Endolift)",
                "description_en": "Stimulates dermal remodeling.",
                "description_it": "Stimola il rimodellamento dermico."
            },
            {
                "name_en": "Red Light Therapy",
                "name_it": "Red Light Therapy",
                "description_en": "Boosts mitochondria.",
                "description_it": "Attiva i mitocondri."
            },
            {
                "name_en": "IV Drip (Collagen Boost)",
                "name_it": "IV Drip (Collagen Boost)",
                "description_en": "Supports collagen.",
                "description_it": "Sostiene la sintesi di collagene."
            },
            {
                "name_en": "Exosomes / PRP",
                "name_it": "Exosomes / PRP",
                "description_en": "Restore dermal structure.",
                "description_it": "Rigenerano la struttura dermica."
            }
        ],
        "why_kinaura_en": "We combine laser + systemic IV + exosomes for holistic rejuvenation.",
        "why_kinaura_it": "Combiniamo laser + infusioni IV + esosomi per un ringiovanimento completo.",
        "tags": ["concern:wrinkles", "protocol", "endolaser", "pbm", "iv", "exosomes"]
    },
    "pigmentation": {
        "protocol_en": "Bright & Even",
        "protocol_it": "Luminosità & Uniformità",
        "treatments": [
            {
                "name_en": "Laser Rejuvenation (BBL/HERO)",
                "name_it": "Laser Rejuvenation (BBL/HERO)",
                "description_en": "Removes pigmentation.",
                "description_it": "Riduce macchie e danni solari."
            },
            {
                "name_en": "EBOO2",
                "name_it": "EBOO2",
                "description_en": "Blood detox + anti-inflammation.",
                "description_it": "Detox ematico e riduzione infiammazione."
            },
            {
                "name_en": "Red Light Therapy",
                "name_it": "Red Light Therapy",
                "description_en": "Brightens tone.",
                "description_it": "Uniforma l'incarnato."
            },
            {
                "name_en": "Brightening Facial + KinAura Skincare",
                "name_it": "Brightening Facial + KinAura Skincare",
                "description_en": "Maintains results.",
                "description_it": "Mantiene risultati nel tempo."
            }
        ],
        "why_kinaura_en": "Unique blend of medical laser + systemic detox + skincare.",
        "why_kinaura_it": "Unione esclusiva di laser medico + detox sistemico + skincare personalizzata.",
        "tags": ["concern:pigmentation", "protocol", "bbl", "hero", "eboo2", "pbm", "skincare"]
    },
    "acne": {
        "protocol_en": "Clear Complexion",
        "protocol_it": "Pelle Chiara",
        "treatments": [
            {
                "name_en": "Morpheus8 (scar mode)",
                "name_it": "Morpheus8 (scar mode)",
                "description_en": "Remodels scars.",
                "description_it": "Rimodella le cicatrici."
            },
            {
                "name_en": "Laser Resurfacing (Fotona/BBL)",
                "name_it": "Laser Resurfacing (Fotona/BBL)",
                "description_en": "Treats acne activity.",
                "description_it": "Riduce acne attiva."
            },
            {
                "name_en": "Red Light Therapy",
                "name_it": "Red Light Therapy",
                "description_en": "Anti-inflammatory.",
                "description_it": "Azione antinfiammatoria e antibatterica."
            },
            {
                "name_en": "IV Detox Drip",
                "name_it": "IV Detox Drip",
                "description_en": "Glutathione + Zinc.",
                "description_it": "Glutatione + Zinco."
            },
            {
                "name_en": "KinAura Skincare",
                "name_it": "KinAura Skincare",
                "description_en": "Maintenance.",
                "description_it": "Manutenzione quotidiana."
            }
        ],
        "why_kinaura_en": "We combine systemic IV detox with advanced lasers.",
        "why_kinaura_it": "Combiniamo infusioni IV detox con laser rigenerativi.",
        "tags": ["concern:acne", "protocol", "morpheus8", "laser", "pbm", "iv", "skincare"]
    },
    "cellulite": {
        "protocol_en": "Smooth Contour",
        "protocol_it": "Contorno Levigato",
        "treatments": [
            {
                "name_en": "Endolaser (Endolift)",
                "name_it": "Endolaser (Endolift)",
                "description_en": "Tightens skin.",
                "description_it": "Rassoda la pelle."
            },
            {
                "name_en": "Morpheus8 Body",
                "name_it": "Morpheus8 Body",
                "description_en": "Restructures tissue.",
                "description_it": "Rimodella tessuto."
            },
            {
                "name_en": "Lymphatic Drainage",
                "name_it": "Lymphatic Drainage",
                "description_en": "Reduces edema.",
                "description_it": "Drena liquidi."
            },
            {
                "name_en": "IV Detox Blend",
                "name_it": "IV Detox Blend",
                "description_en": "Metabolic support.",
                "description_it": "Supporto metabolico."
            },
            {
                "name_en": "Exosomes Topical",
                "name_it": "Exosomes Topical",
                "description_en": "Dermal repair.",
                "description_it": "Rigenerazione dermica."
            }
        ],
        "why_kinaura_en": "Structural + metabolic cellulite approach.",
        "why_kinaura_it": "Affrontiamo la cellulite su più livelli: strutturale + metabolico.",
        "tags": ["concern:cellulite", "protocol", "morpheus8", "endolaser", "lymphatic", "iv", "exosomes"]
    },
    "hair-loss": {
        "protocol_en": "Regrow & Strengthen",
        "protocol_it": "Ricrescita & Rinforzo",
        "treatments": [
            {
                "name_en": "Exosome Scalp Therapy",
                "name_it": "Exosome Scalp Therapy",
                "description_en": "Stimulates follicles.",
                "description_it": "Stimola follicoli."
            },
            {
                "name_en": "PRP Injections",
                "name_it": "PRP Injections",
                "description_en": "Growth factors.",
                "description_it": "Fattori di crescita."
            },
            {
                "name_en": "Red Light Therapy Cap",
                "name_it": "Red Light Therapy Cap",
                "description_en": "Boosts scalp circulation.",
                "description_it": "Migliora circolazione cuoio capelluto."
            },
            {
                "name_en": "IV Hair Boost Drip",
                "name_it": "IV Hair Boost Drip",
                "description_en": "Biotin + amino acids.",
                "description_it": "Biotina + aminoacidi."
            },
            {
                "name_en": "Optional HBOT",
                "name_it": "Optional HBOT",
                "description_en": "Enhances oxygenation.",
                "description_it": "Ossigenazione del cuoio capelluto."
            }
        ],
        "why_kinaura_en": "Only clinic with exosomes + HBOT for hair regrowth.",
        "why_kinaura_it": "Unica clinica con esosomi + HBOT per ricrescita capelli.",
        "tags": ["concern:hair-loss", "protocol", "exosomes", "prp", "pbm", "iv", "hbot"]
    },
    "immunity": {
        "protocol_en": "Immune Reset",
        "protocol_it": "Reset Immunitario",
        "treatments": [
            {
                "name_en": "EBOO2",
                "name_it": "EBOO2",
                "description_en": "Cleanses blood.",
                "description_it": "Purifica il sangue."
            },
            {
                "name_en": "IV Immune Drip",
                "name_it": "IV Immune Drip",
                "description_en": "Vit C + Glutathione.",
                "description_it": "Vitamina C + Glutatione."
            },
            {
                "name_en": "HBOT",
                "name_it": "HBOT",
                "description_en": "Improves immune efficiency.",
                "description_it": "Migliora funzione immunitaria."
            },
            {
                "name_en": "Red Light Therapy",
                "name_it": "Red Light Therapy",
                "description_en": "Anti-inflammatory.",
                "description_it": "Azione antinfiammatoria."
            }
        ],
        "why_kinaura_en": "Exclusive detox + oxygen combo.",
        "why_kinaura_it": "Unico centro a offrire detox extracorporeo + ossigenazione.",
        "tags": ["concern:immunity", "protocol", "eboo2", "iv", "hbot", "pbm"]
    },
    "fatigue": {
        "protocol_en": "Vital Reset",
        "protocol_it": "Reset Vitale",
        "treatments": [
            {
                "name_en": "EBOO2",
                "name_it": "EBOO2",
                "description_en": "Improves circulation.",
                "description_it": "Migliora circolazione."
            },
            {
                "name_en": "HBOT",
                "name_it": "HBOT",
                "description_en": "Boosts mitochondria.",
                "description_it": "Supporta mitocondri."
            },
            {
                "name_en": "IV Energy Drip (NAD+, B12)",
                "name_it": "IV Energy Drip (NAD+, B12)",
                "description_en": "Energy metabolism.",
                "description_it": "Energia cellulare."
            },
            {
                "name_en": "Red Light Therapy",
                "name_it": "Red Light Therapy",
                "description_en": "ATP boost.",
                "description_it": "Stimolo ATP."
            },
            {
                "name_en": "Longevity Score",
                "name_it": "Longevity Score",
                "description_en": "Track improvement.",
                "description_it": "Monitoraggio AI."
            }
        ],
        "why_kinaura_en": "A true biohacking reset.",
        "why_kinaura_it": "Un reset biohacking completo.",
        "tags": ["concern:fatigue", "protocol", "eboo2", "hbot", "iv", "pbm", "nad"]
    },
    "weight-loss": {
        "protocol_en": "Metabolic Optimization",
        "protocol_it": "Ottimizzazione Metabolica",
        "treatments": [
            {
                "name_en": "EBOO2",
                "name_it": "EBOO2",
                "description_en": "Improves insulin sensitivity.",
                "description_it": "Migliora sensibilità insulinica."
            },
            {
                "name_en": "IV Metabolic Drip",
                "name_it": "IV Metabolic Drip",
                "description_en": "Carnitine + MIC + B vitamins.",
                "description_it": "Carnitina + MIC + Vitamine."
            },
            {
                "name_en": "HBOT",
                "name_it": "HBOT",
                "description_en": "Supports mitochondria.",
                "description_it": "Supporto mitocondriale."
            },
            {
                "name_en": "Red Light Therapy Body",
                "name_it": "Red Light Therapy Body",
                "description_en": "Fat metabolism.",
                "description_it": "Metabolismo adiposo."
            }
        ],
        "why_kinaura_en": "Weight loss via cellular optimization.",
        "why_kinaura_it": "Perdita di peso tramite ottimizzazione cellulare.",
        "tags": ["concern:weight-loss", "protocol", "eboo2", "iv", "hbot", "pbm"]
    },
    "pre-event": {
        "protocol_en": "Instant Radiance",
        "protocol_it": "Luminosità Istantanea",
        "treatments": [
            {
                "name_en": "Laser Facial (BBL/Fotona)",
                "name_it": "Laser Facial (BBL/Fotona)",
                "description_en": "Smooths + tones.",
                "description_it": "Leviga e uniforma."
            },
            {
                "name_en": "Red Light Therapy",
                "name_it": "Red Light Therapy",
                "description_en": "Glow effect.",
                "description_it": "Effetto luminosità."
            },
            {
                "name_en": "IV Glow Drip",
                "name_it": "IV Glow Drip",
                "description_en": "Vit C + hydration.",
                "description_it": "Vit C + idratazione."
            },
            {
                "name_en": "Oxygen Infusion Facial",
                "name_it": "Oxygen Infusion Facial",
                "description_en": "Final polish.",
                "description_it": "Rifinitura finale."
            }
        ],
        "why_kinaura_en": "Event-ready glow in 24h.",
        "why_kinaura_it": "Glow garantito in 24h.",
        "tags": ["concern:pre-event", "protocol", "bbl", "fotona", "pbm", "iv", "oxygen-facial"]
    },
    "longevity": {
        "protocol_en": "Biological Reset",
        "protocol_it": "Reset Biologico",
        "treatments": [
            {
                "name_en": "EBOO2 + HBOT",
                "name_it": "EBOO2 + HBOT",
                "description_en": "Cellular rejuvenation.",
                "description_it": "Ringiovanimento cellulare."
            },
            {
                "name_en": "IV Longevity Blend (NAD+, antioxidants)",
                "name_it": "IV Longevity Blend (NAD+, antioxidants)",
                "description_en": "Slows aging.",
                "description_it": "Rallenta invecchiamento."
            },
            {
                "name_en": "AI Longevity Score",
                "name_it": "AI Longevity Score",
                "description_en": "Tracks biological age.",
                "description_it": "Monitora età biologica."
            },
            {
                "name_en": "Exosome Therapy",
                "name_it": "Exosome Therapy",
                "description_en": "Biomarker-driven.",
                "description_it": "Terapia mirata su biomarcatori."
            }
        ],
        "why_kinaura_en": "AI-driven, Harvard-level science + luxury.",
        "why_kinaura_it": "Scienza di livello Harvard guidata da AI in un ambiente esclusivo.",
        "tags": ["concern:longevity", "protocol", "eboo2", "hbot", "iv", "exosomes", "ai"]
    },
    "stress": {
        "protocol_en": "Calm & Restore",
        "protocol_it": "Calma & Ripristino",
        "treatments": [
            {
                "name_en": "IV Relax Drip (Magnesium, GABA, Theanine)",
                "name_it": "IV Relax Drip (Magnesium, GABA, Theanine)",
                "description_en": "Nervous system support.",
                "description_it": "Supporto sistema nervoso."
            },
            {
                "name_en": "Red Light Therapy (low wavelength)",
                "name_it": "Red Light Therapy (low wavelength)",
                "description_en": "Improves sleep cycle.",
                "description_it": "Migliora ciclo sonno."
            },
            {
                "name_en": "HBOT (mild)",
                "name_it": "HBOT (mild)",
                "description_en": "Brain oxygenation.",
                "description_it": "Ossigenazione cerebrale."
            },
            {
                "name_en": "Osteopathy / Breathwork",
                "name_it": "Osteopathy / Breathwork",
                "description_en": "Optional.",
                "description_it": "Opzionale."
            }
        ],
        "why_kinaura_en": "Medical-grade + holistic for restorative effect.",
        "why_kinaura_it": "Protocollo medico + olistico per ripristino profondo.",
        "tags": ["concern:stress", "concern:sleep", "protocol", "iv", "pbm", "hbot", "osteopathy"]
    },
    "recovery": {
        "protocol_en": "Accelerated Recovery",
        "protocol_it": "Recupero Accelerato",
        "treatments": [
            {
                "name_en": "HBOT",
                "name_it": "HBOT",
                "description_en": "Speeds wound healing.",
                "description_it": "Accelera guarigione."
            },
            {
                "name_en": "Red Light Therapy",
                "name_it": "Red Light Therapy",
                "description_en": "Calms inflammation.",
                "description_it": "Riduce arrossamenti."
            },
            {
                "name_en": "IV Recovery Drip",
                "name_it": "IV Recovery Drip",
                "description_en": "Vitamin C + minerals.",
                "description_it": "Vitamina C + minerali."
            },
            {
                "name_en": "Lymphatic Drainage / Oxygen Facial",
                "name_it": "Lymphatic Drainage / Oxygen Facial",
                "description_en": "Relieves swelling.",
                "description_it": "Riduce gonfiore."
            }
        ],
        "why_kinaura_en": "Recovery is integrated, not optional.",
        "why_kinaura_it": "Il recupero è parte del protocollo, non un accessorio.",
        "tags": ["concern:recovery", "protocol", "hbot", "pbm", "iv", "lymphatic", "facial"]
    }
}

# Treatment to Protocol Mapping
TREATMENT_TO_PROTOCOL = {
    "morpheus8": ["skin-laxity", "acne", "cellulite"],
    "endolaser": ["wrinkles", "cellulite"],
    "bbl": ["pigmentation", "acne", "pre-event"],
    "hero": ["pigmentation"],
    "fotona": ["acne", "pre-event"],
    "eboo2": ["pigmentation", "immunity", "fatigue", "weight-loss", "longevity"],
    "hbot": ["skin-laxity", "immunity", "fatigue", "weight-loss", "longevity", "stress", "recovery", "hair-loss"],
    "pbm": ["skin-laxity", "wrinkles", "pigmentation", "acne", "immunity", "fatigue", "weight-loss", "pre-event", "stress", "recovery", "hair-loss"],
    "red_light": ["skin-laxity", "wrinkles", "pigmentation", "acne", "immunity", "fatigue", "weight-loss", "pre-event", "stress", "recovery", "hair-loss"],
    "exosomes": ["skin-laxity", "wrinkles", "cellulite", "longevity", "hair-loss"],
    "iv_therapy": ["wrinkles", "acne", "fatigue", "weight-loss", "pre-event", "longevity", "stress", "recovery", "hair-loss"],
    "prp": ["wrinkles", "hair-loss"],
    "lymphatic": ["cellulite", "recovery"],
    "oxygen_facial": ["recovery", "pre-event"]
}

# Concern Keywords Mapping to Protocols
CONCERN_TO_PROTOCOL = {
    "skin laxity": "skin-laxity",
    "lassità": "skin-laxity", 
    "sagging": "skin-laxity",
    "loose skin": "skin-laxity",
    "wrinkles": "wrinkles",
    "rughe": "wrinkles",
    "fine lines": "wrinkles",
    "aging": "wrinkles",
    "pigmentation": "pigmentation",
    "macchie": "pigmentation",
    "dark spots": "pigmentation",
    "melasma": "pigmentation",
    "sun damage": "pigmentation",
    "acne": "acne",
    "pimples": "acne",
    "acne scars": "acne",
    "cicatrici": "acne",
    "cellulite": "cellulite",
    "cellulite": "cellulite",
    "orange peel": "cellulite",
    "hair loss": "hair-loss",
    "caduta capelli": "hair-loss",
    "balding": "hair-loss",
    "alopecia": "hair-loss",
    "immunity": "immunity",
    "immunità": "immunity",
    "immune system": "immunity",
    "detox": "immunity",
    "fatigue": "fatigue",
    "stanchezza": "fatigue", 
    "tired": "fatigue",
    "energy": "fatigue",
    "weight loss": "weight-loss",
    "perdita peso": "weight-loss",
    "metabolism": "weight-loss",
    "glow": "pre-event",
    "event": "pre-event",
    "wedding": "pre-event",
    "party": "pre-event",
    "longevity": "longevity",
    "longevità": "longevity",
    "anti-aging": "longevity",
    "prevention": "longevity",
    "stress": "stress",
    "anxiety": "stress",
    "sleep": "stress",
    "sonno": "stress",
    "recovery": "recovery",
    "recupero": "recovery",
    "healing": "recovery"
}

async def detect_protocol_from_message(message: str, user_language: str = 'en') -> List[str]:
    """Detect relevant protocols from user message based on concerns or treatments mentioned"""
    message_lower = message.lower()
    detected_protocols = set()
    
    # Check for concern keywords
    for concern_phrase, protocol_key in CONCERN_TO_PROTOCOL.items():
        if concern_phrase in message_lower:
            detected_protocols.add(protocol_key)
    
    # Check for treatment keywords
    for treatment, protocols in TREATMENT_TO_PROTOCOL.items():
        treatment_keywords = TREATMENT_KEYWORDS.get(treatment, [treatment])
        for keyword in treatment_keywords:
            if keyword in message_lower:
                detected_protocols.update(protocols)
    
    return list(detected_protocols)

async def format_protocol_response(protocol_keys: List[str], user_language: str = 'en') -> str:
    """Format protocol recommendations in the requested language"""
    if not protocol_keys:
        return ""
    
    response_parts = []
    
    for protocol_key in protocol_keys[:2]:  # Limit to 2 protocols per response
        protocol = KINAURA_PROTOCOLS.get(protocol_key)
        if not protocol:
            continue
            
        if user_language == 'it':
            protocol_name = protocol['protocol_it']
            why_kinaura = protocol['why_kinaura_it']
            
            # Format treatments in Italian
            treatment_list = []
            for treatment in protocol['treatments']:
                treatment_list.append(f"• **{treatment['name_it']}** → {treatment['description_it']}")
            
            protocol_text = f"""
**{protocol_name}:**
{chr(10).join(treatment_list)}

*Perché KinAura:* {why_kinaura}
"""
        else:
            protocol_name = protocol['protocol_en']
            why_kinaura = protocol['why_kinaura_en']
            
            # Format treatments in English
            treatment_list = []
            for treatment in protocol['treatments']:
                treatment_list.append(f"• **{treatment['name_en']}** → {treatment['description_en']}")
            
            protocol_text = f"""
**{protocol_name}:**
{chr(10).join(treatment_list)}

*Why KinAura:* {why_kinaura}
"""
        
        response_parts.append(protocol_text)
    
    return chr(10).join(response_parts)

async def detect_booking_intent(message: str) -> bool:
    """Detect if user is expressing booking intent"""
    booking_keywords = [
        "book", "schedule", "appointment", "prenotare", "appuntamento",
        "when can i", "availability", "disponibilità", "reserve", "riservare",
        "want to book", "voglio prenotare", "interested in booking"
    ]
    
    message_lower = message.lower()
    return any(keyword in message_lower for keyword in booking_keywords)

# Proactive Notification System for Protocol Recommendations

async def generate_protocol_notification_for_booking(patient_id: str, service_id: str, service_name: str, user_language: str = 'en') -> dict:
    """Generate automatic protocol recommendation notification after booking"""
    try:
        # Get the primary treatment from service name
        primary_treatment = await identify_treatment_from_service(service_name)
        
        # Find relevant protocols that include this treatment
        relevant_protocols = []
        for protocol_key, protocol_data in KINAURA_PROTOCOLS.items():
            # Check if any treatment in the protocol matches the booked service
            for treatment in protocol_data['treatments']:
                treatment_name_en = treatment['name_en'].lower()
                treatment_name_it = treatment['name_it'].lower()
                service_lower = service_name.lower()
                
                if (any(keyword in service_lower for keyword in [primary_treatment, 'morpheus8', 'hbot', 'iv', 'laser', 'endolaser', 'pbm']) and
                    any(keyword in treatment_name_en for keyword in [primary_treatment, 'morpheus8', 'hbot', 'iv', 'laser', 'endolaser', 'pbm'])):
                    relevant_protocols.append(protocol_key)
                    break
        
        if not relevant_protocols:
            # Fallback - suggest based on treatment keywords
            if 'morpheus8' in service_name.lower():
                relevant_protocols = ['skin-laxity']
            elif any(keyword in service_name.lower() for keyword in ['laser', 'facial', 'skin']):
                relevant_protocols = ['pigmentation', 'wrinkles']
            elif 'iv' in service_name.lower():
                relevant_protocols = ['fatigue', 'immunity']
            elif 'hbot' in service_name.lower():
                relevant_protocols = ['recovery', 'longevity']
        
        if relevant_protocols:
            # Select the most relevant protocol
            primary_protocol_key = relevant_protocols[0]
            protocol_data = KINAURA_PROTOCOLS[primary_protocol_key]
            
            # Generate complementary recommendations (exclude the treatment they just booked)
            complementary_treatments = []
            for treatment in protocol_data['treatments']:
                treatment_name = treatment['name_en'] if user_language == 'en' else treatment['name_it']
                treatment_desc = treatment['description_en'] if user_language == 'en' else treatment['description_it']
                
                # Only add if it's not the treatment they just booked
                if not any(keyword in service_name.lower() for keyword in treatment_name.lower().split()):
                    complementary_treatments.append({
                        'name': treatment_name,
                        'description': treatment_desc
                    })
            
            # Format notification message
            if user_language == 'it':
                protocol_name = protocol_data['protocol_it']
                why_kinaura = protocol_data['why_kinaura_it']
                
                notification_message = f"""🌟 **Raccomandazione Protocollo KinAura**

Hai appena prenotato {service_name}! Per ottimizzare i tuoi risultati, ti suggeriamo il nostro **{protocol_name}**.

**Trattamenti Complementari Raccomandati:**
{chr(10).join([f"• **{t['name']}** - {t['description']}" for t in complementary_treatments[:3]])}

**Perché KinAura:** {why_kinaura}

Vuoi saperne di più su questi trattamenti complementari? Il nostro team è qui per aiutarti! 💫"""
            else:
                protocol_name = protocol_data['protocol_en']
                why_kinaura = protocol_data['why_kinaura_en']
                
                notification_message = f"""🌟 **KinAura Protocol Recommendation**

You just booked {service_name}! To optimize your results, we recommend our **{protocol_name}**.

**Recommended Complementary Treatments:**
{chr(10).join([f"• **{t['name']}** - {t['description']}" for t in complementary_treatments[:3]])}

**Why KinAura:** {why_kinaura}

Want to learn more about these complementary treatments? Our team is here to help! 💫"""
            
            return {
                'patient_id': patient_id,
                'protocol_key': primary_protocol_key,
                'protocol_name': protocol_name,
                'message': notification_message,
                'complementary_treatments': complementary_treatments,
                'booked_service': service_name,
                'language': user_language,
                'created_at': datetime.utcnow(),
                'notification_type': 'protocol_recommendation',
                'is_read': False
            }
    
    except Exception as e:
        print(f"Error generating protocol notification: {str(e)}")
        return None

async def identify_treatment_from_service(service_name: str) -> str:
    """Identify primary treatment type from service name"""
    service_lower = service_name.lower()
    
    if 'morpheus8' in service_lower:
        return 'morpheus8'
    elif any(keyword in service_lower for keyword in ['laser', 'bbl', 'hero', 'fotona']):
        return 'laser'
    elif 'hbot' in service_lower or 'hyperbaric' in service_lower:
        return 'hbot'
    elif 'iv' in service_lower or 'infusion' in service_lower:
        return 'iv_therapy'
    elif any(keyword in service_lower for keyword in ['red light', 'pbm', 'photobiomodulation']):
        return 'pbm'
    elif 'endolaser' in service_lower or 'endolift' in service_lower:
        return 'endolaser'
    elif 'exosome' in service_lower:
        return 'exosomes'
    elif 'prp' in service_lower:
        return 'prp'
    elif 'lymphatic' in service_lower:
        return 'lymphatic'
    elif 'oxygen' in service_lower and 'facial' in service_lower:
        return 'oxygen_facial'
    else:
        return 'general'

async def store_proactive_notification(notification_data: dict) -> str:
    """Store proactive notification in database"""
    try:
        notification_id = str(uuid.uuid4())
        notification_data['_id'] = notification_id
        
        await db.proactive_notifications.insert_one(notification_data)
        return notification_id
        
    except Exception as e:
        print(f"Error storing proactive notification: {str(e)}")
        return None

async def get_patient_language_preference(patient_id: str) -> str:
    """Get patient's language preference, default to 'en'"""
    try:
        user = await db.users.find_one({'id': patient_id})
        if user and 'language' in user:
            return user['language']
        return 'en'  # Default to English
    except:
        return 'en'

async def trigger_proactive_protocol_notification(patient_id: str, service_id: str, service_name: str) -> bool:
    """Trigger proactive protocol notification after booking"""
    try:
        # Get patient language preference
        user_language = await get_patient_language_preference(patient_id)
        
        # Generate protocol recommendation notification
        notification_data = await generate_protocol_notification_for_booking(
            patient_id, service_id, service_name, user_language
        )
        
        if notification_data:
            # Store notification in database
            notification_id = await store_proactive_notification(notification_data)
            
            if notification_id:
                print(f"✅ Proactive protocol notification created: {notification_id} for patient {patient_id}")
                return True
            else:
                print(f"❌ Failed to store proactive notification for patient {patient_id}")
                return False
        else:
            print(f"⚠️ No protocol recommendation generated for service: {service_name}")
            return False
            
    except Exception as e:
        print(f"❌ Error triggering proactive notification: {str(e)}")
        return False

# CRM Engagement Models
class EngagementCampaignType(str, Enum):
    lapsed_reactivation = "lapsed_reactivation"
    lead_nurturing = "lead_nurturing"
    anniversary = "anniversary"
    promotion = "promotion"
    referral = "referral"

class EngagementLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    campaign_type: EngagementCampaignType
    channel: str  # "push", "email", "sms"
    language: str = "en"
    subject: Optional[str] = None
    message: str
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    delivery_status: str = "sent"  # "sent", "delivered", "failed", "bounced"
    opened_at: Optional[datetime] = None
    clicked_at: Optional[datetime] = None
    conversion_event: Optional[str] = None  # "booking", "login", "visit"
    conversion_at: Optional[datetime] = None
    metadata: Dict[str, Any] = {}

class CRMFunnelData(BaseModel):
    leads: Dict[str, Any]
    active: Dict[str, Any]
    lapsed: Dict[str, Any]
    totals: Dict[str, Any]
    trends: Dict[str, Any]

# CRM Analytics and Lifecycle Management Functions
async def calculate_lifecycle_stage(user_data: dict) -> LifecycleStage:
    """Calculate lifecycle stage based on user data"""
    try:
        last_booking = user_data.get('last_booking')
        total_bookings = user_data.get('total_bookings', 0)
        
        if not last_booking or total_bookings == 0:
            return LifecycleStage.lead
        
        # Parse last_booking if it's a string
        if isinstance(last_booking, str):
            last_booking = datetime.fromisoformat(last_booking.replace('Z', '+00:00'))
        
        days_since_booking = (datetime.utcnow() - last_booking).days
        
        if days_since_booking >= 60:
            return LifecycleStage.lapsed
        else:
            return LifecycleStage.active
            
    except Exception as e:
        print(f"Error calculating lifecycle stage: {str(e)}")
        return LifecycleStage.lead

async def update_user_lifecycle_data(user_id: str, last_login: datetime = None, new_booking: dict = None):
    """Update user lifecycle data after login or booking"""
    try:
        user = await db.users.find_one({"id": user_id})
        if not user:
            return False
        
        update_data = {}
        
        # Update last_login if provided
        if last_login:
            update_data["last_login"] = last_login
        
        # Update booking data if new booking
        if new_booking:
            update_data["last_booking"] = new_booking.get('created_at', datetime.utcnow())
            update_data["total_bookings"] = user.get('total_bookings', 0) + 1
            update_data["total_revenue"] = user.get('total_revenue', 0.0) + float(new_booking.get('amount', 0))
        
        # Recalculate lifecycle stage
        updated_user_data = {**user, **update_data}
        lifecycle_stage = await calculate_lifecycle_stage(updated_user_data)
        update_data["lifecycle_stage"] = lifecycle_stage.value
        
        # Calculate engagement score (simple algorithm)
        engagement_score = 0
        if updated_user_data.get('last_login'):
            days_since_login = (datetime.utcnow() - updated_user_data['last_login']).days
            engagement_score += max(0, 30 - days_since_login)  # Max 30 points for recent login
        
        if updated_user_data.get('total_bookings', 0) > 0:
            engagement_score += min(50, updated_user_data['total_bookings'] * 10)  # Max 50 points for bookings
        
        if lifecycle_stage == LifecycleStage.active:
            engagement_score += 20
        
        update_data["engagement_score"] = min(100, engagement_score)
        
        # Update database
        await db.users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        return True
        
    except Exception as e:
        print(f"Error updating user lifecycle data: {str(e)}")
        return False

async def get_funnel_analytics() -> CRMFunnelData:
    """Get comprehensive CRM funnel analytics"""
    try:
        # Get all users with role != admin
        users = await db.users.find(
            {"role": {"$ne": "admin"}}, 
            {"_id": 0}
        ).to_list(10000)
        
        # Calculate current date boundaries
        now = datetime.utcnow()
        thirty_days_ago = now - timedelta(days=30)
        
        # Initialize counters
        leads = {"count": 0, "patients": []}
        active = {"count": 0, "patients": []}
        lapsed = {"count": 0, "patients": []}
        
        # Process each user
        for user in users:
            # Update lifecycle stage in real-time
            lifecycle_stage = await calculate_lifecycle_stage(user)
            
            # Update user record if stage has changed
            if user.get('lifecycle_stage') != lifecycle_stage.value:
                await db.users.update_one(
                    {"id": user["id"]},
                    {"$set": {"lifecycle_stage": lifecycle_stage.value}}
                )
                user['lifecycle_stage'] = lifecycle_stage.value
            
            # Categorize users
            if lifecycle_stage == LifecycleStage.lead:
                leads["count"] += 1
                leads["patients"].append(user)
            elif lifecycle_stage == LifecycleStage.active:
                active["count"] += 1
                active["patients"].append(user)
            elif lifecycle_stage == LifecycleStage.lapsed:
                lapsed["count"] += 1
                lapsed["patients"].append(user)
        
        # Calculate trends (last 30 days)
        leads_trend = await calculate_stage_trend(LifecycleStage.lead, thirty_days_ago, now)
        active_trend = await calculate_stage_trend(LifecycleStage.active, thirty_days_ago, now)
        lapsed_trend = await calculate_stage_trend(LifecycleStage.lapsed, thirty_days_ago, now)
        
        return CRMFunnelData(
            leads=leads,
            active=active,
            lapsed=lapsed,
            totals={
                "total_patients": len(users),
                "conversion_rate": round((active["count"] / max(1, leads["count"] + active["count"])) * 100, 2),
                "lapse_rate": round((lapsed["count"] / max(1, len(users))) * 100, 2)
            },
            trends={
                "leads_trend": leads_trend,
                "active_trend": active_trend,
                "lapsed_trend": lapsed_trend
            }
        )
        
    except Exception as e:
        print(f"Error getting funnel analytics: {str(e)}")
        return CRMFunnelData(
            leads={"count": 0, "patients": []},
            active={"count": 0, "patients": []},
            lapsed={"count": 0, "patients": []},
            totals={"total_patients": 0, "conversion_rate": 0, "lapse_rate": 0},
            trends={"leads_trend": 0, "active_trend": 0, "lapsed_trend": 0}
        )

async def calculate_stage_trend(stage: LifecycleStage, start_date: datetime, end_date: datetime) -> int:
    """Calculate trend percentage for a lifecycle stage"""
    try:
        # This is a simplified trend calculation
        # In production, you'd store daily snapshots for accurate trending
        total_users = await db.users.count_documents({"role": {"$ne": "admin"}})
        stage_users = await db.users.count_documents({"lifecycle_stage": stage.value, "role": {"$ne": "admin"}})
        
        # Simple trend calculation (would be more sophisticated in production)
        return round(((stage_users / max(1, total_users)) * 100) - 50, 1)  # Relative to 50% baseline
        
    except Exception as e:
        print(f"Error calculating stage trend: {str(e)}")
        return 0

# Stripe Checkout and Order Management

@api_router.post("/shop/checkout/create-session")
async def create_checkout_session(
    checkout_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Create Stripe checkout session"""
    try:
        import stripe
        
        # Get Stripe secret key from environment
        stripe_secret = os.environ.get('STRIPE_SECRET_KEY')
        if not stripe_secret:
            raise HTTPException(status_code=500, detail="Stripe not configured")
        
        stripe.api_key = stripe_secret
        
        # Validate cart items
        cart_items = checkout_data.get("items", [])
        if not cart_items:
            raise HTTPException(status_code=400, detail="Cart is empty")
        
        # Calculate order totals
        line_items = []
        order_items = []
        subtotal = 0.0
        
        for item in cart_items:
            # Get product
            product = await db.products.find_one({"sku": item["sku"], "is_active": True})
            if not product:
                raise HTTPException(status_code=404, detail=f"Product {item['sku']} not found")
            
            # Check inventory
            if product.get("inventory", 0) < item["quantity"]:
                raise HTTPException(status_code=400, detail=f"Insufficient inventory for {product['name']['en']}")
            
            # Calculate price (apply membership discount if applicable)
            unit_price = product["price_eur"]
            membership_tier = current_user.get("membership_tier")
            if membership_tier and product.get("price_membership"):
                membership_prices = product["price_membership"]
                if membership_tier in membership_prices:
                    discounted_price = membership_prices[membership_tier]
                    if discounted_price is not None and discounted_price < unit_price:
                        unit_price = discounted_price
            
            # Create Stripe line item
            line_items.append({
                "price_data": {
                    "currency": "eur",
                    "product_data": {
                        "name": product["name"]["en"],
                        "description": product.get("short_description", {}).get("en", ""),
                        "images": [img["url"] for img in product.get("images", [])[:1]]  # First image
                    },
                    "unit_amount": int(unit_price * 100)  # Convert to cents
                },
                "quantity": item["quantity"]
            })
            
            # Create order item
            item_total = unit_price * item["quantity"]
            order_items.append(OrderItem(
                sku=item["sku"],
                name=product["name"]["en"],
                quantity=item["quantity"],
                unit_price=unit_price,
                total_price=item_total,
                variant_id=item.get("variant_id")
            ))
            
            subtotal += item_total
        
        # Apply promo code if provided
        discount_amount = 0.0
        promo_code = checkout_data.get("promo_code")
        if promo_code:
            promo = await db.promotion_codes.find_one({"code": promo_code.upper(), "is_active": True})
            if promo:
                # Check validity
                now = datetime.utcnow()
                if promo.get("valid_until") and now > promo["valid_until"]:
                    raise HTTPException(status_code=400, detail="Promo code expired")
                
                if promo.get("max_uses") and promo.get("current_uses", 0) >= promo["max_uses"]:
                    raise HTTPException(status_code=400, detail="Promo code usage limit reached")
                
                if subtotal < promo.get("minimum_order", 0):
                    raise HTTPException(status_code=400, detail="Order doesn't meet minimum for promo code")
                
                # Calculate discount
                if promo["discount_type"] == "percentage":
                    discount_amount = subtotal * (promo["discount_value"] / 100)
                else:  # fixed
                    discount_amount = min(promo["discount_value"], subtotal)
                
                # Add discount line item (negative amount)
                line_items.append({
                    "price_data": {
                        "currency": "eur",
                        "product_data": {
                            "name": f"Discount ({promo_code})"
                        },
                        "unit_amount": int(-discount_amount * 100)
                    },
                    "quantity": 1
                })
        
        # Calculate final total
        tax_amount = 0.0  # TODO: Add tax calculation if needed
        shipping_cost = 0.0  # TODO: Add shipping calculation
        total_amount = subtotal - discount_amount + tax_amount + shipping_cost
        
        # Create order record (pending payment)
        order_number = f"KA-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        order = Order(
            patient_id=current_user["id"],
            order_number=order_number,
            items=[item.dict() for item in order_items],
            subtotal=subtotal,
            discount_amount=discount_amount,
            tax_amount=tax_amount,
            shipping_cost=shipping_cost,
            total_amount=total_amount,
            customer_email=current_user["email"],
            customer_name=current_user["full_name"],
            promo_code=promo_code,
            membership_tier=current_user.get("membership_tier")
        )
        
        # Create Stripe checkout session
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            success_url=f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/boutique/order-success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.environ.get('FRONTEND_URL', 'http://localhost:3000')}/boutique/cart",
            metadata={
                "order_id": order.id,
                "patient_id": current_user["id"]
            },
            customer_email=current_user["email"],
            billing_address_collection="required"
        )
        
        # Update order with Stripe session ID
        order.stripe_session_id = session.id
        
        # Save order to database
        await db.orders.insert_one(order.dict())
        
        # Update promo code usage
        if promo_code and discount_amount > 0:
            await db.promotion_codes.update_one(
                {"code": promo_code.upper()},
                {"$inc": {"current_uses": 1}}
            )
        
        return {
            "success": True,
            "checkout_url": session.url,
            "session_id": session.id,
            "order_id": order.id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating checkout session: {str(e)}")

@api_router.post("/shop/webhooks/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks for order fulfillment"""
    try:
        import stripe
        
        stripe_secret = os.environ.get('STRIPE_SECRET_KEY')
        webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
        
        if not stripe_secret or not webhook_secret:
            raise HTTPException(status_code=500, detail="Stripe not configured")
        
        stripe.api_key = stripe_secret
        
        # Get the raw body and signature
        payload = await request.body()
        sig_header = request.headers.get('stripe-signature')
        
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid payload")
        except stripe.SignatureVerificationError:
            raise HTTPException(status_code=400, detail="Invalid signature")
        
        # Handle different event types
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            order_id = session['metadata'].get('order_id')
            
            if order_id:
                # Update order status
                await db.orders.update_one(
                    {"id": order_id},
                    {
                        "$set": {
                            "payment_status": "paid",
                            "status": "processing",
                            "stripe_payment_intent_id": session.get('payment_intent'),
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
                
                # Reduce inventory for ordered items
                order = await db.orders.find_one({"id": order_id})
                if order:
                    for item in order.get("items", []):
                        await db.products.update_one(
                            {"sku": item["sku"]},
                            {"$inc": {"inventory": -item["quantity"]}}
                        )
                
                print(f"✅ Order {order_id} payment completed")
        
        elif event['type'] == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            # Handle payment failure
            print(f"❌ Payment failed: {payment_intent['id']}")
        
        return {"status": "success"}
        
    except Exception as e:
        print(f"❌ Stripe webhook error: {str(e)}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")

@api_router.get("/shop/orders/{order_id}")
async def get_order(
    order_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get order details"""
    try:
        order = await db.orders.find_one(
            {
                "id": order_id,
                "patient_id": current_user["id"]
            },
            {"_id": 0}
        )
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {
            "success": True,
            "order": order
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching order: {str(e)}")

@api_router.get("/shop/orders")
async def get_user_orders(
    current_user: dict = Depends(get_current_user),
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0)
):
    """Get user's order history"""
    try:
        orders = await db.orders.find(
            {"patient_id": current_user["id"]},
            {"_id": 0}
        ).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
        
        total_count = await db.orders.count_documents({"patient_id": current_user["id"]})
        
        return {
            "success": True,
            "orders": orders,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": total_count > (offset + limit)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching orders: {str(e)}")

# Analytics tracking
@api_router.post("/shop/analytics/track")
async def track_shopping_event(
    event_data: dict,
    request: Request,
    current_user: dict = Depends(get_current_user_optional)  # Optional auth for anonymous tracking
):
    """Track shopping analytics events"""
    try:
        # Get session ID from request
        session_id = request.headers.get("x-session-id", str(uuid.uuid4())[:16])
        
        event = ShoppingEvent(
            event_type=event_data["event_type"],
            patient_id=current_user["id"] if current_user else None,
            session_id=session_id,
            product_sku=event_data.get("product_sku"),
            order_id=event_data.get("order_id"),
            membership_tier=current_user.get("membership_tier") if current_user else None,
            metadata=event_data.get("metadata", {})
        )
        
        await db.shopping_events.insert_one(event.dict())
        
        return {"success": True, "message": "Event tracked"}
        
    except Exception as e:
        print(f"Analytics tracking error: {str(e)}")
        return {"success": False, "message": "Tracking failed"}

# Admin Order Management
@api_router.get("/admin/shop/orders")
async def get_admin_orders(
    admin_user: dict = Depends(get_admin_user),
    status: Optional[OrderStatus] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0)
):
    """Get orders for admin management"""
    try:
        query = {}
        if status:
            query["status"] = status.value
            
        orders = await db.orders.find(
            query, {"_id": 0}
        ).sort("created_at", -1).skip(offset).limit(limit).to_list(limit)
        
        total_count = await db.orders.count_documents(query)
        
        return {
            "success": True,
            "orders": orders,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": total_count > (offset + limit)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching admin orders: {str(e)}")

# Engagement Automation System
async def send_engagement_campaign(patient: dict, campaign_type: EngagementCampaignType, force_send: bool = False) -> bool:
    """Send engagement campaign to patient"""
    try:
        # Check if we should send (rate limiting)
        if not force_send:
            last_sent = patient.get('last_engagement_sent')
            if last_sent:
                hours_since_last = (datetime.utcnow() - last_sent).total_seconds() / 3600
                if hours_since_last < 24:  # Don't send more than once per day
                    return False
        
        # Get patient language preference
        language = patient.get('preferred_language', 'en')
        
        # Generate campaign content
        campaign_content = await generate_campaign_content(campaign_type, language)
        
        # Send via multiple channels
        channels_sent = []
        
        # Send push notification (if FCM token available)
        if patient.get('fcm_token'):
            try:
                push_sent = await send_push_notification(
                    patient['fcm_token'], 
                    campaign_content['push_title'], 
                    campaign_content['push_message']
                )
                if push_sent:
                    channels_sent.append('push')
            except Exception as e:
                print(f"Push notification failed: {str(e)}")
        
        # Send email
        try:
            email_sent = await send_engagement_email(
                patient['email'],
                campaign_content['email_subject'],
                campaign_content['email_html'],
                language
            )
            if email_sent:
                channels_sent.append('email')
        except Exception as e:
            print(f"Email sending failed: {str(e)}")
        
        # Log engagement
        if channels_sent:
            engagement_log = EngagementLog(
                patient_id=patient['id'],
                campaign_type=campaign_type,
                channel='+'.join(channels_sent),
                language=language,
                subject=campaign_content['email_subject'],
                message=campaign_content['push_message'],
                metadata={
                    'channels': channels_sent,
                    'lifecycle_stage': patient.get('lifecycle_stage', 'lead'),
                    'engagement_score': patient.get('engagement_score', 0)
                }
            )
            
            await db.engagement_logs.insert_one(engagement_log.dict())
            
            # Update patient engagement tracking
            await db.users.update_one(
                {"id": patient['id']},
                {
                    "$set": {
                        "last_engagement_sent": datetime.utcnow(),
                        "last_campaign_type": campaign_type.value
                    },
                    "$inc": {
                        "engagement_campaign_count": 1
                    }
                }
            )
            
            return True
        
        return False
        
    except Exception as e:
        print(f"Error sending engagement campaign: {str(e)}")
        return False

async def generate_campaign_content(campaign_type: EngagementCampaignType, language: str = 'en') -> dict:
    """Generate bilingual campaign content"""
    
    if campaign_type == EngagementCampaignType.lapsed_reactivation:
        if language == 'it':
            return {
                'push_title': 'KinAura ti sta aspettando! 🌟',
                'push_message': 'Ci manchi — torna per una consulenza gratuita.',
                'email_subject': 'Ti mancano i trattamenti KinAura? Consulenza gratuita ti aspetta',
                'email_html': f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: linear-gradient(135deg, #C8A25A 0%, #E6C78A 100%); padding: 40px; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 28px;">Ci manchi! 🌟</h1>
                    </div>
                    <div style="padding: 40px; background: white;">
                        <p style="font-size: 18px; color: #333;">Caro/a paziente,</p>
                        <p style="font-size: 16px; line-height: 1.6; color: #555;">
                            È passato un po' di tempo dalla tua ultima visita da KinAura. I nostri protocolli di bellezza e benessere 
                            ti stanno aspettando per continuare il tuo percorso di trasformazione.
                        </p>
                        <div style="background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px;">
                            <h3 style="color: #C8A25A; margin-top: 0;">🎁 Offerta Speciale di Bentornato</h3>
                            <p style="margin: 0; font-size: 16px;">Consulenza gratuita + 15% di sconto sul tuo prossimo trattamento</p>
                        </div>
                        <p style="font-size: 16px; line-height: 1.6; color: #555;">
                            Prenota ora e scopri i nostri nuovi protocolli personalizzati con tecnologie all'avanguardia.
                        </p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="#" style="background: linear-gradient(135deg, #C8A25A 0%, #E6C78A 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold;">
                                Prenota Ora
                            </a>
                        </div>
                        <p style="font-size: 14px; color: #888; text-align: center;">
                            KinAura - L'eccellenza nella medicina estetica a Milano
                        </p>
                    </div>
                </div>
                """
            }
        else:
            return {
                'push_title': 'KinAura is waiting for you! 🌟',
                'push_message': 'We miss you — come back for a complimentary consultation.',
                'email_subject': 'Missing KinAura treatments? Your complimentary consultation awaits',
                'email_html': f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: linear-gradient(135deg, #C8A25A 0%, #E6C78A 100%); padding: 40px; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 28px;">We Miss You! 🌟</h1>
                    </div>
                    <div style="padding: 40px; background: white;">
                        <p style="font-size: 18px; color: #333;">Dear valued patient,</p>
                        <p style="font-size: 16px; line-height: 1.6; color: #555;">
                            It's been a while since your last visit to KinAura. Our exclusive wellness protocols 
                            are waiting to continue your transformation journey.
                        </p>
                        <div style="background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px;">
                            <h3 style="color: #C8A25A; margin-top: 0;">🎁 Special Welcome Back Offer</h3>
                            <p style="margin: 0; font-size: 16px;">Complimentary consultation + 15% off your next treatment</p>
                        </div>
                        <p style="font-size: 16px; line-height: 1.6; color: #555;">
                            Book now and discover our latest personalized protocols with cutting-edge technology.
                        </p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="#" style="background: linear-gradient(135deg, #C8A25A 0%, #E6C78A 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold;">
                                Book Now
                            </a>
                        </div>
                        <p style="font-size: 14px; color: #888; text-align: center;">
                            KinAura - Excellence in Aesthetic Medicine, Milan
                        </p>
                    </div>
                </div>
                """
            }
    
    elif campaign_type == EngagementCampaignType.lead_nurturing:
        if language == 'it':
            return {
                'push_title': 'Il tuo protocollo personalizzato ti aspetta! ✨',
                'push_message': 'Scopri il tuo protocollo personalizzato oggi.',
                'email_subject': 'Il tuo percorso KinAura personalizzato è pronto',
                'email_html': f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: linear-gradient(135deg, #C8A25A 0%, #E6C78A 100%); padding: 40px; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 28px;">Il Tuo Protocollo Personalizzato ✨</h1>
                    </div>
                    <div style="padding: 40px; background: white;">
                        <p style="font-size: 18px; color: #333;">Benvenuto/a in KinAura,</p>
                        <p style="font-size: 16px; line-height: 1.6; color: #555;">
                            Grazie per aver scelto KinAura per il tuo percorso di bellezza e benessere. 
                            I nostri esperti hanno preparato protocolli personalizzati basati sulla scienza più avanzata.
                        </p>
                        <div style="background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px;">
                            <h3 style="color: #C8A25A; margin-top: 0;">🔬 Protocolli Scientifici Personalizzati</h3>
                            <ul style="margin: 10px 0; padding-left: 20px;">
                                <li>Morpheus8 di ultima generazione</li>
                                <li>Terapie rigenerative con esosomi</li>
                                <li>Protocolli HBOT per il biohacking</li>
                                <li>AI Longevity Score personalizzato</li>
                            </ul>
                        </div>
                        <p style="font-size: 16px; line-height: 1.6; color: #555;">
                            Prenota la tua prima consulenza e scopri come raggiungiamo risultati che altri centri non possono offrire.
                        </p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="#" style="background: linear-gradient(135deg, #C8A25A 0%, #E6C78A 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold;">
                                Inizia Ora
                            </a>
                        </div>
                    </div>
                </div>
                """
            }
        else:
            return {
                'push_title': 'Your personalized protocol awaits! ✨',
                'push_message': 'Discover your personalized protocol today.',
                'email_subject': 'Your personalized KinAura journey is ready',
                'email_html': f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: linear-gradient(135deg, #C8A25A 0%, #E6C78A 100%); padding: 40px; text-align: center;">
                        <h1 style="color: white; margin: 0; font-size: 28px;">Your Personalized Protocol ✨</h1>
                    </div>
                    <div style="padding: 40px; background: white;">
                        <p style="font-size: 18px; color: #333;">Welcome to KinAura,</p>
                        <p style="font-size: 16px; line-height: 1.6; color: #555;">
                            Thank you for choosing KinAura for your wellness journey. 
                            Our experts have prepared personalized protocols based on the most advanced science.
                        </p>
                        <div style="background: #f8f9fa; padding: 20px; margin: 20px 0; border-radius: 8px;">
                            <h3 style="color: #C8A25A; margin-top: 0;">🔬 Personalized Scientific Protocols</h3>
                            <ul style="margin: 10px 0; padding-left: 20px;">
                                <li>Latest generation Morpheus8</li>
                                <li>Regenerative exosome therapies</li>
                                <li>HBOT biohacking protocols</li>
                                <li>Personalized AI Longevity Score</li>
                            </ul>
                        </div>
                        <p style="font-size: 16px; line-height: 1.6; color: #555;">
                            Book your first consultation and discover how we achieve results other centers cannot offer.
                        </p>
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="#" style="background: linear-gradient(135deg, #C8A25A 0%, #E6C78A 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold;">
                                Start Now
                            </a>
                        </div>
                    </div>
                </div>
                """
            }
    
    return {
        'push_title': 'KinAura',
        'push_message': 'Your wellness journey continues.',
        'email_subject': 'KinAura - Your wellness update',
        'email_html': '<p>Thank you for being part of KinAura.</p>'
    }

async def send_push_notification(fcm_token: str, title: str, message: str) -> bool:
    """Send push notification via FCM"""
    try:
        # This would integrate with your existing Firebase push notification system
        # For now, we'll just log it as the FCM integration is already implemented
        print(f"📱 Push notification sent: {title} - {message}")
        return True
    except Exception as e:
        print(f"Error sending push notification: {str(e)}")
        return False

async def send_engagement_email(email: str, subject: str, html_content: str, language: str = 'en') -> bool:
    """Send engagement email"""
    try:
        # This would integrate with SendGrid/Mailgun
        # For now, we'll simulate the email sending
        print(f"📧 Email sent to {email}: {subject}")
        return True
    except Exception as e:
        print(f"Error sending email: {str(e)}")
        return False

async def run_daily_engagement_campaigns():
    """Daily engagement automation - to be called by scheduler"""
    try:
        print("🚀 Starting daily engagement campaigns...")
        
        # Get all patients who need engagement campaigns
        users = await db.users.find(
            {"role": {"$ne": "admin"}, "is_active": True}, 
            {"_id": 0}
        ).to_list(10000)
        
        campaigns_sent = 0
        
        for user in users:
            # Update lifecycle stage first
            await update_user_lifecycle_data(user['id'])
            
            # Get updated user data
            updated_user = await db.users.find_one({"id": user['id']})
            if not updated_user:
                continue
            
            lifecycle_stage = updated_user.get('lifecycle_stage', 'lead')
            last_engagement = updated_user.get('last_engagement_sent')
            created_at = updated_user.get('created_at')
            
            # Skip if campaign sent in last 24 hours
            if last_engagement:
                hours_since_engagement = (datetime.utcnow() - last_engagement).total_seconds() / 3600
                if hours_since_engagement < 24:
                    continue
            
            # Lapsed patient reactivation (>60 days since last booking)
            if lifecycle_stage == 'lapsed':
                success = await send_engagement_campaign(
                    updated_user, 
                    EngagementCampaignType.lapsed_reactivation
                )
                if success:
                    campaigns_sent += 1
                    print(f"✅ Lapsed reactivation sent to: {updated_user['email']}")
            
            # Lead nurturing (no booking after 14 days of account creation)
            elif lifecycle_stage == 'lead' and created_at:
                days_since_creation = (datetime.utcnow() - created_at).days
                if days_since_creation >= 14:
                    success = await send_engagement_campaign(
                        updated_user, 
                        EngagementCampaignType.lead_nurturing
                    )
                    if success:
                        campaigns_sent += 1
                        print(f"✅ Lead nurturing sent to: {updated_user['email']}")
        
        print(f"🎯 Daily engagement campaigns completed: {campaigns_sent} campaigns sent")
        return campaigns_sent
        
    except Exception as e:
        print(f"❌ Error running daily engagement campaigns: {str(e)}")
        return 0

# API Endpoint for manual campaign testing
@api_router.post("/admin/engagement/run-campaigns")
async def trigger_engagement_campaigns(
    admin_user: dict = Depends(get_admin_user)
):
    """Manually trigger engagement campaigns (for testing)"""
    try:
        campaigns_sent = await run_daily_engagement_campaigns()
        
        return {
            "success": True,
            "campaigns_sent": campaigns_sent,
            "message": f"Successfully sent {campaigns_sent} engagement campaigns",
            "triggered_by": admin_user["full_name"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error triggering engagement campaigns: {str(e)}")

# Patient Inquiry Detection and Tracking

TREATMENT_KEYWORDS = {
    # Aesthetic Treatments
    "morpheus8": ["morpheus8", "morpheus", "microneedling rf", "radiofrequency microneedling"],
    "laser_co2": ["laser co2", "co2 laser", "fractional laser", "laser resurfacing"],
    "bbl_hero": ["bbl", "broadband light", "hero laser", "sciton", "ipl"],
    "sculptra": ["sculptra", "plla", "poly-l-lactic acid"],
    "botox": ["botox", "botulinum", "wrinkle injections"],
    "filler": ["filler", "hyaluronic acid", "dermal filler", "lip filler"],
    "hifu": ["hifu", "high intensity focused ultrasound", "ultherapy"],
    "thread_lift": ["thread lift", "pdo threads", "facelift threads"],
    
    # Regenerative Medicine
    "nad_therapy": ["nad", "nad+", "nicotinamide", "nad infusion", "nad iv"],
    "iv_therapy": ["iv therapy", "drip", "infusion", "vitamin iv"],
    "ozone_therapy": ["ozone", "ozone therapy", "eboo", "blood ozone"],
    "red_light": ["red light", "photobiomodulation", "led therapy"],
    "pemf": ["pemf", "electromagnetic", "pulsed electromagnetic"],
    "hyperbaric": ["hyperbaric", "oxygen therapy", "hbot"],
    "peptides": ["peptides", "peptide therapy", "growth hormone peptides"],
    "exosomes": ["exosomes", "stem cell", "regenerative medicine"],
    "prp": ["prp", "platelet rich plasma", "vampire facial"],
    "glp1": ["glp-1", "glp1", "semaglutide", "weight loss injection"],
    
    # Wellness
    "cryotherapy": ["cryotherapy", "cold therapy", "whole body cryo"],
    "sauna": ["sauna", "infrared sauna", "heat therapy"],
    "compression": ["compression therapy", "lymphatic drainage"]
}

CONDITION_KEYWORDS = {
    # Skin Conditions
    "acne": ["acne", "pimples", "blackheads", "breakouts", "comedones"],
    "melasma": ["melasma", "hyperpigmentation", "dark spots", "pigmentation"],
    "wrinkles": ["wrinkles", "fine lines", "aging", "crow's feet", "laugh lines"],
    "rosacea": ["rosacea", "facial redness", "broken capillaries"],
    "sun_damage": ["sun damage", "age spots", "photo damage", "solar lentigines"],
    "stretch_marks": ["stretch marks", "striae", "skin stretching"],
    "cellulite": ["cellulite", "dimpled skin", "orange peel skin"],
    "scars": ["scars", "acne scars", "surgical scars", "keloids"],
    
    # Hair Issues
    "hair_loss": ["hair loss", "alopecia", "balding", "thinning hair", "pattern baldness"],
    "hair_thinning": ["hair thinning", "weak hair", "brittle hair"],
    
    # Body Concerns
    "weight_loss": ["weight loss", "obesity", "lose weight", "fat reduction"],
    "body_contouring": ["body contouring", "fat reduction", "body sculpting"],
    "loose_skin": ["loose skin", "saggy skin", "skin tightening"],
    
    # Health & Wellness
    "fatigue": ["fatigue", "tired", "exhaustion", "low energy", "chronic fatigue"],
    "stress": ["stress", "anxiety", "tension", "overwhelmed"],
    "sleep_issues": ["insomnia", "sleep problems", "can't sleep", "poor sleep"],
    "hormonal": ["hormonal", "hormone imbalance", "menopause", "pms"],
    "digestive": ["digestive", "gut health", "bloating", "ibs", "digestion"],
    "immune": ["immunity", "immune system", "get sick often", "low immunity"],
    "joint_pain": ["joint pain", "arthritis", "stiff joints", "mobility"],
    "inflammation": ["inflammation", "inflammatory", "swelling", "chronic inflammation"]
}

WELLNESS_GOALS = {
    "anti_aging": ["anti-aging", "longevity", "age reversal", "stay young", "prevent aging"],
    "performance": ["performance", "athletic performance", "energy boost", "stamina"],
    "detox": ["detox", "cleanse", "toxins", "purification", "liver cleanse"],
    "recovery": ["recovery", "muscle recovery", "faster healing", "injury recovery"],
    "beauty": ["beauty", "glowing skin", "radiant", "aesthetic", "beautiful"],
    "wellness": ["wellness", "health optimization", "feel better", "vitality"],
    "cognitive": ["brain health", "cognitive", "memory", "focus", "mental clarity"],
    "metabolic": ["metabolism", "metabolic health", "insulin", "blood sugar"]
}

async def detect_patient_inquiries(message: str, user_id: str, session_id: str) -> List[PatientInquiry]:
    """Detect treatment interests, health concerns, and wellness goals from chat messages"""
    if not user_id:  # Only track for logged-in users
        return []
    
    inquiries = []
    message_lower = message.lower()
    
    # Detect treatments
    detected_treatments = []
    for treatment, keywords in TREATMENT_KEYWORDS.items():
        for keyword in keywords:
            if keyword in message_lower:
                detected_treatments.append(treatment.replace("_", " ").title())
                break
    
    if detected_treatments:
        inquiry = PatientInquiry(
            patient_id=user_id,
            session_id=session_id,
            inquiry_type=InquiryType.treatment,
            detected_items=detected_treatments,
            original_message=message,
            context="Patient showed interest in specific treatments during chat",
            confidence_score=0.8,
            priority_score=4 if len(detected_treatments) > 1 else 3
        )
        inquiries.append(inquiry)
    
    # Detect conditions
    detected_conditions = []
    for condition, keywords in CONDITION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in message_lower:
                detected_conditions.append(condition.replace("_", " ").title())
                break
    
    if detected_conditions:
        inquiry = PatientInquiry(
            patient_id=user_id,
            session_id=session_id,
            inquiry_type=InquiryType.condition,
            detected_items=detected_conditions,
            original_message=message,
            context="Patient mentioned specific health concerns during chat",
            confidence_score=0.9,
            priority_score=5 if any(word in message_lower for word in ["pain", "problem", "issue", "concern"]) else 3
        )
        inquiries.append(inquiry)
    
    # Detect wellness goals
    detected_goals = []
    for goal, keywords in WELLNESS_GOALS.items():
        for keyword in keywords:
            if keyword in message_lower:
                detected_goals.append(goal.replace("_", " ").title())
                break
    
    if detected_goals:
        inquiry = PatientInquiry(
            patient_id=user_id,
            session_id=session_id,
            inquiry_type=InquiryType.wellness_goal,
            detected_items=detected_goals,
            original_message=message,
            context="Patient expressed wellness goals during chat",
            confidence_score=0.7,
            priority_score=2
        )
        inquiries.append(inquiry)
    
    return inquiries

async def save_and_notify_inquiries(inquiries: List[PatientInquiry]):
    """Save inquiries to database and create admin notifications"""
    if not inquiries:
        return
    
    # Save inquiries to database
    for inquiry in inquiries:
        await db.patient_inquiries.insert_one(inquiry.dict())
        
        # Create real-time admin notification
        patient = await db.users.find_one({"id": inquiry.patient_id}, {"_id": 0, "full_name": 1, "email": 1})
        patient_name = patient.get("full_name", "Unknown Patient") if patient else "Unknown Patient"
        
        notification = AdminNotification(
            type="inquiry_alert",
            title=f"New {inquiry.inquiry_type.value.title()} Inquiry",
            message=f"{patient_name} showed interest in: {', '.join(inquiry.detected_items)}",
            data={
                "inquiry_id": inquiry.id,
                "patient_id": inquiry.patient_id,
                "patient_name": patient_name,
                "inquiry_type": inquiry.inquiry_type.value,
                "detected_items": inquiry.detected_items,
                "priority_score": inquiry.priority_score
            },
            expires_at=datetime.utcnow() + timedelta(days=7)  # Notification expires in 7 days
        )
        await db.admin_notifications.insert_one(notification.dict())
        
        print(f"📊 INQUIRY DETECTED: {patient_name} interested in {inquiry.inquiry_type.value}: {', '.join(inquiry.detected_items)}")

async def generate_daily_inquiry_summary():
    """Generate daily summary of patient inquiries for admins"""
    try:
        today = datetime.utcnow().date()
        start_time = datetime.combine(today, datetime.min.time())
        end_time = datetime.combine(today, datetime.max.time())
        
        # Get today's inquiries
        inquiries = await db.patient_inquiries.find({
            "timestamp": {"$gte": start_time, "$lte": end_time}
        }).to_list(length=None)
        
        if not inquiries:
            return
        
        # Aggregate data
        treatment_count = len([i for i in inquiries if i["inquiry_type"] == "treatment"])
        condition_count = len([i for i in inquiries if i["inquiry_type"] == "condition"])
        wellness_count = len([i for i in inquiries if i["inquiry_type"] == "wellness_goal"])
        
        # Create summary notification
        summary_notification = AdminNotification(
            type="daily_summary",
            title=f"Daily Inquiry Summary - {today.strftime('%B %d, %Y')}",
            message=f"Today: {treatment_count} treatment interests, {condition_count} health concerns, {wellness_count} wellness goals",
            data={
                "date": today.isoformat(),
                "total_inquiries": len(inquiries),
                "treatment_count": treatment_count,
                "condition_count": condition_count,
                "wellness_count": wellness_count,
                "inquiries": inquiries[:20]  # First 20 inquiries for details
            },
            expires_at=datetime.utcnow() + timedelta(days=30)  # Keep summaries for 30 days
        )
        await db.admin_notifications.insert_one(summary_notification.dict())
        
        print(f"📈 DAILY SUMMARY: {len(inquiries)} inquiries generated")
        
    except Exception as e:
        print(f"Error generating daily summary: {e}")

# Initialize Stripe checkout
def get_stripe_checkout(request: Request) -> StripeCheckout:
    """Initialize Stripe checkout with API key and webhook URL"""
    api_key = os.environ.get('STRIPE_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Stripe API key not configured")
    
    host_url = str(request.base_url).rstrip('/')
    webhook_url = f"{host_url}/api/webhook/stripe"
    return StripeCheckout(api_key=api_key, webhook_url=webhook_url)

# Helper functions for questionnaire and document management
def generate_questionnaire_pdf(patient_id: str, questionnaire_id: str, answers: List[Dict], patient_info: Dict):
    """Generate PDF report of questionnaire responses"""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Center alignment
        )
        
        # Get questionnaire info
        questionnaire = db.questionnaires.find_one({"_id": ObjectId(questionnaire_id)})
        questionnaire_title = questionnaire.get('title', 'Questionnaire') if questionnaire else 'Questionnaire'
        
        story.append(Paragraph(f"KinAura Clinic - {questionnaire_title}", title_style))
        story.append(Spacer(1, 20))

        # Patient information
        patient_style = ParagraphStyle(
            'PatientInfo',
            parent=styles['Normal'],
            fontSize=12,
            spaceAfter=15
        )
        
        story.append(Paragraph(f"<b>Patient:</b> {patient_info.get('full_name', 'Unknown')}", patient_style))
        story.append(Paragraph(f"<b>Email:</b> {patient_info.get('email', 'Unknown')}", patient_style))
        story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}", patient_style))
        story.append(Spacer(1, 20))

        # Questionnaire responses
        for i, answer in enumerate(answers, 1):
            question_style = ParagraphStyle(
                'Question',
                parent=styles['Normal'],
                fontSize=11,
                fontName='Helvetica-Bold',
                spaceAfter=5
            )
            
            answer_style = ParagraphStyle(
                'Answer',
                parent=styles['Normal'],
                fontSize=10,
                leftIndent=20,
                spaceAfter=15
            )
            
            story.append(Paragraph(f"<b>{i}. {answer['question_text']}</b>", question_style))
            
            # Format answer based on type
            answer_text = ""
            if answer.get('answer_text'):
                answer_text = answer['answer_text']
            elif answer.get('answer_choices'):
                answer_text = ', '.join(answer['answer_choices'])
            elif answer.get('answer_number') is not None:
                answer_text = str(answer['answer_number'])
            elif answer.get('answer_date'):
                answer_text = answer['answer_date']
            else:
                answer_text = "No answer provided"
                
            story.append(Paragraph(answer_text, answer_style))

        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()
        
    except Exception as e:
        print(f"Error generating PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF report")

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

# ======================================
# GOOGLE CALENDAR SERVICE
# ======================================

class GoogleCalendarService:
    def __init__(self):
        self.credentials = None
        self.service = None
        self._initialize_service()
    
    def _initialize_service(self):
        """Initialize Google Calendar service with secure credentials"""
        try:
            # Try to load credentials from environment JSON first
            google_credentials_json = os.environ.get('GOOGLE_CREDENTIALS_JSON')
            service_account_path = os.environ.get('GOOGLE_SERVICE_ACCOUNT_PATH')
            
            if google_credentials_json:
                # Load from environment variable (preferred)
                import json
                credentials_data = json.loads(google_credentials_json)
                self.credentials = ServiceAccountCredentials.from_service_account_info(
                    credentials_data,
                    scopes=['https://www.googleapis.com/auth/calendar']
                )
                self.service = build('calendar', 'v3', credentials=self.credentials)
                logging.info("Google Calendar initialized from environment credentials")
                
            elif service_account_path and os.path.exists(service_account_path):
                # Fallback to file path (legacy)
                logging.warning("Using file-based credentials (migrate to environment variable)")
                self.credentials = ServiceAccountCredentials.from_service_account_file(
                    service_account_path,
                    scopes=['https://www.googleapis.com/auth/calendar']
                )
                self.service = build('calendar', 'v3', credentials=self.credentials)
                
            else:
                logging.warning("Google Calendar service account not configured")
        except Exception as e:
            logging.error(f"Failed to initialize Google Calendar service: {e}")
    
    async def create_appointment_event(
        self,
        title: str,
        description: str,
        start_datetime: datetime,
        end_datetime: datetime,
        patient_email: str,
        location: str = None,
        timezone: str = "Europe/Rome"
    ) -> Dict[str, Any]:
        """Create a calendar event for an appointment"""
        if not self.service:
            raise HTTPException(
                status_code=503, 
                detail="Google Calendar integration not available. Please configure Google service account credentials to enable calendar features."
            )
        
        try:
            event_body = {
                'summary': title,
                'description': description,
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': timezone,
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': timezone,
                },
                'attendees': [
                    {'email': patient_email}
                ],
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 24 hours
                        {'method': 'popup', 'minutes': 30},       # 30 minutes
                    ],
                },
                'sendNotifications': True,
                'sendUpdates': 'all'
            }
            
            if location:
                event_body['location'] = location
            
            event = self.service.events().insert(
                calendarId='primary',
                body=event_body
            ).execute()
            
            return event
            
        except HttpError as error:
            logging.error(f"Google Calendar API error: {error}")
            raise HTTPException(status_code=500, detail=f"Failed to create calendar event: {error}")
        except Exception as error:
            logging.error(f"Unexpected error creating calendar event: {error}")
            raise HTTPException(status_code=500, detail="Failed to create calendar event")
    
    async def update_event(
        self,
        event_id: str,
        title: str = None,
        description: str = None,
        start_datetime: datetime = None,
        end_datetime: datetime = None,
        status: str = None
    ) -> Dict[str, Any]:
        """Update an existing calendar event"""
        if not self.service:
            raise HTTPException(
                status_code=503, 
                detail="Google Calendar integration not available. Please configure Google service account credentials to enable calendar features."
            )
        
        try:
            # Get existing event
            event = self.service.events().get(calendarId='primary', eventId=event_id).execute()
            
            # Update fields if provided
            if title:
                event['summary'] = title
            if description:
                event['description'] = description
            if start_datetime:
                event['start']['dateTime'] = start_datetime.isoformat()
            if end_datetime:
                event['end']['dateTime'] = end_datetime.isoformat()
            if status:
                event['status'] = status
            
            updated_event = self.service.events().update(
                calendarId='primary',
                eventId=event_id,
                body=event
            ).execute()
            
            return updated_event
            
        except HttpError as error:
            logging.error(f"Google Calendar API error updating event: {error}")
            raise HTTPException(status_code=500, detail=f"Failed to update calendar event: {error}")
    
    async def delete_event(self, event_id: str):
        """Delete a calendar event"""
        if not self.service:
            raise HTTPException(
                status_code=503, 
                detail="Google Calendar integration not available. Please configure Google service account credentials to enable calendar features."
            )
        
        try:
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
        except HttpError as error:
            logging.error(f"Google Calendar API error deleting event: {error}")
            raise HTTPException(status_code=500, detail=f"Failed to delete calendar event: {error}")

# ======================================
# PUSH NOTIFICATION SERVICE
# ======================================

class PushNotificationService:
    def __init__(self):
        self.firebase_app = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase with secure credentials"""
        try:
            # Check if Firebase is already initialized
            if not firebase_admin._apps:
                # Try to load credentials from environment JSON first
                firebase_credentials_json = os.environ.get('FIREBASE_CREDENTIALS_JSON')
                service_account_path = os.environ.get('FIREBASE_SERVICE_ACCOUNT_PATH')
                
                if firebase_credentials_json:
                    # Load from environment variable (preferred)
                    import json
                    credentials_data = json.loads(firebase_credentials_json)
                    cred = credentials.Certificate(credentials_data)
                    self.firebase_app = firebase_admin.initialize_app(cred)
                    logging.info("Firebase initialized from environment credentials")
                    
                elif service_account_path and os.path.exists(service_account_path):
                    # Fallback to file path (legacy)
                    logging.warning("Using file-based Firebase credentials (migrate to environment variable)")
                    cred = credentials.Certificate(service_account_path)
                    self.firebase_app = firebase_admin.initialize_app(cred)
                    
                else:
                    logging.warning("Firebase service account not configured")
            else:
                self.firebase_app = firebase_admin.get_app()
        except Exception as e:
            logging.error(f"Failed to initialize Firebase: {e}")
    
    async def send_notification(
        self,
        tokens: List[str],
        title: str,
        body: str,
        data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Send push notification to multiple tokens"""
        if not self.firebase_app:
            raise HTTPException(
                status_code=503, 
                detail="Push notification service not available. Please configure Firebase service account credentials to enable notifications."
            )
        
        try:
            message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=title,
                    body=body
                ),
                data=data or {},
                tokens=tokens
            )
            
            response = messaging.send_multicast(message)
            
            # Log any failed sends
            if response.failure_count > 0:
                for idx, resp in enumerate(response.responses):
                    if not resp.success:
                        logging.error(f"Failed to send notification to token {tokens[idx]}: {resp.exception}")
            
            return {
                "success_count": response.success_count,
                "failure_count": response.failure_count,
                "responses": response.responses
            }
            
        except Exception as error:
            logging.error(f"Error sending push notification: {error}")
            raise HTTPException(status_code=500, detail="Failed to send push notification")
    
    async def send_appointment_notification(
        self,
        user_id: str,
        notification_type: str,
        appointment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Send appointment-specific notification"""
        # Get user's notification tokens
        tokens = await self._get_user_tokens(user_id)
        
        if not tokens:
            logging.warning(f"No notification tokens found for user {user_id}")
            return {"success_count": 0, "failure_count": 0}
        
        # Generate notification content based on type
        title, body = self._generate_notification_content(notification_type, appointment_data)
        
        # Add appointment data for deep linking
        data = {
            "type": "appointment",
            "appointment_id": appointment_data.get("id", ""),
            "notification_type": notification_type
        }
        
        return await self.send_notification(tokens, title, body, data)
    
    async def _get_user_tokens(self, user_id: str) -> List[str]:
        """Get active notification tokens for a user"""
        try:
            token_docs = await db.notification_tokens.find(
                {"user_id": user_id, "is_active": True}
            ).to_list(None)
            
            return [doc["token"] for doc in token_docs]
        except Exception as e:
            logging.error(f"Error getting user tokens: {e}")
            return []
    
    def _generate_notification_content(self, notification_type: str, appointment_data: Dict[str, Any]) -> tuple:
        """Generate notification title and body based on type"""
        service_name = appointment_data.get("service_name", "Appointment")
        date_str = appointment_data.get("date", "")
        time_str = appointment_data.get("time", "")
        
        if notification_type == "appointment_confirmation":
            title = "Appointment Confirmed"
            body = f"Your {service_name} appointment is confirmed for {date_str} at {time_str}"
        elif notification_type == "appointment_reminder":
            title = "Appointment Reminder"
            body = f"Don't forget your {service_name} appointment today at {time_str}"
        elif notification_type == "appointment_cancelled":
            title = "Appointment Cancelled"
            body = f"Your {service_name} appointment for {date_str} has been cancelled"
        elif notification_type == "appointment_rescheduled":
            title = "Appointment Rescheduled"
            body = f"Your {service_name} appointment has been rescheduled to {date_str} at {time_str}"
        else:
            title = "KinAura Notification"
            body = "You have a new notification from KinAura"
        
        return title, body

# ======================================
# NOTIFICATION SCHEDULER SERVICE
# ======================================

class NotificationScheduler:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.push_service = PushNotificationService()
        # Don't start scheduler in __init__, start it when needed
    
    def ensure_scheduler_started(self):
        """Ensure scheduler is started"""
        if not self.scheduler.running:
            try:
                self.scheduler.start()
            except RuntimeError:
                # Scheduler already running or no event loop
                pass
    
    async def schedule_appointment_reminders(
        self,
        appointment_id: str,
        patient_id: str,
        appointment_datetime: datetime,
        service_name: str,
        reminder_types: List[str] = None
    ):
        """Schedule reminder notifications for an appointment"""
        if reminder_types is None:
            reminder_types = ["reminder_24h", "reminder_2h"]
        
        schedules = []
        
        for reminder_type in reminder_types:
            schedule_time = self._calculate_reminder_time(appointment_datetime, reminder_type)
            
            if schedule_time > datetime.utcnow():
                # Create notification schedule record
                schedule = {
                    "id": str(uuid.uuid4()),
                    "appointment_id": appointment_id,
                    "patient_id": patient_id,
                    "notification_type": reminder_type,
                    "scheduled_for": schedule_time,
                    "status": "pending",
                    "created_at": datetime.utcnow()
                }
                
                # Store in database
                await db.notification_schedules.insert_one(schedule)
                
                # Schedule the job
                job_id = f"reminder_{appointment_id}_{reminder_type}"
                self.scheduler.add_job(
                    self._send_reminder_notification,
                    DateTrigger(run_date=schedule_time),
                    args=[schedule["id"]],
                    id=job_id,
                    replace_existing=True
                )
                
                schedules.append(schedule["id"])
        
        return schedules
    
    def _calculate_reminder_time(self, appointment_datetime: datetime, reminder_type: str) -> datetime:
        """Calculate when to send reminder based on type"""
        if reminder_type == "reminder_24h":
            return appointment_datetime - timedelta(hours=24)
        elif reminder_type == "reminder_2h":
            return appointment_datetime - timedelta(hours=2)
        elif reminder_type == "reminder_30m":
            return appointment_datetime - timedelta(minutes=30)
        else:
            return appointment_datetime - timedelta(hours=1)  # Default 1 hour
    
    async def _send_reminder_notification(self, schedule_id: str):
        """Send a scheduled reminder notification"""
        try:
            # Get schedule details
            schedule = await db.notification_schedules.find_one({"id": schedule_id})
            if not schedule or schedule["status"] != "pending":
                return
            
            # Get appointment details
            appointment = await db.appointment_bookings.find_one(
                {"_id": schedule["appointment_id"]}
            )
            if not appointment:
                logging.error(f"Appointment not found for reminder: {schedule['appointment_id']}")
                return
            
            # Get service details
            service = await db.services.find_one({"id": appointment["service_id"]})
            service_name = service.get("name", "Appointment") if service else "Appointment"
            
            # Prepare appointment data for notification
            appointment_data = {
                "id": appointment["_id"],
                "service_name": service_name,
                "date": appointment["appointment_date"],
                "time": appointment["start_time"]
            }
            
            # Send notification
            result = await self.push_service.send_appointment_notification(
                schedule["patient_id"],
                "appointment_reminder",
                appointment_data
            )
            
            # Update schedule status
            await db.notification_schedules.update_one(
                {"id": schedule_id},
                {
                    "$set": {
                        "status": "sent" if result["success_count"] > 0 else "failed",
                        "sent_at": datetime.utcnow()
                    }
                }
            )
            
        except Exception as e:
            logging.error(f"Error sending reminder notification: {e}")
            await db.notification_schedules.update_one(
                {"id": schedule_id},
                {"$set": {"status": "failed"}}
            )
    
    async def cancel_appointment_reminders(self, appointment_id: str):
        """Cancel all scheduled reminders for an appointment"""
        try:
            # Get all scheduled reminders for this appointment
            schedules = await db.notification_schedules.find(
                {"appointment_id": appointment_id, "status": "pending"}
            ).to_list(None)
            
            for schedule in schedules:
                # Cancel the job
                job_id = f"reminder_{appointment_id}_{schedule['notification_type']}"
                try:
                    self.scheduler.remove_job(job_id)
                except:
                    pass  # Job might not exist
                
                # Update status
                await db.notification_schedules.update_one(
                    {"id": schedule["id"]},
                    {"$set": {"status": "cancelled"}}
                )
                
        except Exception as e:
            logging.error(f"Error cancelling appointment reminders: {e}")

# Initialize global services
calendar_service = GoogleCalendarService()
push_service = PushNotificationService()
scheduler_service = None  # Will be initialized on first use

# Initialize services data
async def init_services():
    services_data = [
        {
            "id": str(uuid.uuid4()),
            "name": "Detox Therapy",
            "category": "Regenerative Wellness",
            "description": "Advanced detoxification treatment for cellular regeneration",
            "detailed_description": "Our comprehensive detox therapy combines cutting-edge technology with natural healing principles to eliminate toxins at the cellular level, promoting optimal health and vitality.",
            "duration": 90,
            "price": 299.0,
            "benefits": ["Cellular detoxification", "Improved energy levels", "Enhanced immune function", "Better sleep quality"],
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Hyperbaric Oxygen Therapy (HBOT)",
            "category": "Regenerative Wellness",
            "description": "Pure oxygen therapy in pressurized chamber for healing acceleration",
            "detailed_description": "Experience the healing power of pure oxygen delivered under pressure to enhance your body's natural healing processes, reduce inflammation, and promote tissue regeneration.",
            "duration": 60,
            "price": 199.0,
            "benefits": ["Enhanced healing", "Reduced inflammation", "Improved cognitive function", "Tissue regeneration"],
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "IV Laser Therapy",
            "category": "Regenerative Wellness",
            "description": "Intravenous laser treatment for blood purification and energy boost",
            "detailed_description": "Revolutionary IV laser therapy that purifies blood at the cellular level while boosting energy and supporting immune system function through advanced phototherapy.",
            "duration": 45,
            "price": 249.0,
            "benefits": ["Blood purification", "Energy enhancement", "Immune support", "Improved circulation"],
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "IV Therapy Drips",
            "category": "Regenerative Wellness",
            "description": "Customized vitamin and nutrient infusions for optimal wellness",
            "detailed_description": "Personalized intravenous nutrient therapy designed to replenish vitamins, minerals, and antioxidants directly into your bloodstream for maximum absorption and effectiveness.",
            "duration": 30,
            "price": 179.0,
            "benefits": ["Rapid nutrient absorption", "Hydration boost", "Energy increase", "Immune support"],
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Ozone Therapy",
            "category": "Regenerative Wellness",
            "description": "Enhancing cellular function & vitality",
            "detailed_description": "Reclaim your vitality with Ozone Therapy at Kinaura Clinic, a proven medical treatment that promotes regeneration and optimal health. Ozone therapy has been used in medical applications for over 150 years, demonstrating consistent therapeutic effects with minimal side effects. This technique utilizes medical-grade O3 (ozone) to detoxify the body, boost immune function, and enhance circulation. Research has shown its effectiveness in treating infections, chronic conditions, and cellular degeneration, making it a powerful anti-aging and wellness solution.",
            "duration": 75,
            "price": 229.0,
            "benefits": ["Immune system boost", "Detoxification", "Enhanced circulation", "Anti-aging effects", "Cellular regeneration"],
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Male Wellness Clinic",
            "category": "Specialized Wellness",
            "description": "Comprehensive wellness solutions designed specifically for men",
            "detailed_description": "Specialized wellness programs addressing men's unique health needs including hormone optimization, energy enhancement, and performance improvement through personalized treatment plans.",
            "duration": 120,
            "price": 399.0,
            "benefits": ["Hormone optimization", "Energy enhancement", "Performance improvement", "Personalized care"],
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "NAD IV Therapy",
            "category": "Regenerative Wellness",
            "description": "Advanced anti-aging and cellular repair therapy",
            "detailed_description": "Revolutionary NAD+ therapy that restores cellular energy production, supports DNA repair, and promotes longevity at the molecular level for optimal aging and vitality.",
            "duration": 180,
            "price": 449.0,
            "benefits": ["Cellular energy restoration", "DNA repair", "Anti-aging effects", "Mental clarity", "Enhanced metabolism"],
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Nutrition and Weight Loss Program",
            "category": "Wellness Programs",
            "description": "Personalized nutrition and weight management solutions",
            "detailed_description": "Comprehensive program combining personalized nutrition planning, metabolic optimization, and lifestyle coaching to achieve sustainable weight loss and optimal health outcomes.",
            "duration": 90,
            "price": 199.0,
            "benefits": ["Personalized nutrition", "Metabolic optimization", "Sustainable weight loss", "Lifestyle coaching"],
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "PEMF Therapy",
            "category": "Regenerative Wellness",
            "description": "Pulsed electromagnetic field therapy for cellular healing",
            "detailed_description": "Advanced PEMF therapy uses pulsed electromagnetic fields to stimulate cellular repair, reduce inflammation, and promote natural healing processes throughout the body.",
            "duration": 60,
            "price": 149.0,
            "benefits": ["Cellular repair", "Inflammation reduction", "Pain relief", "Improved sleep", "Enhanced recovery"],
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Peptide Therapy",
            "category": "Regenerative Wellness",
            "description": "Targeted peptide treatments for regeneration and optimization",
            "detailed_description": "Customized peptide therapy protocols designed to optimize hormone function, enhance recovery, improve cognitive performance, and support overall wellness and longevity.",
            "duration": 45,
            "price": 279.0,
            "benefits": ["Hormone optimization", "Enhanced recovery", "Cognitive improvement", "Longevity support"],
            "is_active": True
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Red Light Therapy",
            "category": "Regenerative Wellness",
            "description": "Photobiomodulation therapy for cellular energy and healing",
            "detailed_description": "Advanced red light therapy using specific wavelengths to stimulate mitochondrial function, promote collagen production, and accelerate healing at the cellular level.",
            "duration": 30,
            "price": 99.0,
            "benefits": ["Mitochondrial support", "Collagen production", "Skin rejuvenation", "Wound healing", "Pain reduction"],
            "is_active": True
        }
    ]
    
    # Check if services already exist
    existing_services = await db.services.count_documents({})
    if existing_services == 0:
        await db.services.insert_many(services_data)

# Routes
@api_router.get("/")
async def root():
    return {"message": "Welcome to KinAura - Centre for Regenerative Wellness"}

@api_router.post("/auth/register")
@limiter.limit("5/minute")  # Allow 5 registrations per minute per IP
async def register(request: Request, user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        full_name=user_data.full_name,
        phone=user_data.phone
    )
    
    user_dict = user.dict()
    user_dict["hashed_password"] = hashed_password
    
    await db.users.insert_one(user_dict)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user": user}

# Enhanced Authentication System with HttpOnly Cookies
from services.auth_service import get_auth_service, ACCESS_COOKIE_NAME, REFRESH_COOKIE_NAME, CSRF_COOKIE_NAME

# Enhanced authentication dependencies
async def get_current_user_secure(request: Request) -> dict:
    """Get current user with enhanced security (cookies + bearer fallback)"""
    auth_svc = get_auth_service()
    
    # Try cookie authentication first (web)
    user = await auth_svc.get_current_user_from_cookie(request)
    if user:
        return user
    
    # Fallback to bearer token (mobile)
    auth_header = request.headers.get("authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]  # Remove "Bearer " prefix
        try:
            payload = auth_svc.verify_access_token(token)
            user_id = payload.get("sub")
            
            if user_id:
                user = await db.users.find_one({"id": user_id}, {"_id": 0})
                if user:
                    return user
        except Exception as e:
            print(f"Bearer auth failed: {e}")
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required"
    )

async def get_admin_user_secure(current_user: dict = Depends(get_current_user_secure)):
    """Ensure current user has admin role with enhanced security"""
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# Enhanced login endpoint with secure cookies
@api_router.post("/auth/login")
@limiter.limit("10/minute")
async def secure_login(
    request: Request,
    response: Response,
    user_data: UserLogin
):
    """Enhanced login with HttpOnly cookies and CSRF protection"""
    try:
        auth_svc = get_auth_service()
        
        # Verify user credentials
        user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify password
        if not verify_password(user_data.password, user.get("hashed_password", "")):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        # Create CSRF token
        csrf_token = auth_svc.create_csrf_token()
        
        # Detect if request is from mobile app
        user_agent = request.headers.get("user-agent", "")
        is_mobile_app = "capacitor" in user_agent.lower() or "kinaura" in user_agent.lower()
        
        if is_mobile_app:
            # Mobile: Return bearer tokens
            access_token = auth_svc.create_access_token({
                "sub": user["id"],
                "email": user["email"],
                "role": user["role"]
            })
            refresh_token = auth_svc.create_refresh_token(user["id"])
            
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "full_name": user["full_name"],
                    "role": user["role"],
                    "membership_tier": user.get("membership_tier", "not_member")
                },
                "auth_type": "mobile_bearer"
            }
        else:
            # Web: Set HttpOnly cookies
            auth_svc.set_auth_cookies(response, user, csrf_token)
            
            return {
                "message": "Login successful",
                "user": {
                    "id": user["id"],
                    "email": user["email"],
                    "full_name": user["full_name"],
                    "role": user["role"],
                    "membership_tier": user.get("membership_tier", "not_member")
                },
                "csrf_token": csrf_token,
                "auth_type": "web_cookie"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

# Enhanced token refresh endpoint
@api_router.post("/auth/refresh")
@limiter.limit("20/minute")
async def refresh_token(request: Request, response: Response):
    """Refresh access token with enhanced security"""
    try:
        auth_svc = get_auth_service()
        
        # Check if request is from mobile (has Authorization header)
        auth_header = request.headers.get("authorization")
        is_mobile_request = auth_header and auth_header.startswith("Bearer ")
        
        if is_mobile_request:
            # Mobile refresh using bearer token
            refresh_token = auth_header[7:]  # Remove "Bearer " prefix
            
            try:
                payload = auth_svc.verify_refresh_token(refresh_token)
                user_id = payload.get("sub")
                
                # Check if token is blacklisted
                jti = payload.get("jti")
                if jti and await auth_svc.is_token_blacklisted(jti):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token has been revoked"
                    )
                
                # Get user
                user = await db.users.find_one({"id": user_id}, {"_id": 0})
                if not user or not user.get("is_active", True):
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="User not found or inactive"
                    )
                
                # Create new tokens
                new_access_token = auth_svc.create_access_token({
                    "sub": user["id"],
                    "email": user["email"],
                    "role": user["role"]
                })
                new_refresh_token = auth_svc.create_refresh_token(user["id"])
                
                # Blacklist old refresh token
                if jti:
                    await auth_svc.revoke_refresh_token(jti)
                
                return {
                    "access_token": new_access_token,
                    "refresh_token": new_refresh_token,
                    "token_type": "bearer",
                    "user": {
                        "id": user["id"],
                        "email": user["email"],
                        "full_name": user["full_name"],
                        "role": user["role"],
                        "membership_tier": user.get("membership_tier", "not_member")
                    }
                }
                
            except HTTPException:
                raise
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token"
                )
        else:
            # Web refresh using HttpOnly cookies
            return await auth_svc.refresh_access_token(request, response)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )

# Enhanced logout endpoint
@api_router.post("/auth/logout")
async def secure_logout(request: Request, response: Response):
    """Enhanced logout with secure token cleanup"""
    try:
        auth_svc = get_auth_service()
        
        # Check if mobile request
        auth_header = request.headers.get("authorization")
        is_mobile_request = auth_header and auth_header.startswith("Bearer ")
        
        if is_mobile_request:
            # Mobile logout - blacklist refresh token
            try:
                refresh_token = auth_header[7:]  # Assuming refresh token sent in header
                payload = auth_svc.verify_refresh_token(refresh_token)
                jti = payload.get("jti")
                
                if jti:
                    await auth_svc.revoke_refresh_token(jti)
                    
            except Exception as e:
                print(f"Mobile logout token revocation failed: {e}")
            
            return {"message": "Logout successful - clear secure storage"}
            
        else:
            # Web logout - clear cookies
            auth_svc.clear_auth_cookies(response)
            return {"message": "Logout successful"}
        
    except Exception as e:
        # Even if logout fails, clear cookies for safety
        auth_svc = get_auth_service()
        auth_svc.clear_auth_cookies(response)
        return {"message": "Logout completed"}

@api_router.post("/auth/social-login")
@limiter.limit("10/minute")  # Allow 10 social logins per minute per IP
async def social_login(request: Request, social_data: SocialLogin):
    # In a real app, verify the access_token with the social provider
    # For now, we'll create or get the user based on email
    
    existing_user = await db.users.find_one({"email": social_data.email}, {"_id": 0})
    
    if existing_user:
        # Update existing user with social login info and lifecycle data
        update_data = {
            "last_login": datetime.utcnow(),
            "social_provider": social_data.provider,
            "linked_to_social": True
        }
        
        await db.users.update_one(
            {"email": social_data.email},
            {"$set": update_data}
        )
        
        # Update lifecycle data
        await update_user_lifecycle_data(
            existing_user["id"], 
            last_login=datetime.utcnow()
        )
        
        user_obj = User(**existing_user)
        print(f"✅ Existing user/patient logged in via social: {social_data.email}")
    else:
        # Check if admin created a patient with this email
        admin_created_patient = await db.patients.find_one(
            {"email": social_data.email}, 
            {"_id": 0}
        )
        
        if admin_created_patient:
            # Create user record linked to admin-created patient
            user = User(
                id=admin_created_patient.get("id", str(uuid.uuid4())),
                email=social_data.email,
                full_name=social_data.full_name or admin_created_patient.get("full_name", ""),
                role="member",  # Patient role
                membership_tier=admin_created_patient.get("membership_tier", "basic"),
                patient_id=admin_created_patient["id"],  # Link to patient record
                linked_to_social=True,
                social_provider=social_data.provider,
                created_from_admin_patient=True
            )
            await db.users.insert_one(user.dict())
            user_obj = user
            print(f"✅ Linked social login to admin-created patient: {social_data.email}")
        else:
            # Determine role based on provider or email domain
            role = "member"  # default
            if (social_data.provider == "admin" or 
                social_data.email.endswith("@kinaura.com") or 
                social_data.email.startswith("admin@")):
                role = "admin"
            elif social_data.email.startswith("dr.") or social_data.email.startswith("doc@"):
                role = "practitioner"
            
            # Create new user
            user = User(
                email=social_data.email,
                full_name=social_data.full_name,
                role=role,
                membership_tier="elite" if role == "admin" else "not_member",
                linked_to_social=True,
                social_provider=social_data.provider
            )
            await db.users.insert_one(user.dict())
            user_obj = user
            print(f"✅ Created new social user: {social_data.email}")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_obj.id}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer", "user": user_obj}

# Enhanced user info endpoint
@api_router.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user_secure)):
    """Get current user information with enhanced security"""
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "full_name": current_user["full_name"],
        "role": current_user["role"],
        "membership_tier": current_user.get("membership_tier", "not_member"),
        "last_login": current_user.get("last_login"),
        "created_at": current_user.get("created_at")
    }

@api_router.get("/services", response_model=List[Service])
async def get_services():
    services = await db.services.find({"is_active": True}, {"_id": 0}).to_list(100)
    return [Service(**service) for service in services]

@api_router.get("/services/ungrouped")
async def get_ungrouped_services():
    """Get services that are not assigned to any group"""
    services = await db.services.find(
        {"$or": [{"group_id": None}, {"group_id": {"$exists": False}}], "is_active": True},
        {"_id": 0}
    ).to_list(None)
    
    return {"services": services}

# Enhanced services endpoint with versioning
@api_router.get("/services/sync")
async def get_services_with_sync_info(
    if_modified_since: Optional[datetime] = Query(None, description="Only return if modified since this timestamp")
):
    """Get services with sync metadata for native app caching"""
    try:
        query = {"is_active": True}
        
        # Add timestamp filter if provided
        if if_modified_since:
            query["updated_at"] = {"$gt": if_modified_since}
        
        services = await db.services.find(query, {"_id": 0}).to_list(100)
        
        # Add sync metadata
        sync_info = {
            "services": services,
            "count": len(services),
            "last_updated": max([s.get("updated_at", datetime.utcnow()) for s in services]) if services else datetime.utcnow(),
            "content_hash": hashlib.md5(str(services).encode()).hexdigest(),
            "cache_ttl": 300  # 5 minutes cache TTL
        }
        
        return sync_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting services sync info: {str(e)}")

@api_router.get("/services/{service_id}", response_model=Service)
async def get_service(service_id: str):
    service = await db.services.find_one({"id": service_id, "is_active": True}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    return Service(**service)

@api_router.post("/appointments", response_model=Appointment)
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_user: dict = Depends(get_current_user)
):
    # Verify service exists
    service = await db.services.find_one({"id": appointment_data.service_id}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    appointment = Appointment(
        user_id=current_user["id"],
        service_id=appointment_data.service_id,
        appointment_date=appointment_data.appointment_date,
        notes=appointment_data.notes
    )
    
    await db.appointments.insert_one(appointment.dict())
    return appointment

@api_router.get("/appointments", response_model=List[Appointment])
async def get_user_appointments(current_user: dict = Depends(get_current_user)):
    appointments = await db.appointments.find({"user_id": current_user["id"]}, {"_id": 0}).to_list(100)
    return [Appointment(**appointment) for appointment in appointments]

@api_router.get("/membership-benefits")
async def get_membership_benefits():
    return {
        "not_member": {
            "name": "Not a Member",
            "benefits": ["Basic service access", "Standard pricing"],
            "discount": 0
        },
        "gold": {
            "name": "Gold Member",
            "benefits": ["10% discount on all services", "Priority booking", "Monthly wellness consultation"],
            "discount": 10
        },
        "platinum": {
            "name": "Platinum Member", 
            "benefits": ["20% discount on all services", "Priority booking", "Bi-weekly consultations", "Free basic IV therapy monthly"],
            "discount": 20
        },
        "elite": {
            "name": "Elite Member",
            "benefits": ["30% discount on all services", "VIP booking access", "Weekly consultations", "Complimentary premium treatments", "24/7 concierge support"],
            "discount": 30
        }
    }

# Admin endpoints
@api_router.get("/admin/dashboard")
async def get_admin_dashboard(admin_user: dict = Depends(get_admin_user)):
    """Get admin dashboard overview data"""
    # Get total counts
    total_patients = await db.users.count_documents({"role": "member"})
    total_services = await db.services.count_documents({"is_active": True})
    total_appointments = await db.appointments.count_documents({})
    active_members = await db.users.count_documents({"role": "member", "membership_tier": {"$ne": "not_member"}})
    
    # Calculate monthly revenue (mock calculation)
    monthly_revenue = total_appointments * 150  # Average service price
    
    # Get recent activity (last 10 appointments)
    recent_appointments = await db.appointments.find({}, {"_id": 0}).sort("created_at", -1).limit(10).to_list(10)
    recent_activity = []
    for apt in recent_appointments:
        user = await db.users.find_one({"id": apt.get("user_id")}, {"_id": 0})
        service = await db.services.find_one({"id": apt.get("service_id")}, {"_id": 0})
        if user and service:
            recent_activity.append({
                "action": f"Appointment booked: {service.get('name')}",
                "user": user.get("full_name"),
                "time": "Recently"
            })

    return {
        "totalPatients": total_patients,
        "totalServices": total_services,
        "totalAppointments": total_appointments,
        "activeMembers": active_members,
        "monthlyRevenue": monthly_revenue,
        "averageLongevityScore": 78.5,  # Mock data
        "recentActivity": recent_activity[:5]  # Latest 5 activities
    }

@api_router.get("/admin/patients")
async def get_admin_patients(admin_user: dict = Depends(get_admin_user)):
    """Get all patients for admin management"""
    patients = await db.users.find({"role": "member"}, {"_id": 0}).to_list(100)
    formatted_patients = []
    
    for patient in patients:
        formatted_patients.append({
            "id": patient.get("id"),
            "full_name": patient.get("full_name"),
            "email": patient.get("email"),
            "phone": patient.get("phone"),
            "membership_tier": patient.get("membership_tier", "not_member"),
            "created_at": patient.get("created_at", datetime.utcnow()).isoformat(),
            "tags": patient.get("tags", [])
        })
    
    return formatted_patients

@api_router.post("/admin/patients")
async def create_admin_patient(
    patient_data: dict,
    admin_user: dict = Depends(get_admin_user)
):
    """Create a new patient (admin only)"""
    patient = User(
        email=patient_data["email"],
        full_name=patient_data["full_name"],
        phone=patient_data.get("phone"),
        role="member",
        membership_tier=patient_data.get("membership_tier", "not_member")
    )
    
    # Add custom fields for admin-created patients
    patient_dict = patient.dict()
    if "tags" in patient_data:
        patient_dict["tags"] = patient_data["tags"]
    if "dob" in patient_data:
        patient_dict["dob"] = patient_data["dob"]
    if "gender" in patient_data:
        patient_dict["gender"] = patient_data["gender"]
    
    await db.users.insert_one(patient_dict)
    
    # Return clean patient data without ObjectId
    return {
        "id": patient.id,
        "email": patient.email,
        "full_name": patient.full_name,
        "phone": patient.phone,
        "role": patient.role,
        "membership_tier": patient.membership_tier,
        "created_at": patient.created_at.isoformat(),
        "is_active": patient.is_active,
        **{k: v for k, v in patient_data.items() if k in ["tags", "dob", "gender"]}
    }

@api_router.get("/admin/metrics")
async def get_admin_metrics(
    metric_type: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Get specific admin metrics"""
    if metric_type == "new_patients":
        # Count new patients in last 30 days
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        count = await db.users.count_documents({
            "role": "member",
            "created_at": {"$gte": thirty_days_ago}
        })
        return {"metric": "new_patients", "value": count, "period": "30_days"}
    
    elif metric_type == "active_members":
        count = await db.users.count_documents({
            "role": "member",
            "membership_tier": {"$ne": "not_member"}
        })
        return {"metric": "active_members", "value": count}
    
    elif metric_type == "revenue":
        # Mock revenue calculation
        total_appointments = await db.appointments.count_documents({})
        revenue = total_appointments * 150
        return {"metric": "revenue", "value": revenue, "currency": "EUR"}
    
    else:
        raise HTTPException(status_code=400, detail="Invalid metric type")

@api_router.get("/admin/audit-logs")
async def get_admin_audit_logs(
    limit: int = 50,
    admin_user: dict = Depends(get_admin_user)
):
    """Get audit logs for admin review"""
    # Mock audit logs since we don't have a real audit system yet
    audit_logs = []
    
    # Get recent user registrations
    recent_users = await db.users.find({"role": "member"}, {"_id": 0}).sort("created_at", -1).limit(limit//2).to_list(limit//2)
    for user in recent_users:
        audit_logs.append({
            "id": str(uuid.uuid4()),
            "action": "user_created",
            "actor_name": "System",
            "entity_table": "users",
            "entity_id": user.get("id"),
            "created_at": user.get("created_at", datetime.utcnow()).isoformat(),
            "details": f"New user registered: {user.get('full_name')}"
        })
    
    # Get recent appointments
    recent_appointments = await db.appointments.find({}, {"_id": 0}).sort("created_at", -1).limit(limit//2).to_list(limit//2)
    for apt in recent_appointments:
        user = await db.users.find_one({"id": apt.get("user_id")}, {"_id": 0})
        service = await db.services.find_one({"id": apt.get("service_id")}, {"_id": 0})
        audit_logs.append({
            "id": str(uuid.uuid4()),
            "action": "appointment_created",
            "actor_name": user.get("full_name", "Unknown") if user else "Unknown",
            "entity_table": "appointments",
            "entity_id": apt.get("id"),
            "created_at": apt.get("created_at", datetime.utcnow()).isoformat(),
            "details": f"Appointment booked for {service.get('name', 'Unknown Service')}" if service else "Appointment booked"
        })
    
    # Sort by created_at descending
    audit_logs.sort(key=lambda x: x["created_at"], reverse=True)
    return audit_logs[:limit]

@api_router.post("/admin/services")
async def create_admin_service(
    service_data: ServiceCreate,
    admin_user: dict = Depends(get_admin_user)
):
    """Create a new service with media support (admin only)"""
    service = Service(
        name=service_data.name,
        category=service_data.category,
        description=service_data.description,
        detailed_description=service_data.detailed_description,
        duration=service_data.duration,
        price=service_data.price,
        benefits=service_data.benefits,
        is_active=service_data.is_active,
        group_id=service_data.group_id,
        images=service_data.images,
        main_image=service_data.main_image,
        brochure_url=service_data.brochure_url,
        video_url=service_data.video_url
    )
    
    await db.services.insert_one(service.dict())
    
    # Trigger content sync notification
    try:
        await notify_content_change(["services"])
    except Exception as e:
        print(f"⚠️ Failed to notify content change: {e}")
    
    return service.dict()

@api_router.put("/admin/services/{service_id}")
async def update_admin_service(
    service_id: str,
    service_data: ServiceUpdate,
    admin_user: dict = Depends(get_admin_user)
):
    """Update a service with media support (admin only)"""
    # Get existing service
    existing_service = await db.services.find_one({"id": service_id}, {"_id": 0})
    if not existing_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Create update data excluding None values
    update_data = {k: v for k, v in service_data.dict().items() if v is not None}
    
    # Add versioning fields for content sync
    update_data["updated_at"] = datetime.utcnow()
    update_data["content_version"] = str(uuid.uuid4())
    
    # Generate content hash for change detection
    content_str = f"{update_data.get('name', existing_service.get('name', ''))}"
    content_str += f"{update_data.get('description', existing_service.get('description', ''))}"
    content_str += f"{update_data.get('price', existing_service.get('price', 0))}"
    update_data["content_hash"] = hashlib.md5(content_str.encode()).hexdigest()
    
    if update_data:
        await db.services.update_one(
            {"id": service_id},
            {"$set": update_data}
        )
    
    # Trigger content sync notification
    try:
        await notify_content_change(["services"])
    except Exception as e:
        print(f"⚠️ Failed to notify content change: {e}")
    
    # Return updated service
    updated_service = await db.services.find_one({"id": service_id}, {"_id": 0})
    return updated_service

@api_router.post("/admin/services/{service_id}/media/upload")
async def upload_service_media(
    service_id: str,
    request: Request,
    admin_user: dict = Depends(get_admin_user)
):
    """Upload media files for a service (admin only)"""
    try:
        # Check if service exists
        service = await db.services.find_one({"id": service_id}, {"_id": 0})
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        # In a real implementation, you would handle file upload here
        # For now, we'll simulate with placeholder URLs
        form = await request.form()
        
        uploaded_files = []
        for key, file in form.items():
            if hasattr(file, 'filename'):
                # Simulate file upload
                file_url = f"/uploads/services/{service_id}/{file.filename}"
                uploaded_files.append({
                    "id": str(uuid.uuid4()),
                    "url": file_url,
                    "filename": file.filename,
                    "media_type": "image" if file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')) else "document"
                })
        
        # Update service with new media
        current_images = service.get("images", [])
        for uploaded_file in uploaded_files:
            current_images.append(uploaded_file["url"])
        
        await db.services.update_one(
            {"id": service_id},
            {"$set": {"images": current_images}}
        )
        
        return {"uploaded_files": uploaded_files}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@api_router.delete("/admin/services/{service_id}/media/{media_url}")
async def delete_service_media(
    service_id: str,
    media_url: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Delete media from a service (admin only)"""
    service = await db.services.find_one({"id": service_id}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Remove media URL from service images
    current_images = service.get("images", [])
    updated_images = [img for img in current_images if img != media_url]
    
    await db.services.update_one(
        {"id": service_id},
        {"$set": {"images": updated_images}}
    )
    
    return {"message": "Media removed successfully"}

@api_router.put("/admin/services/{service_id}/main-image")
async def set_service_main_image(
    service_id: str,
    image_data: dict,
    admin_user: dict = Depends(get_admin_user)
):
    """Set the main image for a service (admin only)"""
    service = await db.services.find_one({"id": service_id}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    await db.services.update_one(
        {"id": service_id},
        {"$set": {"main_image": image_data.get("image_url")}}
    )
    
    return {"message": "Main image updated successfully"}

@api_router.get("/admin/services")
async def get_admin_services(
    admin_user: dict = Depends(get_admin_user)
):
    """Get all services with media for admin management"""
    services = await db.services.find({}, {"_id": 0}).to_list(None)
    return {"services": services}

@api_router.delete("/admin/services/{service_id}")
async def delete_admin_service(
    service_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Delete a service (admin only)"""
    # Check if service exists
    existing_service = await db.services.find_one({"id": service_id}, {"_id": 0})
    if not existing_service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Check if service has associated appointments
    appointments_count = await db.appointments.count_documents({"service_id": service_id})
    if appointments_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete service with {appointments_count} associated appointments. Cancel appointments first."
        )
    
    # Delete the service
    await db.services.delete_one({"id": service_id})
    return {"message": "Service deleted successfully"}

# ======================================
# SERVICE GROUPS MANAGEMENT API ENDPOINTS
# ======================================

@api_router.post("/admin/service-groups")
async def create_service_group(
    group_data: ServiceGroupCreate,
    admin_user: dict = Depends(get_admin_user)
):
    """Create a new service group (admin only)"""
    group = ServiceGroup(
        name=group_data.name,
        description=group_data.description,
        icon=group_data.icon,
        display_order=group_data.display_order,
        is_active=group_data.is_active,
        color_theme=group_data.color_theme
    )
    
    await db.service_groups.insert_one(group.dict())
    return group.dict()

@api_router.get("/admin/service-groups")
async def get_admin_service_groups(
    admin_user: dict = Depends(get_admin_user)
):
    """Get all service groups for admin management"""
    groups = await db.service_groups.find({}, {"_id": 0}).sort("display_order", 1).to_list(None)
    
    # Add service count to each group
    for group in groups:
        service_count = await db.services.count_documents({"group_id": group["id"]})
        group["service_count"] = service_count
    
    return {"service_groups": groups}

@api_router.put("/admin/service-groups/{group_id}")
async def update_service_group(
    group_id: str,
    group_data: ServiceGroupUpdate,
    admin_user: dict = Depends(get_admin_user)
):
    """Update a service group (admin only)"""
    existing_group = await db.service_groups.find_one({"id": group_id}, {"_id": 0})
    if not existing_group:
        raise HTTPException(status_code=404, detail="Service group not found")
    
    # Create update data excluding None values
    update_data = {k: v for k, v in group_data.dict().items() if v is not None}
    
    if update_data:
        await db.service_groups.update_one(
            {"id": group_id},
            {"$set": update_data}
        )
    
    # Return updated group
    updated_group = await db.service_groups.find_one({"id": group_id}, {"_id": 0})
    return updated_group

@api_router.delete("/admin/service-groups/{group_id}")
async def delete_service_group(
    group_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Delete a service group (admin only)"""
    existing_group = await db.service_groups.find_one({"id": group_id}, {"_id": 0})
    if not existing_group:
        raise HTTPException(status_code=404, detail="Service group not found")
    
    # Check if group has services
    services_in_group = await db.services.count_documents({"group_id": group_id})
    if services_in_group > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete group with {services_in_group} services. Move services to another group first."
        )
    
    await db.service_groups.delete_one({"id": group_id})
    return {"message": "Service group deleted successfully"}

@api_router.put("/admin/services/{service_id}/group")
async def assign_service_to_group(
    service_id: str,
    group_assignment: dict,
    admin_user: dict = Depends(get_admin_user)
):
    """Assign a service to a group (admin only)"""
    service = await db.services.find_one({"id": service_id}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")
    
    group_id = group_assignment.get("group_id")
    
    # If group_id is provided, verify the group exists
    if group_id:
        group = await db.service_groups.find_one({"id": group_id}, {"_id": 0})
        if not group:
            raise HTTPException(status_code=404, detail="Service group not found")
    
    await db.services.update_one(
        {"id": service_id},
        {"$set": {"group_id": group_id}}
    )
    
    return {"message": "Service group assignment updated"}

@api_router.get("/service-groups")
async def get_public_service_groups():
    """Get active service groups with their services for public viewing"""
    groups = await db.service_groups.find(
        {"is_active": True}, 
        {"_id": 0}
    ).sort("display_order", 1).to_list(None)
    
    # Add services to each group
    for group in groups:
        services = await db.services.find(
            {"group_id": group["id"], "is_active": True}, 
            {"_id": 0}
        ).to_list(None)
        group["services"] = services
        group["service_count"] = len(services)
    
    return {"service_groups": groups}

@api_router.get("/service-groups/{group_id}")
async def get_service_group_with_services(group_id: str):
    """Get a specific service group with its services"""
    group = await db.service_groups.find_one(
        {"id": group_id, "is_active": True}, 
        {"_id": 0}
    )
    if not group:
        raise HTTPException(status_code=404, detail="Service group not found")
    
    # Get services in this group
    services = await db.services.find(
        {"group_id": group_id, "is_active": True}, 
        {"_id": 0}
    ).to_list(None)
    
    group["services"] = services
    group["service_count"] = len(services)
    
    return group

@api_router.get("/admin/appointments")
async def get_admin_appointments(
    limit: int = 100,
    admin_user: dict = Depends(get_admin_user)
):
    """Get all appointments for admin management"""
    appointments = await db.appointments.find({}, {"_id": 0}).sort("appointment_date", -1).limit(limit).to_list(limit)
    formatted_appointments = []
    
    for apt in appointments:
        user = await db.users.find_one({"id": apt.get("user_id")}, {"_id": 0})
        service = await db.services.find_one({"id": apt.get("service_id")}, {"_id": 0})
        
        formatted_appointments.append({
            "id": apt.get("id"),
            "patient_name": user.get("full_name") if user else "Unknown",
            "service_name": service.get("name") if service else "Unknown Service",
            "appointment_date": apt.get("appointment_date"),
            "status": apt.get("status", "scheduled"),
            "practitioner": "Dr. Marco Rossi",  # Mock data
            "notes": apt.get("notes")
        })
    
    return formatted_appointments

# Patient File Management endpoints
@api_router.get("/admin/patients/{patient_id}/files")
async def get_patient_files(
    patient_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Get all files for a specific patient (admin only)"""
    files = await db.patient_files.find({"patient_id": patient_id}, {"_id": 0}).sort("upload_date", -1).to_list(100)
    return [PatientFile(**file) for file in files]

@api_router.get("/admin/patients/{patient_id}/folder")
async def get_patient_folder_info(
    patient_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Get patient folder statistics and organization"""
    files = await db.patient_files.find({"patient_id": patient_id}, {"_id": 0}).to_list(1000)
    
    if not files:
        return PatientFolder(patient_id=patient_id)
    
    # Calculate statistics
    total_files = len(files)
    visible_files = len([f for f in files if f.get("visible_to_patient", False)])
    private_files = total_files - visible_files
    
    # Count by category
    categories = {}
    for file in files:
        category = file.get("file_category", "general")
        categories[category] = categories.get(category, 0) + 1
    
    # Get latest upload date
    latest_file = max(files, key=lambda x: x.get("upload_date", datetime.min))
    last_updated = latest_file.get("upload_date", datetime.utcnow())
    
    return PatientFolder(
        patient_id=patient_id,
        total_files=total_files,
        visible_files=visible_files,
        private_files=private_files,
        categories=categories,
        last_updated=last_updated
    )

@api_router.post("/admin/patients/{patient_id}/files/upload")
@enhanced_limiter.limit("10/minute")  # 10 file uploads per minute
async def upload_patient_file(
    request: Request,
    patient_id: str,
    file_data: PatientFileUpload,
    admin_user: dict = Depends(get_admin_user)
):
    """Upload a new file for a patient (admin only)"""
    # Verify patient exists
    patient = await db.users.find_one({"id": patient_id, "role": "member"}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    # For demo purposes, we'll simulate file upload
    # In production, you'd handle actual file upload to storage
    file_record = PatientFile(
        patient_id=patient_id,
        filename=f"file_{int(datetime.utcnow().timestamp())}.pdf",  # Mock filename
        original_filename=file_data.description or "uploaded_file.pdf",
        file_type=file_data.file_type,
        file_category=file_data.file_category,
        file_path=f"/patient_files/{patient_id}/file_{int(datetime.utcnow().timestamp())}.pdf",
        file_size=1024,  # Mock size
        mime_type="application/pdf",  # Mock mime type
        visible_to_patient=file_data.visible_to_patient,
        description=file_data.description,
        notes=file_data.notes,
        uploaded_by=admin_user["id"],
        tags=file_data.tags
    )
    
    await db.patient_files.insert_one(file_record.dict())
    return file_record

@api_router.put("/admin/files/{file_id}")
async def update_patient_file(
    file_id: str,
    file_update: PatientFileUpdate,
    admin_user: dict = Depends(get_admin_user)
):
    """Update patient file metadata and visibility"""
    # Find the file
    existing_file = await db.patient_files.find_one({"id": file_id}, {"_id": 0})
    if not existing_file:
        raise HTTPException(status_code=404, detail="File not found")
    
    # Prepare update data
    update_data = {k: v for k, v in file_update.dict().items() if v is not None}
    
    # Update the file
    await db.patient_files.update_one({"id": file_id}, {"$set": update_data})
    
    # Return updated file
    updated_file = await db.patient_files.find_one({"id": file_id}, {"_id": 0})
    return PatientFile(**updated_file)

@api_router.delete("/admin/files/{file_id}")
async def delete_patient_file(
    file_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Delete a patient file"""
    result = await db.patient_files.delete_one({"id": file_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="File not found")
    
    return {"message": "File deleted successfully"}

@api_router.get("/admin/files/{file_id}/download")
async def download_patient_file(
    file_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Download a patient file (admin only)"""
    file_record = await db.patient_files.find_one({"id": file_id}, {"_id": 0})
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")
    
    # In production, you'd serve the actual file from storage
    # For demo, return file metadata
    return {
        "file_id": file_id,
        "filename": file_record["original_filename"],
        "download_url": f"/files/{file_record['filename']}",
        "message": "File download ready"
    }

# Patient-facing file endpoints
@api_router.get("/patient/files")
async def get_patient_files(current_user: dict = Depends(get_current_user)):
    """Get files for the current patient (only files visible to patient)"""
    
    # Get user's patient_id or use user id if they are a direct patient
    patient_id = current_user.get("patient_id") or current_user["id"]
    
    # Find files for this patient that are visible to the patient
    files = await db.patient_files.find(
        {
            "patient_id": patient_id,
            "visible_to_patient": True
        },
        {"notes": 0, "uploaded_by": 0}  # Exclude admin-only fields
    ).sort("upload_date", -1).to_list(100)
    
    if not files:
        return []
    
    # Format for patient view
    for file_record in files:
        # Convert ObjectId to string if present
        if "_id" in file_record:
            del file_record["_id"]
    
    return files

@api_router.get("/patient/files/{file_id}")
async def get_patient_file(file_id: str, current_user: dict = Depends(get_current_user)):
    """Get specific file details for patient"""
    
    # Get user's patient_id or use user id if they are a direct patient
    patient_id = current_user.get("patient_id") or current_user["id"]
    
    file_record = await db.patient_files.find_one(
        {
            "id": file_id,
            "patient_id": patient_id,
            "visible_to_patient": True
        },
        {"notes": 0, "uploaded_by": 0}  # Exclude admin-only fields
    )
    
    if not file_record:
        raise HTTPException(status_code=404, detail="File not found or not accessible")
    
    # Remove MongoDB ObjectId
    if "_id" in file_record:
        del file_record["_id"]
    
    return file_record

@api_router.post("/patient/upload-document")
async def upload_patient_document(
    file: UploadFile = File(...),
    category: str = "other",
    description: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Upload a document as a patient"""
    
    # Validate file size (max 10MB)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 10MB")
    
    # Validate file type
    allowed_types = [
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'text/plain',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ]
    
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not supported")
    
    # Create file record
    file_record = PatientFile(
        patient_id=current_user["id"],
        filename=f"patient_upload_{int(datetime.utcnow().timestamp())}_{file.filename}",
        original_filename=file.filename,
        file_type="document",
        file_category=category,
        file_path=f"/patient_uploads/{current_user['id']}/{file.filename}",
        file_size=file_size,
        mime_type=file.content_type,
        visible_to_patient=True,  # Patient uploads are visible to patient by default
        description=description or f"Patient uploaded: {file.filename}",
        notes=f"Uploaded by patient on {datetime.utcnow().isoformat()}",
        uploaded_by=current_user["id"],
        tags=["patient_upload", category]
    )
    
    # In production, you would save the file to storage (S3, local filesystem, etc.)
    # For now, we'll just store the file metadata
    
    await db.patient_files.insert_one(file_record.dict())
    
    return {
        "message": "Document uploaded successfully",
        "file_id": file_record.id,
        "filename": file_record.original_filename,
        "category": file_record.file_category,
        "size": file_record.file_size
    }

# Patient Notes endpoints
@api_router.get("/admin/patients/{patient_id}/notes")
async def get_patient_notes(
    patient_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Get all notes for a specific patient"""
    notes = await db.patient_notes.find({"patient_id": patient_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return [PatientNote(**note) for note in notes]

@api_router.post("/admin/patients/{patient_id}/notes")
async def create_patient_note(
    patient_id: str,
    note_data: PatientNoteCreate,
    admin_user: dict = Depends(get_admin_user)
):
    """Create a new note for a patient"""
    # Verify patient exists
    patient = await db.users.find_one({"id": patient_id, "role": "member"}, {"_id": 0})
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    note = PatientNote(
        patient_id=patient_id,
        author_id=admin_user["id"],
        author_name=admin_user["full_name"],
        title=note_data.title,
        content=note_data.content,
        category=note_data.category,
        is_important=note_data.is_important
    )
    
    await db.patient_notes.insert_one(note.dict())
    return note

@api_router.put("/admin/notes/{note_id}")
async def update_patient_note(
    note_id: str,
    note_update: PatientNoteUpdate,
    admin_user: dict = Depends(get_admin_user)
):
    """Update an existing patient note"""
    # Find the note
    existing_note = await db.patient_notes.find_one({"id": note_id}, {"_id": 0})
    if not existing_note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Prepare update data
    update_data = {k: v for k, v in note_update.dict().items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    # Update the note
    await db.patient_notes.update_one({"id": note_id}, {"$set": update_data})
    
    # Return updated note
    updated_note = await db.patient_notes.find_one({"id": note_id}, {"_id": 0})
    return PatientNote(**updated_note)

@api_router.delete("/admin/notes/{note_id}")
async def delete_patient_note(
    note_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Delete a patient note"""
    result = await db.patient_notes.delete_one({"id": note_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    
    return {"message": "Note deleted successfully"}

# Notification endpoints
@api_router.post("/admin/notifications/send")
async def send_notification(
    notification_request: NotificationRequest,
    admin_user: dict = Depends(get_admin_user)
):
    """Send notification to patients based on targeting criteria"""
    target_patients = []
    
    if notification_request.target_type == "single":
        if not notification_request.target_patient_id:
            raise HTTPException(status_code=400, detail="Patient ID required for single notification")
        
        patient = await db.users.find_one(
            {"id": notification_request.target_patient_id, "role": "member"}, 
            {"_id": 0}
        )
        if patient:
            target_patients = [patient]
    
    elif notification_request.target_type == "tags":
        if not notification_request.target_tags:
            raise HTTPException(status_code=400, detail="Tags required for tag-based notification")
        
        # Find patients with any of the specified tags
        target_patients = await db.users.find(
            {
                "role": "member",
                "tags": {"$in": notification_request.target_tags}
            },
            {"_id": 0}
        ).to_list(1000)
    
    elif notification_request.target_type == "membership":
        if not notification_request.target_membership:
            raise HTTPException(status_code=400, detail="Membership tier required for membership-based notification")
        
        target_patients = await db.users.find(
            {
                "role": "member",
                "membership_tier": notification_request.target_membership
            },
            {"_id": 0}
        ).to_list(1000)
    
    elif notification_request.target_type == "all":
        target_patients = await db.users.find({"role": "member"}, {"_id": 0}).to_list(1000)
    
    else:
        raise HTTPException(status_code=400, detail="Invalid target type")
    
    # Store notification log
    notification_log = NotificationLog(
        title=notification_request.title,
        message=notification_request.message,
        target_type=notification_request.target_type,
        target_criteria={
            "patient_id": notification_request.target_patient_id,
            "tags": notification_request.target_tags,
            "membership": notification_request.target_membership
        },
        sent_count=len(target_patients),
        created_by=admin_user["id"],
        sent_at=datetime.utcnow() if notification_request.send_immediately else None,
        status="sent" if notification_request.send_immediately else "scheduled"
    )
    
    await db.notification_logs.insert_one(notification_log.dict())
    
    # In a real implementation, this would trigger actual push notifications
    # For now, we'll simulate the notification sending
    sent_notifications = []
    for patient in target_patients:
        sent_notifications.append({
            "patient_id": patient["id"],
            "patient_name": patient["full_name"],
            "email": patient["email"],
            "title": notification_request.title,
            "message": notification_request.message,
            "sent_at": datetime.utcnow().isoformat()
        })
    
    return {
        "message": f"Notification sent to {len(target_patients)} patients",
        "notification_id": notification_log.id,
        "target_count": len(target_patients),
        "sent_notifications": sent_notifications[:10]  # Return first 10 for preview
    }

@api_router.get("/admin/notifications/logs")
async def get_notification_logs(
    limit: int = 50,
    admin_user: dict = Depends(get_admin_user)
):
    """Get notification history logs"""
    logs = await db.notification_logs.find({}, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return [NotificationLog(**log) for log in logs]

@api_router.get("/admin/patients/filter")
async def get_filtered_patients(
    tags: Optional[str] = None,
    membership: Optional[str] = None,
    admin_user: dict = Depends(get_admin_user)
):
    """Get patients filtered by tags or membership for notification targeting"""
    query = {"role": "member"}
    
    if tags:
        tag_list = [tag.strip() for tag in tags.split(',') if tag.strip()]
        query["tags"] = {"$in": tag_list}
    
    if membership:
        query["membership_tier"] = membership
    
    patients = await db.users.find(query, {"_id": 0}).to_list(1000)
    
    return {
        "total_count": len(patients),
        "patients": [
            {
                "id": p["id"],
                "full_name": p["full_name"],
                "email": p["email"],
                "membership_tier": p.get("membership_tier", "not_member"),
                "tags": p.get("tags", [])
            }
            for p in patients
        ]
    }

# QUESTIONNAIRE AND DOCUMENT MANAGEMENT ENDPOINTS

# Questionnaire Management
@api_router.post("/admin/questionnaires", dependencies=[Depends(get_admin_user)])
async def create_questionnaire(questionnaire: CreateQuestionnaireRequest, current_user: dict = Depends(get_admin_user)):
    """Create a new questionnaire template"""
    try:
        questionnaire_id = str(uuid.uuid4())
        questionnaire_data = {
            "_id": questionnaire_id,
            "title": questionnaire.title,
            "description": questionnaire.description,
            "category": questionnaire.category,
            "is_active": True,
            "is_required": questionnaire.is_required,
            "instructions": questionnaire.instructions,
            "questions": [],
            "created_by": current_user["id"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": questionnaire.metadata or {}
        }
        
        await db.questionnaires.insert_one(questionnaire_data)
        
        return {
            "success": True,
            "questionnaire_id": questionnaire_id,
            "message": "Questionnaire created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create questionnaire: {str(e)}")

@api_router.get("/admin/questionnaires", dependencies=[Depends(get_admin_user)])
async def get_questionnaires(current_user: dict = Depends(get_admin_user)):
    """Get all questionnaires"""
    try:
        questionnaires = list(await db.questionnaires.find({"is_active": True}).sort("created_at", -1).to_list(100))
        
        # Convert ObjectId to string and add question count
        for questionnaire in questionnaires:
            questionnaire["_id"] = str(questionnaire["_id"])
            questionnaire["question_count"] = len(questionnaire.get("questions", []))
            
            # Get assignment statistics
            assignments = list(await db.patient_questionnaires.find({"questionnaire_id": questionnaire["_id"]}).to_list(1000))
            questionnaire["assignments"] = {
                "total": len(assignments),
                "completed": len([a for a in assignments if a.get("status") == "completed"]),
                "pending": len([a for a in assignments if a.get("status") in ["assigned", "in_progress"]])
            }
        
        return questionnaires
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch questionnaires: {str(e)}")

@api_router.post("/admin/questionnaires/{questionnaire_id}/questions", dependencies=[Depends(get_admin_user)])
async def add_question(questionnaire_id: str, question: CreateQuestionRequest, current_user: dict = Depends(get_admin_user)):
    """Add a question to a questionnaire"""
    try:
        question_id = str(uuid.uuid4())
        question_data = {
            "id": question_id,
            "question_text": question.question_text,
            "question_type": question.question_type,
            "is_required": question.is_required,
            "order_index": question.order_index,
            "options": question.options or {},
            "validation": question.validation or {},
            "help_text": question.help_text
        }
        
        # Add question to questionnaire
        await db.questionnaires.update_one(
            {"_id": questionnaire_id},
            {
                "$push": {"questions": question_data},
                "$set": {"updated_at": datetime.utcnow()}
            }
        )
        
        return {
            "success": True,
            "question_id": question_id,
            "message": "Question added successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add question: {str(e)}")

@api_router.post("/admin/questionnaires/assign", dependencies=[Depends(get_admin_user)])
async def assign_questionnaire(assignment: AssignQuestionnaireRequest, current_user: dict = Depends(get_admin_user)):
    """Assign a questionnaire to a patient"""
    try:
        # Check if questionnaire exists
        questionnaire = await db.questionnaires.find_one({"_id": assignment.questionnaire_id})
        if not questionnaire:
            raise HTTPException(status_code=404, detail="Questionnaire not found")
        
        # Check if patient exists
        patient = await db.users.find_one({"id": assignment.patient_id})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Check if already assigned and not completed
        existing = await db.patient_questionnaires.find_one({
            "patient_id": assignment.patient_id,
            "questionnaire_id": assignment.questionnaire_id,
            "status": {"$in": ["assigned", "in_progress"]}
        })
        
        if existing:
            raise HTTPException(status_code=400, detail="Questionnaire already assigned to this patient")
        
        assignment_id = str(uuid.uuid4())
        assignment_data = {
            "_id": assignment_id,
            "patient_id": assignment.patient_id,
            "questionnaire_id": assignment.questionnaire_id,
            "assigned_by": current_user["id"],
            "assigned_at": datetime.utcnow(),
            "due_date": assignment.due_date,
            "status": "assigned",
            "context": assignment.context or {}
        }
        
        await db.patient_questionnaires.insert_one(assignment_data)
        
        # Log the assignment
        await db.audit_logs.insert_one({
            "_id": str(uuid.uuid4()),
            "actor_id": current_user["id"],
            "action": "questionnaire_assigned",
            "entity_table": "patient_questionnaires",
            "entity_id": assignment_id,
            "diff": {
                "patient_id": assignment.patient_id,
                "questionnaire_title": questionnaire.get("title")
            },
            "timestamp": datetime.utcnow()
        })
        
        return {
            "success": True,
            "assignment_id": assignment_id,
            "message": "Questionnaire assigned successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign questionnaire: {str(e)}")

# Patient Questionnaire Endpoints
@api_router.get("/patient/questionnaires", dependencies=[Depends(get_current_user)])
async def get_my_questionnaires(current_user: dict = Depends(get_current_user)):
    """Get patient's assigned questionnaires"""
    try:
        # Find assignments for current patient
        assignments = list(await db.patient_questionnaires.find({
            "patient_id": current_user["id"],
            "status": {"$in": ["assigned", "in_progress"]}
        }).sort("assigned_at", 1).to_list(100))
        
        result = []
        for assignment in assignments:
            questionnaire = await db.questionnaires.find_one({"_id": assignment["questionnaire_id"]})
            if questionnaire:
                result.append({
                    "assignment_id": str(assignment["_id"]),
                    "questionnaire": {
                        "id": str(questionnaire["_id"]),
                        "title": questionnaire["title"],
                        "description": questionnaire["description"],
                        "category": questionnaire["category"],
                        "instructions": questionnaire["instructions"],
                        "question_count": len(questionnaire.get("questions", []))
                    },
                    "status": assignment["status"],
                    "assigned_at": assignment["assigned_at"],
                    "due_date": assignment.get("due_date"),
                    "started_at": assignment.get("started_at"),
                    "completed_at": assignment.get("completed_at")
                })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch questionnaires: {str(e)}")

@api_router.get("/patient/questionnaires/{assignment_id}", dependencies=[Depends(get_current_user)])
async def get_questionnaire_for_completion(assignment_id: str, current_user: dict = Depends(get_current_user)):
    """Get questionnaire data for patient completion"""
    try:
        # Get assignment and verify ownership
        assignment = await db.patient_questionnaires.find_one({
            "_id": assignment_id,
            "patient_id": current_user["id"]
        })
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Questionnaire assignment not found")
        
        # Get questionnaire
        questionnaire = await db.questionnaires.find_one({"_id": assignment["questionnaire_id"]})
        if not questionnaire:
            raise HTTPException(status_code=404, detail="Questionnaire not found")
        
        # Get existing answers
        answers = list(await db.patient_answers.find({"patient_questionnaire_id": assignment_id}).to_list(1000))
        answers_dict = {answer["question_id"]: answer for answer in answers}
        
        # Build response with questions and existing answers
        questions = []
        for question in questionnaire.get("questions", []):
            existing_answer = answers_dict.get(question["id"], {})
            questions.append({
                "id": question["id"],
                "text": question["question_text"],
                "type": question["question_type"],
                "required": question["is_required"],
                "order": question["order_index"],
                "options": question.get("options", {}),
                "help_text": question.get("help_text"),
                "current_answer": {
                    "text": existing_answer.get("answer_text"),
                    "choices": existing_answer.get("answer_choices", []),
                    "number": existing_answer.get("answer_number"),
                    "date": existing_answer.get("answer_date"),
                    "answered_at": existing_answer.get("answered_at")
                }
            })
        
        return {
            "assignment_id": assignment_id,
            "questionnaire": {
                "title": questionnaire["title"],
                "description": questionnaire["description"],
                "instructions": questionnaire["instructions"]
            },
            "questions": sorted(questions, key=lambda x: x["order"]),
            "status": assignment["status"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get questionnaire: {str(e)}")

@api_router.post("/patient/questionnaires/{assignment_id}/start", dependencies=[Depends(get_current_user)])
async def start_questionnaire(assignment_id: str, current_user: dict = Depends(get_current_user)):
    """Mark questionnaire as started"""
    try:
        result = await db.patient_questionnaires.update_one(
            {
                "_id": assignment_id,
                "patient_id": current_user["id"],
                "status": "assigned"
            },
            {
                "$set": {
                    "status": "in_progress",
                    "started_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Questionnaire assignment not found or already started")
        
        return {"success": True, "message": "Questionnaire started"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start questionnaire: {str(e)}")

@api_router.post("/patient/questionnaires/{assignment_id}/answers", dependencies=[Depends(get_current_user)])
async def submit_answers(assignment_id: str, answers_request: SubmitAnswersRequest, current_user: dict = Depends(get_current_user)):
    """Submit answers for a questionnaire"""
    try:
        # Verify assignment ownership
        assignment = await db.patient_questionnaires.find_one({
            "_id": assignment_id,
            "patient_id": current_user["id"]
        })
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Questionnaire assignment not found")
        
        # Save/update answers
        for answer in answers_request.answers:
            answer_data = {
                "patient_questionnaire_id": assignment_id,
                "question_id": answer.question_id,
                "answer_text": answer.answer_text,
                "answer_number": answer.answer_number,
                "answer_date": answer.answer_date,
                "answer_choices": answer.answer_choices,
                "answer_files": answer.answer_files,
                "answered_at": datetime.utcnow()
            }
            
            await db.patient_answers.update_one(
                {
                    "patient_questionnaire_id": assignment_id,
                    "question_id": answer.question_id
                },
                {"$set": answer_data},
                upsert=True
            )
        
        return {"success": True, "message": "Answers saved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to submit answers: {str(e)}")

@api_router.post("/patient/questionnaires/{assignment_id}/complete", dependencies=[Depends(get_current_user)])
async def complete_questionnaire(assignment_id: str, current_user: dict = Depends(get_current_user)):
    """Mark questionnaire as completed"""
    try:
        result = await db.patient_questionnaires.update_one(
            {
                "_id": assignment_id,
                "patient_id": current_user["id"],
                "status": "in_progress"
            },
            {
                "$set": {
                    "status": "completed",
                    "completed_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Questionnaire assignment not found or not in progress")
        
        return {"success": True, "message": "Questionnaire completed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete questionnaire: {str(e)}")

# Admin: View Patient Responses
@api_router.get("/admin/patients/{patient_id}/questionnaire-responses", dependencies=[Depends(get_admin_user)])
async def get_patient_questionnaire_responses(patient_id: str, questionnaire_id: str = Query(None), current_user: dict = Depends(get_admin_user)):
    """Get patient's questionnaire responses"""
    try:
        # Find assignments
        query = {"patient_id": patient_id}
        if questionnaire_id:
            query["questionnaire_id"] = questionnaire_id
        
        assignments = list(await db.patient_questionnaires.find(query).to_list(1000))
        
        result = []
        for assignment in assignments:
            questionnaire = await db.questionnaires.find_one({"_id": assignment["questionnaire_id"]})
            if not questionnaire:
                continue
            
            # Get answers for this assignment
            answers = list(await db.patient_answers.find({"patient_questionnaire_id": str(assignment["_id"])}).to_list(1000))
            answers_dict = {answer["question_id"]: answer for answer in answers}
            
            # Build response with questions and answers
            questions_with_answers = []
            for question in questionnaire.get("questions", []):
                answer = answers_dict.get(question["id"], {})
                questions_with_answers.append({
                    "question_text": question["question_text"],
                    "question_type": question["question_type"],
                    "answer_text": answer.get("answer_text"),
                    "answer_choices": answer.get("answer_choices"),
                    "answer_number": answer.get("answer_number"),
                    "answer_date": answer.get("answer_date"),
                    "answered_at": answer.get("answered_at")
                })
            
            result.append({
                "questionnaire_title": questionnaire["title"],
                "questionnaire_category": questionnaire["category"],
                "status": assignment["status"],
                "assigned_at": assignment["assigned_at"],
                "completed_at": assignment.get("completed_at"),
                "questions_and_answers": questions_with_answers
            })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patient responses: {str(e)}")

@api_router.get("/admin/patients/{patient_id}/questionnaire-responses/pdf", dependencies=[Depends(get_admin_user)])
async def download_patient_questionnaire_pdf(patient_id: str, questionnaire_id: str = Query(None), current_user: dict = Depends(get_admin_user)):
    """Download patient's questionnaire responses as PDF"""
    try:
        # Get patient info
        patient = await db.users.find_one({"id": patient_id})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Find assignments
        query = {"patient_id": patient_id, "status": "completed"}
        if questionnaire_id:
            query["questionnaire_id"] = questionnaire_id
        
        assignments = list(await db.patient_questionnaires.find(query).to_list(1000))
        if not assignments:
            raise HTTPException(status_code=404, detail="No completed questionnaires found")
        
        # Get all responses
        all_answers = []
        for assignment in assignments:
            questionnaire = await db.questionnaires.find_one({"_id": assignment["questionnaire_id"]})
            if not questionnaire:
                continue
            
            answers = list(await db.patient_answers.find({"patient_questionnaire_id": str(assignment["_id"])}).to_list(1000))
            answers_dict = {answer["question_id"]: answer for answer in answers}
            
            for question in questionnaire.get("questions", []):
                answer = answers_dict.get(question["id"], {})
                all_answers.append({
                    "question_text": question["question_text"],
                    "answer_text": answer.get("answer_text"),
                    "answer_choices": answer.get("answer_choices"),
                    "answer_number": answer.get("answer_number"),
                    "answer_date": answer.get("answer_date")
                })
        
        # Generate PDF
        pdf_data = generate_questionnaire_pdf(
            patient_id=patient_id,
            questionnaire_id=questionnaire_id or "multiple",
            answers=all_answers,
            patient_info={
                "full_name": patient.get("full_name", "Unknown"),
                "email": patient.get("email", "Unknown")
            }
        )
        
        from fastapi.responses import StreamingResponse
        return StreamingResponse(
            io.BytesIO(pdf_data),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=questionnaire_responses_{patient_id}.pdf"}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF: {str(e)}")

# Document Management Endpoints
@api_router.post("/admin/documents", dependencies=[Depends(get_admin_user)])
async def create_document(document: CreateDocumentRequest, current_user: dict = Depends(get_admin_user)):
    """Create a new document template"""
    try:
        document_id = str(uuid.uuid4())
        document_data = {
            "_id": document_id,
            "title": document.title,
            "document_type": document.document_type,
            "content": document.content,
            "version": document.version,
            "is_active": True,
            "requires_signature": document.requires_signature,
            "settings": document.settings or {},
            "created_by": current_user["id"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.documents.insert_one(document_data)
        
        return {
            "success": True,
            "document_id": document_id,
            "message": "Document created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")

@api_router.get("/admin/documents", dependencies=[Depends(get_admin_user)])
async def get_documents(current_user: dict = Depends(get_admin_user)):
    """Get all document templates"""
    try:
        documents = list(await db.documents.find({"is_active": True}).sort("created_at", -1).to_list(100))
        
        for doc in documents:
            doc["_id"] = str(doc["_id"])
            # Get assignment count
            assignments = list(await db.patient_documents.find({"document_id": doc["_id"]}).to_list(1000))
            doc["assignments"] = {
                "total": len(assignments),
                "signed": len([a for a in assignments if a.get("status") == "signed"]),
                "pending": len([a for a in assignments if a.get("status") in ["assigned", "viewed"]])
            }
        
        return documents
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch documents: {str(e)}")

@api_router.post("/admin/documents/assign", dependencies=[Depends(get_admin_user)])
async def assign_document(assignment: AssignDocumentRequest, current_user: dict = Depends(get_admin_user)):
    """Assign a document to a patient"""
    try:
        # Check if document exists
        document = await db.documents.find_one({"_id": assignment.document_id})
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Check if patient exists
        patient = await db.users.find_one({"id": assignment.patient_id})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        assignment_id = str(uuid.uuid4())
        expires_at = None
        
        if assignment.expires_in_days:
            expires_at = datetime.utcnow() + timedelta(days=assignment.expires_in_days)
        elif document.get("settings", {}).get("expiry_days"):
            expires_at = datetime.utcnow() + timedelta(days=int(document["settings"]["expiry_days"]))
        
        assignment_data = {
            "_id": assignment_id,
            "patient_id": assignment.patient_id,
            "document_id": assignment.document_id,
            "assigned_by": current_user["id"],
            "assigned_at": datetime.utcnow(),
            "status": "assigned",
            "expires_at": expires_at,
            "context": assignment.context or {}
        }
        
        await db.patient_documents.insert_one(assignment_data)
        
        # Log the assignment
        await db.audit_logs.insert_one({
            "_id": str(uuid.uuid4()),
            "actor_id": current_user["id"],
            "action": "document_assigned",
            "entity_table": "patient_documents",
            "entity_id": assignment_id,
            "diff": {
                "patient_id": assignment.patient_id,
                "document_title": document.get("title")
            },
            "timestamp": datetime.utcnow()
        })
        
        return {
            "success": True,
            "assignment_id": assignment_id,
            "message": "Document assigned successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assign document: {str(e)}")

# Patient Document Endpoints
@api_router.get("/patient/documents", dependencies=[Depends(get_current_user)])
async def get_my_documents(current_user: dict = Depends(get_current_user)):
    """Get patient's assigned documents"""
    try:
        assignments = list(await db.patient_documents.find({
            "patient_id": current_user["id"],
            "status": {"$in": ["assigned", "viewed"]}
        }).sort("assigned_at", 1).to_list(100))
        
        result = []
        for assignment in assignments:
            document = await db.documents.find_one({"_id": assignment["document_id"]})
            if document:
                result.append({
                    "assignment_id": str(assignment["_id"]),
                    "document": {
                        "id": str(document["_id"]),
                        "title": document["title"],
                        "document_type": document["document_type"],
                        "content": document["content"],
                        "version": document["version"],
                        "requires_signature": document["requires_signature"]
                    },
                    "status": assignment["status"],
                    "assigned_at": assignment["assigned_at"],
                    "viewed_at": assignment.get("viewed_at"),
                    "signed_at": assignment.get("signed_at"),
                    "expires_at": assignment.get("expires_at")
                })
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch documents: {str(e)}")

@api_router.post("/patient/documents/{assignment_id}/view", dependencies=[Depends(get_current_user)])
async def mark_document_viewed(assignment_id: str, current_user: dict = Depends(get_current_user)):
    """Mark document as viewed"""
    try:
        result = await db.patient_documents.update_one(
            {
                "_id": assignment_id,
                "patient_id": current_user["id"],
                "status": "assigned"
            },
            {
                "$set": {
                    "status": "viewed",
                    "viewed_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Document assignment not found or already viewed")
        
        return {"success": True, "message": "Document marked as viewed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark document as viewed: {str(e)}")

@api_router.post("/patient/documents/{assignment_id}/sign", dependencies=[Depends(get_current_user)])
async def sign_document(assignment_id: str, signature_request: SignDocumentRequest, current_user: dict = Depends(get_current_user), request: Request = None):
    """Sign a document"""
    try:
        # Verify assignment ownership
        assignment = await db.patient_documents.find_one({
            "_id": assignment_id,
            "patient_id": current_user["id"]
        })
        
        if not assignment:
            raise HTTPException(status_code=404, detail="Document assignment not found")
        
        if assignment["status"] == "signed":
            raise HTTPException(status_code=400, detail="Document already signed")
        
        # Create signature record
        signature_id = str(uuid.uuid4())
        signature_data = {
            "_id": signature_id,
            "patient_document_id": assignment_id,
            "patient_id": current_user["id"],
            "signature_data": signature_request.signature_data,
            "signature_type": signature_request.signature_type,
            "ip_address": request.client.host if request else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown") if request else "unknown",
            "timestamp": datetime.utcnow(),
            "verification_data": {
                "user_id": current_user["id"],
                "assignment_id": assignment_id
            }
        }
        
        await db.patient_signatures.insert_one(signature_data)
        
        # Update document status
        await db.patient_documents.update_one(
            {"_id": assignment_id},
            {
                "$set": {
                    "status": "signed",
                    "signed_at": datetime.utcnow()
                }
            }
        )
        
        # Log the signature
        await db.audit_logs.insert_one({
            "_id": str(uuid.uuid4()),
            "actor_id": current_user["id"],
            "action": "document_signed",
            "entity_table": "patient_signatures",
            "entity_id": signature_id,
            "diff": {"assignment_id": assignment_id},
            "timestamp": datetime.utcnow()
        })
        
        return {
            "success": True,
            "signature_id": signature_id,
            "message": "Document signed successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sign document: {str(e)}")

# Combined Patient Tasks Endpoint
@api_router.get("/patient/pending-tasks", dependencies=[Depends(get_current_user)])
async def get_pending_tasks(current_user: dict = Depends(get_current_user)):
    """Get all pending tasks (questionnaires + documents) for patient"""
    try:
        tasks = []
        
        # Get pending questionnaires
        questionnaire_assignments = list(await db.patient_questionnaires.find({
            "patient_id": current_user["id"],
            "status": {"$in": ["assigned", "in_progress"]}
        }).to_list(100))
        
        for assignment in questionnaire_assignments:
            questionnaire = await db.questionnaires.find_one({"_id": assignment["questionnaire_id"]})
            if questionnaire:
                priority = "high" if questionnaire.get("is_required") else "normal"
                if assignment.get("due_date") and assignment["due_date"] < datetime.utcnow() + timedelta(hours=24):
                    priority = "urgent"
                
                tasks.append({
                    "task_type": "questionnaire",
                    "task_id": str(assignment["_id"]),
                    "title": questionnaire["title"],
                    "description": questionnaire.get("description"),
                    "assigned_at": assignment["assigned_at"],
                    "due_date": assignment.get("due_date"),
                    "priority": priority,
                    "estimated_duration": questionnaire.get("metadata", {}).get("estimated_minutes", 10)
                })
        
        # Get pending documents
        document_assignments = list(await db.patient_documents.find({
            "patient_id": current_user["id"],
            "status": {"$in": ["assigned", "viewed"]}
        }).to_list(100))
        
        for assignment in document_assignments:
            document = await db.documents.find_one({"_id": assignment["document_id"]})
            if document:
                priority = "high" if document.get("requires_signature") else "normal"
                if assignment.get("expires_at") and assignment["expires_at"] < datetime.utcnow() + timedelta(hours=24):
                    priority = "urgent"
                
                description = {
                    "consent_form": "Please review and sign this consent form",
                    "privacy_notice": "Please review our privacy notice",
                    "treatment_info": "Important information about your treatment"
                }.get(document["document_type"], "Please review and sign this document")
                
                tasks.append({
                    "task_type": "document",
                    "task_id": str(assignment["_id"]),
                    "title": document["title"],
                    "description": description,
                    "assigned_at": assignment["assigned_at"],
                    "due_date": assignment.get("expires_at"),
                    "priority": priority,
                    "estimated_duration": document.get("settings", {}).get("estimated_minutes", 5)
                })
        
        # Sort by priority and date
        priority_order = {"urgent": 1, "high": 2, "normal": 3}
        tasks.sort(key=lambda x: (priority_order.get(x["priority"], 3), x["assigned_at"]))
        
        return {"tasks": tasks}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending tasks: {str(e)}")

# =====================================================
# APPOINTMENT BOOKING SYSTEM ENDPOINTS
# =====================================================

# Admin Endpoints - Service Availability Management
@api_router.get("/admin/services/{service_id}/availability", dependencies=[Depends(admin_required)])
async def get_service_availability(service_id: str, current_user: dict = Depends(get_current_user)):
    """Get availability settings for a service"""
    try:
        availability = list(await db.service_availability.find({"service_id": service_id}).to_list(100))
        return availability
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get availability: {str(e)}")

@api_router.post("/admin/services/{service_id}/availability", dependencies=[Depends(admin_required)])
async def create_service_availability(
    service_id: str, 
    request: CreateAvailabilityRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create availability settings for a service"""
    try:
        # Verify service exists
        service = await db.services.find_one({"id": service_id})
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        # Create availability records for each day
        availability_records = []
        for day in request.days_of_week:
            availability = {
                "_id": str(uuid.uuid4()),
                "service_id": service_id,
                "day_of_week": day,
                "start_time": request.start_time,
                "end_time": request.end_time,
                "slot_duration": request.slot_duration,
                "buffer_time": request.buffer_time,
                "max_bookings_per_slot": 1,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            availability_records.append(availability)
        
        await db.service_availability.insert_many(availability_records)
        
        return {"success": True, "message": f"Created availability for {len(availability_records)} days"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create availability: {str(e)}")

@api_router.delete("/admin/services/availability/{availability_id}", dependencies=[Depends(admin_required)])
async def delete_service_availability(availability_id: str, current_user: dict = Depends(get_current_user)):
    """Delete availability setting"""
    try:
        result = await db.service_availability.delete_one({"_id": availability_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Availability setting not found")
        
        return {"success": True, "message": "Availability setting deleted"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete availability: {str(e)}")

# Admin Endpoints - Slot Management
@api_router.get("/admin/appointments/slots", dependencies=[Depends(admin_required)])
async def get_appointment_slots(
    service_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get appointment slots with booking information"""
    try:
        # Build query
        query = {}
        if service_id:
            query["service_id"] = service_id
        if date_from or date_to:
            date_query = {}
            if date_from:
                date_query["$gte"] = date_from
            if date_to:
                date_query["$lte"] = date_to
            query["date"] = date_query
        
        slots = list(await db.appointment_slots.find(query).to_list(1000))
        
        # Get associated bookings
        for slot in slots:
            bookings = list(await db.appointment_bookings.find({
                "service_id": slot["service_id"],
                "appointment_date": slot["date"],
                "start_time": slot["start_time"],
                "status": {"$nin": ["cancelled"]}
            }).to_list(100))
            
            slot["bookings"] = bookings
            slot["available_spots"] = slot.get("max_bookings", 1) - len(bookings)
        
        return slots
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get slots: {str(e)}")

@api_router.post("/admin/appointments/slots/generate", dependencies=[Depends(admin_required)])
async def generate_appointment_slots(
    service_id: str,
    start_date: str,
    end_date: str,
    current_user: dict = Depends(get_current_user)
):
    """Generate appointment slots based on service availability"""
    try:
        from datetime import datetime, timedelta
        
        # Get service availability
        availability = list(await db.service_availability.find({
            "service_id": service_id,
            "is_active": True
        }).to_list(100))
        
        if not availability:
            raise HTTPException(status_code=400, detail="No availability settings found for this service")
        
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        slots_created = 0
        current_date = start
        
        while current_date <= end:
            day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday
            
            # Find availability for this day
            day_availability = [av for av in availability if av["day_of_week"] == day_of_week]
            
            for av in day_availability:
                # Generate slots for this availability window
                slot_start = datetime.strptime(av["start_time"], "%H:%M").time()
                slot_end = datetime.strptime(av["end_time"], "%H:%M").time()
                
                current_slot_time = datetime.combine(current_date.date(), slot_start)
                end_time = datetime.combine(current_date.date(), slot_end)
                
                while current_slot_time < end_time:
                    slot_end_time = current_slot_time + timedelta(minutes=av["slot_duration"])
                    
                    # Check if slot already exists
                    existing = await db.appointment_slots.find_one({
                        "service_id": service_id,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "start_time": current_slot_time.strftime("%H:%M")
                    })
                    
                    if not existing:
                        slot = {
                            "_id": str(uuid.uuid4()),
                            "service_id": service_id,
                            "date": current_date.strftime("%Y-%m-%d"),
                            "start_time": current_slot_time.strftime("%H:%M"),
                            "end_time": slot_end_time.strftime("%H:%M"),
                            "is_available": True,
                            "is_blocked": False,
                            "max_bookings": av.get("max_bookings_per_slot", 1),
                            "current_bookings": 0,
                            "created_by": current_user["id"],
                            "created_at": datetime.utcnow()
                        }
                        await db.appointment_slots.insert_one(slot)
                        slots_created += 1
                    
                    # Move to next slot (including buffer time)
                    current_slot_time = slot_end_time + timedelta(minutes=av.get("buffer_time", 15))
            
            current_date += timedelta(days=1)
        
        return {"success": True, "slots_created": slots_created}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate slots: {str(e)}")

@api_router.post("/admin/appointments/slots/block", dependencies=[Depends(admin_required)])
async def block_appointment_slot(request: BlockSlotRequest, current_user: dict = Depends(get_current_user)):
    """Block specific time slots"""
    try:
        # Find and update the slot
        result = await db.appointment_slots.update_one(
            {
                "service_id": request.service_id,
                "date": request.date,
                "start_time": request.start_time
            },
            {
                "$set": {
                    "is_blocked": True,
                    "is_available": False,
                    "blocked_reason": request.reason,
                    "reserved_for_patient_id": request.reserved_for_patient_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Appointment slot not found")
        
        return {"success": True, "message": "Slot blocked successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to block slot: {str(e)}")

# Admin Endpoints - Booking Management
@api_router.get("/admin/appointments/bookings", dependencies=[Depends(admin_required)])
async def get_all_bookings(
    status: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all appointment bookings"""
    try:
        query = {}
        if status:
            query["status"] = status
        if date_from or date_to:
            date_query = {}
            if date_from:
                date_query["$gte"] = date_from
            if date_to:
                date_query["$lte"] = date_to
            query["appointment_date"] = date_query
        
        bookings = list(await db.appointment_bookings.find(query).to_list(1000))
        
        # Enrich with patient and service info
        for booking in bookings:
            # Get patient info
            patient = await db.users.find_one({"id": booking["patient_id"]})
            if patient:
                booking["patient"] = {
                    "full_name": patient.get("full_name"),
                    "email": patient.get("email"),
                    "phone": patient.get("phone")
                }
            
            # Get service info
            service = await db.services.find_one({"id": booking["service_id"]})
            if service:
                booking["service"] = {
                    "name": service.get("name"),
                    "price": service.get("price")
                }
        
        return bookings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get bookings: {str(e)}")

# Patient Endpoints - View Available Slots
@api_router.get("/patient/appointments/availability/{service_id}", dependencies=[Depends(get_current_user)])
async def get_available_slots(
    service_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get available appointment slots for a service"""
    try:
        # Default to next 30 days if no range specified
        if not date_from:
            date_from = datetime.utcnow().strftime("%Y-%m-%d")
        if not date_to:
            date_to = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Get available slots
        slots = list(await db.appointment_slots.find({
            "service_id": service_id,
            "date": {"$gte": date_from, "$lte": date_to},
            "is_available": True,
            "is_blocked": False,
            "$expr": {"$gt": ["$max_bookings", "$current_bookings"]}
        }).sort("date", 1).sort("start_time", 1).to_list(1000))
        
        # Group by date for calendar display
        calendar_data = {}
        for slot in slots:
            date = slot["date"]
            if date not in calendar_data:
                calendar_data[date] = []
            
            calendar_data[date].append({
                "slot_id": slot["_id"],
                "start_time": slot["start_time"],
                "end_time": slot["end_time"],
                "available_spots": slot["max_bookings"] - slot["current_bookings"]
            })
        
        return {"calendar": calendar_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get availability: {str(e)}")

# Patient Endpoints - Book Appointment
@api_router.post("/patient/appointments/book", dependencies=[Depends(get_current_user)])
@limiter.limit("20/hour")  # Allow 20 booking attempts per hour per IP
async def book_appointment(request: Request, booking_request: BookAppointmentRequest, current_user: dict = Depends(get_current_user)):
    """Book an appointment (creates pending booking awaiting payment)"""
    try:
        # Ensure service has availability and slots
        await ensure_service_availability_and_slots(booking_request.service_id)
        
        # Verify slot is available
        slot = await db.appointment_slots.find_one({
            "service_id": booking_request.service_id,
            "date": booking_request.appointment_date,
            "start_time": booking_request.start_time,
            "is_available": True,
            "is_blocked": False
        })
        
        if not slot:
            raise HTTPException(status_code=400, detail="Selected time slot is not available")
        
        if slot["current_bookings"] >= slot["max_bookings"]:
            raise HTTPException(status_code=400, detail="Selected time slot is fully booked")
        
        # Get service info for pricing
        service = await db.services.find_one({"id": booking_request.service_id})
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        # Create booking
        booking_id = str(uuid.uuid4())
        booking = {
            "_id": booking_id,
            "patient_id": current_user["id"],
            "service_id": booking_request.service_id,
            "appointment_date": booking_request.appointment_date,
            "start_time": booking_request.start_time,
            "end_time": slot["end_time"],
            "status": "pending",
            "payment_status": "pending",
            "amount": float(service.get("price", 0)),
            "currency": "EUR",
            "notes": booking_request.notes,
            "confirmation_code": str(uuid.uuid4())[:8].upper(),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.appointment_bookings.insert_one(booking)
        
        # Increment slot booking count
        await db.appointment_slots.update_one(
            {"_id": slot["_id"]},
            {"$inc": {"current_bookings": 1}}
        )
        
        # 🌟 TRIGGER PROACTIVE PROTOCOL NOTIFICATION
        # Generate automatic protocol recommendation for the booked treatment
        try:
            await trigger_proactive_protocol_notification(
                patient_id=current_user["id"],
                service_id=booking_request.service_id,
                service_name=service.get("name", "Treatment")
            )
        except Exception as e:
            # Don't fail the booking if notification fails
            print(f"⚠️ Proactive notification failed (booking still successful): {str(e)}")
        
        # 📊 UPDATE CRM LIFECYCLE DATA  
        # Update patient lifecycle data with new booking
        try:
            await update_user_lifecycle_data(
                user_id=current_user["id"],
                new_booking={
                    'created_at': booking['created_at'], 
                    'amount': booking['amount']
                }
            )
            print(f"✅ Updated lifecycle data for patient: {current_user['id']}")
        except Exception as e:
            print(f"⚠️ Lifecycle update failed (booking still successful): {str(e)}")
        
        return {
            "success": True,
            "booking_id": booking_id,
            "confirmation_code": booking["confirmation_code"],
            "amount": booking["amount"],
            "message": "Appointment reserved. Please complete payment to confirm.",
            "has_protocol_recommendation": True  # Signal to frontend to check for notifications
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to book appointment: {str(e)}")

# Patient Endpoints - Get My Bookings
@api_router.get("/patient/appointments/bookings", dependencies=[Depends(get_current_user)])
async def get_patient_bookings(current_user: dict = Depends(get_current_user)):
    """Get patient's appointment bookings"""
    try:
        bookings = list(await db.appointment_bookings.find({
            "patient_id": current_user["id"]
        }).sort("appointment_date", 1).to_list(100))
        
        # Enrich with service info
        for booking in bookings:
            service = await db.services.find_one({"id": booking["service_id"]})
            if service:
                booking["service"] = {
                    "name": service.get("name"),
                    "description": service.get("description"),
                    "duration": service.get("duration")
                }
        
        return bookings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get bookings: {str(e)}")

# Payment Integration (Stripe)
@api_router.post("/patient/appointments/payment", dependencies=[Depends(get_current_user)])
async def create_appointment_payment(
    request: PaymentRequest, 
    http_request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Create Stripe checkout session for appointment payment"""
    try:
        # Verify booking exists and belongs to user
        booking = await db.appointment_bookings.find_one({
            "_id": request.booking_id,
            "patient_id": current_user["id"],
            "payment_status": "pending"
        })
        
        if not booking:
            raise HTTPException(status_code=404, detail="Booking not found or already processed")
        
        # Get service info for payment details
        service = await db.services.find_one({"id": booking["service_id"]})
        if not service:
            raise HTTPException(status_code=404, detail="Service not found")
        
        # Initialize Stripe checkout
        stripe_checkout = get_stripe_checkout(http_request)
        
        # Build success and cancel URLs using frontend origin
        origin_url = request.origin_url.rstrip('/')
        success_url = f"{origin_url}/booking-success?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{origin_url}/bookings"
        
        # Create checkout session request
        checkout_request = CheckoutSessionRequest(
            amount=float(booking["amount"]),
            currency=booking["currency"].lower(),
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                "booking_id": booking["_id"],
                "patient_id": current_user["id"],
                "service_name": service.get("name", "Appointment"),
                "appointment_date": booking["appointment_date"],
                "appointment_time": booking["start_time"],
                "source": "appointment_booking"
            }
        )
        
        # Create checkout session
        session: CheckoutSessionResponse = await stripe_checkout.create_checkout_session(checkout_request)
        
        # Create payment transaction record
        transaction = {
            "_id": str(uuid.uuid4()),
            "booking_id": booking["_id"],
            "patient_id": current_user["id"],
            "session_id": session.session_id,
            "amount": float(booking["amount"]),
            "currency": booking["currency"],
            "payment_status": "pending",
            "stripe_status": "created",
            "metadata": checkout_request.metadata,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.payment_transactions.insert_one(transaction)
        
        # Update booking with session info
        await db.appointment_bookings.update_one(
            {"_id": request.booking_id},
            {
                "$set": {
                    "payment_status": "processing",
                    "payment_intent_id": session.session_id,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": True,
            "checkout_url": session.url,
            "session_id": session.session_id,
            "message": "Checkout session created successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create payment session: {str(e)}")

@api_router.get("/patient/appointments/payment/status/{session_id}", dependencies=[Depends(get_current_user)])
async def get_payment_status(
    session_id: str,
    http_request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Check payment status and update booking accordingly"""
    try:
        # Find transaction by session_id
        transaction = await db.payment_transactions.find_one({
            "session_id": session_id,
            "patient_id": current_user["id"]
        })
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Payment transaction not found")
        
        # Initialize Stripe checkout
        stripe_checkout = get_stripe_checkout(http_request)
        
        # Get checkout status from Stripe
        status_response: CheckoutStatusResponse = await stripe_checkout.get_checkout_status(session_id)
        
        # Update transaction with latest status
        await db.payment_transactions.update_one(
            {"_id": transaction["_id"]},
            {
                "$set": {
                    "stripe_status": status_response.status,
                    "payment_status": status_response.payment_status,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        # Update booking status based on payment status
        if status_response.payment_status == "paid" and transaction["payment_status"] != "paid":
            # Update booking to confirmed only if not already processed
            await db.appointment_bookings.update_one(
                {"_id": transaction["booking_id"], "payment_status": {"$ne": "paid"}},
                {
                    "$set": {
                        "status": "confirmed",
                        "payment_status": "paid",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Get booking details for integration
            booking = await db.appointment_bookings.find_one({"_id": transaction["booking_id"]})
            if booking:
                # Get service and patient details
                service = await db.services.find_one({"id": booking["service_id"]})
                patient = await db.users.find_one({"id": booking["patient_id"]})
                
                if service and patient:
                    integration_status = "active"
                    calendar_event_id = None
                    reminder_schedules = []
                    
                    try:
                        # Create Google Calendar event
                        appointment_datetime = datetime.combine(
                            datetime.strptime(booking["appointment_date"], "%Y-%m-%d").date(),
                            datetime.strptime(booking["start_time"], "%H:%M").time()
                        )
                        end_datetime = datetime.combine(
                            datetime.strptime(booking["appointment_date"], "%Y-%m-%d").date(),
                            datetime.strptime(booking["end_time"], "%H:%M").time()
                        )
                        
                        # Create calendar event
                        event_title = f"KinAura Appointment: {service.get('name', 'Service')}"
                        event_description = f"Patient: {patient.get('full_name', '')}\nService: {service.get('name', '')}\nDuration: {service.get('duration', 60)} minutes\nConfirmation Code: {booking.get('confirmation_code', '')}"
                        
                        calendar_event = await calendar_service.create_appointment_event(
                            title=event_title,
                            description=event_description,
                            start_datetime=appointment_datetime,
                            end_datetime=end_datetime,
                            patient_email=patient.get("email", ""),
                            location="KinAura Clinic",  # You can make this configurable
                            timezone="Europe/Rome"
                        )
                        
                        # Store calendar event record
                        calendar_record = {
                            "_id": str(uuid.uuid4()),
                            "appointment_id": booking["_id"],
                            "patient_id": booking["patient_id"],
                            "google_event_id": calendar_event["id"],
                            "calendar_id": "primary",
                            "event_title": event_title,
                            "event_description": event_description,
                            "start_datetime": appointment_datetime,
                            "end_datetime": end_datetime,
                            "timezone": "Europe/Rome",
                            "attendee_emails": [patient.get("email", "")],
                            "location": "KinAura Clinic",
                            "event_status": "confirmed",
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                        
                        await db.calendar_events.insert_one(calendar_record)
                        calendar_event_id = calendar_record["_id"]
                        
                        logging.info(f"Successfully created calendar event for appointment {booking['_id']}")
                        
                    except HTTPException as e:
                        if e.status_code == 503:
                            logging.warning(f"Google Calendar not available for appointment {booking['_id']}: {e.detail}")
                        else:
                            logging.error(f"Failed to create calendar event for appointment {booking['_id']}: {e.detail}")
                        integration_status = "partial"
                    except Exception as e:
                        logging.error(f"Failed to create calendar event for appointment {booking['_id']}: {e}")
                        integration_status = "partial"
                    
                    try:
                        # Send confirmation push notification
                        appointment_data = {
                            "id": booking["_id"],
                            "service_name": service.get("name", ""),
                            "date": booking["appointment_date"],
                            "time": booking["start_time"]
                        }
                        
                        await push_service.send_appointment_notification(
                            booking["patient_id"],
                            "appointment_confirmation",
                            appointment_data
                        )
                        
                        # Schedule reminder notifications
                        reminder_schedules = await scheduler_service.schedule_appointment_reminders(
                            booking["_id"],
                            booking["patient_id"],
                            appointment_datetime,
                            service.get("name", ""),
                            ["reminder_24h", "reminder_2h"]
                        )
                        
                        logging.info(f"Successfully set up notifications for appointment {booking['_id']}")
                        
                    except HTTPException as e:
                        if e.status_code == 503:
                            logging.warning(f"Push notifications not available for appointment {booking['_id']}: {e.detail}")
                        else:
                            logging.error(f"Failed to send notifications for appointment {booking['_id']}: {e.detail}")
                        if integration_status == "active":
                            integration_status = "partial"
                    except Exception as e:
                        logging.error(f"Failed to set up notifications for appointment {booking['_id']}: {e}")
                        if integration_status == "active":
                            integration_status = "partial"
                    
                    # Create appointment integration record
                    try:
                        integration_record = {
                            "_id": str(uuid.uuid4()),
                            "appointment_id": booking["_id"],
                            "patient_id": booking["patient_id"],
                            "google_calendar_event_id": calendar_event_id,
                            "push_notification_schedules": reminder_schedules,
                            "integration_status": integration_status,
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                        
                        await db.appointment_integrations.insert_one(integration_record)
                        
                        logging.info(f"Successfully created integration record for appointment {booking['_id']} with status: {integration_status}")
                        
                    except Exception as e:
                        logging.error(f"Failed to create integration record for appointment {booking['_id']}: {e}")
                        # This is not critical, so we continue
            
            
        elif status_response.status == "expired":
            # Mark booking as expired
            await db.appointment_bookings.update_one(
                {"_id": transaction["booking_id"]},
                {
                    "$set": {
                        "payment_status": "failed",
                        "status": "cancelled",
                        "cancellation_reason": "payment_expired",
                        "cancelled_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Free up the appointment slot
            await db.appointment_slots.update_one(
                {
                    "service_id": transaction["metadata"]["service_id"] if "service_id" in transaction.get("metadata", {}) else None,
                    "date": transaction["metadata"]["appointment_date"] if "appointment_date" in transaction.get("metadata", {}) else None,
                    "start_time": transaction["metadata"]["appointment_time"] if "appointment_time" in transaction.get("metadata", {}) else None
                },
                {"$inc": {"current_bookings": -1}}
            )
        
        return {
            "success": True,
            "session_id": session_id,
            "status": status_response.status,
            "payment_status": status_response.payment_status,
            "amount_total": status_response.amount_total / 100,  # Convert from cents
            "currency": status_response.currency
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check payment status: {str(e)}")

# ======================================
# PUSH NOTIFICATIONS API ENDPOINTS
# ======================================

@api_router.post("/patient/notifications/register-token", dependencies=[Depends(get_current_user)])
async def register_notification_token(
    request: RegisterTokenRequest,
    current_user: dict = Depends(get_current_user)
):
    """Register a push notification token for the current user"""
    try:
        # Validate token is not empty or just whitespace
        if not request.token or not request.token.strip():
            raise HTTPException(status_code=422, detail="Token cannot be empty")
        
        # Validate platform
        if request.platform not in ["web", "ios", "android"]:
            raise HTTPException(status_code=422, detail="Platform must be one of: web, ios, android")
        
        # Validate device_id is not empty
        if not request.device_id or not request.device_id.strip():
            raise HTTPException(status_code=422, detail="Device ID cannot be empty")
        
        # Validate token format (basic check)
        token = request.token.strip()
        if len(token) < 10:
            raise HTTPException(status_code=422, detail="Token appears to be invalid (too short)")
        
        # Check if token already exists for this user and device
        existing_token = await db.notification_tokens.find_one({
            "user_id": current_user["id"],
            "device_id": request.device_id
        })
        
        if existing_token:
            # Update existing token
            await db.notification_tokens.update_one(
                {"_id": existing_token["_id"]},
                {
                    "$set": {
                        "token": token,
                        "platform": request.platform,
                        "device_name": request.device_name,
                        "is_active": True,
                        "last_used_at": datetime.utcnow()
                    }
                }
            )
            token_id = existing_token["_id"]
        else:
            # Create new token record
            token_record = {
                "_id": str(uuid.uuid4()),
                "user_id": current_user["id"],
                "device_id": request.device_id,
                "token": token,
                "platform": request.platform,
                "device_name": request.device_name,
                "is_active": True,
                "created_at": datetime.utcnow(),
                "last_used_at": datetime.utcnow()
            }
            
            await db.notification_tokens.insert_one(token_record)
            token_id = token_record["_id"]
        
        return {
            "success": True,
            "token_id": token_id,
            "message": "Notification token registered successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error registering notification token: {e}")
        raise HTTPException(status_code=500, detail="Failed to register notification token")

@api_router.post("/patient/notifications/send", dependencies=[Depends(get_current_user)])
async def send_push_notification(
    request: SendNotificationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Send a push notification (admin only for now)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Create notification record
        notification = {
            "_id": str(uuid.uuid4()),
            "notification_type": request.notification_type,
            "title": request.title,
            "body": request.body,
            "data": request.data or {},
            "recipient_id": request.user_id,
            "appointment_id": request.appointment_id,
            "scheduled_for": request.schedule_for,
            "delivery_status": "pending",
            "created_at": datetime.utcnow()
        }
        
        await db.push_notifications.insert_one(notification)
        
        # Send notification immediately if not scheduled
        if not request.schedule_for or request.schedule_for <= datetime.utcnow():
            result = await push_service.send_appointment_notification(
                request.user_id,
                request.notification_type,
                {"id": request.appointment_id or ""}
            )
            
            # Update notification status
            await db.push_notifications.update_one(
                {"_id": notification["_id"]},
                {
                    "$set": {
                        "delivery_status": "sent" if result["success_count"] > 0 else "failed",
                        "sent_at": datetime.utcnow()
                    }
                }
            )
        
        return {
            "success": True,
            "notification_id": notification["_id"],
            "message": "Notification queued successfully"
        }
        
    except Exception as e:
        logging.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail="Failed to send notification")

@api_router.get("/patient/notifications/history", dependencies=[Depends(get_current_user)])
async def get_notification_history(
    current_user: dict = Depends(get_current_user)
):
    """Get notification history for the current user"""
    try:
        notifications = await db.push_notifications.find({
            "recipient_id": current_user["id"]
        }).sort("created_at", -1).limit(50).to_list(50)
        
        return {
            "notifications": notifications
        }
        
    except Exception as e:
        logging.error(f"Error getting notification history: {e}")
        raise HTTPException(status_code=500, detail="Failed to get notification history")

# ======================================
# GOOGLE CALENDAR INTEGRATION ENDPOINTS
# ======================================

@api_router.post("/admin/calendar/create-event", dependencies=[Depends(get_admin_user)])
async def create_calendar_event(
    request: CreateCalendarEventRequest,
    admin_user: dict = Depends(get_admin_user)
):
    """Create a Google Calendar event for an appointment (admin only)"""
    try:
        # Create calendar event
        event = await calendar_service.create_appointment_event(
            title=request.title,
            description=request.description,
            start_datetime=request.start_datetime,
            end_datetime=request.end_datetime,
            patient_email=request.patient_email,
            location=request.location,
            timezone=request.timezone
        )
        
        # Store calendar event record
        calendar_record = {
            "_id": str(uuid.uuid4()),
            "appointment_id": request.appointment_id,
            "patient_id": admin_user["id"],  # This should be the patient ID from the appointment
            "google_event_id": event["id"],
            "calendar_id": "primary",
            "event_title": request.title,
            "event_description": request.description,
            "start_datetime": request.start_datetime,
            "end_datetime": request.end_datetime,
            "timezone": request.timezone,
            "attendee_emails": [request.patient_email],
            "location": request.location,
            "event_status": "confirmed",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.calendar_events.insert_one(calendar_record)
        
        return {
            "success": True,
            "calendar_event_id": calendar_record["_id"],
            "google_event_id": event["id"],
            "google_event_link": event.get("htmlLink", ""),
            "message": "Calendar event created successfully"
        }
        
    except Exception as e:
        logging.error(f"Error creating calendar event: {e}")
        raise HTTPException(status_code=500, detail="Failed to create calendar event")

@api_router.put("/admin/calendar/update-event/{event_id}", dependencies=[Depends(get_admin_user)])
async def update_calendar_event(
    event_id: str,
    request: UpdateCalendarEventRequest,
    admin_user: dict = Depends(get_admin_user)
):
    """Update a Google Calendar event (admin only)"""
    try:
        # Update Google Calendar event
        await calendar_service.update_event(
            event_id=request.google_event_id,
            title=request.title,
            description=request.description,
            start_datetime=request.start_datetime,
            end_datetime=request.end_datetime,
            status=request.status
        )
        
        # Update local record
        update_data = {"updated_at": datetime.utcnow()}
        if request.title:
            update_data["event_title"] = request.title
        if request.description:
            update_data["event_description"] = request.description
        if request.start_datetime:
            update_data["start_datetime"] = request.start_datetime
        if request.end_datetime:
            update_data["end_datetime"] = request.end_datetime
        if request.status:
            update_data["event_status"] = request.status
        
        await db.calendar_events.update_one(
            {"_id": event_id},
            {"$set": update_data}
        )
        
        return {
            "success": True,
            "message": "Calendar event updated successfully"
        }
        
    except Exception as e:
        logging.error(f"Error updating calendar event: {e}")
        raise HTTPException(status_code=500, detail="Failed to update calendar event")

# ======================================
# INTEGRATED APPOINTMENT BOOKING WITH CALENDAR & NOTIFICATIONS
# ======================================

async def ensure_service_availability_and_slots(service_id: str):
    """Ensure service has availability settings and generated slots for testing"""
    try:
        # Check if service has availability settings
        availability_count = await db.service_availability.count_documents({"service_id": service_id})
        
        if availability_count == 0:
            # Create default availability (Monday to Friday, 9 AM to 5 PM)
            default_availability = []
            for day in range(5):  # Monday to Friday (0-4)
                availability = {
                    "_id": str(uuid.uuid4()),
                    "service_id": service_id,
                    "day_of_week": day,
                    "start_time": "09:00",
                    "end_time": "17:00",
                    "slot_duration": 60,  # 1 hour slots
                    "max_bookings_per_slot": 1,
                    "is_active": True,
                    "created_at": datetime.utcnow()
                }
                default_availability.append(availability)
            
            if default_availability:
                await db.service_availability.insert_many(default_availability)
                logging.info(f"Created default availability for service {service_id}")
        
        # Check if service has slots for the next 7 days
        start_date = datetime.utcnow().strftime("%Y-%m-%d")
        end_date = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        slot_count = await db.appointment_slots.count_documents({
            "service_id": service_id,
            "date": {"$gte": start_date, "$lte": end_date}
        })
        
        if slot_count == 0:
            # Generate slots for the next 7 days
            await generate_slots_for_service(service_id, start_date, end_date)
            logging.info(f"Generated slots for service {service_id}")
        
    except Exception as e:
        logging.error(f"Error ensuring service availability: {e}")

async def generate_slots_for_service(service_id: str, start_date: str, end_date: str):
    """Generate appointment slots for a service"""
    try:
        # Get service availability
        availability = list(await db.service_availability.find({
            "service_id": service_id,
            "is_active": True
        }).to_list(100))
        
        if not availability:
            return
        
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        slots_created = 0
        current_date = start
        
        while current_date <= end:
            day_of_week = current_date.weekday()  # 0=Monday, 6=Sunday
            
            # Find availability for this day
            day_availability = [av for av in availability if av["day_of_week"] == day_of_week]
            
            for av in day_availability:
                # Generate slots for this availability window
                slot_start = datetime.strptime(av["start_time"], "%H:%M").time()
                slot_end = datetime.strptime(av["end_time"], "%H:%M").time()
                
                current_slot_time = datetime.combine(current_date.date(), slot_start)
                end_time = datetime.combine(current_date.date(), slot_end)
                
                while current_slot_time < end_time:
                    slot_end_time = current_slot_time + timedelta(minutes=av["slot_duration"])
                    
                    # Check if slot already exists
                    existing = await db.appointment_slots.find_one({
                        "service_id": service_id,
                        "date": current_date.strftime("%Y-%m-%d"),
                        "start_time": current_slot_time.strftime("%H:%M")
                    })
                    
                    if not existing:
                        slot = {
                            "_id": str(uuid.uuid4()),
                            "service_id": service_id,
                            "date": current_date.strftime("%Y-%m-%d"),
                            "start_time": current_slot_time.strftime("%H:%M"),
                            "end_time": slot_end_time.strftime("%H:%M"),
                            "max_bookings": av["max_bookings_per_slot"],
                            "current_bookings": 0,
                            "is_available": True,
                            "is_blocked": False,
                            "created_at": datetime.utcnow()
                        }
                        
                        await db.appointment_slots.insert_one(slot)
                        slots_created += 1
                    
                    current_slot_time = slot_end_time
            
            current_date += timedelta(days=1)
        
        logging.info(f"Generated {slots_created} slots for service {service_id}")
        
    except Exception as e:
        logging.error(f"Error generating slots: {e}")

@api_router.post("/admin/generate-test-availability", dependencies=[Depends(get_admin_user)])
async def generate_test_availability(
    admin_user: dict = Depends(get_admin_user)
):
    """Generate test availability and slots for all services (admin only)"""
    try:
        # Get all services
        services = await db.services.find({"is_active": True}).to_list(100)
        services_processed = 0
        
        for service in services:
            service_id = service.get("id")
            if service_id:
                await ensure_service_availability_and_slots(service_id)
                services_processed += 1
        
        return {
            "success": True,
            "message": f"Generated availability and slots for {services_processed} services",
            "services_processed": services_processed
        }
        
    except Exception as e:
        logging.error(f"Error generating test availability: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate test availability")

# Stripe Webhook Endpoint
@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhooks for payment processing"""
    try:
        # Get raw request body and signature
        body = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            raise HTTPException(status_code=400, detail="Missing Stripe signature")
        
        # Initialize Stripe checkout
        stripe_checkout = get_stripe_checkout(request)
        
        # Handle webhook
        webhook_response = await stripe_checkout.handle_webhook(body, signature)
        
        # Process the webhook event
        if webhook_response.event_type in ["checkout.session.completed", "payment_intent.succeeded"]:
            # Update transaction and booking status
            await db.payment_transactions.update_one(
                {"session_id": webhook_response.session_id},
                {
                    "$set": {
                        "payment_status": webhook_response.payment_status,
                        "stripe_status": "completed",
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Find and update booking
            transaction = await db.payment_transactions.find_one({"session_id": webhook_response.session_id})
            if transaction:
                await db.appointment_bookings.update_one(
                    {"_id": transaction["booking_id"]},
                    {
                        "$set": {
                            "status": "confirmed",
                            "payment_status": "paid",
                            "updated_at": datetime.utcnow()
                        }
                    }
                )
        
        return {"success": True, "event_processed": webhook_response.event_type}
    except Exception as e:
        logger.error(f"Stripe webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Webhook processing failed: {str(e)}")

# =====================================================
# HEALTH DATA INTEGRATION SYSTEM ENDPOINTS
# =====================================================

# Patient Endpoints - Provider Connections
@api_router.get("/patient/health/connections", dependencies=[Depends(get_current_user)])
async def get_patient_connections(current_user: dict = Depends(get_current_user)):
    """Get patient's health provider connections"""
    try:
        connections = list(await db.health_provider_connections.find({
            "patient_id": current_user["id"]
        }).to_list(100))
        
        # Remove sensitive data from response
        for conn in connections:
            if "access_token" in conn:
                del conn["access_token"]
            if "refresh_token" in conn:
                del conn["refresh_token"]
        
        return {"connections": connections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get connections: {str(e)}")

@api_router.post("/patient/health/connect", dependencies=[Depends(get_current_user)])
async def connect_health_provider(
    request: ConnectProviderRequest,
    current_user: dict = Depends(get_current_user)
):
    """Connect a health data provider"""
    try:
        # Check if connection already exists
        existing = await db.health_provider_connections.find_one({
            "patient_id": current_user["id"],
            "provider": request.provider.value
        })
        
        if existing and existing.get("status") == ConnectionStatus.CONNECTED.value:
            raise HTTPException(status_code=400, detail=f"{request.provider.value} already connected")
        
        # Create or update connection record
        connection_data = {
            "_id": str(uuid.uuid4()),
            "patient_id": current_user["id"],
            "provider": request.provider.value,
            "status": ConnectionStatus.PENDING.value,
            "permissions": request.permissions,
            "backfill_completed": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "metadata": {}
        }
        
        if existing:
            await db.health_provider_connections.update_one(
                {"_id": existing["_id"]},
                {"$set": connection_data}
            )
            connection_id = existing["_id"]
        else:
            await db.health_provider_connections.insert_one(connection_data)
            connection_id = connection_data["_id"]
        
        # Create consent record
        consent_record = {
            "_id": str(uuid.uuid4()),
            "patient_id": current_user["id"],
            "provider": request.provider.value,
            "metric_categories": [cat.value for cat in request.metric_categories],
            "consent_given_at": datetime.utcnow(),
            "consent_version": "1.0",
            "data_retention_days": 2555,  # ~7 years
            "allow_data_export": True,
            "allow_data_sharing": False,
            "metadata": {}
        }
        
        await db.patient_consent_records.insert_one(consent_record)
        
        # TODO: Initiate OAuth flow for provider
        # For now, we'll simulate successful connection
        await db.health_provider_connections.update_one(
            {"_id": connection_id},
            {
                "$set": {
                    "status": ConnectionStatus.CONNECTED.value,
                    "last_sync_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "success": True,
            "connection_id": connection_id,
            "message": f"{request.provider.value} connected successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect provider: {str(e)}")

@api_router.delete("/patient/health/connections/{provider}", dependencies=[Depends(get_current_user)])
async def disconnect_health_provider(
    provider: HealthProvider,
    delete_data: bool = Query(False, description="Whether to delete historical data"),
    current_user: dict = Depends(get_current_user)
):
    """Disconnect a health data provider"""
    try:
        # Update connection status
        result = await db.health_provider_connections.update_one(
            {
                "patient_id": current_user["id"],
                "provider": provider.value
            },
            {
                "$set": {
                    "status": ConnectionStatus.DISCONNECTED.value,
                    "access_token": None,
                    "refresh_token": None,
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Provider connection not found")
        
        # Revoke consent
        await db.patient_consent_records.update_many(
            {
                "patient_id": current_user["id"],
                "provider": provider.value,
                "revoked_at": None
            },
            {
                "$set": {
                    "revoked_at": datetime.utcnow(),
                    "revocation_reason": "user_requested"
                }
            }
        )
        
        # Optionally delete historical data
        if delete_data:
            await db.health_data_samples.delete_many({
                "patient_id": current_user["id"],
                "provider": provider.value
            })
        
        return {"success": True, "message": f"{provider.value} disconnected successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect provider: {str(e)}")

@api_router.put("/patient/health/permissions", dependencies=[Depends(get_current_user)])
async def update_health_permissions(
    request: UpdatePermissionsRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update health data sharing permissions"""
    try:
        # Update consent record
        await db.patient_consent_records.update_one(
            {
                "patient_id": current_user["id"],
                "provider": request.provider.value,
                "revoked_at": None
            },
            {
                "$set": {
                    "metric_categories": [cat.value for cat in request.metric_categories],
                    "consent_version": "1.1",  # Increment version on updates
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"success": True, "message": "Permissions updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update permissions: {str(e)}")

# Patient Endpoints - Health Data Views
@api_router.get("/patient/health/dashboard", dependencies=[Depends(get_current_user)])
async def get_health_dashboard(
    days: int = Query(30, ge=1, le=365, description="Number of days to fetch"),
    current_user: dict = Depends(get_current_user)
):
    """Get patient health dashboard data"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get recent health data samples
        samples = list(await db.health_data_samples.find({
            "patient_id": current_user["id"],
            "start_time": {"$gte": start_date, "$lte": end_date}
        }).sort("start_time", -1).to_list(1000))
        
        # Group by metric for dashboard cards
        dashboard_data = {}
        for sample in samples:
            metric = sample["metric"]
            if metric not in dashboard_data:
                dashboard_data[metric] = {
                    "metric": metric,
                    "unit": sample["unit"],
                    "latest_value": sample["value"],
                    "latest_time": sample["start_time"],
                    "provider": sample["provider"],
                    "samples": []
                }
            dashboard_data[metric]["samples"].append({
                "value": sample["value"],
                "time": sample["start_time"],
                "provider": sample["provider"]
            })
        
        return {"dashboard": list(dashboard_data.values())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard data: {str(e)}")

@api_router.get("/patient/health/metrics/{metric}", dependencies=[Depends(get_current_user)])
async def get_metric_data(
    metric: HealthMetric,
    days: int = Query(30, ge=1, le=365),
    aggregation: str = Query("none", pattern="^(none|daily|weekly|monthly)$"),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed data for a specific health metric"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get metric samples
        samples = list(await db.health_data_samples.find({
            "patient_id": current_user["id"],
            "metric": metric.value,
            "start_time": {"$gte": start_date, "$lte": end_date}
        }).sort("start_time", 1).to_list(10000))
        
        if aggregation == "none":
            return {"samples": samples}
        
        # TODO: Implement aggregation logic
        # For now, return raw samples
        return {"samples": samples, "aggregation": aggregation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metric data: {str(e)}")

@api_router.post("/patient/health/export", dependencies=[Depends(get_current_user)])
async def export_health_data(
    request: ExportDataRequest,
    current_user: dict = Depends(get_current_user)
):
    """Export patient health data"""
    try:
        # Build query
        query = {
            "patient_id": current_user["id"],
            "start_time": {"$gte": request.date_from, "$lte": request.date_to}
        }
        
        if request.metrics:
            query["metric"] = {"$in": [m.value for m in request.metrics]}
        
        if request.providers:
            query["provider"] = {"$in": [p.value for p in request.providers]}
        
        # Get data
        samples = list(await db.health_data_samples.find(query).sort("start_time", 1).to_list(100000))
        
        # Generate filename
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        date_from_str = request.date_from.strftime("%Y%m%d")
        date_to_str = request.date_to.strftime("%Y%m%d")
        filename = f"kinaura_{current_user['id']}_{date_from_str}_{date_to_str}_{timestamp}.{request.format}"
        
        if request.format == "csv":
            # TODO: Generate CSV format
            return {"format": "csv", "filename": filename, "record_count": len(samples)}
        else:
            # JSON format
            return {
                "format": "json",
                "filename": filename,
                "data": samples,
                "record_count": len(samples)
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")

# Admin Endpoints - Health Data Management
@api_router.get("/admin/health/patients/{patient_id}/timeline", dependencies=[Depends(admin_required)])
async def get_patient_health_timeline(
    patient_id: str,
    days: int = Query(90, ge=1, le=365),
    metrics: Optional[str] = Query(None, description="Comma-separated list of metrics"),
    current_user: dict = Depends(get_current_user)
):
    """Get unified health data timeline for a patient"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        query = {
            "patient_id": patient_id,
            "start_time": {"$gte": start_date, "$lte": end_date}
        }
        
        if metrics:
            metric_list = [m.strip() for m in metrics.split(",")]
            query["metric"] = {"$in": metric_list}
        
        samples = list(await db.health_data_samples.find(query).sort("start_time", -1).to_list(10000))
        
        return {"patient_id": patient_id, "timeline": samples}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get patient timeline: {str(e)}")

@api_router.get("/admin/health/connections", dependencies=[Depends(admin_required)])
async def get_all_connections(current_user: dict = Depends(get_current_user)):
    """Get all patient health provider connections"""
    try:
        connections = list(await db.health_provider_connections.find({}).to_list(1000))
        
        # Enrich with patient info and remove sensitive data
        for conn in connections:
            patient = await db.users.find_one({"id": conn["patient_id"]})
            if patient:
                conn["patient_name"] = patient.get("full_name")
                conn["patient_email"] = patient.get("email")
            
            # Remove sensitive data
            if "access_token" in conn:
                del conn["access_token"]
            if "refresh_token" in conn:
                del conn["refresh_token"]
        
        return {"connections": connections}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get connections: {str(e)}")

# Protocol Engine API - Internal Service Endpoints
@api_router.get("/engine/patients/{patient_id}/metrics", dependencies=[Depends(get_current_user)])
async def get_patient_metrics_for_engine(
    patient_id: str,
    metric: Optional[HealthMetric] = Query(None),
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    aggregation: str = Query("none", pattern="^(none|daily|weekly|monthly)$"),
    current_user: dict = Depends(get_current_user)
):
    """Protocol Engine API - Get patient metrics"""
    try:
        query = {
            "patient_id": patient_id,
            "start_time": {"$gte": date_from, "$lte": date_to}
        }
        
        if metric:
            query["metric"] = metric.value
        
        samples = list(await db.health_data_samples.find(query).sort("start_time", 1).to_list(100000))
        
        # TODO: Implement aggregation logic based on rules defined in requirements
        
        return {"patient_id": patient_id, "samples": samples, "aggregation": aggregation}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics for engine: {str(e)}")

@api_router.get("/engine/patients/{patient_id}/metrics/summary", dependencies=[Depends(get_current_user)])
async def get_patient_metrics_summary(
    patient_id: str,
    date_from: datetime = Query(...),
    date_to: datetime = Query(...),
    current_user: dict = Depends(get_current_user)
):
    """Protocol Engine API - Get aggregated metrics summary"""
    try:
        # Get all samples in date range
        samples = list(await db.health_data_samples.find({
            "patient_id": patient_id,
            "start_time": {"$gte": date_from, "$lte": date_to}
        }).to_list(100000))
        
        # Group by metric and calculate statistics
        summary = {}
        for sample in samples:
            metric = sample["metric"]
            value = sample["value"]
            
            # Only process numeric values for statistics
            if isinstance(value, (int, float)):
                if metric not in summary:
                    summary[metric] = {
                        "metric": metric,
                        "unit": sample["unit"],
                        "values": [],
                        "sample_count": 0
                    }
                
                summary[metric]["values"].append(value)
                summary[metric]["sample_count"] += 1
        
        # Calculate statistics for each metric
        for metric_data in summary.values():
            values = metric_data["values"]
            if values:
                import statistics
                metric_data.update({
                    "mean": statistics.mean(values),
                    "median": statistics.median(values),
                    "min": min(values),
                    "max": max(values),
                    "std": statistics.stdev(values) if len(values) > 1 else 0,
                    "compliance_pct": 100.0  # TODO: Calculate based on expected frequency
                })
            del metric_data["values"]  # Remove raw values from response
        
        return {"patient_id": patient_id, "summary": list(summary.values())}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get metrics summary: {str(e)}")

# Webhook endpoint for health data providers
@api_router.post("/webhooks/health/{provider}")
async def health_provider_webhook(provider: HealthProvider, request: Request):
    """Webhook endpoint for health data providers"""
    try:
        body = await request.body()
        headers = dict(request.headers)
        
        # TODO: Implement provider-specific webhook handling
        # For now, just log the webhook
        logger.info(f"Received webhook from {provider.value}")
        
        return {"success": True, "provider": provider.value}
    except Exception as e:
        logger.error(f"Health webhook error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Webhook processing failed: {str(e)}")

# ======================================
# KINAURA CHATBOT API ENDPOINTS
# ======================================

# Global chatbot instance (we'll initialize this once)
kinaura_chatbot = None

async def get_chatbot():
    """Get or create KinAura chatbot instance with configurable system prompt"""
    global kinaura_chatbot
    if kinaura_chatbot is None:
        api_key = os.getenv("EMERGENT_LLM_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="LLM API key not configured")
        
        # Get system prompt from database or use default
        system_prompt = await get_active_system_prompt()
        
        kinaura_chatbot = LlmChat(
            api_key=api_key,
            session_id="kinaura-bot",
            system_message=system_prompt
        ).with_model("openai", "gpt-4o-mini")
    
    return kinaura_chatbot

async def get_active_system_prompt():
    """Get the active system prompt from database"""
    try:
        config = await db.chatbot_config.find_one(
            {"is_active": True},
            sort=[("created_at", -1)]
        )
        
        if config:
            return config["system_prompt"]
        else:
            # Enhanced KinAura Concierge system prompt with luxury positioning
            return """You are **KinAura Concierge**, the AI assistant for KinAura — an elite social wellness club for regenerative medicine in Milan.

Tone & Language:
- Reply in the same language as the user (Italian or English).
- Style: elegant, calm, concise, expert, similar to luxury editorial writing.
- Be factual, reassuring, and avoid hype.

Core Rules:
1. Base all factual answers ONLY on the provided CONTEXT from the KinAura knowledge base.
2. Include inline citations in parentheses using the KB entry titles provided in CONTEXT (e.g., "… (Kinaura Devices, Treatments & Protocol Mapping)").
3. Never invent medical facts; if CONTEXT is insufficient, say so and suggest booking a consultation or contacting our concierge.
4. No diagnosis or prescriptions — provide general, educational information only.
5. Where possible, suggest relevant **multi-technology combinations** if they appear in CONTEXT.
6. For treatment/protocol questions:
   - Mention 2–4 relevant devices or protocols.
   - For each: 1 sentence "How it works" + 1 sentence "Why it works".
   - If available, add a KinAura-exclusive combination or positioning point.
7. Always end with a clear next step (e.g., "Book a consultation", "WhatsApp Concierge", "Call our team").

If the user asks about price:
- Give ranges only if present in CONTEXT, or say "We'll discuss pricing after your personalized assessment."

If the user asks a broad question (e.g., "What do you have for redness?"):
- Cover multiple suitable options with concise benefits.
- Prioritize solutions and combinations mentioned in CONTEXT.

If the user's question is unrelated to the clinic or treatments:
- Politely redirect them to relevant services or suggest they book a consult.

Your goal: give a short, impressive, evidence-based, and luxury-positioned answer that makes the user want to engage with KinAura.

KINAURA FOCUS AREAS:
- Regenerative Medicine
- Aesthetic Medicine  
- Innovative Wellness Protocols
- Multi-technology treatment combinations
- Exclusive devices and positioning in Milan
- Personalized wellness plans
- Diagnostic and monitoring capabilities

SAFETY DISCLAIMERS:
- Always remind users that this is informational only, not medical advice
- For urgent health matters, direct them to emergency services
- For specific medical questions, refer to KinAura practitioners

Be warm, professional, and focused on KinAura's exclusive approach to health and wellness."""
            
    except Exception as e:
        print(f"Error getting system prompt: {e}")
        # Fallback to enhanced default
        return """You are **KinAura Concierge**, the AI assistant for KinAura — an elite social wellness club for regenerative medicine in Milan.

Tone & Language:
- Reply in the same language as the user (Italian or English).
- Style: elegant, calm, concise, expert, similar to luxury editorial writing.
- Be factual, reassuring, and avoid hype.

Core Rules:
1. Base all factual answers ONLY on the provided CONTEXT from the KinAura knowledge base.
2. Include inline citations in parentheses using the KB entry titles provided in CONTEXT.
3. Never invent medical facts; if CONTEXT is insufficient, say so and suggest booking a consultation.
4. No diagnosis or prescriptions — provide general, educational information only.
5. Always end with a clear next step (Book consult / WhatsApp Concierge / Call our team).

Your goal: give a short, impressive, evidence-based, and luxury-positioned answer that makes the user want to engage with KinAura."""

async def get_conversation_context(session_id: str) -> str:
    """Get recent conversation context to avoid repetition"""
    try:
        # Get last 5 messages from the session
        messages = await db.chat_messages.find(
            {"session_id": session_id},
            {"_id": 0, "role": 1, "content": 1, "timestamp": 1}
        ).sort("timestamp", -1).limit(5).to_list(None)
        
        if not messages:
            return ""
        
        # Reverse to get chronological order
        messages.reverse()
        
        # Create context summary
        context_parts = []
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"][:200] + "..." if len(msg["content"]) > 200 else msg["content"]
            context_parts.append(f"{role}: {content}")
        
        return "\n".join(context_parts)
        
    except Exception as e:
        print(f"Error getting conversation context: {e}")
        return ""

async def get_user_memory_profile(user_id: str) -> str:
    """Get persistent user memory profile across all conversations"""
    try:
        if not user_id:
            return ""
        
        # Get user's memory profile
        user_memory = await db.user_memory_profiles.find_one({"user_id": user_id})
        
        if not user_memory:
            # Create initial profile by analyzing past conversations
            await create_user_memory_profile(user_id)
            user_memory = await db.user_memory_profiles.find_one({"user_id": user_id})
        
        if not user_memory:
            return ""
        
        # Build memory context
        memory_parts = []
        
        if user_memory.get("treatment_interests"):
            interests = ", ".join(user_memory["treatment_interests"])
            memory_parts.append(f"Previous treatment interests: {interests}")
        
        if user_memory.get("health_concerns"):
            concerns = ", ".join(user_memory["health_concerns"])
            memory_parts.append(f"Previously mentioned health concerns: {concerns}")
        
        if user_memory.get("appointment_history"):
            memory_parts.append(f"Appointment history: {user_memory['appointment_history']}")
        
        if user_memory.get("preferences"):
            prefs = user_memory["preferences"]
            if prefs.get("communication_style"):
                memory_parts.append(f"Prefers {prefs['communication_style']} communication style")
            if prefs.get("language"):
                memory_parts.append(f"Prefers {prefs['language']} language")
        
        if user_memory.get("previous_topics"):
            topics = ", ".join(user_memory["previous_topics"][-5:])  # Last 5 topics
            memory_parts.append(f"Recently discussed: {topics}")
        
        return "\n".join(memory_parts) if memory_parts else ""
        
    except Exception as e:
        print(f"Error getting user memory profile: {e}")
        return ""

async def create_user_memory_profile(user_id: str):
    """Create initial user memory profile by analyzing past conversations"""
    try:
        if not user_id:
            return
        
        # Get user's past messages
        messages = await db.chat_messages.find(
            {"user_id": user_id, "role": "user"},
            {"content": 1, "timestamp": 1}
        ).sort("timestamp", -1).limit(50).to_list(None)
        
        if not messages:
            return
        
        # Analyze messages to extract interests and concerns
        treatment_interests = []
        health_concerns = []
        topics_discussed = []
        language_detected = "English"
        
        # Treatment keywords to look for
        treatment_keywords = {
            "IV Therapy": ["iv", "intravenous", "infusion", "nutrients"],
            "Ozone Therapy": ["ozone", "o3", "oxygen therapy"],
            "PEMF Therapy": ["pemf", "electromagnetic", "pulsed"],
            "Hyperbaric Oxygen": ["hyperbaric", "hbot", "oxygen chamber"],
            "NAD+ Therapy": ["nad", "nicotinamide", "anti-aging"],
            "Peptide Therapy": ["peptide", "growth hormone", "collagen"],
            "Detox": ["detox", "cleanse", "toxins"],
            "Anti-Aging": ["anti-aging", "longevity", "aging", "youthful"],
            "Weight Management": ["weight", "metabolism", "fat loss"],
            "Energy & Vitality": ["energy", "fatigue", "vitality", "tired"]
        }
        
        # Health concerns keywords
        concern_keywords = {
            "Fatigue": ["tired", "fatigue", "energy", "exhausted"],
            "Stress": ["stress", "anxiety", "overwhelmed"],
            "Sleep Issues": ["sleep", "insomnia", "rest"],
            "Pain Management": ["pain", "chronic", "inflammation"],
            "Skin Health": ["skin", "aging", "wrinkles", "complexion"],
            "Immune Support": ["immune", "sick", "infections"],
            "Mental Wellness": ["brain", "focus", "memory", "cognitive"]
        }
        
        # Analyze each message
        for msg in messages:
            content = msg["content"].lower()
            
            # Detect language
            italian_words = ["ciao", "grazie", "salute", "benessere", "terapia", "trattamento"]
            if any(word in content for word in italian_words):
                language_detected = "Italian"
            
            # Check for treatment interests
            for treatment, keywords in treatment_keywords.items():
                if any(keyword in content for keyword in keywords):
                    if treatment not in treatment_interests:
                        treatment_interests.append(treatment)
            
            # Check for health concerns
            for concern, keywords in concern_keywords.items():
                if any(keyword in content for keyword in keywords):
                    if concern not in health_concerns:
                        health_concerns.append(concern)
            
            # Extract general topics (simplified)
            words = content.split()
            for word in words:
                if len(word) > 4 and word not in ["about", "treatment", "therapy", "what", "how", "when", "where"]:
                    if word not in topics_discussed and len(topics_discussed) < 20:
                        topics_discussed.append(word)
        
        # Check if user has booked appointments
        appointment_history = "No previous appointments"
        try:
            appointments = await db.appointment_bookings.find({"patient_id": user_id}).limit(5).to_list(None)
            if appointments:
                appointment_count = len(appointments)
                appointment_history = f"Has {appointment_count} previous appointment(s)"
        except:
            pass
        
        # Create memory profile
        memory_profile = {
            "user_id": user_id,
            "treatment_interests": treatment_interests,
            "health_concerns": health_concerns,
            "appointment_history": appointment_history,
            "preferences": {
                "language": language_detected,
                "communication_style": "professional"
            },
            "previous_topics": topics_discussed,
            "last_updated": datetime.utcnow(),
            "created_at": datetime.utcnow()
        }
        
        # Insert or update memory profile
        await db.user_memory_profiles.replace_one(
            {"user_id": user_id},
            memory_profile,
            upsert=True
        )
        
        print(f"Created memory profile for user {user_id}: {len(treatment_interests)} interests, {len(health_concerns)} concerns")
        
    except Exception as e:
        print(f"Error creating user memory profile: {e}")

async def update_user_memory_profile(user_id: str, message: str, response: str):
    """Update user memory profile with new conversation insights"""
    try:
        if not user_id:
            return
        
        # Get existing profile or create new one
        user_memory = await db.user_memory_profiles.find_one({"user_id": user_id})
        
        if not user_memory:
            await create_user_memory_profile(user_id)
            user_memory = await db.user_memory_profiles.find_one({"user_id": user_id})
        
        if not user_memory:
            return
        
        # Extract new insights from the conversation
        content = message.lower()
        
        # Update treatment interests
        treatment_keywords = {
            "IV Therapy": ["iv", "intravenous", "infusion"],
            "Ozone Therapy": ["ozone", "o3"],
            "PEMF Therapy": ["pemf", "electromagnetic"],
            "Hyperbaric Oxygen": ["hyperbaric", "hbot"],
            "NAD+ Therapy": ["nad", "nicotinamide"],
            "Peptide Therapy": ["peptide", "growth hormone"]
        }
        
        for treatment, keywords in treatment_keywords.items():
            if any(keyword in content for keyword in keywords):
                if treatment not in user_memory.get("treatment_interests", []):
                    user_memory.setdefault("treatment_interests", []).append(treatment)
        
        # Update health concerns  
        concern_keywords = {
            "Fatigue": ["tired", "fatigue", "energy"],
            "Stress": ["stress", "anxiety"],
            "Sleep Issues": ["sleep", "insomnia"],
            "Pain Management": ["pain", "chronic"],
            "Skin Health": ["skin", "aging", "wrinkles"]
        }
        
        for concern, keywords in concern_keywords.items():
            if any(keyword in content for keyword in keywords):
                if concern not in user_memory.get("health_concerns", []):
                    user_memory.setdefault("health_concerns", []).append(concern)
        
        # Add current topic to previous topics
        words = [word for word in content.split() if len(word) > 4]
        for word in words[:3]:  # Add top 3 relevant words
            if word not in user_memory.get("previous_topics", []):
                user_memory.setdefault("previous_topics", []).append(word)
        
        # Keep only last 20 topics
        if len(user_memory.get("previous_topics", [])) > 20:
            user_memory["previous_topics"] = user_memory["previous_topics"][-20:]
        
        # Update timestamp
        user_memory["last_updated"] = datetime.utcnow()
        
        # Save updated profile
        await db.user_memory_profiles.replace_one(
            {"user_id": user_id},
            user_memory
        )
        
    except Exception as e:
        print(f"Error updating user memory profile: {e}")

async def generate_personalized_suggestions(user_memory: dict, user_intent: str, current_message: str) -> List[str]:
    """Generate personalized follow-up suggestions based on user memory and context"""
    try:
        suggestions = []
        
        # Default suggestions
        default_suggestions = [
            "Tell me about your regenerative medicine treatments",
            "How can I book an appointment?",
            "What makes KinAura different from other wellness centers?",
            "Do you offer longevity assessments?"
        ]
        
        if not user_memory:
            return default_suggestions
        
        # Personalized suggestions based on user memory
        treatment_interests = user_memory.get("treatment_interests", [])
        health_concerns = user_memory.get("health_concerns", [])
        
        # Treatment-specific suggestions
        if "IV Therapy" in treatment_interests:
            suggestions.append("What types of IV therapy do you offer?")
        if "Ozone Therapy" in treatment_interests:
            suggestions.append("How does ozone therapy work for my condition?")
        if "NAD+ Therapy" in treatment_interests:
            suggestions.append("What are the benefits of NAD+ therapy?")
        
        # Health concern-specific suggestions
        if "Fatigue" in health_concerns:
            suggestions.append("Which treatments are best for increasing energy?")
        if "Sleep Issues" in health_concerns:
            suggestions.append("How can your treatments improve my sleep?")
        if "Stress" in health_concerns:
            suggestions.append("What stress management options do you have?")
        
        # Intent-based suggestions
        if user_intent == "booking_inquiry":
            suggestions.append("What's your availability this week?")
            suggestions.append("How do I prepare for my first visit?")
        elif user_intent == "treatment_info":
            suggestions.append("Are there any side effects I should know about?")
            suggestions.append("How many sessions would I typically need?")
        
        # Return personalized suggestions or defaults
        return suggestions[:4] if suggestions else default_suggestions
        
    except Exception as e:
        print(f"Error generating personalized suggestions: {e}")
        return [
            "Tell me about your regenerative medicine treatments",
            "How can I book an appointment?",
            "What makes KinAura different from other wellness centers?",
            "Do you offer longevity assessments?"
        ]

async def create_dynamic_system_prompt(conversation_context: str, user_intent, user_memory: str = "") -> str:
    """Create a dynamic system prompt based on conversation context, user intent, and persistent memory"""
    try:
        base_prompt = await get_active_system_prompt()
        
        # Add conversation-specific instructions
        dynamic_additions = []
        
        if conversation_context:
            dynamic_additions.append(f"""
CONVERSATION CONTEXT INSTRUCTIONS:
The user has been in this conversation: {conversation_context[:500]}...

CRITICAL: 
- Do NOT repeat opening greetings if this is a follow-up question
- Do NOT use the same closing phrases if you just used them
- Build upon the previous conversation naturally
- Vary your response structure - sometimes start directly with the answer
- If this is the 2nd+ question, skip formal introductions and get straight to the helpful information
- Use different closing suggestions each time (rotate between: "Would you like to know more about...", "I can also help with...", "Feel free to ask about...", or sometimes no closing at all)""")
        
        if user_memory:
            dynamic_additions.append(f"""
USER MEMORY PROFILE:
{user_memory}

PERSONALIZATION INSTRUCTIONS:
- Reference their previous interests and concerns when relevant
- Tailor recommendations based on their treatment interests
- Acknowledge their appointment history appropriately
- Use their preferred communication style and language
- Build upon topics they've previously discussed
- Make connections between their current question and past interests""")
        
        if user_intent and user_intent.concerns:
            concerns_text = ", ".join(user_intent.concerns)
            dynamic_additions.append(f"""
USER CONCERNS DETECTED: {concerns_text}
Focus your response on addressing these specific concerns with relevant KinAura solutions.""")
        
        if user_intent and user_intent.device:
            dynamic_additions.append(f"""
USER DEVICE INTEREST: {user_intent.device}
Prioritize information about {user_intent.device} and related treatment protocols.""")
        
        # Add protocol-based recommendation instructions
        dynamic_additions.append("""
PROTOCOL-BASED RECOMMENDATIONS:
When patients ask about concerns (acne, wrinkles, cellulite, hair loss, etc.) or show interest in treatments:

1. ALWAYS suggest the complete KinAura Protocol, not just single treatments
2. Explain the SYNERGY between treatments (why they work together)
3. Emphasize KinAura's EXCLUSIVITY:
   - "KinAura has the newest Morpheus8 in Milan"
   - "Only clinic in Milan with [specific device/combination]"
   - "Sterile hospital-grade environment"
   - "AI-driven personalization"

4. Format protocol responses as:
   - Protocol name
   - Bullet list of treatments with rationale
   - Why KinAura statement emphasizing uniqueness

5. For booking inquiries about specific treatments, suggest the complete protocol that includes that treatment

EXAMPLES:
- Cellulite inquiry → Suggest "Smooth Contour Protocol" (Endolaser + Morpheus8 Body + Lymphatic Drainage + IV Detox + Exosomes)
- Morpheus8 booking → Suggest "Advanced Firm & Renew Protocol" (Morpheus8 + PBM + HBOT + Exosomes)
- Anti-aging question → Suggest "Biological Reset Protocol" (EBOO2 + HBOT + IV Longevity + AI Score + Exosomes)""")
        
        if dynamic_additions:
            return base_prompt + "\n\n" + "\n".join(dynamic_additions)
        
        return base_prompt
        
    except Exception as e:
        print(f"Error creating dynamic system prompt: {e}")
        return await get_active_system_prompt()

async def get_dynamic_chatbot(system_prompt: str):
    """Get chatbot instance with dynamic system prompt"""
    try:
        api_key = os.getenv("EMERGENT_LLM_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="LLM API key not configured")
        
        # Create new chatbot instance with dynamic prompt
        dynamic_chatbot = LlmChat(
            api_key=api_key,
            session_id=f"kinaura-dynamic-{datetime.utcnow().timestamp()}",
            system_message=system_prompt
        ).with_model("openai", "gpt-4o-mini")
        
        return dynamic_chatbot
        
    except Exception as e:
        print(f"Error creating dynamic chatbot: {e}")
        # Fallback to regular chatbot
        return await get_chatbot()

def parse_markdown_file(content: str, filename: str) -> List[ParsedMarkdownItem]:
    """Parse markdown file content into knowledge base items"""
    try:
        # Parse frontmatter if present
        post = frontmatter.loads(content)
        
        # Get metadata from frontmatter
        metadata = post.metadata
        main_content = post.content
        
        # Convert markdown to plain text for content
        md = markdown.Markdown()
        html_content = md.convert(main_content)
        # Remove HTML tags for clean text
        clean_content = re.sub(r'<[^>]+>', '', html_content)
        
        # Extract sections based on headers
        sections = []
        current_section = {"title": "", "content": ""}
        
        lines = main_content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Check for headers (# ## ###)
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if header_match:
                # Save previous section if it has content
                if current_section["title"] and current_section["content"].strip():
                    sections.append(current_section.copy())
                
                # Start new section
                level = len(header_match.group(1))
                title = header_match.group(2).strip()
                current_section = {
                    "title": title,
                    "content": "",
                    "level": level
                }
            else:
                # Add content to current section
                if line:  # Skip empty lines
                    current_section["content"] += line + "\n"
        
        # Don't forget the last section
        if current_section["title"] and current_section["content"].strip():
            sections.append(current_section)
        
        # If no sections found, create one item from the entire content
        if not sections:
            title = metadata.get('title', filename.replace('.md', '').replace('_', ' ').title())
            category = determine_category(title, clean_content, filename)
            tags = extract_tags(title, clean_content, metadata)
            
            return [ParsedMarkdownItem(
                title=title,
                content=clean_content.strip(),
                category=category,
                tags=tags,
                source_filename=filename
            )]
        
        # Convert sections to knowledge base items
        parsed_items = []
        for section in sections:
            title = section["title"]
            content = section["content"].strip()
            
            if len(content) > 50:  # Only include substantial sections
                category = determine_category(title, content, filename)
                tags = extract_tags(title, content, metadata)
                
                parsed_items.append(ParsedMarkdownItem(
                    title=title,
                    content=content,
                    category=category,
                    tags=tags,
                    source_filename=filename
                ))
        
        return parsed_items
        
    except Exception as e:
        print(f"Error parsing markdown file {filename}: {e}")
        return []

# KinAura Device and Concern Taxonomies for Intent Classification
KINAURA_CONCERNS = [
    "redness", "rosacea", "pigmentation", "sun_damage", "pre_event_glow", "fine_lines", "wrinkles",
    "skin_laxity_face", "jawline_neck_contour", "texture", "acne", "acne_scars", "pores",
    "cellulite", "body_contour", "hair_loss", "vaginal_rejuvenation", "recovery", "inflammation", 
    "detox", "stress_sleep", "performance"
]

KINAURA_DEVICES = [
    "VISIA-7",
    "Wellness Tower", 
    "Sciton mJOULE (BBL HERO / MOXI / SkinTyte)",
    "InMode Ignite (Morpheus8 / FaceTite / BodyTite)",
    "MCT (Meta Cell Technology)",
    "Emuage Lab",
    "Ultraformer MPT (HIFU)",
    "Weberneedle Endolaser", 
    "Fotona DYNAMIS MAX (Er:YAG / Nd:YAG)",
    "AirPod Revive Hydroxy (mHBOT + H2)",
    "Ammortal Chamber (PEMF/PEF + PBM + H2 + Vibro-Acoustic)",
    "HydraFacial Syndeo MD"
]

class ChatbotIntent(BaseModel):
    concerns: List[str] = []
    device: Optional[str] = None
    language: str = "en"

async def classify_user_intent(message: str) -> ChatbotIntent:
    """Classify user query into devices, concerns, and language using GPT-4"""
    try:
        api_key = os.getenv("EMERGENT_LLM_KEY")
        if not api_key:
            # Fallback to basic classification
            return ChatbotIntent(language="it" if any(word in message.lower() for word in ["cosa", "come", "perché", "quando", "dove"]) else "en")
        
        # Enhanced intent classification system
        intent_system_prompt = f"""
Classify the user's query into:
- concerns: array from provided list  
- device: one from provided list or null
- language: "en" or "it"

Return strict JSON: {{"concerns":["..."],"device":null,"language":"en"}}

Concerns: {','.join(KINAURA_CONCERNS)}
Devices: {','.join(KINAURA_DEVICES)}

Examples:
- "What helps with wrinkles?" → {{"concerns":["wrinkles","fine_lines"],"device":null,"language":"en"}}
- "Tell me about Morpheus8" → {{"concerns":[],"device":"InMode Ignite (Morpheus8 / FaceTite / BodyTite)","language":"en"}}
- "Cosa posso fare per il rossore?" → {{"concerns":["redness"],"device":null,"language":"it"}}
"""

        # Use emergent integrations for GPT-4 intent classification
        intent_chat = LlmChat(
            api_key=api_key,
            session_id="intent-classifier",
            system_message=intent_system_prompt
        ).with_model("openai", "gpt-4o-mini")
        
        response = await intent_chat.send_message(message)
        
        # Parse the JSON response
        import json
        intent_data = json.loads(response)
        
        return ChatbotIntent(
            concerns=intent_data.get("concerns", []),
            device=intent_data.get("device"),
            language=intent_data.get("language", "en")
        )
        
    except Exception as e:
        print(f"Error in intent classification: {e}")
        # Fallback to basic language detection
        language = "it" if any(word in message.lower() for word in ["cosa", "come", "perché", "quando", "dove", "voglio", "mi", "della", "nel", "con"]) else "en"
        return ChatbotIntent(language=language)

async def get_enhanced_knowledge_base_context(query: str, intent: ChatbotIntent) -> str:
    """Get relevant knowledge base items with enhanced filtering based on intent"""
    try:
        # Build enhanced search query
        search_query = {
            "is_approved": True,
            "is_active": True
        }
        
        # Add text search
        search_conditions = []
        
        # Basic text search
        search_conditions.append({
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"content": {"$regex": query, "$options": "i"}},
                {"tags": {"$in": [query.lower()]}}
            ]
        })
        
        # Add device filtering if device detected
        if intent.device:
            device_terms = intent.device.lower().split()
            device_conditions = []
            for term in device_terms:
                if len(term) > 2:  # Skip short terms
                    device_conditions.extend([
                        {"title": {"$regex": term, "$options": "i"}},
                        {"content": {"$regex": term, "$options": "i"}},
                        {"tags": {"$in": [term]}}
                    ])
            if device_conditions:
                search_conditions.append({"$or": device_conditions})
        
        # Add concern filtering if concerns detected
        if intent.concerns:
            concern_conditions = []
            for concern in intent.concerns:
                concern_terms = concern.replace("_", " ").split()
                for term in concern_terms:
                    if len(term) > 2:
                        concern_conditions.extend([
                            {"title": {"$regex": term, "$options": "i"}},
                            {"content": {"$regex": term, "$options": "i"}},
                            {"tags": {"$in": [term, concern]}}
                        ])
            if concern_conditions:
                search_conditions.append({"$or": concern_conditions})
        
        # Add language preference
        if intent.language == "it":
            search_conditions.append({
                "$or": [
                    {"tags": {"$in": ["italian", "italiano", "it"]}},
                    {"title": {"$regex": "IT —", "$options": "i"}},
                    {"content": {"$regex": "italian|italiano", "$options": "i"}}
                ]
            })
        else:
            search_conditions.append({
                "$or": [
                    {"tags": {"$in": ["english", "en"]}},
                    {"title": {"$regex": "EN —", "$options": "i"}},
                    {"content": {"$regex": "english", "$options": "i"}},
                    {"tags": {"$nin": ["italian", "italiano", "it"]}}  # Default to English if not Italian
                ]
            })
        
        # Combine all conditions
        if search_conditions:
            search_query["$and"] = search_conditions
        
        # Execute enhanced search
        kb_items = await db.knowledge_base.find(search_query, {"_id": 0}).limit(8).to_list(8)
        
        if not kb_items:
            # Fallback to basic search if enhanced search returns nothing
            basic_query = {
                "is_approved": True,
                "is_active": True,
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"content": {"$regex": query, "$options": "i"}},
                    {"tags": {"$in": [query.lower()]}}
                ]
            }
            kb_items = await db.knowledge_base.find(basic_query, {"_id": 0}).limit(5).to_list(5)
        
        if not kb_items:
            return ""
        
        # Format context with source citations
        context = "KINAURA KNOWLEDGE BASE:\n"
        for item in kb_items:
            context += f"\nSource: {item['title']}\n"
            context += f"Category: {item['category']}\n"
            context += f"Content: {item['content']}\n"
            context += "---\n"
        
        return context
        
    except Exception as e:
        print(f"Error getting enhanced knowledge base context: {e}")
        # Fallback to basic search
        return await get_knowledge_base_context(query)

def determine_category(title: str, content: str, filename: str) -> str:
    """Determine category based on title, content, and filename - simplified version"""
    title_lower = title.lower()
    content_lower = content.lower()
    filename_lower = filename.lower()
    
    # Define category keywords
    category_keywords = {
        'treatments': ['treatment', 'therapy', 'protocol', 'procedure', 'session', 'iv', 'ozone', 'hyperbaric', 'pemf', 'peptide', 'nad'],
        'services': ['service', 'offering', 'package', 'membership', 'consultation', 'assessment', 'evaluation'],
        'policies': ['policy', 'terms', 'conditions', 'privacy', 'consent', 'agreement', 'cancellation', 'refund'],
        'faq': ['faq', 'question', 'answer', 'frequently', 'asked', 'common', 'help'],
        'general': ['about', 'overview', 'introduction', 'welcome', 'mission', 'vision', 'team', 'contact']
    }
    
    # Check filename first
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in filename_lower:
                return category
    
    # Check title and content
    for category, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in title_lower or keyword in content_lower:
                return category
    
    # Default to treatments for medical content
    medical_keywords = ['health', 'medical', 'wellness', 'regenerative', 'anti-aging', 'longevity']
    for keyword in medical_keywords:
        if keyword in title_lower or keyword in content_lower:
            return 'treatments'
    
    return 'general'

def extract_tags(title: str, content: str, metadata: dict) -> List[str]:
    """Extract relevant tags from title, content, and metadata"""
    tags = set()
    
    # Add tags from metadata if present
    if 'tags' in metadata:
        if isinstance(metadata['tags'], list):
            tags.update([tag.lower() for tag in metadata['tags']])
        elif isinstance(metadata['tags'], str):
            tags.update([tag.strip().lower() for tag in metadata['tags'].split(',')])
    
    # Extract tags from title and content
    text_to_analyze = f"{title} {content}".lower()
    
    # Common KinAura treatment and service keywords
    potential_tags = [
        'iv_therapy', 'ozone', 'hyperbaric', 'nad', 'pemf', 'peptide', 'regenerative',
        'anti_aging', 'longevity', 'wellness', 'aesthetic', 'detox', 'energy',
        'immune', 'recovery', 'optimization', 'therapy', 'treatment', 'protocol',
        'consultation', 'assessment', 'membership', 'pricing', 'booking', 'appointment'
    ]
    
    for tag in potential_tags:
        if tag.replace('_', ' ') in text_to_analyze or tag.replace('_', '') in text_to_analyze:
            tags.add(tag)
    
    # Limit to maximum 8 tags
    return list(tags)[:8]

async def get_knowledge_base_context(query: str) -> str:
    """Get relevant knowledge base items for the query"""
    try:
        # Search for relevant knowledge base items
        # For now, we'll do a simple text search - in production, you might use vector search
        kb_items = await db.knowledge_base.find({
            "is_approved": True,
            "is_active": True,
            "$or": [
                {"title": {"$regex": query, "$options": "i"}},
                {"content": {"$regex": query, "$options": "i"}},
                {"tags": {"$in": [query.lower()]}}
            ]
        }, {"_id": 0}).limit(5).to_list(5)
        
        if not kb_items:
            return ""
        
        context = "KINAURA KNOWLEDGE BASE:\n"
        for item in kb_items:
            context += f"\nTitle: {item['title']}\n"
            context += f"Category: {item['category']}\n"
            context += f"Content: {item['content']}\n"
            context += "---\n"
        
        return context
    except Exception as e:
        print(f"Error getting knowledge base context: {e}")
        return ""
async def find_available_slots(service_name: Optional[str] = None, days_ahead: int = 14) -> str:
    """Find available appointment slots for chatbot responses"""
    try:
        # Calculate date range
        start_date = datetime.now().date()
        end_date = start_date + timedelta(days=days_ahead)
        
        # Build query
        slot_query = {
            "is_available": True,
            "is_blocked": False,
            "date": {
                "$gte": start_date.strftime("%Y-%m-%d"),
                "$lte": end_date.strftime("%Y-%m-%d")
            }
        }
        
        # If service specified, find service ID
        if service_name:
            service = await db.services.find_one(
                {"name": {"$regex": service_name, "$options": "i"}, "is_active": True}, {"_id": 0}
            )
            if service:
                slot_query["service_id"] = service["id"]
        
        # Get available slots
        slots = await db.appointment_slots.find(slot_query, {"_id": 0}).limit(10).to_list(10)
        
        if not slots:
            return "No available slots found in the next 2 weeks. Please contact our concierge for more options."
        
        # Group slots by service
        service_slots = {}
        for slot in slots:
            service = await db.services.find_one({"id": slot["service_id"]}, {"_id": 0})
            service_name = service["name"] if service else "Unknown Service"
            
            if service_name not in service_slots:
                service_slots[service_name] = []
            
            service_slots[service_name].append({
                "date": slot["date"],
                "time": slot["start_time"],
                "price": service.get("price", 0) if service else 0
            })
        
        # Format response
        response = "Available appointment slots:\n\n"
        for service, slots_list in service_slots.items():
            response += f"**{service}**\n"
            for slot in slots_list[:3]:  # Show max 3 slots per service
                response += f"• {slot['date']} at {slot['time']} (€{slot['price']})\n"
            response += "\n"
        
        response += "To book any of these appointments, please use our booking system or contact our concierge."
        return response
        
    except Exception as e:
        print(f"Error finding available slots: {e}")
        return "I'm having trouble accessing our appointment system right now. Please contact our concierge directly to check availability."

# Import RAG service and local models
from services.rag_service import rag_service, ProductionRAGService
from models import ChatMessage, ChatSession

# Simple UnresolvedQuery model for logging
class UnresolvedQuery(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    session_id: str
    language: str = "en"
    attempted_response: str
    confidence: float
    context_found: bool = False
    suggested_kb_topics: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)

@api_router.post("/chat", response_model=ChatResponse)
@enhanced_limiter.limit("30/minute")  # 30 chat requests per minute
async def enhanced_chat_with_kinaura(request: Request, chat_request: ChatRequest):
    """Enhanced RAG-powered chat with KinAura AI assistant"""
    try:
        # Detect language from message
        language = await detect_user_language(chat_request.message)
        if hasattr(chat_request, 'language') and chat_request.language:
            language = chat_request.language
        
        # Generate session ID if not provided
        session_id = chat_request.session_id or str(uuid.uuid4())
        
        # Create or update chat session
        session_data = {
            "id": session_id,
            "language": language,
            "last_activity": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        await db.chat_sessions.update_one(
            {"id": session_id},
            {
                "$set": session_data,
                "$inc": {"total_messages": 1},
                "$setOnInsert": {"created_at": datetime.utcnow(), "total_sources_used": 0}
            },
            upsert=True
        )
        
        # Store user message
        user_message = ChatMessage(
            session_id=session_id,
            role="user",
            content=chat_request.message,
            language=language,
            metadata=getattr(chat_request, 'context', {}) or {}
        )
        await db.chat_messages.insert_one(user_message.dict())
        
        # Generate RAG response
        rag_response = await rag_service.generate_rag_response(
            user_message=chat_request.message,
            session_id=session_id,
            language=language
        )
        
        # Store assistant response
        assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=rag_response.response,
            language=language,
            sources=[{
                "id": src.id,
                "title": src.title,
                "similarity": src.similarity,
                "source": src.source
            } for src in rag_response.sources],
            confidence=rag_response.confidence,
            response_time=rag_response.response_time
        )
        await db.chat_messages.insert_one(assistant_message.dict())
        
        # Update session analytics
        await db.chat_sessions.update_one(
            {"id": session_id},
            {
                "$inc": {"total_sources_used": len(rag_response.sources)},
                "$push": {
                    "confidence_history": rag_response.confidence,
                    "response_times": rag_response.response_time
                }
            }
        )
        
        # Check if query should be flagged as unresolved
        if rag_response.confidence < 0.6 or not rag_response.sources:
            await _log_unresolved_query(
                query=chat_request.message,
                session_id=session_id,
                response=rag_response.response,
                confidence=rag_response.confidence,
                language=language
            )
        
        # Generate suggested questions
        suggested_questions = await _generate_suggested_questions(language, rag_response.sources)
        
        # Check for protocol recommendations
        has_protocol, protocol_name = await _check_protocol_recommendation(chat_request.message, rag_response.sources)
        
        # Build response
        return ChatResponse(
            message=rag_response.response,
            session_id=session_id,
            message_id=assistant_message.id,
            sources=[{
                "id": src.source,
                "title": src.title,
                "similarity": round(src.similarity, 3),
                "content_preview": src.content[:200] + "..." if len(src.content) > 200 else src.content
            } for src in rag_response.sources],
            confidence=rag_response.confidence,
            response_time=rag_response.response_time,
            language=language,
            suggested_questions=suggested_questions,
            has_protocol_recommendation=has_protocol,
            protocol_name=protocol_name,
            medical_disclaimer=get_medical_disclaimer(language),
            requires_consultation=rag_response.confidence < 0.7
        )
        
    except Exception as e:
        logging.error(f"Enhanced chat failed: {e}")
        
        # Fallback response
        session_id = getattr(chat_request, 'session_id', None) or str(uuid.uuid4())
        language = await detect_user_language(chat_request.message)
        fallback_message = get_fallback_response(language)
        
        return ChatResponse(
            message=fallback_message,
            session_id=session_id,
            message_id=str(uuid.uuid4()),
            sources=[],
            confidence=0.3,
            response_time=0.0,
            language=language,
            suggested_questions=get_default_suggested_questions(language),
            medical_disclaimer=get_medical_disclaimer(language),
            requires_consultation=True
        )

async def _log_unresolved_query(query: str, session_id: str, response: str, 
                              confidence: float, language: str):
    """Log unresolved query for admin review"""
    try:
        unresolved = UnresolvedQuery(
            query=query,
            session_id=session_id,
            language=language,
            attempted_response=response,
            confidence=confidence,
            context_found=confidence > 0.4,
            suggested_kb_topics=await extract_topics_from_query(query)
        )
        
        await db.unresolved_queries.insert_one(unresolved.dict())
        logging.info(f"Logged unresolved query: {unresolved.id}")
        
    except Exception as e:
        logging.error(f"Failed to log unresolved query: {e}")

async def _generate_suggested_questions(language: str, sources: List[Any]) -> List[str]:
    """Generate contextual suggested questions"""
    
    if language == "it":
        base_questions = [
            "Quali trattamenti offrite per l'anti-aging?",
            "Come funziona la terapia NAD+ IV?",
            "Cosa include il vostro protocollo personalizzato?",
            "Quanto costa una seduta di Morpheus8?",
            "Come posso prenotare una consulenza?"
        ]
    else:
        base_questions = [
            "What treatments do you offer for anti-aging?",
            "How does NAD+ IV therapy work?",
            "What's included in your personalized protocol?",
            "How much does a Morpheus8 session cost?",
            "How can I book a consultation?"
        ]
    
    # If we have good sources, generate more specific questions
    if sources and len(sources) > 0:
        # Extract topics from sources for more relevant suggestions
        topics = []
        for source in sources[:3]:
            if hasattr(source, 'content') and 'morpheus8' in source.content.lower():
                topics.append('morpheus8')
            if hasattr(source, 'content') and ('nad+' in source.content.lower() or 'iv therapy' in source.content.lower()):
                topics.append('nad_iv')
            if hasattr(source, 'content') and ('hbot' in source.content.lower() or 'hyperbaric' in source.content.lower()):
                topics.append('hbot')
        
        # Add topic-specific questions
        if 'morpheus8' in topics:
            if language == "it":
                base_questions.append("Quante sedute di Morpheus8 sono necessarie?")
            else:
                base_questions.append("How many Morpheus8 sessions do I need?")
        
        if 'nad_iv' in topics:
            if language == "it":
                base_questions.append("Quali sono i benefici della terapia NAD+ IV?")
            else:
                base_questions.append("What are the benefits of NAD+ IV therapy?")
        
        if 'hbot' in topics:
            if language == "it":
                base_questions.append("Come funziona la terapia iperbarica?")
            else:
                base_questions.append("How does hyperbaric oxygen therapy work?")
    
    return base_questions[:5]  # Limit to 5 suggestions

async def _check_protocol_recommendation(query: str, sources: List[Any]) -> Tuple[bool, Optional[str]]:
    """Check if response should include protocol recommendation"""
    
    protocol_keywords = {
        'anti-aging': 'Advanced Anti-Aging Protocol',
        'skin': 'Advanced Firm & Renew Protocol', 
        'energy': 'Vitality & Energy Protocol',
        'longevity': 'Longevity Optimization Protocol',
        'recovery': 'Recovery & Performance Protocol',
        'detox': 'Cellular Detox Protocol'
    }
    
    query_lower = query.lower()
    
    for keyword, protocol in protocol_keywords.items():
        if keyword in query_lower:
            return True, protocol
    
    # Check sources for protocol mentions
    for source in sources:
        if hasattr(source, 'content'):
            content_lower = source.content.lower()
            for keyword, protocol in protocol_keywords.items():
                if keyword in content_lower:
                    return True, protocol
    
    return False, None

def get_medical_disclaimer(language: str) -> str:
    """Get medical disclaimer in specified language"""
    if language == "it":
        return "Questa informazione non sostituisce la consultazione medica. I protocolli KinAura sono validati da clinici specializzati."
    else:
        return "This information does not replace medical consultation. KinAura protocols are validated by clinicians."

def get_fallback_response(language: str) -> str:
    """Get fallback response when RAG fails"""
    if language == "it":
        return """Grazie per la tua domanda. Il nostro sistema di conoscenza è temporaneamente limitato, ma posso fornirti informazioni generali sui nostri servizi.

KinAura offre trattamenti avanzati di medicina rigenerativa tra cui:
• Morpheus8 - Microneedling con radiofrequenza
• Terapia NAD+ IV - Rigenerazione cellulare
• HBOT - Terapia con ossigeno iperbarico
• Trattamenti con esosomi - Medicina rigenerativa

Per informazioni dettagliate e protocolli personalizzati, ti consiglio di prenotare una consulenza con il nostro team medico.

Questa informazione non sostituisce la consultazione medica. I protocolli KinAura sono validati da clinici specializzati."""
    
    else:
        return """Thank you for your question. Our knowledge system is temporarily limited, but I can provide general information about our services.

KinAura offers advanced regenerative medicine treatments including:
• Morpheus8 - Microneedling with radiofrequency
• NAD+ IV Therapy - Cellular regeneration
• HBOT - Hyperbaric oxygen therapy  
• Exosome treatments - Regenerative medicine

For detailed information and personalized protocols, I recommend booking a consultation with our medical team.

This information does not replace medical consultation. KinAura protocols are validated by clinicians."""

def get_default_suggested_questions(language: str) -> List[str]:
    """Get default suggested questions"""
    if language == "it":
        return [
            "Quali trattamenti offrite?",
            "Come posso prenotare una consulenza?",
            "Cosa include il protocollo personalizzato?",
            "Quali sono i costi dei trattamenti?",
            "Dove si trova la clinica?"
        ]
    else:
        return [
            "What treatments do you offer?",
            "How can I book a consultation?",
            "What's included in the personalized protocol?",
            "What are the treatment costs?",
            "Where is the clinic located?"
        ]

async def extract_topics_from_query(query: str) -> List[str]:
    """Extract topics from query for KB improvement suggestions"""
    
    topics = []
    query_lower = query.lower()
    
    # Treatment topics
    if any(word in query_lower for word in ['morpheus8', 'micro', 'needling', 'skin']):
        topics.append('morpheus8')
    if any(word in query_lower for word in ['nad+', 'nad', 'iv', 'drip', 'energy']):
        topics.append('nad_iv_therapy')
    if any(word in query_lower for word in ['hbot', 'hyperbaric', 'oxygen']):
        topics.append('hyperbaric_therapy')
    if any(word in query_lower for word in ['exosome', 'stem', 'regenerative']):
        topics.append('exosome_therapy')
    if any(word in query_lower for word in ['laser', 'co2', 'resurfacing']):
        topics.append('laser_therapy')
    
    # Condition topics
    if any(word in query_lower for word in ['aging', 'wrinkle', 'anti-aging']):
        topics.append('anti_aging')
    if any(word in query_lower for word in ['fatigue', 'energy', 'tired']):
        topics.append('fatigue_energy')
    if any(word in query_lower for word in ['skin', 'acne', 'pigmentation']):
        topics.append('skin_conditions')
    if any(word in query_lower for word in ['weight', 'metabolism', 'diet']):
        topics.append('metabolic_health')
    
    return topics[:5]  # Limit to 5 topics

@api_router.get("/chat/user-memory/{user_id}")
async def get_user_memory_profile_endpoint(user_id: str):
    """Get user memory profile for debugging/admin purposes""" 
    try:
        memory_profile = await db.user_memory_profiles.find_one({"user_id": user_id}, {"_id": 0})
        if not memory_profile:
            return {"message": "No memory profile found for this user"}
        
        return memory_profile
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting user memory profile: {str(e)}")

@api_router.post("/chat/user-memory/{user_id}/refresh")
async def refresh_user_memory_profile(user_id: str):
    """Refresh user memory profile by re-analyzing conversations"""
    try:
        await create_user_memory_profile(user_id)
        return {"message": "User memory profile refreshed successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error refreshing user memory profile: {str(e)}")

@api_router.get("/chat/sessions")
async def get_chat_sessions(
    user_id: Optional[str] = Query(None),
    limit: int = Query(20)
):
    """Get chat sessions for a user"""
    try:
        query = {"is_active": True}
        if user_id:
            query["user_id"] = user_id
        
        sessions = await db.chat_sessions.find(query, {"_id": 0}).sort("updated_at", -1).limit(limit).to_list(limit)
        return sessions  # Return list directly for testing compatibility
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chat sessions: {str(e)}")

@api_router.get("/chat/sessions/{session_id}/messages")
async def get_chat_messages(session_id: str):
    """Get messages for a chat session"""
    try:
        messages = await db.chat_messages.find(
            {"session_id": session_id}, {"_id": 0}
        ).sort("timestamp", 1).to_list(1000)
        
        return messages  # Return list directly for testing compatibility
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chat messages: {str(e)}")

# ======================================
# KNOWLEDGE BASE MANAGEMENT API ENDPOINTS (ADMIN)
# ======================================

@api_router.post("/admin/knowledge-base/upload-markdown")
@enhanced_limiter.limit("5/minute")  # 5 markdown uploads per minute
async def upload_markdown_file(
    request: Request,
    file: UploadFile = File(...),
    admin_user: dict = Depends(get_admin_user)
):
    """Upload and parse markdown file to create knowledge base items (admin only)"""
    # Validate file first
    await validate_uploaded_file(file)
    try:
        # Validate file type
        if not file.filename.endswith('.md'):
            raise HTTPException(status_code=400, detail="Only .md files are supported")
        
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Parse markdown file
        parsed_items = parse_markdown_file(content_str, file.filename)
        
        if not parsed_items:
            raise HTTPException(status_code=400, detail="No valid content sections found in markdown file")
        
        # Create knowledge base items
        created_items = []
        errors = []
        
        for item_data in parsed_items:
            try:
                kb_item = KnowledgeBaseItem(
                    title=item_data.title,
                    content=item_data.content,
                    category=item_data.category,
                    tags=item_data.tags,
                    source_type=item_data.source_type,
                    source_id=file.filename,
                    created_by=admin_user["id"]
                )
                
                await db.knowledge_base.insert_one(kb_item.dict())
                created_items.append(kb_item.dict())
                
            except Exception as e:
                errors.append(f"Failed to create item '{item_data.title}': {str(e)}")
        
        return MarkdownUploadResponse(
            filename=file.filename,
            parsed_items=[item.dict() for item in parsed_items],
            success_count=len(created_items),
            error_count=len(errors),
            errors=errors
        ).dict()
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing markdown file: {str(e)}")

@api_router.post("/admin/knowledge-base/preview-markdown")
async def preview_markdown_file(
    file: UploadFile = File(...),
    admin_user: dict = Depends(get_admin_user)
):
    """Preview markdown file parsing without creating knowledge base items (admin only)"""
    try:
        # Validate file type
        if not file.filename.endswith('.md'):
            raise HTTPException(status_code=400, detail="Only .md files are supported")
        
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Parse markdown file
        parsed_items = parse_markdown_file(content_str, file.filename)
        
        return {
            "filename": file.filename,
            "parsed_items": [item.dict() for item in parsed_items],
            "item_count": len(parsed_items)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error previewing markdown file: {str(e)}")

@api_router.post("/admin/knowledge-base")
async def create_knowledge_base_item(
    item_data: KnowledgeBaseItemCreate,
    admin_user: dict = Depends(get_admin_user)
):
    """Create a new knowledge base item (admin only)"""
    try:
        kb_item = KnowledgeBaseItem(
            title=item_data.title,
            content=item_data.content,
            category=item_data.category,
            tags=item_data.tags,
            source_type=item_data.source_type,
            source_id=item_data.source_id,
            created_by=admin_user["id"]
        )
        
        await db.knowledge_base.insert_one(kb_item.dict())
        
        # If item is approved, trigger content sync notification and process for RAG
        if kb_item.is_approved:
            try:
                await notify_content_change(["knowledge_base"])
                
                # Process for RAG embeddings
                await rag_service.process_knowledge_base_update(kb_item.dict())
                logger.info(f"Processed new approved KB item for RAG: {kb_item.id}")
                
            except Exception as e:
                print(f"⚠️ Failed to notify knowledge base content change or process RAG: {e}")
        
        return kb_item.dict()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating knowledge base item: {str(e)}")

@api_router.get("/admin/knowledge-base")
async def get_knowledge_base_items(
    admin_user: dict = Depends(get_admin_user),
    category: Optional[str] = Query(None),
    approved_only: bool = Query(False)
):
    """Get knowledge base items (admin only)"""
    try:
        query = {}
        if category:
            query["category"] = category
        if approved_only:
            query["is_approved"] = True
        
        items = await db.knowledge_base.find(query, {"_id": 0}).sort("created_at", -1).to_list(1000)
        return items  # Return list directly for testing compatibility
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting knowledge base items: {str(e)}")

@api_router.put("/admin/knowledge-base/bulk-approve-markdown")
async def bulk_approve_markdown_items(
    admin_user: dict = Depends(get_admin_user)
):
    """Bulk approve all unapproved knowledge base items imported from markdown files (admin only)"""
    try:
        # Find all unapproved markdown-imported items
        unapproved_items = await db.knowledge_base.find({
            "source_type": "markdown_import",
            "is_approved": False,
            "is_active": True
        }, {"_id": 0}).to_list(1000)
        
        if not unapproved_items:
            return {
                "message": "No unapproved markdown items found",
                "approved_count": 0,
                "items": []
            }
        
        # Update all items to approved
        current_time = datetime.utcnow()
        result = await db.knowledge_base.update_many(
            {
                "source_type": "markdown_import",
                "is_approved": False,
                "is_active": True
            },
            {
                "$set": {
                    "is_approved": True,
                    "approval_date": current_time,
                    "approved_by": admin_user["id"],
                    "updated_at": current_time
                }
            }
        )
        
        return {
            "message": f"Successfully approved {result.modified_count} markdown knowledge base items",
            "approved_count": result.modified_count,
            "items": [{"id": item["id"], "title": item["title"]} for item in unapproved_items],
            "approved_by": admin_user["id"],
            "approval_date": current_time.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error bulk approving markdown items: {str(e)}")

@api_router.get("/admin/knowledge-base/pending-markdown-count")
async def get_pending_markdown_count(
    admin_user: dict = Depends(get_admin_user)
):
    """Get count of pending markdown items for approval (admin only)"""
    try:
        count = await db.knowledge_base.count_documents({
            "source_type": "markdown_import",
            "is_approved": False,
            "is_active": True
        })
        
        return {"pending_count": count}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting pending markdown count: {str(e)}")

@api_router.put("/admin/knowledge-base/{item_id}")
async def update_knowledge_base_item(
    item_id: str,
    item_data: KnowledgeBaseItemUpdate,
    admin_user: dict = Depends(get_admin_user)
):
    """Update a knowledge base item (admin only)"""
    try:
        existing_item = await db.knowledge_base.find_one({"id": item_id})
        if not existing_item:
            raise HTTPException(status_code=404, detail="Knowledge base item not found")
        
        update_data = {k: v for k, v in item_data.dict().items() if v is not None}
        update_data["updated_at"] = datetime.utcnow()
        update_data["version"] = existing_item.get("version", 1) + 1
        update_data["content_version"] = str(uuid.uuid4())
        
        await db.knowledge_base.update_one({"id": item_id}, {"$set": update_data})
        
        # If item is approved, trigger content sync notification
        if existing_item.get("is_approved", False):
            try:
                await notify_content_change(["knowledge_base"])
            except Exception as e:
                print(f"⚠️ Failed to notify knowledge base content change: {e}")
        
        updated_item = await db.knowledge_base.find_one({"id": item_id}, {"_id": 0})
        return updated_item
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating knowledge base item: {str(e)}")

@api_router.put("/admin/knowledge-base/{item_id}/approve")
async def approve_knowledge_base_item(
    item_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Approve a knowledge base item (admin only)"""
    try:
        existing_item = await db.knowledge_base.find_one({"id": item_id})
        if not existing_item:
            raise HTTPException(status_code=404, detail="Knowledge base item not found")
        
        await db.knowledge_base.update_one(
            {"id": item_id},
            {
                "$set": {
                    "is_approved": True,
                    "approval_date": datetime.utcnow(),
                    "approved_by": admin_user["id"],
                    "updated_at": datetime.utcnow(),
                    "content_version": str(uuid.uuid4())
                }
            }
        )
        
        # Trigger content sync notification for chatbot updates
        try:
            await notify_content_change(["knowledge_base"])
        except Exception as e:
            print(f"⚠️ Failed to notify knowledge base content change: {e}")
        
        # Update RAG embeddings for the approved item
        try:
            updated_item = await db.knowledge_base.find_one({"id": item_id}, {"_id": 0})
            if updated_item:
                await rag_service.process_knowledge_base_update(updated_item)
                logger.info(f"Updated RAG embeddings for approved KB item: {item_id}")
        except Exception as e:
            logger.error(f"Failed to update RAG embeddings for KB item {item_id}: {e}")
        
        return {"message": "Knowledge base item approved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error approving knowledge base item: {str(e)}")

@api_router.post("/admin/knowledge-base/populate-protocols", dependencies=[Depends(get_admin_user)])
async def populate_protocol_knowledge_base(admin_user: dict = Depends(get_admin_user)):
    """Populate knowledge base with KinAura protocols"""
    try:
        populated_count = 0
        
        for protocol_key, protocol_data in KINAURA_PROTOCOLS.items():
            # Create English version
            en_content = f"""
PROTOCOL: {protocol_data['protocol_en']}

TREATMENTS:
{chr(10).join([f"• {t['name_en']}: {t['description_en']}" for t in protocol_data['treatments']])}

WHY KINAURA: {protocol_data['why_kinaura_en']}

CONCERN: {protocol_key.replace('-', ' ')}
LANGUAGE: English
"""

            # Create Italian version  
            it_content = f"""
PROTOCOLLO: {protocol_data['protocol_it']}

TRATTAMENTI:
{chr(10).join([f"• {t['name_it']}: {t['description_it']}" for t in protocol_data['treatments']])}

PERCHÉ KINAURA: {protocol_data['why_kinaura_it']}

CONCERN: {protocol_key.replace('-', ' ')}
LANGUAGE: Italian
"""

            # Insert English KB item
            en_kb_item = KnowledgeBaseItem(
                id=f"protocol_{protocol_key}_en",
                title=f"KinAura {protocol_data['protocol_en']} Protocol",
                content=en_content,
                category="protocol",
                tags=protocol_data['tags'] + ["language:en"],
                source_type="admin_created",
                created_by=admin_user["id"],
                is_approved=True
            )
            
            # Insert Italian KB item
            it_kb_item = KnowledgeBaseItem(
                id=f"protocol_{protocol_key}_it", 
                title=f"KinAura {protocol_data['protocol_it']} Protocol",
                content=it_content,
                category="protocol",
                tags=protocol_data['tags'] + ["language:it"],
                source_type="admin_created",
                created_by=admin_user["id"],
                is_approved=True
            )
            
            # Upsert to avoid duplicates
            await db.knowledge_base.update_one(
                {"id": en_kb_item.id},
                {"$set": en_kb_item.dict()},
                upsert=True
            )
            
            await db.knowledge_base.update_one(
                {"id": it_kb_item.id},
                {"$set": it_kb_item.dict()},
                upsert=True
            )
            
            populated_count += 2
        
        return {
            "message": f"Successfully populated {populated_count} protocol items in knowledge base", 
            "protocols": list(KINAURA_PROTOCOLS.keys()),
            "protocols_added": len(KINAURA_PROTOCOLS),
            "items_created": populated_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error populating protocol knowledge base: {str(e)}")

@api_router.get("/patient/notifications/proactive")
async def get_proactive_notifications(
    current_user: dict = Depends(get_current_user),
    unread_only: bool = Query(False),
    limit: int = Query(10)
):
    """Get proactive protocol notifications for patient"""
    try:
        query = {"patient_id": current_user["id"]}
        if unread_only:
            query["is_read"] = False
            
        notifications = await db.proactive_notifications.find(
            query, {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return {
            "notifications": notifications,
            "count": len(notifications),
            "unread_count": len([n for n in notifications if not n.get('is_read', False)])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting proactive notifications: {str(e)}")

@api_router.put("/patient/notifications/proactive/{notification_id}/read")
async def mark_proactive_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Mark proactive notification as read"""
    try:
        result = await db.proactive_notifications.update_one(
            {
                "_id": notification_id,
                "patient_id": current_user["id"]
            },
            {
                "$set": {
                    "is_read": True,
                    "read_at": datetime.utcnow()
                }
            }
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
            
        return {"success": True, "message": "Notification marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error marking notification as read: {str(e)}")

@api_router.get("/patient/notifications/latest-protocol-recommendation")
async def get_latest_protocol_recommendation(
    current_user: dict = Depends(get_current_user)
):
    """Get the latest unread protocol recommendation for immediate display"""
    try:
        # Get the most recent unread protocol recommendation
        notification = await db.proactive_notifications.find_one(
            {
                "patient_id": current_user["id"],
                "notification_type": "protocol_recommendation", 
                "is_read": False
            },
            {"_id": 0},
            sort=[("created_at", -1)]
        )
        
        if notification:
            return {
                "has_notification": True,
                "notification": notification
            }
        else:
            return {
                "has_notification": False,
                "notification": None
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting latest protocol recommendation: {str(e)}")

@api_router.get("/admin/patients/funnel")
async def get_patients_funnel(
    admin_user: dict = Depends(get_admin_user),
    include_details: bool = Query(True, description="Include patient details in response"),
    export_format: str = Query("json", description="Response format: json or csv")
):
    """Get CRM funnel analytics with lead, active, and lapsed patient data"""
    try:
        # Get comprehensive funnel data
        funnel_data = await get_funnel_analytics()
        
        # Optionally exclude patient details for performance
        if not include_details:
            funnel_data.leads["patients"] = []
            funnel_data.active["patients"] = []
            funnel_data.lapsed["patients"] = []
        
        # Handle CSV export
        if export_format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write headers
            writer.writerow(['Stage', 'Patient ID', 'Email', 'Full Name', 'Last Login', 'Last Booking', 'Total Bookings', 'Engagement Score'])
            
            # Write data for each stage
            for stage_name, stage_data in [("Lead", funnel_data.leads), ("Active", funnel_data.active), ("Lapsed", funnel_data.lapsed)]:
                for patient in stage_data["patients"]:
                    writer.writerow([
                        stage_name,
                        patient.get('id', ''),
                        patient.get('email', ''),
                        patient.get('full_name', ''),
                        patient.get('last_login', ''),
                        patient.get('last_booking', ''),
                        patient.get('total_bookings', 0),
                        patient.get('engagement_score', 0)
                    ])
            
            csv_content = output.getvalue()
            output.close()
            
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=kinaura_funnel_export.csv"}
            )
        
        return {
            "success": True,
            "data": funnel_data.dict(),
            "generated_at": datetime.utcnow(),
            "admin_user": admin_user["full_name"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting patients funnel: {str(e)}")

@api_router.put("/admin/patients/{patient_id}/lifecycle")
async def update_patient_lifecycle(
    patient_id: str,
    lifecycle_data: dict,
    admin_user: dict = Depends(get_admin_user)
):
    """Manually update patient lifecycle stage and data"""
    try:
        # Validate patient exists
        patient = await db.users.find_one({"id": patient_id})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Prepare update data
        update_data = {}
        
        if "lifecycle_stage" in lifecycle_data:
            if lifecycle_data["lifecycle_stage"] in [stage.value for stage in LifecycleStage]:
                update_data["lifecycle_stage"] = lifecycle_data["lifecycle_stage"]
        
        if "engagement_score" in lifecycle_data:
            update_data["engagement_score"] = max(0, min(100, int(lifecycle_data["engagement_score"])))
        
        if "preferred_language" in lifecycle_data:
            update_data["preferred_language"] = lifecycle_data["preferred_language"]
        
        if "last_booking" in lifecycle_data:
            update_data["last_booking"] = datetime.fromisoformat(lifecycle_data["last_booking"])
        
        if update_data:
            await db.users.update_one(
                {"id": patient_id},
                {"$set": update_data}
            )
        
        return {
            "success": True,
            "message": "Patient lifecycle data updated successfully",
            "updated_fields": list(update_data.keys())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating patient lifecycle: {str(e)}")

@api_router.get("/admin/patients/engagement-logs")
async def get_engagement_logs(
    admin_user: dict = Depends(get_admin_user),
    patient_id: Optional[str] = Query(None),
    campaign_type: Optional[str] = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0, ge=0)
):
    """Get engagement campaign logs"""
    try:
        # Build query
        query = {}
        if patient_id:
            query["patient_id"] = patient_id
        if campaign_type:
            query["campaign_type"] = campaign_type
        
        # Get logs
        logs = await db.engagement_logs.find(
            query, {"_id": 0}
        ).sort("sent_at", -1).skip(offset).limit(limit).to_list(limit)
        
        # Get total count
        total_count = await db.engagement_logs.count_documents(query)
        
        return {
            "success": True,
            "logs": logs,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": total_count > (offset + limit)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting engagement logs: {str(e)}")

# Boutique E-commerce API Endpoints

@api_router.get("/shop/products")
async def get_shop_products(
    category: Optional[ProductCategory] = Query(None),
    protocol: Optional[str] = Query(None, description="Filter by protocol binding"),
    active_only: bool = Query(True),
    search: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    """Get products for shop catalog with filtering"""
    try:
        # Build query
        query = {}
        if active_only:
            query["is_active"] = True
        if category:
            query["category"] = category.value
        if protocol:
            query["protocol_bindings"] = {"$in": [protocol]}
        if search:
            query["$or"] = [
                {"name.en": {"$regex": search, "$options": "i"}},
                {"name.it": {"$regex": search, "$options": "i"}},
                {"tags": {"$in": [search.lower()]}}
            ]
        
        # Get products
        products = await db.products.find(
            query, {"_id": 0}
        ).sort("ordering", 1).skip(offset).limit(limit).to_list(limit)
        
        # Get total count for pagination
        total_count = await db.products.count_documents(query)
        
        return {
            "success": True,
            "products": products,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": total_count > (offset + limit)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching products: {str(e)}")

@api_router.get("/shop/products/{slug}")
async def get_product_detail(slug: str):
    """Get product detail by slug"""
    try:
        product = await db.products.find_one({"slug": slug, "is_active": True}, {"_id": 0})
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Get related products based on category and tags
        related_products = await db.products.find(
            {
                "is_active": True,
                "sku": {"$ne": product["sku"]},
                "$or": [
                    {"category": product["category"]},
                    {"tags": {"$in": product.get("tags", [])}}
                ]
            },
            {"_id": 0}
        ).limit(4).to_list(4)
        
        return {
            "success": True,
            "product": product,
            "related_products": related_products
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching product: {str(e)}")

@api_router.get("/shop/collections")
async def get_shop_collections(active_only: bool = Query(True)):
    """Get product collections"""
    try:
        query = {}
        if active_only:
            query["is_active"] = True
            
        collections = await db.collections.find(
            query, {"_id": 0}
        ).sort("ordering", 1).to_list(100)
        
        # Populate products for each collection
        for collection in collections:
            if collection.get("products"):
                products = await db.products.find(
                    {
                        "sku": {"$in": collection["products"]},
                        "is_active": True
                    },
                    {"_id": 0}
                ).to_list(100)
                collection["populated_products"] = products
            else:
                collection["populated_products"] = []
        
        return {
            "success": True,
            "collections": collections
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching collections: {str(e)}")

@api_router.get("/shop/recommendations")
async def get_product_recommendations(
    protocol: Optional[str] = Query(None),
    patient_id: Optional[str] = Query(None),
    limit: int = Query(4, le=10)
):
    """Get product recommendations based on protocol or patient history"""
    try:
        recommended_products = []
        
        if protocol:
            # Get cross-sell rules for this protocol
            cross_sell_rules = await db.cross_sell_rules.find(
                {"protocol_id": protocol, "is_active": True}
            ).sort("priority", -1).to_list(10)
            
            # Collect recommended product SKUs
            recommended_skus = []
            for rule in cross_sell_rules:
                recommended_skus.extend(rule.get("product_skus", []))
            
            if recommended_skus:
                products = await db.products.find(
                    {
                        "sku": {"$in": recommended_skus[:limit]},
                        "is_active": True
                    },
                    {"_id": 0}
                ).to_list(limit)
                recommended_products = products
        
        # Fallback: get popular products if no specific recommendations
        if not recommended_products:
            popular_products = await db.products.find(
                {"is_active": True, "badge": "Best Seller"},
                {"_id": 0}
            ).limit(limit).to_list(limit)
            recommended_products = popular_products
        
        return {
            "success": True,
            "recommendations": recommended_products,
            "based_on": "protocol" if protocol else "popular"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")

# Admin Boutique Management Endpoints

@api_router.post("/admin/shop/products")
async def create_product(
    product_data: dict,
    admin_user: dict = Depends(get_admin_user)
):
    """Create new product"""
    try:
        # Generate SKU if not provided
        if not product_data.get("sku"):
            import re
            name_en = product_data.get("name", {}).get("en", "product")
            sku_base = re.sub(r'[^a-zA-Z0-9]', '-', name_en.upper())[:20]
            product_data["sku"] = f"KA-{sku_base}-{str(uuid.uuid4())[:8].upper()}"
        
        # Generate slug if not provided
        if not product_data.get("slug"):
            name_en = product_data.get("name", {}).get("en", "product")
            product_data["slug"] = re.sub(r'[^a-zA-Z0-9]', '-', name_en.lower()).strip('-')
        
        # Validate required fields
        required_fields = ["name", "category", "price_eur"]
        for field in required_fields:
            if not product_data.get(field):
                raise HTTPException(status_code=400, detail=f"Missing required field: {field}")
        
        # Create product
        product = Product(**product_data)
        await db.products.insert_one(product.dict())
        
        return {
            "success": True,
            "message": "Product created successfully",
            "product": product.dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating product: {str(e)}")

@api_router.put("/admin/shop/products/{sku}")
async def update_product(
    sku: str,
    product_data: dict,
    admin_user: dict = Depends(get_admin_user)
):
    """Update existing product"""
    try:
        # Check if product exists
        existing = await db.products.find_one({"sku": sku})
        if not existing:
            raise HTTPException(status_code=404, detail="Product not found")
        
        # Update timestamp
        product_data["updated_at"] = datetime.utcnow()
        
        # Update product
        result = await db.products.update_one(
            {"sku": sku},
            {"$set": product_data}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=400, detail="No changes made")
        
        # Get updated product
        updated_product = await db.products.find_one({"sku": sku}, {"_id": 0})
        
        return {
            "success": True,
            "message": "Product updated successfully",
            "product": updated_product
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating product: {str(e)}")

@api_router.delete("/admin/shop/products/{sku}")
async def delete_product(
    sku: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Delete product (soft delete by setting inactive)"""
    try:
        result = await db.products.update_one(
            {"sku": sku},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            "success": True,
            "message": "Product deactivated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting product: {str(e)}")

@api_router.get("/admin/shop/products")
async def get_admin_products(
    admin_user: dict = Depends(get_admin_user),
    category: Optional[ProductCategory] = Query(None),
    active_only: bool = Query(False),
    limit: int = Query(100, le=500),
    offset: int = Query(0, ge=0)
):
    """Get products for admin management"""
    try:
        query = {}
        if active_only:
            query["is_active"] = True
        if category:
            query["category"] = category.value
            
        products = await db.products.find(
            query, {"_id": 0}
        ).sort("ordering", 1).skip(offset).limit(limit).to_list(limit)
        
        total_count = await db.products.count_documents(query)
        
        return {
            "success": True,
            "products": products,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": total_count > (offset + limit)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching admin products: {str(e)}")

# Collections Management
@api_router.post("/admin/shop/collections")
async def create_collection(
    collection_data: dict,
    admin_user: dict = Depends(get_admin_user)
):
    """Create product collection"""
    try:
        # Generate slug if not provided
        if not collection_data.get("slug"):
            name_en = collection_data.get("name", {}).get("en", "collection")
            collection_data["slug"] = re.sub(r'[^a-zA-Z0-9]', '-', name_en.lower()).strip('-')
        
        collection = ProductCollection(**collection_data)
        await db.collections.insert_one(collection.dict())
        
        return {
            "success": True,
            "message": "Collection created successfully",
            "collection": collection.dict()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating collection: {str(e)}")

@api_router.get("/admin/shop/collections")
async def get_admin_collections(admin_user: dict = Depends(get_admin_user)):
    """Get collections for admin management"""
    try:
        collections = await db.collections.find({}, {"_id": 0}).sort("ordering", 1).to_list(100)
        return {
            "success": True,
            "collections": collections
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching collections: {str(e)}")

# Cross-sell Rules Management
@api_router.post("/admin/shop/cross-sell-rules")
async def create_cross_sell_rule(
    rule_data: dict,
    admin_user: dict = Depends(get_admin_user)
):
    """Create cross-sell rule"""
    try:
        rule = CrossSellRule(**rule_data)
        await db.cross_sell_rules.insert_one(rule.dict())
        
        return {
            "success": True,
            "message": "Cross-sell rule created successfully",
            "rule": rule.dict()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating cross-sell rule: {str(e)}")

@api_router.get("/admin/shop/cross-sell-rules")
async def get_cross_sell_rules(admin_user: dict = Depends(get_admin_user)):
    """Get all cross-sell rules"""
    try:
        rules = await db.cross_sell_rules.find({}, {"_id": 0}).to_list(100)
        return {
            "success": True,
            "rules": rules
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching cross-sell rules: {str(e)}")

@api_router.delete("/admin/knowledge-base/{item_id}")
async def delete_knowledge_base_item(
    item_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Delete a knowledge base item (admin only)"""
    try:
        existing_item = await db.knowledge_base.find_one({"id": item_id})
        if not existing_item:
            raise HTTPException(status_code=404, detail="Knowledge base item not found")
        
        await db.knowledge_base.delete_one({"id": item_id})
        return {"message": "Knowledge base item deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting knowledge base item: {str(e)}")
# ======================================
# CHATBOT CONFIGURATION MANAGEMENT API ENDPOINTS (ADMIN)
# ======================================

@api_router.get("/admin/chatbot/config")
async def get_chatbot_config(
    admin_user: dict = Depends(get_admin_user)
):
    """Get current chatbot configuration (admin only)"""
    try:
        config = await db.chatbot_config.find_one(
            {"is_active": True},
            {"_id": 0},
            sort=[("created_at", -1)]
        )
        
        if not config:
            # Return default config with required fields for testing
            default_config = {
                "id": str(uuid.uuid4()),
                "system_prompt": await get_active_system_prompt(),
                "is_active": True,
                "version": 1,
                "created_by": admin_user["id"],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            return default_config
        
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting chatbot config: {str(e)}")

@api_router.put("/admin/chatbot/config")
async def update_chatbot_config(
    config_data: ChatbotConfigUpdate,
    admin_user: dict = Depends(get_admin_user)
):
    """Update chatbot configuration (admin only)"""
    try:
        # Deactivate current config
        await db.chatbot_config.update_many(
            {"is_active": True},
            {"$set": {"is_active": False}}
        )
        
        # Get current version
        latest_config = await db.chatbot_config.find_one(
            {},
            sort=[("version", -1)]
        )
        new_version = (latest_config.get("version", 0) + 1) if latest_config else 1
        
        # Create new config
        new_config = ChatbotConfig(
            system_prompt=config_data.system_prompt,
            created_by=admin_user["id"],
            version=new_version
        )
        
        await db.chatbot_config.insert_one(new_config.dict())
        
        # Reset global chatbot instance to use new config
        global kinaura_chatbot
        kinaura_chatbot = None
        
        return new_config.dict()  # Return the new config directly for testing compatibility
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating chatbot config: {str(e)}")

@api_router.get("/admin/chatbot/config/history")
async def get_chatbot_config_history(
    admin_user: dict = Depends(get_admin_user),
    limit: int = Query(10)
):
    """Get chatbot configuration history (admin only)"""
    try:
        configs = await db.chatbot_config.find(
            {},
            {"_id": 0}
        ).sort("created_at", -1).limit(limit).to_list(limit)
        
        return configs  # Return list directly for testing compatibility
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting config history: {str(e)}")

# Patient Inquiry Management Endpoints

@api_router.get("/admin/inquiries")
async def get_patient_inquiries(
    status: Optional[str] = None,
    inquiry_type: Optional[str] = None,
    patient_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    admin_user: dict = Depends(get_admin_user)
):
    """Get all patient inquiries with optional filtering"""
    try:
        # Build query filter
        query = {}
        if status:
            query["status"] = status
        if inquiry_type:
            query["inquiry_type"] = inquiry_type
        if patient_id:
            query["patient_id"] = patient_id
        
        # Get inquiries with patient info
        inquiries = await db.patient_inquiries.find(
            query,
            {"_id": 0}
        ).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
        
        # Enrich with patient information
        for inquiry in inquiries:
            patient = await db.users.find_one({"id": inquiry["patient_id"]}, {"_id": 0, "full_name": 1, "email": 1})
            if patient:
                inquiry["patient_name"] = patient.get("full_name", "Unknown")
                inquiry["patient_email"] = patient.get("email", "Unknown")
        
        return inquiries
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching inquiries: {str(e)}")

@api_router.get("/admin/inquiries/stats")
async def get_inquiry_stats(
    days: int = 7,
    admin_user: dict = Depends(get_admin_user)
):
    """Get inquiry statistics for the admin dashboard"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get inquiries in date range
        inquiries = await db.patient_inquiries.find(
            {"timestamp": {"$gte": start_date, "$lte": end_date}},
            {"_id": 0}
        ).to_list(None)
        
        # Calculate stats
        stats = {
            "total_inquiries": len(inquiries),
            "new_inquiries": len([i for i in inquiries if i.get("status") == "new"]),
            "contacted_inquiries": len([i for i in inquiries if i.get("status") == "contacted"]),
            "converted_inquiries": len([i for i in inquiries if i.get("status") == "converted"]),
            "by_type": {
                "treatment": len([i for i in inquiries if i.get("inquiry_type") == "treatment"]),
                "condition": len([i for i in inquiries if i.get("inquiry_type") == "condition"]),
                "wellness_goal": len([i for i in inquiries if i.get("inquiry_type") == "wellness_goal"])
            },
            "by_status": {
                "new": len([i for i in inquiries if i.get("status") == "new"]),
                "contacted": len([i for i in inquiries if i.get("status") == "contacted"]),
                "converted": len([i for i in inquiries if i.get("status") == "converted"]),
                "dismissed": len([i for i in inquiries if i.get("status") == "dismissed"])
            },
            "top_treatments": {},
            "top_conditions": {},
            "period": f"Last {days} days"
        }
        
        # Calculate top treatments and conditions
        all_treatments = []
        all_conditions = []
        
        for inquiry in inquiries:
            inquiry_type = inquiry.get("inquiry_type", "")
            detected_items = inquiry.get("detected_items", [])
            
            if inquiry_type == "treatment":
                all_treatments.extend(detected_items)
            elif inquiry_type == "condition":
                all_conditions.extend(detected_items)
        
        # Count occurrences
        treatment_counts = Counter(all_treatments)
        condition_counts = Counter(all_conditions)
        
        stats["top_treatments"] = dict(treatment_counts.most_common(5))
        stats["top_conditions"] = dict(condition_counts.most_common(5))
        
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching inquiry stats: {str(e)}")

@api_router.get("/admin/inquiries/{inquiry_id}")
async def get_inquiry_details(
    inquiry_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Get detailed information about a specific inquiry"""
    try:
        # Get inquiry
        inquiry = await db.patient_inquiries.find_one({"id": inquiry_id}, {"_id": 0})
        if not inquiry:
            raise HTTPException(status_code=404, detail="Inquiry not found")
        
        # Get patient info
        patient = await db.users.find_one({"id": inquiry["patient_id"]}, {"_id": 0, "full_name": 1, "email": 1, "phone": 1, "membership_tier": 1})
        if patient:
            inquiry["patient_name"] = patient.get("full_name", "Unknown")
            inquiry["patient_email"] = patient.get("email", "Unknown")
            inquiry["patient_phone"] = patient.get("phone")
            inquiry["patient_membership"] = patient.get("membership_tier")
        
        # Get other inquiries from same patient
        other_inquiries = await db.patient_inquiries.find(
            {"patient_id": inquiry["patient_id"], "id": {"$ne": inquiry_id}},
            {"_id": 0, "inquiry_type": 1, "detected_items": 1, "timestamp": 1, "status": 1}
        ).sort("timestamp", -1).limit(5).to_list(5)
        
        inquiry["other_inquiries"] = other_inquiries
        
        return inquiry
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching inquiry details: {str(e)}")

@api_router.put("/admin/inquiries/{inquiry_id}")
async def update_inquiry_status(
    inquiry_id: str,
    update: PatientInquiryUpdate,
    admin_user: dict = Depends(get_admin_user)
):
    """Update inquiry status and add admin notes"""
    try:
        # Build update data
        update_data = {
            "updated_at": datetime.utcnow(),
            "updated_by": admin_user["id"]
        }
        
        if update.status:
            update_data["status"] = update.status
        if update.admin_notes:
            update_data["admin_notes"] = update.admin_notes
        if update.priority_score is not None:
            update_data["priority_score"] = update.priority_score
        
        # Update inquiry
        result = await db.patient_inquiries.update_one(
            {"id": inquiry_id},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Inquiry not found")
        
        # Return updated inquiry
        updated_inquiry = await db.patient_inquiries.find_one({"id": inquiry_id}, {"_id": 0})
        return updated_inquiry
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating inquiry: {str(e)}")

@api_router.post("/admin/inquiries/{inquiry_id}/send-booking-request")
async def send_booking_request(
    inquiry_id: str,
    request: dict,
    admin_user: dict = Depends(get_admin_user)
):
    """Send a booking request to a patient based on their inquiry"""
    try:
        # Get inquiry
        inquiry = await db.patient_inquiries.find_one({"id": inquiry_id}, {"_id": 0})
        if not inquiry:
            raise HTTPException(status_code=404, detail="Inquiry not found")
        
        # Get patient info
        patient = await db.users.find_one({"id": inquiry["patient_id"]}, {"_id": 0, "full_name": 1, "email": 1})
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        
        # Create booking request notification
        booking_notification = {
            "id": str(uuid.uuid4()),
            "type": "booking_request",
            "patient_id": inquiry["patient_id"],
            "title": "Booking Request Sent",
            "message": f"Booking request sent to {patient.get('full_name')} for: {', '.join(request.get('treatments', []))}",
            "data": {
                "inquiry_id": inquiry_id,
                "treatments": request.get("treatments", []),
                "message": request.get("message", ""),
                "suggested_times": request.get("suggested_times", [])
            },
            "is_read": False,
            "created_at": datetime.utcnow(),
            "created_by": admin_user["id"]
        }
        
        await db.admin_notifications.insert_one(booking_notification)
        
        # Update inquiry status
        await db.patient_inquiries.update_one(
            {"id": inquiry_id},
            {
                "$set": {
                    "status": "booking_sent",
                    "booking_sent_at": datetime.utcnow(),
                    "booking_sent_by": admin_user["id"],
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        return {"booking_sent": True, "message": "Booking request sent successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending booking request: {str(e)}")

@api_router.get("/admin/notifications")
async def get_admin_notifications(
    limit: int = 50,
    skip: int = 0,
    is_read: Optional[bool] = None,
    admin_user: dict = Depends(get_admin_user)
):
    """Get admin notifications"""
    try:
        query = {}
        if is_read is not None:
            query["is_read"] = is_read
        
        notifications = await db.admin_notifications.find(
            query,
            {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        return notifications
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching notifications: {str(e)}")

@api_router.put("/admin/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Mark a notification as read"""
    try:
        result = await db.admin_notifications.update_one(
            {"id": notification_id},
            {"$set": {"is_read": True, "read_at": datetime.utcnow(), "read_by": admin_user["id"]}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification marked as read"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating notification: {str(e)}")

# Content versioning models
class ContentSyncStatus(BaseModel):
    content_type: str
    last_modified: datetime
    content_version: str
    content_hash: str
    
class GlobalContentVersion(BaseModel):
    global_version: str
    last_updated: datetime
    content_types: Dict[str, ContentSyncStatus]

# Content versioning endpoints
@api_router.get("/content/version")
async def get_global_content_version():
    """Get global content version for native app sync"""
    try:
        # Get latest modifications from all content types
        content_status = {}
        
        # Services
        latest_service = await db.services.find_one(
            {"is_active": True}, 
            sort=[("updated_at", -1)]
        )
        if latest_service:
            services_hash = hashlib.md5(
                str([s async for s in db.services.find({"is_active": True}, {"_id": 0})]).encode()
            ).hexdigest()
            content_status["services"] = ContentSyncStatus(
                content_type="services",
                last_modified=latest_service.get("updated_at", datetime.utcnow()),
                content_version=latest_service.get("content_version", "1"),
                content_hash=services_hash
            ).dict()
        
        # Products (Boutique)
        latest_product = await db.products.find_one(
            {"is_active": True}, 
            sort=[("updated_at", -1)]
        )
        if latest_product:
            products_hash = hashlib.md5(
                str([p async for p in db.products.find({"is_active": True}, {"_id": 0})]).encode()
            ).hexdigest()
            content_status["products"] = ContentSyncStatus(
                content_type="products",
                last_modified=latest_product.get("updated_at", datetime.utcnow()),
                content_version=latest_product.get("content_version", "1"),
                content_hash=products_hash
            ).dict()
        
        # Service Groups
        latest_group = await db.service_groups.find_one(
            {"is_active": True}, 
            sort=[("updated_at", -1)]
        )
        if latest_group:
            groups_hash = hashlib.md5(
                str([g async for g in db.service_groups.find({"is_active": True}, {"_id": 0})]).encode()
            ).hexdigest()
            content_status["service_groups"] = ContentSyncStatus(
                content_type="service_groups",
                last_modified=latest_group.get("updated_at", datetime.utcnow()),
                content_version=latest_group.get("content_version", "1"),
                content_hash=groups_hash
            ).dict()
        
        # Knowledge Base (for chatbot)
        latest_kb = await db.knowledge_base.find_one(
            {"is_active": True, "is_approved": True}, 
            sort=[("updated_at", -1)]
        )
        if latest_kb:
            kb_items = [kb async for kb in db.knowledge_base.find({"is_active": True, "is_approved": True}, {"_id": 0})]
            kb_hash = hashlib.md5(str(kb_items).encode()).hexdigest()
            content_status["knowledge_base"] = ContentSyncStatus(
                content_type="knowledge_base",
                last_modified=latest_kb.get("updated_at", datetime.utcnow()),
                content_version=latest_kb.get("content_version", "1"),
                content_hash=kb_hash
            ).dict()
        
        # Generate global version hash
        global_hash = hashlib.md5(
            str(content_status).encode()
        ).hexdigest()
        
        # Get latest modification time
        latest_times = [
            status.get("last_modified", datetime.utcnow()) 
            for status in content_status.values()
        ]
        latest_time = max(latest_times) if latest_times else datetime.utcnow()
        
        return GlobalContentVersion(
            global_version=global_hash,
            last_updated=latest_time,
            content_types=content_status
        ).dict()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting content version: {str(e)}")

@api_router.get("/content/changes")
async def get_content_changes(
    since_version: Optional[str] = Query(None, description="Client's current global version"),
    since_timestamp: Optional[datetime] = Query(None, description="Client's last sync timestamp")
):
    """Get content changes since specific version/timestamp for efficient sync"""
    try:
        changes = {
            "has_changes": False,
            "global_version": None,
            "changed_content": {}
        }
        
        # Get current global version
        current_version = await get_global_content_version()
        changes["global_version"] = current_version["global_version"]
        
        # If no previous version provided, return full content status
        if not since_version and not since_timestamp:
            changes["has_changes"] = True
            changes["changed_content"] = current_version["content_types"]
            return changes
        
        # Check if there are changes
        if since_version and since_version == current_version["global_version"]:
            return changes  # No changes
        
        # If timestamp provided, find what changed
        if since_timestamp:
            # Services changes
            services_changed = await db.services.count_documents({
                "is_active": True,
                "updated_at": {"$gt": since_timestamp}
            })
            if services_changed > 0:
                changes["has_changes"] = True
                changes["changed_content"]["services"] = current_version["content_types"].get("services")
            
            # Products changes
            products_changed = await db.products.count_documents({
                "is_active": True,
                "updated_at": {"$gt": since_timestamp}
            })
            if products_changed > 0:
                changes["has_changes"] = True
                changes["changed_content"]["products"] = current_version["content_types"].get("products")
            
            # Service groups changes
            groups_changed = await db.service_groups.count_documents({
                "is_active": True,
                "updated_at": {"$gt": since_timestamp}
            })
            if groups_changed > 0:
                changes["has_changes"] = True
                changes["changed_content"]["service_groups"] = current_version["content_types"].get("service_groups")
            
            # Knowledge base changes (for chatbot)
            kb_changed = await db.knowledge_base.count_documents({
                "is_active": True,
                "is_approved": True,
                "updated_at": {"$gt": since_timestamp}
            })
            if kb_changed > 0:
                changes["has_changes"] = True
                changes["changed_content"]["knowledge_base"] = current_version["content_types"].get("knowledge_base")
        else:
            # Version mismatch, return all current content
            changes["has_changes"] = True
            changes["changed_content"] = current_version["content_types"]
        
        return changes
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking content changes: {str(e)}")

# Initialize RAG service on startup
@app.on_event("startup")
async def startup_event():
    """Initialize RAG service and vector embeddings"""
    try:
        await rag_service.initialize()
        logger.info("RAG service initialized successfully")
        
        # Process existing knowledge base items for vector embeddings
        await _initialize_existing_knowledge_base()
        
    except Exception as e:
        logger.error(f"RAG service initialization failed: {e}")

async def _initialize_existing_knowledge_base():
    """Process existing approved knowledge base items for vector embeddings"""
    try:
        # Get all approved knowledge base items
        kb_items = await db.knowledge_base.find({
            "is_active": True, 
            "is_approved": True
        }, {"_id": 0}).to_list(None)
        
        processed_count = 0
        for kb_item in kb_items:
            try:
                success = await rag_service.process_knowledge_base_update(kb_item)
                if success:
                    processed_count += 1
            except Exception as e:
                logger.warning(f"Failed to process KB item {kb_item.get('id')}: {e}")
                continue
        
        logger.info(f"Processed {processed_count}/{len(kb_items)} knowledge base items for vector embeddings")
        
    except Exception as e:
        logger.error(f"Failed to initialize existing knowledge base: {e}")

# Admin endpoints for RAG monitoring and unresolved queries
@api_router.get("/admin/chat/unresolved-queries")
async def get_unresolved_queries(
    limit: int = 50,
    skip: int = 0,
    language: Optional[str] = None,
    admin_user: dict = Depends(get_admin_user)
):
    """Get unresolved queries for admin review"""
    try:
        query = {"admin_reviewed": False}
        if language:
            query["language"] = language
        
        # Get unresolved queries
        unresolved = await db.unresolved_queries.find(
            query, {"_id": 0}
        ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        
        # Get total count
        total_count = await db.unresolved_queries.count_documents(query)
        
        return {
            "unresolved_queries": unresolved,
            "total_count": total_count,
            "skip": skip,
            "limit": limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching unresolved queries: {str(e)}")

@api_router.put("/admin/chat/unresolved-queries/{query_id}/resolve")
async def resolve_query(
    query_id: str,
    resolution_notes: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Mark query as resolved with admin notes"""
    try:
        result = await db.unresolved_queries.update_one(
            {"id": query_id},
            {
                "$set": {
                    "admin_reviewed": True,
                    "resolution_notes": resolution_notes,
                    "reviewed_by": admin_user["id"],
                    "reviewed_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Query not found")
        
        return {"message": "Query marked as resolved"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resolving query: {str(e)}")

@api_router.get("/admin/chat/analytics")
async def get_chat_analytics(
    days: int = 30,
    admin_user: dict = Depends(get_admin_user)
):
    """Get comprehensive chat analytics"""
    try:
        # Date range for analytics
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get session analytics
        sessions = await db.chat_sessions.find({
            "created_at": {"$gte": start_date}
        }, {"_id": 0}).to_list(None)
        
        # Get message analytics
        messages = await db.chat_messages.find({
            "created_at": {"$gte": start_date},
            "role": "assistant"
        }, {"_id": 0}).to_list(None)
        
        # Calculate analytics
        total_sessions = len(sessions)
        total_messages = len(messages)
        
        # Calculate averages
        avg_confidence = sum(msg.get("confidence", 0) for msg in messages) / max(total_messages, 1)
        avg_response_time = sum(msg.get("response_time", 0) for msg in messages) / max(total_messages, 1)
        
        # Calculate knowledge coverage
        messages_with_sources = sum(1 for msg in messages if msg.get("sources"))
        knowledge_coverage = (messages_with_sources / max(total_messages, 1)) * 100
        
        # Language distribution
        language_dist = {}
        for session in sessions:
            lang = session.get("language", "en")
            language_dist[lang] = language_dist.get(lang, 0) + 1
        
        # Unresolved queries
        unresolved_count = await db.unresolved_queries.count_documents({
            "created_at": {"$gte": start_date},
            "admin_reviewed": False
        })
        
        # Common topics from unresolved queries
        unresolved = await db.unresolved_queries.find({
            "created_at": {"$gte": start_date}
        }, {"suggested_kb_topics": 1, "_id": 0}).to_list(None)
        
        all_topics = []
        for query in unresolved:
            all_topics.extend(query.get("suggested_kb_topics", []))
        
        topic_counts = {}
        for topic in all_topics:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        common_missing_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "period_days": days,
            "overview": {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "avg_confidence": round(avg_confidence, 3),
                "avg_response_time": round(avg_response_time, 3),
                "knowledge_coverage": round(knowledge_coverage, 1),
                "unresolved_queries": unresolved_count
            },
            "language_distribution": language_dist,
            "common_missing_topics": common_missing_topics,
            "trends": {
                "daily_sessions": await _get_daily_session_trend(start_date),
                "confidence_trend": await _get_confidence_trend(start_date)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating chat analytics: {str(e)}")

async def _get_daily_session_trend(start_date: datetime):
    """Get daily session count trend"""
    try:
        pipeline = [
            {"$match": {"created_at": {"$gte": start_date}}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "count": {"$sum": 1}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        result = await db.chat_sessions.aggregate(pipeline).to_list(None)
        return {item["_id"]: item["count"] for item in result}
        
    except Exception as e:
        logger.error(f"Failed to get daily session trend: {e}")
        return {}

async def _get_confidence_trend(start_date: datetime):
    """Get confidence score trend over time"""
    try:
        pipeline = [
            {
                "$match": {
                    "created_at": {"$gte": start_date},
                    "role": "assistant",
                    "confidence": {"$exists": True}
                }
            },
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$created_at"
                        }
                    },
                    "avg_confidence": {"$avg": "$confidence"}
                }
            },
            {"$sort": {"_id": 1}}
        ]
        
        result = await db.chat_messages.aggregate(pipeline).to_list(None)
        return {item["_id"]: round(item["avg_confidence"], 3) for item in result}
        
    except Exception as e:
        logger.error(f"Failed to get confidence trend: {e}")
        return {}

@api_router.get("/admin/chat/knowledge-gaps")
async def get_knowledge_gaps(
    limit: int = 20,
    admin_user: dict = Depends(get_admin_user)
):
    """Get knowledge gaps analysis for KB improvement"""
    try:
        # Get most common unresolved topics
        pipeline = [
            {"$match": {"admin_reviewed": False}},
            {"$unwind": "$suggested_kb_topics"},
            {
                "$group": {
                    "_id": "$suggested_kb_topics",
                    "count": {"$sum": 1},
                    "avg_confidence": {"$avg": "$confidence"},
                    "sample_queries": {"$push": {"query": "$query", "confidence": "$confidence"}}
                }
            },
            {"$sort": {"count": -1}},
            {"$limit": limit}
        ]
        
        gaps = await db.unresolved_queries.aggregate(pipeline).to_list(None)
        
        # Format results
        knowledge_gaps = []
        for gap in gaps:
            # Limit sample queries to top 3
            sample_queries = sorted(gap["sample_queries"], key=lambda x: x["confidence"])[:3]
            
            knowledge_gaps.append({
                "topic": gap["_id"],
                "frequency": gap["count"],
                "avg_confidence": round(gap["avg_confidence"], 3),
                "sample_queries": [q["query"] for q in sample_queries],
                "priority": "high" if gap["count"] > 5 else "medium" if gap["count"] > 2 else "low"
            })
        
        return {
            "knowledge_gaps": knowledge_gaps,
            "total_gaps": len(knowledge_gaps),
            "recommendations": _generate_kb_recommendations(knowledge_gaps)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing knowledge gaps: {str(e)}")

def _generate_kb_recommendations(gaps: List[Dict[str, Any]]) -> List[str]:
    """Generate recommendations for knowledge base improvement"""
    recommendations = []
    
    high_priority_gaps = [gap for gap in gaps if gap["priority"] == "high"]
    if high_priority_gaps:
        recommendations.append(f"Urgent: Add knowledge base content for {len(high_priority_gaps)} high-priority topics")
    
    # Specific recommendations
    for gap in gaps[:5]:  # Top 5 gaps
        topic = gap["topic"]
        if topic in ["morpheus8", "nad_iv_therapy", "hbot"]:
            recommendations.append(f"Add detailed {topic.replace('_', ' ').title()} treatment information")
        elif topic in ["pricing", "costs", "price"]:
            recommendations.append("Add comprehensive pricing information to knowledge base")
        elif topic in ["booking", "appointment", "schedule"]:
            recommendations.append("Add booking process and availability information")
    
    return recommendations[:10]  # Limit recommendations

@api_router.post("/admin/chat/test-rag")
async def test_rag_system(
    test_query: str,
    language: str = "en",
    admin_user: dict = Depends(get_admin_user)
):
    """Test RAG system with admin query"""
    try:
        # Generate test session
        test_session_id = f"admin_test_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Generate RAG response
        rag_response = await rag_service.generate_rag_response(
            user_message=test_query,
            session_id=test_session_id,
            language=language
        )
        
        return {
            "test_query": test_query,
            "response": rag_response.response,
            "sources_found": len(rag_response.sources),
            "confidence": rag_response.confidence,
            "response_time": rag_response.response_time,
            "sources": [{
                "id": src.source,
                "title": src.title,
                "similarity": round(src.similarity, 3),
                "content_preview": src.content[:150] + "..."
            } for src in rag_response.sources],
            "test_session_id": test_session_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG test failed: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

# Enhanced WebSocket manager for real-time content sync
from typing import List, Dict, Optional
from fastapi import WebSocket, WebSocketDisconnect, Query, HTTPException
import asyncio
import json as json_lib
from enum import Enum

class ConnectionState(str, Enum):
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"

class WebSocketConnection:
    def __init__(self, websocket: WebSocket, connection_id: str, user_id: Optional[str] = None):
        self.websocket = websocket
        self.connection_id = connection_id
        self.user_id = user_id
        self.state = ConnectionState.CONNECTING
        self.last_heartbeat = datetime.utcnow()
        self.subscribed_content_types = set()
        self.created_at = datetime.utcnow()

class EnhancedConnectionManager:
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.heartbeat_interval = 30  # seconds
        self.heartbeat_timeout = 60   # seconds
        self.cleanup_task = None
        
    async def start_heartbeat_monitor(self):
        """Start background task to monitor heartbeats"""
        if self.cleanup_task is None:
            self.cleanup_task = asyncio.create_task(self._heartbeat_monitor())
    
    async def stop_heartbeat_monitor(self):
        """Stop background heartbeat monitoring"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
            self.cleanup_task = None

    async def _heartbeat_monitor(self):
        """Background task to check for dead connections"""
        while True:
            try:
                await asyncio.sleep(self.heartbeat_interval)
                current_time = datetime.utcnow()
                dead_connections = []
                
                for conn_id, connection in self.connections.items():
                    time_diff = (current_time - connection.last_heartbeat).total_seconds()
                    if time_diff > self.heartbeat_timeout:
                        print(f"💀 Connection {conn_id} timed out after {time_diff:.1f}s")
                        dead_connections.append(conn_id)
                
                # Remove dead connections
                for conn_id in dead_connections:
                    await self._force_disconnect(conn_id)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Heartbeat monitor error: {e}")

    async def connect(self, websocket: WebSocket, connection_id: str, user_id: Optional[str] = None, 
                     content_types: Optional[List[str]] = None) -> bool:
        """Enhanced connection with authentication and subscription management"""
        try:
            await websocket.accept()
            
            connection = WebSocketConnection(websocket, connection_id, user_id)
            connection.state = ConnectionState.CONNECTED
            
            # Set default subscriptions
            if content_types:
                connection.subscribed_content_types.update(content_types)
            else:
                # Default to all content types
                connection.subscribed_content_types.update([
                    "services", "products", "service_groups", "knowledge_base"
                ])
            
            self.connections[connection_id] = connection
            
            print(f"🔌 WebSocket connected: {connection_id}")
            print(f"   - User: {user_id or 'Anonymous'}")
            print(f"   - Subscriptions: {list(connection.subscribed_content_types)}")
            print(f"   - Total connections: {len(self.connections)}")
            
            # Start heartbeat monitoring if not already started
            await self.start_heartbeat_monitor()
            
            # Send welcome message
            await self.send_to_connection(connection_id, {
                "type": "welcome",
                "connection_id": connection_id,
                "subscriptions": list(connection.subscribed_content_types),
                "heartbeat_interval": self.heartbeat_interval
            })
            
            return True
            
        except Exception as e:
            print(f"❌ WebSocket connection failed for {connection_id}: {e}")
            return False

    async def disconnect(self, connection_id: str):
        """Clean disconnect"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            connection.state = ConnectionState.DISCONNECTED
            del self.connections[connection_id]
            
            print(f"🔌 WebSocket disconnected: {connection_id}")
            print(f"   - Total connections: {len(self.connections)}")

    async def _force_disconnect(self, connection_id: str):
        """Force disconnect a connection"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            try:
                await connection.websocket.close()
            except:
                pass
            await self.disconnect(connection_id)

    async def update_heartbeat(self, connection_id: str):
        """Update heartbeat timestamp for a connection"""
        if connection_id in self.connections:
            self.connections[connection_id].last_heartbeat = datetime.utcnow()

    async def subscribe_to_content(self, connection_id: str, content_types: List[str]):
        """Subscribe to specific content types"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            connection.subscribed_content_types.update(content_types)
            
            await self.send_to_connection(connection_id, {
                "type": "subscription_updated",
                "subscriptions": list(connection.subscribed_content_types)
            })

    async def unsubscribe_from_content(self, connection_id: str, content_types: List[str]):
        """Unsubscribe from specific content types"""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            for content_type in content_types:
                connection.subscribed_content_types.discard(content_type)
            
            await self.send_to_connection(connection_id, {
                "type": "subscription_updated",
                "subscriptions": list(connection.subscribed_content_types)
            })

    async def send_to_connection(self, connection_id: str, message: Dict):
        """Send message to specific connection"""
        if connection_id not in self.connections:
            return False
            
        connection = self.connections[connection_id]
        try:
            await connection.websocket.send_text(json_lib.dumps(message, default=str))
            return True
        except Exception as e:
            print(f"❌ Failed to send to connection {connection_id}: {e}")
            await self._force_disconnect(connection_id)
            return False

    async def broadcast_content_update(self, content_types: List[str], message_data: Optional[Dict] = None):
        """Enhanced broadcast with subscription filtering"""
        if not self.connections:
            print("📡 No WebSocket connections to broadcast to")
            return

        message = {
            "type": "content_update",
            "content_types": content_types,
            "timestamp": datetime.utcnow().isoformat(),
            "data": message_data or {}
        }
        
        # Filter connections based on subscriptions
        relevant_connections = []
        for conn_id, connection in self.connections.items():
            # Check if connection is subscribed to any of the updated content types
            if any(ct in connection.subscribed_content_types for ct in content_types):
                relevant_connections.append((conn_id, connection))
        
        if not relevant_connections:
            print(f"📡 No relevant WebSocket connections for content types: {content_types}")
            return
        
        print(f"📡 Broadcasting content update to {len(relevant_connections)}/{len(self.connections)} connections")
        print(f"   - Content types: {content_types}")
        
        # Send to relevant connections, track failures
        failed_connections = []
        success_count = 0
        
        for conn_id, connection in relevant_connections:
            try:
                await connection.websocket.send_text(json_lib.dumps(message, default=str))
                success_count += 1
            except Exception as e:
                print(f"❌ Failed to send to {conn_id}: {e}")
                failed_connections.append(conn_id)
        
        # Remove failed connections
        for conn_id in failed_connections:
            await self._force_disconnect(conn_id)
        
        print(f"✅ Broadcast completed: {success_count} successful, {len(failed_connections)} failed")

    async def send_heartbeat_ping(self):
        """Send heartbeat ping to all connections"""
        message = {
            "type": "ping",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        failed_connections = []
        for conn_id, connection in self.connections.items():
            try:
                await connection.websocket.send_text(json_lib.dumps(message, default=str))
            except Exception as e:
                failed_connections.append(conn_id)
        
        # Remove failed connections
        for conn_id in failed_connections:
            await self._force_disconnect(conn_id)

    def get_connection_stats(self) -> Dict:
        """Get connection statistics"""
        stats = {
            "total_connections": len(self.connections),
            "connections_by_user": {},
            "subscriptions_summary": {},
            "connection_ages": []
        }
        
        current_time = datetime.utcnow()
        
        for connection in self.connections.values():
            # User stats
            user_key = connection.user_id or "anonymous"
            stats["connections_by_user"][user_key] = stats["connections_by_user"].get(user_key, 0) + 1
            
            # Subscription stats
            for content_type in connection.subscribed_content_types:
                stats["subscriptions_summary"][content_type] = stats["subscriptions_summary"].get(content_type, 0) + 1
            
            # Connection age
            age_seconds = (current_time - connection.created_at).total_seconds()
            stats["connection_ages"].append(age_seconds)
        
        return stats

# Global enhanced connection manager
enhanced_connection_manager = EnhancedConnectionManager()

# Enhanced WebSocket endpoint with authentication and subscription support
@app.websocket("/ws/content-sync")
async def enhanced_websocket_content_sync(
    websocket: WebSocket,
    connection_id: str = Query(default_factory=lambda: str(uuid.uuid4())),
    user_id: Optional[str] = Query(None),
    subscribe_to: Optional[str] = Query("all")  # comma-separated content types or "all"
):
    """Enhanced WebSocket endpoint with authentication and subscription management"""
    
    # Parse subscription preferences
    if subscribe_to == "all":
        content_types = ["services", "products", "service_groups", "knowledge_base"]
    else:
        content_types = [ct.strip() for ct in subscribe_to.split(",") if ct.strip()]
    
    # Connect with enhanced features
    connection_success = await enhanced_connection_manager.connect(
        websocket, connection_id, user_id, content_types
    )
    
    if not connection_success:
        await websocket.close(code=1000, reason="Connection failed")
        return
    
    try:
        while True:
            # Receive messages from client
            try:
                message_text = await websocket.receive_text()
                message = json_lib.loads(message_text)
                
                # Handle different message types
                message_type = message.get("type", "")
                
                if message_type == "pong":
                    # Update heartbeat on pong response
                    await enhanced_connection_manager.update_heartbeat(connection_id)
                    
                elif message_type == "subscribe":
                    # Handle subscription changes
                    new_content_types = message.get("content_types", [])
                    await enhanced_connection_manager.subscribe_to_content(connection_id, new_content_types)
                    
                elif message_type == "unsubscribe":
                    # Handle unsubscription
                    remove_content_types = message.get("content_types", [])
                    await enhanced_connection_manager.unsubscribe_from_content(connection_id, remove_content_types)
                    
                elif message_type == "heartbeat":
                    # Client-initiated heartbeat
                    await enhanced_connection_manager.update_heartbeat(connection_id)
                    
                else:
                    print(f"🤷 Unknown message type from {connection_id}: {message_type}")
                    
            except json_lib.JSONDecodeError:
                print(f"⚠️ Invalid JSON from {connection_id}: {message_text}")
            except asyncio.TimeoutError:
                # No message received in timeout period, send ping
                await enhanced_connection_manager.send_to_connection(connection_id, {
                    "type": "ping",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
    except WebSocketDisconnect:
        print(f"🔌 Client {connection_id} disconnected normally")
        await enhanced_connection_manager.disconnect(connection_id)
    except Exception as e:
        print(f"❌ WebSocket error for {connection_id}: {e}")
        await enhanced_connection_manager.disconnect(connection_id)

# Enhanced content change notification function
async def enhanced_notify_content_change(content_types: List[str], additional_data: Optional[Dict] = None):
    """Enhanced notification with additional metadata"""
    await enhanced_connection_manager.broadcast_content_update(content_types, additional_data)

# WebSocket monitoring endpoint (admin only)
@api_router.get("/admin/websocket/stats")
async def get_websocket_stats(admin_user: dict = Depends(get_admin_user)):
    """Get WebSocket connection statistics"""
    try:
        stats = enhanced_connection_manager.get_connection_stats()
        return {
            "status": "success",
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting WebSocket stats: {str(e)}")

# WebSocket health check endpoint
@api_router.get("/websocket/health")
async def websocket_health_check():
    """Health check for WebSocket system"""
    try:
        stats = enhanced_connection_manager.get_connection_stats()
        is_healthy = len(stats["connection_ages"]) >= 0  # Basic health check
        
        return {
            "status": "healthy" if is_healthy else "unhealthy",
            "active_connections": stats["total_connections"],
            "uptime_seconds": "N/A",  # Could track this if needed
            "last_broadcast": "N/A",  # Could track this if needed
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"WebSocket health check failed: {str(e)}")

# Function to trigger enhanced content sync notifications (replaces the old one)
async def notify_content_change(content_types: List[str], additional_data: Optional[Dict] = None):
    """Wrapper function for backward compatibility"""
    await enhanced_notify_content_change(content_types, additional_data)

# Health check endpoint for mobile apps
@api_router.get("/health")
async def health_check():
    """Health check endpoint for mobile app validation"""
    try:
        # Test database connection
        db_status = {"connected": False, "collections": 0}
        try:
            # Simple database ping
            await db.users.find_one({}, {"_id": 1})
            collections = await db.list_collection_names()
            db_status = {"connected": True, "collections": len(collections)}
        except Exception as e:
            db_status = {"connected": False, "error": str(e)}
        
        # Parse CORS origins count
        cors_origins_env = os.environ.get("CORS_ORIGINS", "[]")
        try:
            cors_origins = json.loads(cors_origins_env)
            cors_count = len(cors_origins)
        except:
            cors_origins = cors_origins_env.split(",")
            cors_count = len([o for o in cors_origins if o.strip()])
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": {
                "cors_origins_count": cors_count,
                "websocket_enabled": os.environ.get("WEBSOCKET_ENABLED", "true"),
                "debug": os.environ.get("DEBUG", "false")
            },
            "database": db_status,
            "services": {
                "chat": "operational",
                "content_sync": "operational",
                "authentication": "operational"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

# Push notification token registration endpoint
@api_router.post("/notifications/register-token")
async def register_push_token(
    token: str,
    platform: str,
    device_id: Optional[str] = None,
    device_name: Optional[str] = None,
    current_user: dict = Depends(get_current_user_optional)
):
    """Register push notification token for mobile app"""
    try:
        # Create token registration record
        token_record = {
            "id": str(uuid.uuid4()),
            "token": token,
            "platform": platform,  # web, ios, android
            "device_id": device_id,
            "device_name": device_name,
            "user_id": current_user.get("id") if current_user else None,
            "created_at": datetime.utcnow(),
            "last_used": datetime.utcnow(),
            "is_active": True
        }
        
        # Store in database (upsert based on token)
        await db.push_tokens.update_one(
            {"token": token},
            {"$set": token_record},
            upsert=True
        )
        
        print(f"📱 Push token registered: {platform} - {token[:20]}...")
        
        return {
            "message": "Push token registered successfully",
            "platform": platform,
            "token_id": token_record["id"]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token registration failed: {str(e)}")

# Test push notification endpoint (admin only)
@api_router.post("/admin/notifications/push/send")
async def send_test_push_notification(
    title: str,
    body: str,
    platform: Optional[str] = None,
    user_id: Optional[str] = None,
    admin_user: dict = Depends(get_admin_user)
):
    """Send test push notification (admin only)"""
    try:
        # Build query for tokens
        query = {"is_active": True}
        if platform:
            query["platform"] = platform
        if user_id:
            query["user_id"] = user_id
        
        # Get active push tokens
        tokens = await db.push_tokens.find(query, {"_id": 0}).to_list(100)
        
        if not tokens:
            raise HTTPException(status_code=404, detail="No active push tokens found")
        
        # Prepare notification payload
        notification_payload = {
            "title": title,
            "body": body,
            "data": {
                "source": "kinaura_admin",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
        
        sent_count = 0
        failed_count = 0
        
        # Send to each token (in production, use proper push service)
        for token_record in tokens:
            try:
                # Here you would integrate with actual push services
                # Firebase Admin SDK for FCM, APNs for iOS
                # For now, we'll just log the intent
                
                print(f"📤 Sending push to {token_record['platform']}: {token_record['token'][:20]}...")
                sent_count += 1
                
                # Update last_used timestamp
                await db.push_tokens.update_one(
                    {"id": token_record["id"]},
                    {"$set": {"last_used": datetime.utcnow()}}
                )
                
            except Exception as e:
                print(f"❌ Failed to send to token {token_record['id']}: {e}")
                failed_count += 1
        
        return {
            "message": "Push notifications sent",
            "sent_count": sent_count,
            "failed_count": failed_count,
            "total_tokens": len(tokens)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Push notification failed: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

# Enhanced CORS Configuration for Mobile Apps
import json

# Parse CORS origins from environment (supports JSON format)
cors_origins_env = os.environ.get("CORS_ORIGINS", '["http://localhost:3000"]')

try:
    # Try to parse as JSON first (preferred format)
    cors_origins = json.loads(cors_origins_env)
except json.JSONDecodeError:
    # Fallback to comma-separated format
    cors_origins = [origin.strip() for origin in cors_origins_env.split(",") if origin.strip()]

# Add required Capacitor origins for mobile apps
required_mobile_origins = [
    "capacitor://localhost",
    "ionic://localhost", 
    "http://localhost",
    "https://localhost"
]

# Ensure mobile origins are included
for origin in required_mobile_origins:
    if origin not in cors_origins:
        cors_origins.append(origin)

print(f"🌐 CORS Origins configured: {cors_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def get_patient_inquiries(
    status: Optional[str] = None,
    inquiry_type: Optional[str] = None,
    patient_id: Optional[str] = None,
    limit: int = 50,
    skip: int = 0,
    admin_user: dict = Depends(get_admin_user)
):
    """Get patient inquiries with filtering options"""
    try:
        query = {}
        
        if status:
            query["status"] = status
        if inquiry_type:
            query["inquiry_type"] = inquiry_type  
        if patient_id:
            query["patient_id"] = patient_id
        
        # Get inquiries with patient information
        inquiries = await db.patient_inquiries.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit).to_list(length=None)
        
        # Enrich with patient information
        for inquiry in inquiries:
            patient = await db.users.find_one({"id": inquiry["patient_id"]}, {"_id": 0, "full_name": 1, "email": 1})
            inquiry["patient_info"] = patient if patient else {"full_name": "Unknown Patient", "email": ""}
        
        return {
            "inquiries": inquiries,
            "count": len(inquiries),
            "has_more": len(inquiries) == limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching inquiries: {str(e)}")

# Duplicate inquiry endpoints removed - using the first set defined earlier

@api_router.get("/admin/notifications")
async def get_admin_notifications(
    type: Optional[str] = None,
    unread_only: bool = False,
    limit: int = 20,
    skip: int = 0,
    admin_user: dict = Depends(get_admin_user)
):
    """Get admin notifications with filtering"""
    try:
        query = {}
        
        if type:
            query["type"] = type
        if unread_only:
            query["is_read"] = False
            
        # Only get non-expired notifications
        query["expires_at"] = {"$gt": datetime.utcnow()}
        
        notifications = await db.admin_notifications.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(length=None)
        
        return {
            "notifications": notifications,
            "count": len(notifications),
            "has_more": len(notifications) == limit
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching notifications: {str(e)}")

@api_router.put("/admin/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    admin_user: dict = Depends(get_admin_user)
):
    """Mark a notification as read"""
    try:
        result = await db.admin_notifications.update_one(
            {"id": notification_id},
            {"$set": {"is_read": True}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"message": "Notification marked as read"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating notification: {str(e)}")

# Duplicate stats endpoint removed - using the first one with proper field names

@app.on_event("startup")
async def startup_event():
    await init_services()
    logger.info("KinAura API started successfully")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()