"""
Database Models for Sovereign Empire Content API
SQLAlchemy ORM models for production-grade tracking
"""

from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Text, Boolean, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import enum

Base = declarative_base()


class OrderStatus(enum.Enum):
    """Order lifecycle states"""
    PENDING = "pending"  # Payment received, not yet processed
    PROCESSING = "processing"  # Content being generated
    PENDING_APPROVAL = "pending_approval"  # Ready for review
    APPROVED = "approved"  # Approved, ready to publish
    PUBLISHING = "publishing"  # Being published to platforms
    COMPLETED = "completed"  # Fully delivered
    FAILED = "failed"  # Something went wrong
    CANCELLED = "cancelled"  # Customer cancelled


class Order(Base):
    """
    Customer orders - one per paid subscription/purchase
    This is the master record that tracks the entire lifecycle
    """
    __tablename__ = "orders"
    
    id = Column(String, primary_key=True)  # Format: ORD_{timestamp}_{random}
    customer_email = Column(String, nullable=False, index=True)
    customer_name = Column(String)
    tenant_id = Column(String, nullable=False, index=True)  # For multi-tenant isolation
    
    # Payment info
    stripe_payment_id = Column(String, unique=True, index=True)
    stripe_customer_id = Column(String, index=True)
    amount_paid = Column(Float)
    currency = Column(String, default="USD")
    
    # Content details
    topic = Column(String, nullable=False)
    industry = Column(String)  # Optional: helps with targeting
    tone = Column(String)  # Optional: professional, casual, etc.
    
    # Status tracking
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, index=True)
    
    # Cost tracking
    total_tokens_used = Column(Integer, default=0)
    estimated_cost = Column(Float, default=0.0)  # OpenAI cost
    
    # WordPress integration
    wordpress_site_url = Column(String)
    wordpress_post_id = Column(String)  # Post ID after publishing
    wordpress_post_url = Column(String)  # URL to published post
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    
    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)


class Job(Base):
    """
    Background jobs - actual content generation tasks
    One order can have multiple jobs (blog, linkedin, twitter)
    """
    __tablename__ = "jobs"
    
    id = Column(String, primary_key=True)  # Format: JOB_{timestamp}_{random}
    order_id = Column(String, nullable=False, index=True)  # Links to Order
    
    # Job details
    job_type = Column(String, nullable=False)  # "blog", "linkedin", "twitter"
    status = Column(String, default="queued", index=True)  # queued, processing, completed, failed
    
    # Content
    input_prompt = Column(Text)
    generated_content = Column(Text, nullable=True)
    
    # Tracking
    tokens_used = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


class AuditLog(Base):
    """
    Audit trail - every important action gets logged
    Critical for debugging and compliance
    """
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # What happened
    action = Column(String, nullable=False, index=True)  # "order_created", "job_completed", etc.
    entity_type = Column(String, nullable=False)  # "order", "job", "webhook"
    entity_id = Column(String, nullable=False, index=True)
    
    # Context
    user_id = Column(String, nullable=True)  # Who performed the action (admin, system, customer)
    details = Column(Text)  # JSON string with additional context
    
    # Tracking
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    ip_address = Column(String, nullable=True)


class WebhookEvent(Base):
    """
    Webhook deduplication - prevents processing the same Stripe event twice
    Critical for idempotency
    """
    __tablename__ = "webhook_events"
    
    id = Column(String, primary_key=True)  # Stripe event ID
    event_type = Column(String, nullable=False, index=True)
    
    # Processing status
    processed = Column(Boolean, default=False, index=True)
    processed_at = Column(DateTime, nullable=True)
    
    # Data
    payload = Column(Text)  # Full webhook payload (JSON)
    
    # Timestamps
    received_at = Column(DateTime, default=datetime.utcnow)


# Database setup functions
def init_database(database_url: str = "sqlite:///./sovereign_empire.db"):
    """
    Initialize database and create all tables
    """
    engine = create_engine(database_url, echo=False)
    Base.metadata.create_all(engine)
    return engine


def get_session(engine):
    """
    Get a database session
    """
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
