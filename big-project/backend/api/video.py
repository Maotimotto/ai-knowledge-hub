"""
AI创作工坊 - Video Generation API Router

Endpoints for async video generation, task status polling, and task listing.
"""

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from models.schemas import (
    VideoRequest, VideoTask, TaskStatus, PaginatedResponse, ErrorResponse,
)
from security.auth import UserContext, get_current_user
from observability.logger import get_logger
from observability.metrics import ACTIVE_TASKS

logger = get_logger(__name__)
router = APIRouter()

# In-memory task store (replace with DB in production)
_tasks: dict[str, dict] = {}


async def _run_video_generation(task_id: str, request: VideoRequest, user_id: str) -> None:
    """Background task: orchestrate video generation pipeline."""
    try:
        _tasks[task_id]["status"] = TaskStatus.PROCESSING
        _tasks[task_id]["updated_at"] = datetime.now(timezone.utc)
        ACTIVE_TASKS.labels(task_type="video").inc()

        # Simulate multi-step pipeline: script → storyboard → render → voiceover
        steps = ["Generating script", "Creating storyboard", "Rendering video", "Adding voiceover"]
        for i, step in enumerate(steps):
            _tasks[task_id]["progress"] = ((i + 1) / len(steps)) * 100
            logger.info(f"Task {task_id}: {step}", extra={"task_id": task_id, "step": step})

        _tasks[task_id]["status"] = TaskStatus.COMPLETED
        _tasks[task_id]["progress"] = 100.0
        _tasks[task_id]["video_url"] = f"/outputs/{task_id}.mp4"
        _tasks[task_id]["updated_at"] = datetime.now(timezone.utc)
        _tasks[task_id]["completed_at"] = datetime.now(timezone.utc)

    except Exception as e:
        _tasks[task_id]["status"] = TaskStatus.FAILED
        _tasks[task_id]["error"] = str(e)
        _tasks[task_id]["updated_at"] = datetime.now(timezone.utc)
        logger.error(f"Video generation failed: {e}", extra={"task_id": task_id}, exc_info=True)
    finally:
        ACTIVE_TASKS.labels(task_type="video").dec()


@router.post(
    "/generate",
    response_model=VideoTask,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start video generation",
)
async def generate_video(
    request: VideoRequest,
    background_tasks: BackgroundTasks,
    user: UserContext = Depends(get_current_user),
) -> VideoTask:
    """
    Start an asynchronous video generation task.

    Returns immediately with a task_id for polling via GET /tasks/{id}.
    """
    task_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    _tasks[task_id] = {
        "task_id": task_id,
        "status": TaskStatus.PENDING,
        "title": request.title,
        "style": request.style,
        "duration": request.duration,
        "progress": 0.0,
        "video_url": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
        "estimated_completion": None,
        "user_id": user.user_id,
    }

    background_tasks.add_task(_run_video_generation, task_id, request, user.user_id)
    logger.info(f"Video generation task created: {task_id}", extra={"user_id": user.user_id, "title": request.title})

    return VideoTask(**_tasks[task_id])


@router.get(
    "/tasks/{task_id}",
    response_model=VideoTask,
    summary="Get task status",
)
async def get_task(
    task_id: str,
    user: UserContext = Depends(get_current_user),
) -> VideoTask:
    """Get the status and progress of a video generation task."""
    task = _tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["user_id"] != user.user_id and user.role != "admin":
        raise HTTPException(status_code=403, detail="Access denied")
    return VideoTask(**task)


@router.get(
    "/tasks",
    response_model=PaginatedResponse,
    summary="List all tasks",
)
async def list_tasks(
    page: int = 1,
    page_size: int = 20,
    user: UserContext = Depends(get_current_user),
) -> PaginatedResponse:
    """List all tasks for the current user."""
    user_tasks = [t for t in _tasks.values() if t["user_id"] == user.user_id]
    user_tasks.sort(key=lambda t: t["created_at"], reverse=True)

    start = (page - 1) * page_size
    end = start + page_size
    page_items = user_tasks[start:end]

    return PaginatedResponse(
        items=[VideoTask(**t) for t in page_items],
        total=len(user_tasks),
        page=page,
        page_size=page_size,
        has_more=end < len(user_tasks),
    )
