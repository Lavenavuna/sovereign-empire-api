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
        "max_tokens": max_tokens,
    }

    # NOTE: remove proxies={} (can break in some envs). Just let httpx handle it.
    with httpx.Client(timeout=120.0) as client:
        r = client.post(url, headers=headers, json=data)
        r.raise_for_status()
        result = r.json()
        content = result["choices"][0]["message"]["content"]
        tokens = result.get("usage", {}).get("total_tokens", 0)
        return content, tokens


def generate_blog_post(topic: str) -> Tuple[str, int]:
    system = "You are an expert content writer who creates viral, SEO-optimized content."
    prompt = f"""Write a comprehensive, engaging blog post about: {topic}

REQUIREMENTS:
- 1000-1200 words
- Start with a POWERFUL hook
- Use storytelling and real-world examples
- Include 5-7 actionable takeaways
- SEO-optimized
- Conversational tone
- Strong call-to-action
- Short paragraphs (2-3 sentences max)
- Include subheadings (## format)
"""
    return call_openai(system, prompt, max_tokens=2000)


def generate_linkedin_post(blog_content: str, topic: str) -> Tuple[str, int]:
    system = "You are a LinkedIn content expert who writes engaging posts."
    prompt = f"""Based on this blog about '{topic}', create a LinkedIn post.

REQUIREMENTS:
- 150-200 words
- Scroll-stopping hook
- 3 key insights
- Professional but conversational
- Thought-provoking question
- NO hashtags

Blog excerpt: {blog_content[:500]}
"""
    return call_openai(system, prompt, max_tokens=300)


def generate_twitter_thread(blog_content: str, topic: str) -> Tuple[str, int]:
    system = "You are a viral Twitter content creator."
    prompt = f"""Based on this blog about '{topic}', create a Twitter thread.

REQUIREMENTS:
- 5-7 tweets (numbered 1/, 2/, etc.)
- Attention-grabbing first tweet
- Key insights (one per tweet)
- Last tweet: CTA + "Follow for more"
- Under 280 chars each
- Punchy language
- Max 1-2 hashtags in last tweet

Blog excerpt: {blog_content[:500]}
"""
    return call_openai(system, prompt, max_tokens=500)


# -------------------------
# WordPress publishing
# -------------------------
def publish_to_wordpress(
    title: str,
    content: str,
    site_url: str = None,
    username: str = None,
    password: str = None,
    status: str = "draft"
) -> dict:
    site_url = site_url or WORDPRESS_URL
    username = username or WORDPRESS_USERNAME
    password = password or WORDPRESS_APP_PASSWORD

    if not all([site_url, username, password]):
        return {"success": False, "error": "WordPress credentials not configured"}

    try:
        url = f"{site_url.rstrip('/')}/wp-json/wp/v2/posts"
        post_data = {"title": title, "content": content, "status": status}

        with httpx.Client(timeout=60.0) as client:
            r = client.post(url, json=post_data, auth=(username, password))
            r.raise_for_status()
            result = r.json()

        return {
            "success": True,
            "post_id": str(result["id"]),
            "post_url": result.get("link"),
            "error": None,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}


# -------------------------
# Background worker
# -------------------------
async def process_order(order_id: str):
    db = get_session(engine)

    try:
        order = db.query(Order).filter_by(id=order_id).first()
        if not order:
            return

        order.status = OrderStatus.PROCESSING
        db.commit()
        log_action(db, "order_processing_started", "order", order_id)

        total_tokens = 0

        blog_post, blog_tokens = generate_blog_post(order.topic)
        total_tokens += blog_tokens

        linkedin_post, linkedin_tokens = generate_linkedin_post(blog_post, order.topic)
        total_tokens += linkedin_tokens

        twitter_thread, twitter_tokens = generate_twitter_thread(blog_post, order.topic)
        total_tokens += twitter_tokens

        jobs_data = [
            ("blog", blog_post, blog_tokens),
            ("linkedin", linkedin_post, linkedin_tokens),
            ("twitter", twitter_thread, twitter_tokens),
        ]

        for job_type, content, tokens in jobs_data:
            db.add(Job(
                id=f"{order_id}_{job_type}",
                order_id=order_id,
                job_type=job_type,
                status="completed",
                generated_content=content,
                tokens_used=tokens,
                cost=tokens * 0.00003,
                completed_at=datetime.utcnow(),
            ))

        order.total_tokens_used = total_tokens
        order.estimated_cost = total_tokens * 0.00003

        # WordPress draft publish (optional)
        if order.wordpress_site_url:
            wp_result = publish_to_wordpress(
                title=f"Content: {order.topic}",
                content=blog_post,
                site_url=order.wordpress_site_url,
                status="draft",
            )

            if wp_result["success"]:
                order.wordpress_post_id = wp_result["post_id"]
                order.wordpress_post_url = wp_result["post_url"]
                order.status = OrderStatus.COMPLETED
                log_action(db, "wordpress_published", "order", order_id, wp_result)
            else:
                order.status = OrderStatus.PENDING_APPROVAL
                order.error_message = f"WordPress publish failed: {wp_result['error']}"
                log_action(db, "wordpress_failed", "order", order_id, wp_result)
        else:
            order.status = OrderStatus.PENDING_APPROVAL

        order.completed_at = datetime.utcnow()
        db.commit()

        log_action(db, "order_completed", "order", order_id, {
            "tokens": total_tokens,
            "cost": order.estimated_cost
        })

    except Exception as e:
        order = db.query(Order).filter_by(id=order_id).first()
        if order:
            order.status = OrderStatus.FAILED
            order.error_message = str(e)
            order.retry_count += 1
            db.commit()
        log_action(db, "order_failed", "order", order_id, {"error": str(e)})

    finally:
        db.close()


