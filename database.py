"""
database.py - SQLAlchemy models and database initialization
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

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
from sqlalchemy.orm import declarative_base, sessionmaker, Session

Base = declarative_base()

# Global session maker (set by init_database)
SessionLocal: Optional[sessionmaker] = None


class OrderStatus(enum.Enum):
    """Order status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    PUBLISHING = "publishing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Order(Base):
    """Order model for content generation requests"""
    __tablename__ = "orders"

    id = Column(String, primary_key=True)
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
    """Job model for async content generation tasks"""
    __tablename__ = "jobs"

    id = Column(String, primary_key=True)
    order_id = Column(String, nullable=False, index=True)

    job_type = Column(String, nullable=False)
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
    """Audit log for tracking system events"""
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
    """Webhook event tracking (e.g., Stripe webhooks)"""
    __tablename__ = "webhook_events"

    id = Column(String, primary_key=True)
    event_type = Column(String, nullable=False, index=True)

    processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime, nullable=True)

    payload = Column(Text)
    received_at = Column(DateTime, default=datetime.utcnow)


def _normalize_database_url(url: str) -> str:
    """
    Normalize database URL for SQLAlchemy compatibility.
    Railway provides postgres://, but SQLAlchemy 2.x requires postgresql://
    """
    if url.startswith("postgres://") and not url.startswith("postgresql://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


def init_database(database_url: str) -> None:
    """
    Initialize database engine and create all tables.
    
    Args:
        database_url: Database connection string
        
    Raises:
        Exception: If database initialization fails
    """
    global SessionLocal

    try:
        # Normalize URL for SQLAlchemy compatibility
        database_url = _normalize_database_url(database_url)
        
        # Create engine with connection pooling
        engine = create_engine(
            database_url,
            pool_pre_ping=True,  # Verify connections before using them
            pool_recycle=3600,   # Recycle connections after 1 hour
            echo=False,          # Set to True for SQL debugging
        )
        
        # Create session factory
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        
        print("✅ Database initialized successfully")
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise


def get_session() -> Session:
    """
    Get a new database session.
    
    Returns:
        Session: SQLAlchemy session
        
    Raises:
        RuntimeError: If database hasn't been initialized
        
    Usage:
        session = get_session()
        try:
            # Use session
            pass
        finally:
            session.close()
    """
    if SessionLocal is None:
        raise RuntimeError(
            "Database not initialized. Call init_database() first."
        )
    return SessionLocal()
