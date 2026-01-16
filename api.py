"""
api.py - Phase 1: Order Creation API
Updated for PayPal integration (Fiji-compatible)
"""
import os
import uuid
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, validator
from sqlalchemy import select
from database import init_database, get_session, Order, OrderStatus

app = FastAPI(
    title="Sovereign Empire Content API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS for frontend (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Template support
templates = Jinja2Templates(directory="templates")


# ==================== PYDANTIC MODELS ====================

class OrderCreateRequest(BaseModel):
    """Request model for creating a new order"""
    customer_email: EmailStr
    customer_name: Optional[str] = None
    tenant_id: str
    topic: str
    industry: Optional[str] = None
    tone: Optional[str] = "professional"
    
    @validator('topic')
    def topic_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Topic cannot be empty')
        return v.strip()
    
    @validator('tenant_id')
    def tenant_id_format(cls, v):
        if not v or len(v) < 3:
            raise ValueError('Invalid tenant_id format')
        return v.upper()
    
    class Config:
        json_schema_extra = {
            "example": {
                "customer_email": "user@example.com",
                "customer_name": "John Doe",
                "tenant_id": "TENANT_001",
                "topic": "The Future of AI in Healthcare",
                "industry": "Healthcare",
                "tone": "professional"
            }
        }


class OrderResponse(BaseModel):
    """Response model for order operations"""
    order_id: str
    status: str
    message: str
    created_at: str
    payment_url: Optional[str] = None  # For PayPal checkout


# ==================== STARTUP ====================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        db_url = os.getenv("DATABASE_URL", "sqlite:///./sovereign_empire.db")
        init_database(db_url)
        print(f"✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise


# ==================== HEALTH & STATUS ====================

@app.get("/")
def root():
    """Root endpoint"""
    return {
        "status": "ok",
        "service": "sovereign-empire-api",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "admin": "/admin/dashboard",
            "create_order": "/api/orders/create"
        }
    }


@app.get("/health")
def health():
    """Health check for Railway"""
    try:
        session = get_session()
        session.execute(select(1))
        session.close()
        return JSONResponse({"status": "healthy", "database": "connected"}, status_code=200)
    except Exception as e:
        return JSONResponse({"status": "unhealthy", "error": str(e)}, status_code=503)


@app.get("/ping")
def ping():
    """Simple ping"""
    return {"ping": "pong", "timestamp": datetime.utcnow().isoformat()}


# ==================== PHASE 1: ORDER CREATION ====================

@app.post("/api/orders/create", response_model=OrderResponse, status_code=201)
async def create_order(order_data: OrderCreateRequest):
    """
    Create a new content generation order
    
    PHASE 1 ACCEPTANCE CRITERIA:
    ✓ Returns 201 on valid input
    ✓ Generates order_id in format ORD_[16 hex]
    ✓ Creates database record
    ✓ Returns 422 on validation errors
    ✓ Defaults status to PENDING
    ✓ Sets created_at to UTC timestamp
    """
    try:
        session = get_session()
        
        # Generate unique order ID
        order_id = f"ORD_{uuid.uuid4().hex[:16].upper()}"
        
        # Create order object
        new_order = Order(
            id=order_id,
            customer_email=order_data.customer_email,
            customer_name=order_data.customer_name,
            tenant_id=order_data.tenant_id,
            topic=order_data.topic,
            industry=order_data.industry,
            tone=order_data.tone,
            status=OrderStatus.PENDING,
            created_at=datetime.utcnow()
        )
        
        session.add(new_order)
        session.commit()
        session.refresh(new_order)
        
        print(f"✅ Order created: {order_id} for {order_data.customer_email}")
        
        session.close()
        
        return OrderResponse(
            order_id=order_id,
            status="pending",
            message="Order created successfully. Awaiting payment confirmation.",
            created_at=new_order.created_at.isoformat(),
            payment_url=None  # Will add PayPal URL in Phase 2
        )
        
    except Exception as e:
        if 'session' in locals():
            session.rollback()
            session.close()
        print(f"❌ Order creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


@app.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    """Get order details"""
    try:
        session = get_session()
        order = session.execute(
            select(Order).where(Order.id == order_id)
        ).scalar_one_or_none()
        
        if not order:
            session.close()
            raise HTTPException(status_code=404, detail="Order not found")
        
        order_data = {
            "id": order.id,
            "customer_email": order.customer_email,
            "customer_name": order.customer_name,
            "topic": order.topic,
            "industry": order.industry,
            "tone": order.tone,
            "status": order.status.value,
            "created_at": order.created_at.isoformat() if order.created_at else None,
            "completed_at": order.completed_at.isoformat() if order.completed_at else None,
            "amount_paid": order.amount_paid,
            "wordpress_post_url": order.wordpress_post_url,
            "error_message": order.error_message,
        }
        
        session.close()
        return order_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/orders")
async def list_orders(status: Optional[str] = None):
    """List all orders with optional status filter"""
    try:
        session = get_session()
        
        query = select(Order).order_by(Order.created_at.desc())
        
        if status and status != "all":
            try:
                status_enum = OrderStatus(status)
                query = query.where(Order.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        result = session.execute(query)
        orders = result.scalars().all()
        
        orders_data = [
            {
                "order_id": order.id,
                "customer_email": order.customer_email,
                "customer_name": order.customer_name,
                "topic": order.topic,
                "status": order.status.value,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "amount_paid": order.amount_paid,
                "error_message": order.error_message,
            }
            for order in orders
        ]
        
        session.close()
        
        return {"orders": orders_data, "total": len(orders_data)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ADMIN DASHBOARD ====================

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/admin/order/{order_id}", response_class=HTMLResponse)
async def order_detail_page(request: Request, order_id: str):
    """Order detail page"""
    try:
        session = get_session()
        order = session.execute(
            select(Order).where(Order.id == order_id)
        ).scalar_one_or_none()
        
        if not order:
            session.close()
            raise HTTPException(status_code=404, detail="Order not found")
        
        order_data = {
            "id": order.id,
            "customer_email": order.customer_email,
            "customer_name": order.customer_name,
            "topic": order.topic,
            "industry": order.industry,
            "tone": order.tone,
            "status": order.status.value,
            "created_at": order.created_at,
            "completed_at": order.completed_at,
            "amount_paid": order.amount_paid,
            "currency": order.currency,
            "total_tokens_used": order.total_tokens_used,
            "estimated_cost": order.estimated_cost,
            "wordpress_site_url": order.wordpress_site_url,
            "wordpress_post_url": order.wordpress_post_url,
            "error_message": order.error_message,
            "retry_count": order.retry_count,
        }
        
        session.close()
        
        return templates.TemplateResponse(
            "order_detail.html",
            {"request": request, "order": order_data}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== STATISTICS ====================

@app.get("/api/stats")
async def get_stats():
    """Get system statistics"""
    try:
        session = get_session()
        all_orders = session.execute(select(Order)).scalars().all()
        
        stats = {
            "total_orders": len(all_orders),
            "by_status": {},
            "total_revenue": 0.0,
        }
        
        for status in OrderStatus:
            count = len([o for o in all_orders if o.status == status])
            stats["by_status"][status.value] = count
        
        stats["total_revenue"] = sum(o.amount_paid or 0 for o in all_orders)
        
        session.close()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== MANUAL DELIVERY HELPERS ====================

@app.patch("/api/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str, note: Optional[str] = None):
    """
    Manual status update for Phase 1 delivery
    Use this to mark orders as paid, processing, completed manually
    """
    try:
        session = get_session()
        order = session.execute(
            select(Order).where(Order.id == order_id)
        ).scalar_one_or_none()
        
        if not order:
            session.close()
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Validate status
        try:
            new_status = OrderStatus(status)
        except ValueError:
            session.close()
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        order.status = new_status
        order.updated_at = datetime.utcnow()
        
        if status == "completed":
            order.completed_at = datetime.utcnow()
        
        if note:
            order.error_message = note  # Reuse field for admin notes
        
        session.commit()
        session.close()
        
        print(f"✅ Order {order_id} status updated to {status}")
        
        return {
            "success": True,
            "order_id": order_id,
            "new_status": status,
            "message": "Order status updated successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        if 'session' in locals():
            session.rollback()
            session.close()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PLACEHOLDERS FOR NEXT WEEK (PHASE 2) ====================

@app.post("/api/orders/{order_id}/payment/paypal")
async def create_paypal_payment(order_id: str):
    """
    PLACEHOLDER - Will implement in Phase 2 (Week 2)
    PayPal payment integration
    """
    return {
        "message": "PayPal integration - Phase 2 (next week)",
        "order_id": order_id,
        "status": "not_implemented"
    }


@app.post("/webhooks/paypal")
async def paypal_webhook(request: Request):
    """
    PLACEHOLDER - Will implement in Phase 2 (Week 2)
    PayPal IPN/Webhook handler
    """
    return {"received": True, "status": "not_implemented"}
