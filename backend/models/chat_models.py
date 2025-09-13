# Enhanced Chat Models for Production RAG System

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    role: MessageRole
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # RAG-specific fields
    sources: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    confidence: Optional[float] = None
    response_time: Optional[float] = None
    language: str = "en"

class ChatSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: Optional[str] = None
    patient_id: Optional[str] = None
    language: str = "en"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Session metadata
    total_messages: int = 0
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    session_context: Dict[str, Any] = Field(default_factory=dict)
    
    # Analytics
    avg_confidence: Optional[float] = None
    total_sources_used: int = 0
    common_topics: List[str] = Field(default_factory=list)

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000)
    session_id: Optional[str] = None
    language: Optional[str] = "en"
    include_sources: bool = True
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

class UnresolvedQuery(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    query: str
    session_id: str
    user_id: Optional[str] = None
    language: str
    attempted_response: str
    confidence: float
    context_found: bool
    suggested_kb_topics: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    admin_reviewed: bool = False
    resolution_notes: Optional[str] = None

class ChatAnalytics(BaseModel):
    session_id: str
    total_queries: int = 0
    avg_response_time: float = 0.0
    avg_confidence: float = 0.0
    knowledge_coverage: float = 0.0  # % of queries with good KB matches
    common_topics: List[str] = Field(default_factory=list)
    unresolved_count: int = 0
    languages_used: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)