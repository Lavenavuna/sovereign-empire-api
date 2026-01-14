"""
Sovereign Empire Content API - Production Grade v3.1
- Database
- Idempotency
- Audit logging
- WordPress auto-publishing
- Robust template path resolution (Railway-safe)
"""

import os
import json
import uuid
import hashlib
from datetime import datetime
from typing import Optional, Dict, List, Tuple
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, BackgroundTasks, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

# ---- Load env (safe even if .env doesn't exist on Railway) ----
load_dotenv()

# ---- Paths (DO NOT rely on current working directory) ----
BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"

# ---- Import database models ----
from database import (
    init_database, get_session, Order, Job, AuditLog,
    WebhookEvent, OrderStatus
)

# ---- App ----
app = FastAPI(
    title="Sovereign Empire Content API",
    description="Production-grade AI content generation with reliability",
    version="3.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Init database engine once ----
engine = init_database()

# ---- Env config ----
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")  # required for generation calls
WORDPRESS_URL = os.getenv("WORDPRESS_URL")  # optional
WORDPRESS_USERNAME = os.getenv("WORDPRESS_USERNAME")
WORDPRESS_APP_PASSWORD = os.getenv("WORDPRESS_APP_PASSWORD")


# -------------------------
# Pydantic Models
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
# Helpers: Audit + Idempotency
# -------------------------
def log_action(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict = None,
    user_id: str = "system"
):
    audit = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        user_id=user_id,
        details=json.dumps(details) if details else None,
        timestamp=datetime.utcnow()
    )
    db.add(audit)
    db.commit()


def check_idempotency(db: Session, idempotency_key: str) -> bool:
    existing = db.query(WebhookEvent).filter_by(id=idempotency_key).first()
    if existing and existing.processed:
        return True

    if not existing:
        webhook = WebhookEvent(
            id=idempotency_key,
            event_type="api_request",
            processed=False,
            received_at=datetime.utcnow()
        )
        db.add(webhook)
        db.commit()

    return False


def mark_processed(db: Session, idempotency_key: str):
    webhook = db.query(WebhookEvent).filter_by(id=idempotency_key).first()
    if webhook:
        webhook.processed = True
        webhook.processed_at = datetime.utcnow()
        db.commit()


# -------------------------
# OpenAI call (fail only when used, not at import time)
# -------------------------
def call_openai(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> Tuple[str, int]:
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY is not set in environment variables on Railway")

    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    }

    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
        "max_tokens": max_toke
