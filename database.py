"""
database.py
SQLAlchemy models + DB init helpers
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

# Will be set by init_database()
SessionLocal = None


class OrderStatus(enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PUBLISHING = "publishing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Order(Base):
    __tablename__ = "orders"

    id = Column(String, primary_key=True)  # e.g. ORD_...
    customer_email = Column(String, nullable=False, index=True)
    customer_name = Column(String)
    tenant_id = Column(String, nullable=False, index=True)

    stripe_payment_id = Column(String, unique=True, index=True)
    stripe_customer_id = Column(String, index=True)
    amount_paid = Column(Float)
    currency = Column(String, default="USD")

    topic = Column(String, nullable=False)
    industry = Column(String)
    tone = Column(String)

    status = Column(
        SAEnum(OrderStatus, name="order_status", native_enum=False),
        default=OrderStatus.PENDING,
        index=True,
        nullable=False,
    )

    # ✅ this is the correct line (NOT "= C")
    total_tokens_used = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)

    wordpress_site_url = Column(String)
    wordpress_post_id = Column(String)
    wordpress_post_url = Column(String)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)  # e.g. JOB_...
    order_id = Column(String, nullable=False, index=True)

    job_type = Column(String, nullable=False)  # blog/linkedin/twitter
    status = Column(String, default="queued", index=True)

    input_prompt = Column(Text)
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
    details = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String, nullable=True)


class WebhookEvent(Base):
    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True)  # Stripe event id
    event_type = Column(String, nullable=False, index=True)

    processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime, nullable=True)

    payload = Column(Text)
    received_at = Column(DateTime, default=datetime.utcnow)


def _normalize_database_url(url: str) -> str:
    # Railway sometimes provides postgres:// — SQLAlchemy prefers postgresql://
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def init_database(database_url: str) -> None:
    """
    Initializes engine + SessionLocal + creates tables.
    Call this once on app startup.
    """
    global SessionLocal

    database_url = _normalize_database_url(database_url)

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        future=True,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    Base.metadata.create_all(bind=engine)


def get_session():
    """
    Returns a DB session. Requires init_database() to be called first.
    """
    if SessionLocal is None:
        raise RuntimeError("Database not initialized. Did you call init_database() on startup?")
    return SessionLocal()
