"""
AI创作工坊 - Pydantic Schemas

Request/response models for all API endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


# ─── Video ────────────────────────────────────────────────────

class VideoStyle(str, Enum):
    CINEMATIC = "cinematic"
    ANIMATED = "animated"
    MINIMALIST = "minimalist"
    REALISTIC = "realistic"
    CARTOON = "cartoon"


class VideoRequest(BaseModel):
    """Request to generate a video."""
    title: str = Field(..., min_length=1, max_length=200, description="Video title/topic")
    style: VideoStyle = Field(default=VideoStyle.CINEMATIC, description="Visual style")
    duration: int = Field(default=30, ge=5, le=300, description="Duration in seconds")
    description: Optional[str] = Field(default=None, max_length=2000, description="Detailed description")
    voiceover: bool = Field(default=True, description="Include AI voiceover")
    background_music: bool = Field(default=True, description="Include background music")


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class VideoTask(BaseModel):
    """Video generation task status."""
    task_id: str
    status: TaskStatus
    title: str
    style: VideoStyle
    duration: int
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    video_url: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    estimated_completion: Optional[datetime] = None


# ─── Comments ─────────────────────────────────────────────────

class Sentiment(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    MIXED = "mixed"


class CommentAnalysis(BaseModel):
    """Result of comment analysis."""
    text: str
    sentiment: Sentiment
    sentiment_score: float = Field(ge=-1.0, le=1.0)
    intent: str
    topics: list[str] = []
    language: str = "en"
    is_question: bool = False
    urgency: str = "low"


class CommentAnalyzeRequest(BaseModel):
    """Request to analyze a comment."""
    text: str = Field(..., min_length=1, max_length=5000)
    context: Optional[str] = Field(default=None, description="Additional context")


class ReplyRequest(BaseModel):
    """Request to generate a reply to a comment."""
    comment: str = Field(..., min_length=1, max_length=5000)
    tone: str = Field(default="professional", description="Reply tone")
    max_length: int = Field(default=200, ge=10, le=1000)
    context: Optional[str] = None


class ReplyResponse(BaseModel):
    """Generated reply."""
    reply: str
    tone: str
    generated_at: datetime


class CommentDashboard(BaseModel):
    """Comment analytics dashboard data."""
    total_comments: int
    sentiment_distribution: dict[str, int]
    top_topics: list[dict[str, Any]]
    average_sentiment_score: float
    questions_count: int
    period: str


# ─── Knowledge / RAG ──────────────────────────────────────────

class KnowledgeQuery(BaseModel):
    """RAG query request."""
    question: str = Field(..., min_length=1, max_length=5000)
    collection: Optional[str] = None
    top_k: int = Field(default=5, ge=1, le=20)
    use_reranker: bool = True


class KnowledgeAnswer(BaseModel):
    """RAG query response."""
    answer: str
    sources: list[dict[str, Any]]
    question: str
    documents_used: int
    duration_seconds: float


class IngestRequest(BaseModel):
    """Document ingestion request."""
    content: str = Field(..., min_length=1)
    source: str = Field(default="manual")
    title: Optional[str] = None
    collection: Optional[str] = None


class IngestResponse(BaseModel):
    """Document ingestion response."""
    documents_processed: int
    chunks_created: int
    duration_seconds: float


class CollectionInfo(BaseModel):
    """Vector collection metadata."""
    name: str
    document_count: int
    created_at: Optional[datetime] = None


# ─── Admin ────────────────────────────────────────────────────

class UserStats(BaseModel):
    """Platform usage statistics."""
    total_users: int
    active_users_today: int
    total_tasks: int
    tasks_today: int
    total_tokens_used: int
    total_cost_usd: float
    top_models: list[dict[str, Any]]


class AuditLogEntry(BaseModel):
    """Audit log entry."""
    timestamp: datetime
    user_id: str
    action: str
    resource: str
    details: dict[str, Any] = {}
    ip_address: Optional[str] = None


class ConfigUpdate(BaseModel):
    """Configuration update request."""
    key: str
    value: Any
    description: Optional[str] = None


# ─── Common ───────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: list[Any]
    total: int
    page: int = 1
    page_size: int = 20
    has_more: bool = False


class ErrorResponse(BaseModel):
    """Standard error response."""
    detail: str
    correlation_id: Optional[str] = None
    error_type: Optional[str] = None
