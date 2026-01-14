"""
Database Models for Sovereign Empire Content API (Railway-safe)
Includes:
- ORM Models: Order, Job, AuditLog, WebhookEvent
- Enum: OrderStatus
- Functions: init_database(), get_session()
"""

import os
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Text,
    Boolean,
    Enum as SAEnum,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine import Engine

Base = declarative_base()


# -------------------------
# Enum
# -------------------------
class OrderStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PUBLISHING = "publishing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# -------------------------
# Models
# -------------------------
class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True)  # ORD_{timestamp}_{random}
    customer_email = Column(String, nullable=False, index=True)
    customer_name = Column(String, nullable=True)
    tenant_id = Column(String, nullable=False, index=True)

    stripe_payment_id = Column(String, unique=True, index=True, nullable=True)
    stripe_customer_id = Column(String, index=True, nullable=True)
    amount_paid = Column(Float, nullable=True)
    currency = Column(String, default="USD")

    topic = Column(String, nullable=False)
    industry = Column(String, nullable=True)
    tone = Column(String, nullable=True)

    # Portable enum (works in SQLite + Postgres)
    status = Column(
        SAEnum(OrderStatus, name="order_status", native_enum=False),
        default=OrderStatus.PENDING,
        index=True,
        nullable=False,
    )

    total_tokens_used = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)

    wordpress_site_url = Column(String, nullable=True)
    wordpress_post_id = Column(String, nullable=True)
    wordpress_post_url = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)  # you use {order_id}_{type}
    order_id = Column(String, nullable=False, index=True)

    job_type = Column(String, nullable=False)  # blog/linkedin/twitter
    status = Column(String, default="queued", index=True)

    input_prompt = Column(Text, nullable=True)
    generated_content = Column(Text, nullable=True)

    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)

    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)

    action = Column(String, nullable=False, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False, index=True)

    user_id = Column(String, nullable=True)
    details = Column(Text, nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String, nullable=True)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True)  # idempotency key / webhook id
    event_type = Column(String, nullable=False, index=True)

    processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime, nullable=True)

    payload = Column(Text, nullable=True)
    received_at = Column(DateTime, default=datetime.utcnow)


# -------------------------
# Database setup (THIS is what your api.py needs)
# -------------------------
SessionLocal = None


def _normalize_database_url(url: str) -> str:
    # Railway sometimes provides postgres://, SQLAlchemy expects postgresql://
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def init_database(database_url: Optional[str] = None) -> Engine:
    """
    Create engine, create tables, and configure SessionLocal.

    Priority:
    1) passed database_url
    2) env DATABASE_URL (Railway Postgres)
    3) sqlite fallback (local dev)
    """
    global SessionLocal

    database_url = database_url or os.getenv("DATABASE_URL") or "sqlite:///./sovereign_empire.db"
    database_url = _normalize_database_url(database_url)

    connect_args = {}
    if database_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

    engine = create_engine(database_url, echo=False, future=True, connect_args=connect_args)

    # Create tables
    Base.metadata.create_all(engine)

    # Reusable session factory
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return engine


def get_session(engine: Engine):
    """Return a database session."""
    global SessionLocal
    if SessionLocal is None:
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal()
