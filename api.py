"""
Sovereign Empire Content API - Production Grade v3.0
With database, idempotency, audit logging, and WordPress auto-publishing
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, List
import os
from datetime import datetime
import json
import httpx
from dotenv import load_dotenv
import hashlib
import uuid
from sqlalchemy.orm import Session

# Import database models
from database import (
    init_database, get_session, Order, Job, AuditLog, 
    WebhookEvent, OrderStatus
)

# Load environment variables
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="Sovereign Empire Content API",
    description="Production-grade AI content generation with reliability",
    version="3.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database
engine = init_database()

# Get API keys
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")

WORDPRESS_URL = os.environ.get("WORDPRESS_URL")  # Optional
WORDPRESS_USERNAME = os.environ.get("WORDPRESS_USERNAME")
WORDPRESS_APP_PASSWORD = os.environ.get("WORDPRESS_APP_PASSWORD")


# Request/Response Models
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


# Audit Logging Helper
def log_action(db: Session, action: str, entity_type: str, entity_id: str, 
               details: dict = None, user_id: str = "system"):
    """Log an action to audit trail"""
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


# Idempotency Helper
def check_idempotency(db: Session, idempotency_key: str) -> bool:
    """
    Check if we've already processed this request
    Returns True if already processed (skip), False if new (process)
    """
    existing = db.query(WebhookEvent).filter_by(id=idempotency_key).first()
    if existing and existing.processed:
        return True
    
    if not existing:
        # Create record
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
    """Mark an idempotency key as processed"""
    webhook = db.query(WebhookEvent).filter_by(id=idempotency_key).first()
    if webhook:
        webhook.processed = True
        webhook.processed_at = datetime.utcnow()
        db.commit()


# OpenAI API calls (same as before)
def call_openai(system_prompt: str, user_prompt: str, max_tokens: int = 2000) -> tuple:
    """
    Direct HTTP call to OpenAI API
    Returns: (content, tokens_used)
    """
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    
    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": max_tokens
    }
    
    with httpx.Client(timeout=120.0, proxies={}) as client:
        response = client.post(url, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        tokens = result["usage"]["total_tokens"]
        return content, tokens


# Content Generation Functions
def generate_blog_post(topic: str) -> tuple:
    """Generate blog post - returns (content, tokens)"""
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

Make it so good readers can't stop reading."""
    
    return call_openai(system, prompt, max_tokens=2000)


def generate_linkedin_post(blog_content: str, topic: str) -> tuple:
    """Generate LinkedIn post - returns (content, tokens)"""
    system = "You are a LinkedIn content expert who writes engaging posts."
    
    prompt = f"""Based on this blog about '{topic}', create a LinkedIn post.

REQUIREMENTS:
- 150-200 words
- Scroll-stopping hook
- 3 key insights
- Professional but conversational
- Thought-provoking question
- NO hashtags

Blog excerpt: {blog_content[:500]}"""
    
    return call_openai(system, prompt, max_tokens=300)


def generate_twitter_thread(blog_content: str, topic: str) -> tuple:
    """Generate Twitter thread - returns (content, tokens)"""
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

