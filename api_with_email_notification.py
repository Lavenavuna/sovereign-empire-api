"""
api.py - Phase 1.5: Order Creation API + Email Notifications

Adds email notifications for new orders to sretonia@gmail.com
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import os
from database import init_database, get_session, Order, OrderStatus
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager
import uuid

# Email functionality
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email configuration
NOTIFICATION_EMAIL = "sretonia@gmail.com"
SENDER_NAME = "Sovereign Empire Content"
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.sendgrid.net")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")  # SendGrid username
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")  # SendGrid API key

# Order counter (for tracking first 50)
ORDER_COUNTER_FILE = "/tmp/order_count.txt"

def get_order_count():
    """Get current order count"""
    try:
        if os.path.exists(ORDER_COUNTER_FILE):
            with open(ORDER_COUNTER_FILE, 'r') as f:
                return int(f.read().strip())
        return 0
    except:
        return 0

def increment_order_count():
    """Increment and return new order count"""
    count = get_order_count() + 1
    try:
        with open(ORDER_COUNTER_FILE, 'w') as f:
            f.write(str(count))
    except:
        pass
    return count

def send_order_notification(order: Order):
    """Send email notification for new order"""
    
    # Get order count
    order_num = get_order_count()
    remaining = max(0, 50 - order_num)
    
    # Create email content
    subject = f"🎉 New Order Received - ${order.total_price:.2f}"
    
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px 10px 0 0;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 28px;
        }}
        .content {{
            background: #f9f9f9;
            padding: 30px;
            border-radius: 0 0 10px 10px;
        }}
        .section {{
            background: white;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .section-title {{
            font-size: 16px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .detail-row {{
            display: flex;
            padding: 8px 0;
            border-bottom: 1px solid #eee;
        }}
        .detail-row:last-child {{
            border-bottom: none;
        }}
        .detail-label {{
            font-weight: 600;
            width: 140px;
            color: #666;
        }}
        .detail-value {{
            flex: 1;
            color: #333;
        }}
        .action-button {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 12px 30px;
            text-decoration: none;
            border-radius: 5px;
            font-weight: 600;
            margin: 10px 0;
        }}
        .progress {{
            background: #e0e0e0;
            height: 24px;
            border-radius: 12px;
            overflow: hidden;
            margin: 15px 0;
        }}
        .progress-bar {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 12px;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 12px;
        }}
        .urgent {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>💰 New Order Received!</h1>
        <p style="margin: 10px 0 0 0; font-size: 18px;">Order #{order_num} of 50</p>
    </div>
    
    <div class="content">
        <div class="section">
            <div class="section-title">📋 Order Details</div>
            <div class="detail-row">
                <div class="detail-label">Order ID:</div>
                <div class="detail-value"><strong>{order.order_id}</strong></div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Customer:</div>
                <div class="detail-value">{order.customer_name or 'Not provided'}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Email:</div>
                <div class="detail-value"><a href="mailto:{order.customer_email}">{order.customer_email}</a></div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Date:</div>
                <div class="detail-value">{order.created_at.strftime('%B %d, %Y at %I:%M %p')}</div>
            </div>
        </div>
        
        <div class="section">
            <div class="section-title">📝 Content Details</div>
            <div class="detail-row">
                <div class="detail-label">Topic:</div>
                <div class="detail-value">{order.topic}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Industry:</div>
                <div class="detail-value">{order.industry or 'Not specified'}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Tone:</div>
                <div class="detail-value">{order.tone or 'Professional'}</div>
            </div>
            <div class="detail-row">
                <div class="detail-label">Amount:</div>
                <div class="detail-value"><strong>${order.total_price:.2f} USD</strong> (3 blog posts)</div>
            </div>
        </div>
        
        <div class="urgent">
            <strong>⚡ NEXT STEPS:</strong><br><br>
            1. Send PayPal invoice to: <strong>{order.customer_email}</strong><br>
            2. Amount: <strong>${order.total_price:.2f} USD</strong><br>
            3. Description: "3 Blog Posts - Order {order.order_id}"<br><br>
            <a href="https://www.paypal.com/invoice/create" class="action-button" target="_blank">
                Create PayPal Invoice
            </a>
        </div>
        
        <div class="section">
            <div class="section-title">📊 First 50 Progress</div>
            <div class="progress">
                <div class="progress-bar" style="width: {(order_num/50)*100}%">
                    {order_num} / 50 orders
                </div>
            </div>
            <p style="text-align: center; margin: 10px 0 0 0;">
                <strong>{remaining} spots remaining</strong> in launch promotion!
            </p>
        </div>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="https://sovereign-empire-api-production.up.railway.app/admin/dashboard" 
               class="action-button" target="_blank">
                View in Dashboard
            </a>
        </div>
    </div>
    
    <div class="footer">
        <p>This is an automated notification from Sovereign Empire Content</p>
        <p>Order received at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Fiji Time)</p>
    </div>
</body>
</html>
    """
    
    text_content = f"""
NEW ORDER RECEIVED!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Order #{order_num} of 50

ORDER DETAILS:
Order ID: {order.order_id}
Customer: {order.customer_name or 'Not provided'}
Email: {order.customer_email}
Date: {order.created_at.strftime('%B %d, %Y at %I:%M %p')}

CONTENT DETAILS:
Topic: {order.topic}
Industry: {order.industry or 'Not specified'}
Tone: {order.tone or 'Professional'}
Amount: ${order.total_price:.2f} USD (3 blog posts)

NEXT STEPS:
1. Send PayPal invoice to: {order.customer_email}
2. Amount: ${order.total_price:.2f} USD
3. Description: "3 Blog Posts - Order {order.order_id}"

Create invoice: https://www.paypal.com/invoice/create

PROGRESS:
{order_num} / 50 orders ({remaining} spots remaining)

View dashboard: https://sovereign-empire-api-production.up.railway.app/admin/dashboard

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Sovereign Empire Content
Automated notification
    """
    
    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{SENDER_NAME} <{SMTP_USER}>"
        msg['To'] = NOTIFICATION_EMAIL
        msg['Reply-To'] = NOTIFICATION_EMAIL
        
        # Attach both plain text and HTML
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        if SMTP_USER and SMTP_PASSWORD:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASSWORD)
                server.send_message(msg)
            print(f"✅ Email notification sent to {NOTIFICATION_EMAIL}")
        else:
            print(f"⚠️  Email not configured. Would have sent to: {NOTIFICATION_EMAIL}")
            print(f"   Subject: {subject}")
    
    except Exception as e:
        print(f"❌ Failed to send email notification: {e}")
        # Don't fail the order creation if email fails


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup"""
    print("Initializing database...")
    init_database()
    print("Database initialized successfully")
    yield
    print("Shutting down...")


app = FastAPI(
    title="Sovereign Empire Content API",
    description="AI-powered blog post generation service",
    version="1.5.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
class OrderCreateRequest(BaseModel):
    customer_email: EmailStr
    customer_name: Optional[str] = None
    tenant_id: str = Field(default="DIRECT_CUSTOMER")
    topic: str = Field(min_length=5, max_length=500)
    industry: Optional[str] = None
    tone: Optional[str] = "professional"
    wordpress_url: Optional[str] = None


class OrderResponse(BaseModel):
    order_id: str
    status: str
    message: str
    created_at: datetime
    payment_url: Optional[str] = None


# API Endpoints
@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint"""
    return """
    <html>
        <head>
            <title>Sovereign Empire Content API</title>
            <style>
                body {
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    max-width: 800px;
                    margin: 50px auto;
                    padding: 20px;
                    background: #f5f5f5;
                }
                .container {
                    background: white;
                    padding: 40px;
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 { color: #667eea; }
                .links { margin-top: 30px; }
                .links a {
                    display: inline-block;
                    margin: 10px 10px 10px 0;
                    padding: 10px 20px;
                    background: #667eea;
                    color: white;
                    text-decoration: none;
                    border-radius: 5px;
                }
                .links a:hover { background: #5a67d8; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏛️ Sovereign Empire Content API</h1>
                <p>AI-powered blog post generation service</p>
                <div class="links">
                    <a href="/docs">📚 API Documentation</a>
                    <a href="/admin/dashboard">📊 Admin Dashboard</a>
                    <a href="/health">💚 Health Check</a>
                </div>
                <p style="margin-top: 30px; color: #666;">
                    <strong>Email Notifications:</strong> Enabled ✓<br>
                    <strong>Notification Email:</strong> sretonia@gmail.com<br>
                    <strong>Status:</strong> Online and ready!
                </p>
            </div>
        </body>
    </html>
    """


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "sovereign-empire-api",
        "version": "1.5.0",
        "database": "connected",
        "email_notifications": "enabled" if SMTP_USER else "disabled",
        "notification_email": NOTIFICATION_EMAIL if SMTP_USER else "not configured"
    }


