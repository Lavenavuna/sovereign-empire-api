"""
api.py - FastAPI entrypoint with admin dashboard support
"""
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from database import init_database, get_session, Order, OrderStatus

app = FastAPI(
    title="Sovereign Empire Content API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Template support for admin dashboard
templates = Jinja2Templates(directory="templates")


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


@app.get("/")
def root():
    """Root endpoint - simple health check"""
    return {
        "status": "ok",
        "service": "sovereign-empire-api",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    """Health check endpoint for Railway"""
    try:
        # Test database connection
        session = get_session()
        session.execute(select(1))
        session.close()
        
        return JSONResponse(
            {"status": "healthy", "database": "connected"},
            status_code=200
        )
    except Exception as e:
        return JSONResponse(
            {"status": "unhealthy", "error": str(e)},
            status_code=503
        )


@app.get("/ping")
def ping():
    """Simple ping endpoint (no DB check)"""
    return {"ping": "pong"}


# ==================== ADMIN DASHBOARD ENDPOINTS ====================

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Render the admin dashboard HTML"""
    return templates.TemplateResponse("dashboard.html", {"request": request})


@app.get("/orders")
async def list_orders(status: Optional[str] = None):
    """
    Get all orders, optionally filtered by status
    Query param: ?status=pending_approval
    """
    try:
        session = get_session()
        
        # Build query
        query = select(Order).order_by(Order.created_at.desc())
        
        # Filter by status if provided
        if status and status != "all":
            try:
                status_enum = OrderStatus(status)
                query = query.where(Order.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        # Execute query
        result = session.execute(query)
        orders = result.scalars().all()
        
        # Convert to dict for JSON response
        orders_data = [
            {
                "order_id": order.id,
                "customer_email": order.customer_email,
                "customer_name": order.customer_name,
                "topic": order.topic,
                "status": order.status.value,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "completed_at": order.completed_at.isoformat() if order.completed_at else None,
                "cost": order.estimated_cost,
                "amount_paid": order.amount_paid,
                "error_message": order.error_message,
            }
            for order in orders
        ]
        
        session.close()
        
        return {"orders": orders_data, "total": len(orders_data)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/order/{order_id}", response_class=HTMLResponse)
async def order_detail_page(request: Request, order_id: str):
    """Render order detail page"""
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


@app.get("/api/order/{order_id}")
async def get_order(order_id: str):
    """Get order details as JSON"""
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
            "currency": order.currency,
            "total_tokens_used": order.total_tokens_used,
            "estimated_cost": order.estimated_cost,
            "wordpress_site_url": order.wordpress_site_url,
            "wordpress_post_url": order.wordpress_post_url,
            "error_message": order.error_message,
            "retry_count": order.retry_count,
        }
        
        session.close()
        return order_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/retry/{order_id}")
async def retry_order(order_id: str):
    """
    Retry a failed order
    This sets the status back to PENDING and increments retry_count
    """
    try:
        session = get_session()
        order = session.execute(
            select(Order).where(Order.id == order_id)
        ).scalar_one_or_none()
        
        if not order:
            session.close()
            raise HTTPException(status_code=404, detail="Order not found")
        
        # Only retry failed orders
        if order.status != OrderStatus.FAILED:
            session.close()
            raise HTTPException(
                status_code=400,
                detail=f"Cannot retry order with status: {order.status.value}"
            )
        
        # Reset to pending and increment retry count
        order.status = OrderStatus.PENDING
        order.retry_count += 1
        order.error_message = None
        
        session.commit()
        session.close()
        
        return {
            "success": True,
            "message": f"Order {order_id} queued for retry",
            "retry_count": order.retry_count
        }
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        session.close()
        raise HTTPException(status_code=500, detail=str(e))


# ==================== PLACEHOLDER FOR YOUR BUSINESS LOGIC ====================
# Add your order creation, payment webhooks, content generation endpoints here
# Example:
#
# @app.post("/api/orders/create")
# async def create_order(order_data: OrderCreateRequest):
#     # Your logic here
#     pass
#
# @app.post("/webhooks/stripe")
# async def stripe_webhook(request: Request):
#     # Your Stripe webhook handler
#     pass