Blog excerpt: {blog_content[:500]}"""
    
    return call_openai(system, prompt, max_tokens=500)


# WordPress Publishing
def publish_to_wordpress(title: str, content: str, site_url: str = None,
                        username: str = None, password: str = None, 
                        status: str = "draft") -> dict:
    """
    Publish content to WordPress as draft
    Returns: {success: bool, post_id: str, post_url: str, error: str}
    """
    # Use environment variables if not provided
    site_url = site_url or WORDPRESS_URL
    username = username or WORDPRESS_USERNAME
    password = password or WORDPRESS_APP_PASSWORD
    
    if not all([site_url, username, password]):
        return {
            "success": False,
            "error": "WordPress credentials not configured"
        }
    
    try:
        # WordPress REST API endpoint
        url = f"{site_url}/wp-json/wp/v2/posts"
        
        # Prepare post data
        post_data = {
            "title": title,
            "content": content,
            "status": status  # "draft" or "publish"
        }
        
        # Make request with basic auth
        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                url,
                json=post_data,
                auth=(username, password)
            )
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "post_id": str(result["id"]),
                "post_url": result["link"],
                "error": None
            }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# Background Worker
async def process_order(order_id: str):
    """Background worker that generates content for an order"""
    db = get_session(engine)
    
    try:
        # Get order
        order = db.query(Order).filter_by(id=order_id).first()
        if not order:
            return
        
        # Update status
        order.status = OrderStatus.PROCESSING
        db.commit()
        log_action(db, "order_processing_started", "order", order_id)
        
        total_tokens = 0
        
        # Generate blog post
        log_action(db, "job_started", "job", f"{order_id}_blog", {"type": "blog"})
        blog_post, blog_tokens = generate_blog_post(order.topic)
        total_tokens += blog_tokens
        
        # Generate LinkedIn post
        log_action(db, "job_started", "job", f"{order_id}_linkedin", {"type": "linkedin"})
        linkedin_post, linkedin_tokens = generate_linkedin_post(blog_post, order.topic)
        total_tokens += linkedin_tokens
        
        # Generate Twitter thread
        log_action(db, "job_started", "job", f"{order_id}_twitter", {"type": "twitter"})
        twitter_thread, twitter_tokens = generate_twitter_thread(blog_post, order.topic)
        total_tokens += twitter_tokens
        
        # Create job records
        jobs_data = [
            {"type": "blog", "content": blog_post, "tokens": blog_tokens},
            {"type": "linkedin", "content": linkedin_post, "tokens": linkedin_tokens},
            {"type": "twitter", "content": twitter_thread, "tokens": twitter_tokens}
        ]
        
        for job_data in jobs_data:
            job = Job(
                id=f"{order_id}_{job_data['type']}",
                order_id=order_id,
                job_type=job_data['type'],
                status="completed",
                generated_content=job_data['content'],
                tokens_used=job_data['tokens'],
                cost=job_data['tokens'] * 0.00003,  # Rough GPT-4 cost estimate
                completed_at=datetime.utcnow()
            )
            db.add(job)
        
        # Calculate costs
        estimated_cost = total_tokens * 0.00003
        order.total_tokens_used = total_tokens
        order.estimated_cost = estimated_cost
        
        # Try to publish to WordPress
        if order.wordpress_site_url:
            wp_result = publish_to_wordpress(
                title=f"Content: {order.topic}",
                content=blog_post,
                site_url=order.wordpress_site_url,
                status="draft"
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
            "cost": estimated_cost
        })
        
    except Exception as e:
        # Handle failure
        order = db.query(Order).filter_by(id=order_id).first()
        if order:
            order.status = OrderStatus.FAILED
            order.error_message = str(e)
            order.retry_count += 1
            db.commit()
        
        log_action(db, "order_failed", "order", order_id, {"error": str(e)})
    
    finally:
        db.close()


# API Endpoints
@app.get("/")
async def root():
    """Health check"""
    return {
        "service": "Sovereign Empire Content API",
        "version": "3.0.0",
        "status": "online",
        "features": ["database", "idempotency", "audit-logs", "wordpress"]
    }


@app.get("/health")
async def health():
    """Health check with database status"""
    db = get_session(engine)
    try:
        # Test database connection
        db.query(Order).first()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    finally:
        db.close()
    
    return {
        "status": "healthy",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/generate", response_model=OrderResponse)
async def generate_content(
    request: ContentRequest, 
    background_tasks: BackgroundTasks,
    x_idempotency_key: Optional[str] = Header(None)
):
    """
    Create order and queue content generation
    Supports idempotency via X-Idempotency-Key header
    """
    db = get_session(engine)
    
    try:
        # Generate idempotency key if not provided
        if not x_idempotency_key:
            x_idempotency_key = hashlib.sha256(
                f"{request.tenant_id}_{request.topic}_{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()
        
        # Check idempotency
        if check_idempotency(db, x_idempotency_key):
            # Already processed - find and return existing order
            webhook = db.query(WebhookEvent).filter_by(id=x_idempotency_key).first()
            if webhook and webhook.payload:
                existing_order_id = json.loads(webhook.payload).get("order_id")
                return OrderResponse(
                    success=True,
                    order_id=existing_order_id,
                    message="Order already exists (idempotent)",
                    status="duplicate"
                )
        
        # Generate order ID
        order_id = f"ORD_{int(datetime.utcnow().timestamp())}_{uuid.uuid4().hex[:8]}"
        
        # Create order
        order = Order(
            id=order_id,
            customer_email=request.customer_email or "unknown@example.com",
            customer_name=request.customer_name,
            tenant_id=request.tenant_id,
            topic=request.topic,
            stripe_payment_id=request.stripe_payment_id,
            wordpress_site_url=request.wordpress_site_url,
            status=OrderStatus.PENDING
        )
        db.add(order)
        db.commit()
        
        # Log order creation
        log_action(db, "order_created", "order", order_id, {
            "topic": request.topic,
            "tenant": request.tenant_id
        })
        
        # Store order_id in webhook event for idempotency
        webhook = db.query(WebhookEvent).filter_by(id=x_idempotency_key).first()
        if webhook:
            webhook.payload = json.dumps({"order_id": order_id})
            db.commit()
        
        # Queue background job
        background_tasks.add_task(process_order, order_id)
        
        # Mark as processed
        mark_processed(db, x_idempotency_key)
        
        return OrderResponse(
            success=True,
            order_id=order_id,
            message=f"Content generation queued for: {request.topic}",
            status="queued"
        )
    
    finally:
        db.close()


@app.get("/orders/{order_id}", response_model=OrderDetail)
async def get_order(order_id: str):
    """Get order status and content"""
    db = get_session(engine)
    
    try:
        order = db.query(Order).filter_by(id=order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Get jobs
        jobs = db.query(Job).filter_by(order_id=order_id).all()
        
        blog_post = None
        linkedin_post = None
        twitter_thread = None
        
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
            error=order.error_message
        )
    
    finally:
        db.close()


@app.get("/orders")
async def list_orders(status: Optional[str] = None, limit: int = 50):
    """List all orders (admin endpoint)"""
    db = get_session(engine)
    
    try:
        query = db.query(Order)
        
        if status:
            query = query.filter(Order.status == OrderStatus[status.upper()])
        
        orders = query.order_by(Order.created_at.desc()).limit(limit).all()
        
        return {
            "total": len(orders),
            "orders": [
                {
                    "order_id": o.id,
                    "customer_email": o.customer_email,
                    "topic": o.topic,
                    "status": o.status.value,
                    "created_at": o.created_at.isoformat(),
                    "tokens_used": o.total_tokens_used,
                    "cost": o.estimated_cost
                }
                for o in orders
            ]
        }
    
    finally:
        db.close()


@app.get("/admin/failed")
async def get_failed_orders():
    """Get all failed orders (for ops console)"""
    db = get_session(engine)
    
    try:
        failed_orders = db.query(Order).filter_by(status=OrderStatus.FAILED).all()
        
        return {
            "total": len(failed_orders),
            "orders": [
                {
                    "order_id": o.id,
                    "customer_email": o.customer_email,
                    "topic": o.topic,
                    "error": o.error_message,
                    "retry_count": o.retry_count,
                    "created_at": o.created_at.isoformat()
                }
                for o in failed_orders
            ]
        }
    
    finally:
        db.close()


@app.post("/admin/retry/{order_id}")
async def retry_order(order_id: str, background_tasks: BackgroundTasks):
    """Retry a failed order"""
    db = get_session(engine)
    
    try:
        order = db.query(Order).filter_by(id=order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order.retry_count >= 3:
            raise HTTPException(status_code=400, detail="Max retries exceeded")
        
        # Reset status
        order.status = OrderStatus.PENDING
        order.error_message = None
        db.commit()
        
        # Queue retry
        background_tasks.add_task(process_order, order_id)
        
        log_action(db, "order_retry", "order", order_id, {
            "retry_count": order.retry_count
        })
        
        return {"success": True, "message": "Order queued for retry"}
    
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