@app.post("/api/orders/create", response_model=OrderResponse)
async def create_order(order_request: OrderCreateRequest):
    """Create a new order"""
    
    try:
        # Generate unique order ID
        order_id = f"ORD_{uuid.uuid4().hex[:12].upper()}"
        
        # Create order in database
        with get_session() as session:
            order = Order(
                order_id=order_id,
                customer_email=order_request.customer_email,
                customer_name=order_request.customer_name,
                tenant_id=order_request.tenant_id,
                topic=order_request.topic,
                industry=order_request.industry,
                tone=order_request.tone,
                status=OrderStatus.PENDING,
                total_price=79.00,  # First 50 customers promotion
                wordpress_url=order_request.wordpress_url
            )
            
            session.add(order)
            session.commit()
            session.refresh(order)
            
            # Increment order counter
            increment_order_count()
            
            # Send email notification
            send_order_notification(order)
            
            return OrderResponse(
                order_id=order.order_id,
                status=order.status.value,
                message="Order created successfully. Awaiting payment confirmation.",
                created_at=order.created_at,
                payment_url=None  # Will be added in Week 2 with PayPal automation
            )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")


@app.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    """Get order details"""
    
    with get_session() as session:
        order = session.query(Order).filter(Order.order_id == order_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return {
            "order_id": order.order_id,
            "customer_email": order.customer_email,
            "customer_name": order.customer_name,
            "topic": order.topic,
            "industry": order.industry,
            "tone": order.tone,
            "status": order.status.value,
            "total_price": order.total_price,
            "created_at": order.created_at,
            "updated_at": order.updated_at
        }


@app.get("/orders")
async def list_orders(status: Optional[str] = None):
    """List all orders with optional status filter"""
    
    with get_session() as session:
        query = session.query(Order)
        
        if status:
            try:
                status_enum = OrderStatus(status)
                query = query.filter(Order.status == status_enum)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        
        orders = query.order_by(Order.created_at.desc()).all()
        
        return {
            "total": len(orders),
            "orders": [
                {
                    "order_id": order.order_id,
                    "customer_email": order.customer_email,
                    "customer_name": order.customer_name,
                    "topic": order.topic,
                    "status": order.status.value,
                    "total_price": order.total_price,
                    "created_at": order.created_at
                }
                for order in orders
            ]
        }


@app.patch("/api/orders/{order_id}/status")
async def update_order_status(order_id: str, status: str):
    """Update order status"""
    
    try:
        status_enum = OrderStatus(status)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {[s.value for s in OrderStatus]}"
        )
    
    with get_session() as session:
        order = session.query(Order).filter(Order.order_id == order_id).first()
        
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        order.status = status_enum
        order.updated_at = datetime.utcnow()
        session.commit()
        
        return {
            "order_id": order.order_id,
            "status": order.status.value,
            "message": f"Order status updated to {status}",
            "updated_at": order.updated_at
        }


