"""
AI创作工坊 - Admin API Router

Endpoints for platform administration: usage stats, audit logs, config management.
"""

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from models.schemas import (
    UserStats, AuditLogEntry, ConfigUpdate, PaginatedResponse,
)
from security.auth import UserContext, require_admin
from observability.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# In-memory config store (replace with DB in production)
_config_store: dict[str, Any] = {
    "max_video_duration": 300,
    "default_llm_provider": "openai",
    "rate_limit_per_minute": 60,
    "enable_guardrails": True,
}


@router.get(
    "/stats",
    response_model=UserStats,
    summary="Platform usage statistics",
)
async def get_stats(
    admin: UserContext = Depends(require_admin),
) -> UserStats:
    """
    Get platform-wide usage statistics.
    Requires admin role.
    """
    # In production, aggregate from database
    return UserStats(
        total_users=0,
        active_users_today=0,
        total_tasks=0,
        tasks_today=0,
        total_tokens_used=0,
        total_cost_usd=0.0,
        top_models=[
            {"model": "gpt-4o-mini", "requests": 0, "cost": 0.0},
            {"model": "claude-3-5-sonnet", "requests": 0, "cost": 0.0},
        ],
    )


@router.get(
    "/audit-log",
    response_model=PaginatedResponse,
    summary="Get audit log",
)
async def get_audit_log(
    page: int = 1,
    page_size: int = 50,
    admin: UserContext = Depends(require_admin),
) -> PaginatedResponse:
    """
    Retrieve audit log entries.
    Requires admin role.
    """
    logger.info(f"Audit log accessed by admin={admin.user_id}")
    return PaginatedResponse(
        items=[],
        total=0,
        page=page,
        page_size=page_size,
        has_more=False,
    )


@router.post(
    "/config",
    summary="Update platform configuration",
)
async def update_config(
    update: ConfigUpdate,
    admin: UserContext = Depends(require_admin),
) -> dict[str, Any]:
    """
    Update a platform configuration setting.
    Requires admin role.
    """
    old_value = _config_store.get(update.key)
    _config_store[update.key] = update.value

    logger.info(
        f"Config updated: {update.key} = {update.value}",
        extra={"admin_id": admin.user_id, "old_value": old_value},
    )

    return {
        "key": update.key,
        "old_value": old_value,
        "new_value": update.value,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
