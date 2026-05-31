"""
AI创作工坊 - Database Models

SQLAlchemy async setup with tables for users, organizations, tasks, and usage tracking.
"""

from datetime import datetime, timezone
from typing import AsyncGenerator, Optional

from sqlalchemy import (
    Column, DateTime, Float, ForeignKey, Integer, String, Text, Boolean, func,
)
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship

from observability.logger import get_logger

logger = get_logger(__name__)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


# ─── Models ───────────────────────────────────────────────────

class Organization(Base):
    """Organization / tenant."""
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True)
    name = Column(String(200), nullable=False)
    plan = Column(String(50), default="free")  # free, pro, enterprise
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    users = relationship("User", back_populates="organization")


class User(Base):
    """User account."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    name = Column(String(200), default="")
    role = Column(String(50), default="user")  # user, admin
    org_id = Column(String(36), ForeignKey("organizations.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_login = Column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="users")
    tasks = relationship("Task", back_populates="user")


class Task(Base):
    """Async task (video generation, analysis, etc.)."""
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    org_id = Column(String(36), ForeignKey("organizations.id"))
    task_type = Column(String(50), nullable=False)  # video, comment_analysis, rag_query
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    input_data = Column(Text, default="{}")
    output_data = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    progress = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="tasks")
    usage_records = relationship("UsageRecord", back_populates="task")


class UsageRecord(Base):
    """Token and cost usage tracking."""
    __tablename__ = "usage_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), ForeignKey("users.id"), index=True)
    org_id = Column(String(36), ForeignKey("organizations.id"))
    task_id = Column(String(36), ForeignKey("tasks.id"), nullable=True)
    provider = Column(String(50), nullable=False)
    model = Column(String(100), nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    task = relationship("Task", back_populates="usage_records")


# ─── Database Setup ───────────────────────────────────────────

_engine = None
_session_factory = None


async def init_db(database_url: str) -> None:
    """
    Initialize database engine and create tables.

    Args:
        database_url: Async database connection string
    """
    global _engine, _session_factory

    _engine = create_async_engine(database_url, echo=False, pool_size=10, max_overflow=20)
    _session_factory = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)

    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    logger.info("Database initialized and tables created")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency: yield an async database session.

    Usage:
        @router.get("/users")
        async def list_users(db: AsyncSession = Depends(get_session)):
            result = await db.execute(select(User))
            return result.scalars().all()
    """
    if _session_factory is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")

    async with _session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
