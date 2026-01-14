"""
Database Models for Sovereign Empire Content API (Railway-safe)
Provides:
- init_database()
- get_session()
- ORM models: Order, Job, AuditLog, WebhookEvent
- Enum: OrderStatus
"""

import os
import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    create_engine, Column, String, Integer, Float, DateTime,
    Text, Boolean, Enum as SAEnum
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

    id = Column(String, primary_key=True)
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

    status = Column(
        SAEnum(OrderStatus, name="order_status", native_enum=False),
        default=OrderStatus.PENDING,
        index=True,
        nullable=False
    )

    total_tokens_used = C
