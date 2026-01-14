"""
Database Models for Sovereign Empire Content API (Production-safe)
- Railway-safe DATABASE_URL support (Postgres)
- SQLite fallback for local dev
- Reusable SessionLocal factory
"""

import os
import enum
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, DateTime,
    Text, Boolean, Enum as SAEnum
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.engine import Engine

Base = declarative_base()

# -------------------------
# Enums
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

    # Keep it portable across SQLite/Postgres
    status = Column(
        SAEnum(OrderStatus, name="order_status", native_enum=False),
        default=OrderStatus.PENDING,
        index=True,
        nullable=False
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

    id = Column(String, primary_key=True)  # {ord_
