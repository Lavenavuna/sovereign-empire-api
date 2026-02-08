"""
Sovereign Empire API - Clean Working Version
Minimal, reliable API for order management
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
from typing import Optional, List
import os
import uuid

# ============================================================================
# DATABASE SETUP
# ============================================================================

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./orders.db")

# Fix for Railway PostgreSQL URL
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ============================================================================
# DATABASE MODELS
# ============================================================================

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String, unique=True, index=True)
    customer_name = Column(String)
    customer_email = Column(String)
    industry = Column(String, nullable=True)
    topic = Column(String)
    wordpress_url = Column(String, nullable=True)
    tenant_id = Column(String, default="DIRECT_CUSTOMER")
    status = Column(String, default="PENDING")
    cost = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


# Create tables
Base.metadata.create_all(bind=engine)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class OrderCreate(BaseModel):
    customer_name: str
    customer_email: EmailStr
    industry: Optional[str] = None
    topic: str
    wordpress_url: Optional[str] = None
    tenant_id: str = "DIRECT_CUSTOMER"


class OrderResponse(BaseModel):
    order_id: str
    customer_name: str
    customer_email: str
    industry: Optional[str]
    topic: str
    wordpress_url: Optional[str]
    tenant_id: str
    status: str
    cost: float
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(
    title="Sovereign Empire API",
    description="Content Generation Management System",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# DATABASE DEPENDENCY
# ============================================================================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# ROUTES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint"""
    return """
    <html>
        <head>
            <title>Sovereign Empire API</title>
            <style>
                body { font-family: Arial; text-align: center; padding: 50px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
                h1 { font-size: 48px; margin-bottom: 20px; }
                a { color: white; text-decoration: none; background: rgba(255,255,255,0.2); padding: 15px 30px; border-radius: 8px; display: inline-block; margin: 10px; }
                a:hover { background: rgba(255,255,255,0.3); }
            </style>
        </head>
        <body>
            <h1>🏛️ Sovereign Empire API</h1>
            <p>Content Generation Management System</p>
            <br>
            <a href="/admin/dashboard">📊 Dashboard</a>
            <a href="/docs">📚 API Docs</a>
            <a href="/health">💚 Health Check</a>
        </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post("/api/orders/create", response_model=OrderResponse)
async def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    """Create a new order"""
    try:
        # Generate unique order ID
        order_id = f"ORD_{uuid.uuid4().hex[:12].upper()}"
        
        # Create order object
        new_order = Order(
            order_id=order_id,
            customer_name=order.customer_name,
            customer_email=order.customer_email,
            industry=order.industry,
            topic=order.topic,
            wordpress_url=order.wordpress_url,
            tenant_id=order.tenant_id,
            status="PENDING",
            cost=0.0,
            created_at=datetime.utcnow()
        )
        
        # Save to database
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        
        return new_order
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


@app.get("/api/orders", response_model=List[OrderResponse])
async def list_orders(db: Session = Depends(get_db)):
    """List all orders"""
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    return orders


@app.get("/api/orders/{order_id}", response_model=OrderResponse)
async def get_order(order_id: str, db: Session = Depends(get_db)):
    """Get specific order"""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.put("/api/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str, db: Session = Depends(get_db)):
    """Update order status"""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order.status = status
    db.commit()
    
    return {"message": "Status updated", "order_id": order_id, "new_status": status}


@app.delete("/api/orders/{order_id}")
async def delete_order(order_id: str, db: Session = Depends(get_db)):
    """Delete an order"""
    order = db.query(Order).filter(Order.order_id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    db.delete(order)
    db.commit()
    
    return {"message": "Order deleted", "order_id": order_id}


# ============================================================================
# ADMIN DASHBOARD
# ============================================================================

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(db: Session = Depends(get_db)):
    """Admin dashboard to view and manage orders"""
    
    # Get orders
    orders = db.query(Order).order_by(Order.created_at.desc()).all()
    
    # Count by status
    total = len(orders)
    pending = len([o for o in orders if o.status == "PENDING"])
    completed = len([o for o in orders if o.status == "COMPLETED"])
    failed = len([o for o in orders if o.status == "FAILED"])
    
    # Generate order rows HTML
    order_rows = ""
    for order in orders:
        status_color = {
            "PENDING": "#ffc107",
            "COMPLETED": "#28a745",
            "FAILED": "#dc3545"
        }.get(order.status, "#6c757d")
        
        order_rows += f"""
        <tr>
            <td>{order.order_id}</td>
            <td>{order.customer_email}</td>
            <td>{order.topic}</td>
            <td><span style="background: {status_color}; color: white; padding: 5px 10px; border-radius: 4px; font-size: 12px; font-weight: bold;">{order.status}</span></td>
            <td>{order.created_at.strftime('%m/%d/%Y, %I:%M:%S %p')}</td>
            <td>${order.cost:.3f}</td>
            <td>
                <button onclick="viewOrder('{order.order_id}')" style="background: #667eea; color: white; border: none; padding: 8px 16px; border-radius: 4px; cursor: pointer; font-weight: 600;">View</button>
            </td>
        </tr>
        """
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Sovereign Empire - Admin Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: #0f1419;
                color: #e1e8ed;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                padding: 40px;
                border-radius: 12px;
                margin-bottom: 30px;
                text-align: center;
            }}
            .header h1 {{ font-size: 36px; margin-bottom: 10px; }}
            .header p {{ font-size: 16px; opacity: 0.9; }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: #192734;
                padding: 25px;
                border-radius: 12px;
                border: 1px solid #38444d;
            }}
            .stat-card h3 {{ color: #8899a6; font-size: 14px; margin-bottom: 10px; }}
            .stat-card .number {{ font-size: 32px; font-weight: bold; color: #fff; }}
            .controls {{
                margin-bottom: 20px;
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }}
            .btn {{
                padding: 10px 20px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-weight: 600;
                font-size: 14px;
            }}
            .btn-primary {{ background: #667eea; color: white; }}
            .btn-secondary {{ background: #38444d; color: white; }}
            .table-container {{
                background: #192734;
                border-radius: 12px;
                overflow: hidden;
                border: 1px solid #38444d;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
            }}
            th {{
                background: #1c2938;
                padding: 15px;
                text-align: left;
                font-weight: 600;
                color: #8899a6;
                font-size: 12px;
                text-transform: uppercase;
            }}
            td {{
                padding: 15px;
                border-top: 1px solid #38444d;
            }}
            tr:hover {{
                background: #1c2938;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🏛️ Sovereign Empire - Ops Console</h1>
            <p>Content Generation Management Dashboard</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>Total Orders</h3>
                <div class="number">{total}</div>
            </div>
            <div class="stat-card">
                <h3>Pending Approval</h3>
                <div class="number">{pending}</div>
            </div>
            <div class="stat-card">
                <h3>Failed</h3>
                <div class="number">{failed}</div>
            </div>
            <div class="stat-card">
                <h3>Completed</h3>
                <div class="number">{completed}</div>
            </div>
        </div>
        
        <div class="controls">
            <button class="btn btn-primary" onclick="location.reload()">🔄 Refresh</button>
            <button class="btn btn-secondary" onclick="window.location.href='/docs'">📚 API Docs</button>
        </div>
        
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ORDER ID</th>
                        <th>CUSTOMER</th>
                        <th>TOPIC</th>
                        <th>STATUS</th>
                        <th>CREATED</th>
                        <th>COST</th>
                        <th>ACTIONS</th>
                    </tr>
                </thead>
                <tbody>
                    {order_rows if order_rows else '<tr><td colspan="7" style="text-align: center; padding: 40px; color: #8899a6;">No orders yet</td></tr>'}
                </tbody>
            </table>
        </div>
        
        <script>
            function viewOrder(orderId) {{
                window.location.href = `/api/orders/${{orderId}}`;
            }}
        </script>
    </body>
    </html>
    """
    
    return html


# ============================================================================
# STARTUP
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
