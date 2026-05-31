"""
AI创作工坊 - Comment Analysis API Router

Endpoints for sentiment analysis, smart reply generation, and comment analytics.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException

from inference.llm_client import LLMClient
from models.schemas import (
    CommentAnalyzeRequest, CommentAnalysis, CommentDashboard,
    ReplyRequest, ReplyResponse, Sentiment,
)
from security.auth import UserContext, get_current_user
from security.guardrails import guardrails
from observability.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

_llm_client: LLMClient | None = None


def _get_llm() -> LLMClient:
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


@router.post(
    "/analyze",
    response_model=CommentAnalysis,
    summary="Analyze a comment",
)
async def analyze_comment(
    request: CommentAnalyzeRequest,
    user: UserContext = Depends(get_current_user),
) -> CommentAnalysis:
    """
    Analyze a comment for sentiment, intent, topics, and urgency.
    Uses LLM for nuanced analysis with guardrails for safety.
    """
    is_safe, safe_text = guardrails.safe_process(request.text)
    if not is_safe:
        raise HTTPException(status_code=400, detail="Input failed safety checks")

    llm = _get_llm()
    prompt = f"""Analyze the following comment and return a JSON object with:
- sentiment: "positive", "negative", "neutral", or "mixed"
- sentiment_score: float from -1.0 to 1.0
- intent: brief description of what the commenter wants
- topics: list of topics mentioned
- is_question: boolean
- urgency: "low", "medium", or "high"

Comment: {safe_text}
{f"Context: {request.context}" if request.context else ""}

Return ONLY valid JSON."""

    response = await llm.generate(prompt=prompt, system="You are a comment analysis expert. Return only valid JSON.", temperature=0.1, max_tokens=500)

    try:
        import json
        data = json.loads(response.content)
    except (json.JSONDecodeError, ValueError):
        data = {
            "sentiment": "neutral", "sentiment_score": 0.0,
            "intent": "general comment", "topics": [],
            "is_question": False, "urgency": "low",
        }

    return CommentAnalysis(
        text=request.text,
        sentiment=Sentiment(data.get("sentiment", "neutral")),
        sentiment_score=data.get("sentiment_score", 0.0),
        intent=data.get("intent", "general"),
        topics=data.get("topics", []),
        is_question=data.get("is_question", False),
        urgency=data.get("urgency", "low"),
    )


@router.post(
    "/reply",
    response_model=ReplyResponse,
    summary="Generate a smart reply",
)
async def generate_reply(
    request: ReplyRequest,
    user: UserContext = Depends(get_current_user),
) -> ReplyResponse:
    """
    Generate a contextually appropriate reply to a comment.
    Supports configurable tone (professional, friendly, casual).
    """
    is_safe, safe_text = guardrails.safe_process(request.comment)
    if not is_safe:
        raise HTTPException(status_code=400, detail="Input failed safety checks")

    llm = _get_llm()
    prompt = f"""Generate a {request.tone} reply to the following comment.
Keep it under {request.max_length} characters.
{f"Context: {request.context}" if request.context else ""}

Comment: {safe_text}

Reply:"""

    response = await llm.generate(
        prompt=prompt,
        system=f"You are a helpful assistant generating {request.tone} replies to user comments. Be concise and relevant.",
        temperature=0.7,
        max_tokens=300,
    )

    return ReplyResponse(
        reply=response.content.strip(),
        tone=request.tone,
        generated_at=datetime.now(timezone.utc),
    )


@router.get(
    "/dashboard",
    response_model=CommentDashboard,
    summary="Comment analytics dashboard",
)
async def get_dashboard(
    user: UserContext = Depends(get_current_user),
) -> CommentDashboard:
    """
    Get aggregated comment analytics for the dashboard.
    Returns sentiment distribution, top topics, and key metrics.
    """
    # In production, this would query the database
    return CommentDashboard(
        total_comments=0,
        sentiment_distribution={"positive": 0, "negative": 0, "neutral": 0, "mixed": 0},
        top_topics=[],
        average_sentiment_score=0.0,
        questions_count=0,
        period="last_7_days",
    )