# -------------------------
# Routes
# -------------------------
@app.get("/")
async def root():
    return {
        "service": "Sovereign Empire Content API",
        "version": "3.1.0",
        "status": "online",
        "features": ["database", "idempotency", "audit-logs", "wordpress"],
        "templates_dir_exists": TEMPLATES_DIR.exists(),
        "templates_dir": str(TEMPLATES_DIR),
    }


@app.get("/health")
async def health():
    db = get_session(engine)
    try:
        db.query(Order).first()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    finally:
        db.close()

    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat(),
        "openai_key_set": bool(OPENAI_API_KEY),
    }


@app.post("/generate", response_model=OrderResponse)
async def generate_content(
    request: ContentRequest,
    background_tasks: BackgroundTasks,
    x_idempotency_key: Optional[str] = Header(None),
):
    db = get_session(engine)

    try:
        if not x_idempotency_key:
            x_idempotency_key = hashlib.sha256(
                f"{request.tenant_id}_{request.topic}_{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()

        if check_idempotency(db, x_idempotency_key):
            webhook = db.query(WebhookEvent).filter_by(id=x_idempotency_key).first()
            if webhook and webhook.payload:
                existing_order_id = json.loads(webhook.payload).get("order_id")
                return OrderResponse(
                    success=True,
                    order_id=existing_order_id,
                    message="Order already exists (idempotent)",
                    status="duplicate",
                )

        order_id = f"ORD_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:8]}"

        order = Order(
            id=order_id,
            customer_email=request.customer_email or "unknown@example.com",
            customer_name=request.customer_name,
            tenant_id=request.tenant_id,
            topic=request.topic,
            stripe_payment_id=request.stripe_payment_id,
            wordpress_site_url=request.wordpress_site_url,
            status=OrderStatus.PENDING,
        )
        db.add(order)
        db.commit()

        log_action(db, "order_created", "order", order_id, {
            "topic": request.topic,
            "tenant": request.tenant_id
        })

        webhook = db.query(WebhookEvent).filter_by(id=x_idempotency_key).first()
        if webhook:
            webhook.payload = json.dumps({"order_id": order_id})
            db.commit()

        background_tasks.add_task(process_order, order_id)
        mark_processed(db, x_idempotency_key)

        return OrderResponse(
            success=True,
            order_id=order_id,
            message=f"Content generation queued for: {request.topic}",
            status="queued",
        )

    finally:
        db.close()


@app.get("/orders/{order_id}", response_model=OrderDetail)
async def get_order(order_id: str):
    db = get_session(engine)
    try:
        order = db.query(Order).filter_by(id=order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        jobs = db.query(Job).filter_by(order_id=order_id).all()

        blog_post = linkedin_post = twitter_thread = None
        for job in jobs:
            if job.job_type == "blog":
                blog_post = job.generated_content
            elif job.job_type == "linkedin":
                linkedin_post = job.generated_content
            elif job.job_type == "twitter":
                twitter_thread = job.generated_content

        return OrderDetail(
            order_id=order.id,
            status=order.status.value,
            topic=order.topic,
            created_at=order.created_at.isoformat(),
            blog_post=blog_post,
            linkedin_post=linkedin_post,
            twitter_thread=twitter_thread,
            wordpress_url=order.wordpress_post_url,
            error=order.error_message,
        )
    finally:
        db.close()


@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard():
    template_path = TEMPLATES_DIR / "dashboard.html"
    if not template_path.exists():
        return HTMLResponse(f"<h1>Dashboard template not found</h1><p>{template_path}</p>", status_code=500)
    return FileResponse(str(template_path))


@app.get("/admin/order/{order_id}", response_class=HTMLResponse)
async def admin_order_detail(order_id: str):
    template_path = TEMPLATES_DIR / "order_detail.html"
    if not template_path.exists():
        return HTMLResponse(f"<h1>Order detail template not found</h1><p>{template_path}</p>", status_code=500)
    return FileResponse(str(template_path))


@app.post("/admin/retry/{order_id}")
async def retry_order(order_id: str, background_tasks: BackgroundTasks):
    db = get_session(engine)
    try:
        order = db.query(Order).filter_by(id=order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

        if order.retry_count >= 3:
            raise HTTPException(status_code=400, detail="Max retries exceeded")

        order.status = OrderStatus.PENDING
        order.error_message = None
        db.commit()

        background_tasks.add_task(process_order, order_id)
        log_action(db, "order_retry", "order", order_id, {"retry_count": order.retry_count})

        return {"success": True, "message": "Order queued for retry"}

    finally:
        db.close()


# -------------------------
# Local run (Railway uses CMD; keep this for local dev)
# -------------------------
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("api:app", host="0.0.0.0", port=port)