@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard():
    """Admin dashboard to view all orders"""
    
    with get_session() as session:
        orders = session.query(Order).order_by(Order.created_at.desc()).all()
        
        # Calculate statistics
        total_orders = len(orders)
        pending = len([o for o in orders if o.status == OrderStatus.PENDING])
        completed = len([o for o in orders if o.status == OrderStatus.COMPLETED])
        failed = len([o for o in orders if o.status == OrderStatus.FAILED])
        
        # Get order count for first 50 tracking
        order_count = get_order_count()
        remaining = max(0, 50 - order_count)
        
        orders_html = ""
        for order in orders:
            status_class = {
                OrderStatus.PENDING: "pending",
                OrderStatus.PAID: "paid",
                OrderStatus.PROCESSING: "processing",
                OrderStatus.COMPLETED: "completed",
                OrderStatus.FAILED: "failed"
            }.get(order.status, "pending")
            
            orders_html += f"""
            <tr>
                <td>{order.order_id}</td>
                <td>{order.customer_email}</td>
                <td>{order.topic[:50]}...</td>
                <td><span class="status-badge {status_class}">{order.status.value.upper()}</span></td>
                <td>{order.created_at.strftime('%m/%d/%Y, %I:%M %p')}</td>
                <td>${order.total_price:.3f}</td>
                <td>
                    <button class="action-btn" onclick="viewOrder('{order.order_id}')">View</button>
                </td>
            </tr>
            """
        
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sovereign Empire - Ops Console</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            padding: 30px;
            border-radius: 15px 15px 0 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            color: #667eea;
            font-size: 32px;
            margin-bottom: 5px;
        }}
        
        .header p {{
            color: #666;
            font-size: 16px;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .stat-card h3 {{
            color: #666;
            font-size: 14px;
            font-weight: 500;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-card .number {{
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
        }}
        
        .promo-tracker {{
            background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
            color: white;
            padding: 25px;
            border-radius: 10px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(245, 158, 11, 0.3);
        }}
        
        .promo-tracker h3 {{
            font-size: 18px;
            margin-bottom: 15px;
        }}
        
        .progress-bar {{
            background: rgba(255, 255, 255, 0.3);
            height: 30px;
            border-radius: 15px;
            overflow: hidden;
            margin: 15px 0;
        }}
        
        .progress-fill {{
            background: white;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: #d97706;
            transition: width 0.3s ease;
        }}
        
        .filters {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            gap: 15px;
            align-items: center;
            flex-wrap: wrap;
        }}
        
        .filter-btn {{
            padding: 10px 20px;
            border: 2px solid #e0e0e0;
            background: white;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            font-weight: 500;
            transition: all 0.2s;
        }}
        
        .filter-btn:hover {{
            border-color: #667eea;
            color: #667eea;
        }}
        
        .filter-btn.active {{
            background: #667eea;
            color: white;
            border-color: #667eea;
        }}
        
        .refresh-btn {{
            margin-left: auto;
            padding: 10px 25px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .refresh-btn:hover {{
            background: #5a67d8;
        }}
        
        .orders-table {{
            background: white;
            border-radius: 0 0 15px 15px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        
        th {{
            background: #f8f9fa;
            padding: 15px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #e0e0e0;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 1px;
        }}
        
        td {{
            padding: 15px;
            border-bottom: 1px solid #e0e0e0;
            color: #555;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        .status-badge {{
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .status-badge.pending {{
            background: #fef3c7;
            color: #92400e;
        }}
        
        .status-badge.paid {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .status-badge.processing {{
            background: #dbeafe;
            color: #1e40af;
        }}
        
        .status-badge.completed {{
            background: #d1fae5;
            color: #065f46;
        }}
        
        .status-badge.failed {{
            background: #fee2e2;
            color: #991b1b;
        }}
        
        .action-btn {{
            padding: 8px 16px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 13px;
            font-weight: 500;
        }}
        
        .action-btn:hover {{
            background: #5a67d8;
        }}
        
        .email-status {{
            background: #d1fae5;
            color: #065f46;
            padding: 10px 20px;
            border-radius: 5px;
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 14px;
            font-weight: 500;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ Sovereign Empire - Ops Console</h1>
            <p>Content Generation Management Dashboard</p>
            <div class="email-status">
                ✓ Email Notifications: Active (sretonia@gmail.com)
            </div>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>Total Orders</h3>
                <div class="number">{total_orders}</div>
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
        
        <div class="promo-tracker">
            <h3>🎉 First 50 Customers Promotion</h3>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {(order_count/50)*100}%">
                    {order_count} / 50 orders
                </div>
            </div>
            <p style="text-align: center; margin-top: 10px; font-size: 18px; font-weight: bold;">
                {remaining} spots remaining at $79 for 3 posts!
            </p>
        </div>
        
        <div class="filters">
            <button class="filter-btn active" onclick="filterOrders('all')">All Orders</button>
            <button class="filter-btn" onclick="filterOrders('pending')">Pending Approval</button>
            <button class="filter-btn" onclick="filterOrders('failed')">Failed</button>
            <button class="filter-btn" onclick="filterOrders('completed')">Completed</button>
            <button class="refresh-btn" onclick="location.reload()">
                🔄 Refresh
            </button>
        </div>
        
        <div class="orders-table">
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
                    {orders_html if orders_html else '<tr><td colspan="7" style="text-align: center; padding: 40px;">No orders yet</td></tr>'}
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        function filterOrders(status) {{
            // Update active button
            document.querySelectorAll('.filter-btn').forEach(btn => {{
                btn.classList.remove('active');
            }});
            event.target.classList.add('active');
            
            // Filter table rows
            const rows = document.querySelectorAll('tbody tr');
            rows.forEach(row => {{
                if (status === 'all') {{
                    row.style.display = '';
                }} else {{
                    const statusCell = row.querySelector('.status-badge');
                    if (statusCell && statusCell.classList.contains(status)) {{
                        row.style.display = '';
                    }} else {{
                        row.style.display = 'none';
                    }}
                }}
            }});
        }}
        
        function viewOrder(orderId) {{
            window.location.href = `/api/orders/${{orderId}}`;
        }}
    </script>
</body>
</html>
        """


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
