"""
Sovereign Empire Content API - Production Grade v3.1 (Railway-safe)
- Database
- Idempotency
- Audit logging
- WordPress auto-publishing
- Robust template paths (no CWD assumptions)
"""

import os
import json
import uuid
import hashlib
from datetime import datetime
from typing import Optional, Tuple
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

# Load env (safe even if .env doesn't exist on Railway)
load_dotenv()

# Resolve paths relative to this file (Railway-safe)
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

# Import database symbols from database.py (DO NOT paste database.py here)
from database import (
    init_database,
    get_session,
    Order,
    Job,
    AuditLog,
    WebhookEvent,
    OrderStatus,
)

app = FastAPI(
    title="Sovereign Empire Content API",
    description="Production-grade AI content generation with reliability",
    version="3.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Init DB engine once
engine = init_database()

# Env vars
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WORDPRESS_URL = os.getenv("WORDPRESS_URL")
WORDPRESS_USERNAME = os.getenv("WORDPRESS_USERNAME")
WORDPRESS_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")


# -------------------------
# Models
# -------------------------
class ContentRequest(BaseModel):
    topic: str
    tenant_id: str = "default"
    customer_email: Optional[str] = None
    customer_name: Optional[str] = None
    wordpress_site_url: Optional[str] = None
    stripe_payment_id: Optional[str] = None


class OrderResponse(BaseModel):
    success: bool
    order_id: str
    message: str
    status: str


class OrderDetail(BaseModel):
    order_id: str
    status: str
    topic: str
    created_at: str
    blog_post: Optional[str] = None
    linkedin_post: Optional[str] = None
    twitter_thread: Optional[str] = None
    wordpress_url: Optional[str] = None
    error: Optional[str] = None


# -------------------------
# Helpers
# -------------------------
def log_action(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict = None,
    user_id: str = "system",
):
    audit = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        details=json.dumps(details) if details else None,
        timestamp=datetime.utcnow(),
    )
    db.add(audit)
    db.commit()


def check_idempotency(db: Session, idempotency_key: str) -> bool:
    existing = db.query(WebhookEvent).filter_by(id=idempotency_key).first()
    if existing and existing.processed:
        return True

    if not existing:
        db.add(
            WebhookEvent(
                id=idempotency_key,
                event_type="api_request",
                processed=False,
                received_at=datetime.utcnow(),
            )
        )
        db.commit()

    return False


def mark_processed(db: Session, idempotency_key: str):
    webhook = db.query(WebhookEvent).filter_by(id=idempotency_key).first()
    if webhook:
        webhook.processed = True
        webhook.processed_at = datetime.utcnow()
        db
