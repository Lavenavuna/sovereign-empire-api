"""
Sovereign Empire API - Complete with One-Time & Monthly Subscriptions
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
import uuid

app = FastAPI(title="Sovereign Empire API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ENHANCED DATABASE WITH SUBSCRIPTIONS
orders_db = [
    # One-Time Orders
    {
        "order_id": "ORD-0001",
        "customer_name": "John Smith",
        "customer_email": "john@example.com",
        "industry": "Dental Practice",
        "topic": "Dental SEO",
        "wordpress_url": "https://johnsdental.com",
        "tenant_id": "DIRECT_CUSTOMER",
        "order_type": "one_time",  # NEW: order_type field
        "package_type": "dominance",
        "status": "completed",
        "price": 497.00,
        "paid": True,
        "created_at": "2024-01-01T10:00:00",
        "next_billing_date": None  # NEW: For subscriptions
    },
    {
        "order_id": "ORD-0002",
        "customer_name": "Sarah Johnson",
        "customer_email": "sarah@example.com",
        "industry": "Plumbing",
        "topic": "Local Plumbing SEO",
        "wordpress_url": "https://sarahsplumbing.com",
        "tenant_id": "DIRECT_CUSTOMER",
        "order_type": "one_time",
        "package_type": "dominance",
        "status": "in_progress",
        "price": 497.00,
        "paid": True,
        "created_at": "2024-01-02T11:30:00",
        "next_billing_date": None
    },
    {
        "order_id": "ORD-0003",
        "customer_name": "Mike Wilson",
        "customer_email": "mike@example.com",
        "industry": "Law Firm",
        "topic": "Legal Services Marketing",
        "wordpress_url": "https://wilsonlaw.com",
        "tenant_id": "DIRECT_CUSTOMER",
        "order_type": "one_time",
        "package_type": "boost",
        "status": "pending",
        "price": 359.00,
        "paid": True,
        "created_at": "2024-01-03T14:45:00",
        "next_billing_date": None
    },
    # Monthly Subscriptions - NEW!
    {
        "order_id": "SUB-0001",
        "customer_name": "Emma Davis",
        "customer_email": "emma@example.com",
        "industry": "HVAC Services",
        "topic": "Monthly SEO Maintenance",
        "wordpress_url": "https://davishvac.com",
        "tenant_id": "DIRECT_CUSTOMER",
        "order_type": "monthly",  # MONTHLY SUBSCRIPTION
        "package_type": "retainer",
        "status": "active",
        "price": 297.00,
        "paid": True,
        "created_at": "2024-01-04T09:15:00",
        "next_billing_date": "2024-02-04T09:15:00",  # Next billing date
        "billing_cycle": "monthly",
        "total_billed": 297.00  # Total collected so far
    },
    {
        "order_id": "ORD-0005",
        "customer_name": "Robert Brown",
        "customer_email": "robert@example.com",
        "industry": "Car Detailing",
        "topic": "Auto Detailing Marketing",
        "wordpress_url": "https://browndetailing.com",
        "tenant_id": "DIRECT_CUSTOMER",
        "order_type": "one_time",
        "package_type": "boost",
        "status": "pending",
        "price": 359.00,
        "paid": True,
        "created_at": "2024-01-05T16:20:00",
        "next_billing_date": None
    },
    {
        "order_id": "SUB-0002",
        "customer_name": "Lisa Taylor",
        "customer_email": "lisa@example.com",
        "industry": "Cleaning Services",
        "topic": "Monthly Content Strategy",
        "wordpress_url": "https://taylorcleaning.com",
        "tenant_id": "DIRECT_CUSTOMER",
        "order_type": "monthly",  # MONTHLY SUBSCRIPTION
        "package_type": "retainer",
        "status": "active",
        "price": 297.00,
        "paid": True,
        "created_at": "2024-01-06T13:10:00",
        "next_billing_date": "2024-02-06T13:10:00",
        "billing_cycle": "monthly",
        "total_billed": 297.00
    }
]

# Pydantic Models
class OrderCreate(BaseModel):
    customer_name: str
    customer_email: str
    industry: str
    topic: str
    wordpress_url: Optional[str] = ""
    tenant_id: str
    order_type: str = "one_time"  # "one_time" or "monthly"
    package_type: str = "dominance"  # "boost", "dominance", or "retainer"
    price: float = 497.00
    paid: bool = False

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    price: Optional[float] = None
    paid: Optional[bool] = None
    package_type: Optional[str] = None
    order_type: Optional[str] = None
    next_billing_date: Optional[str] = None

# Root endpoint
@app.get("/")
async def root():
    total_one_time = sum(order["price"] for order in orders_db if order.get("order_type") == "one_time")
    total_monthly = sum(order.get("total_billed", 0) for order in orders_db if order.get("order_type") == "monthly")
    monthly_mrr = sum(order["price"] for order in orders_db if order.get("order_type") == "monthly" and order.get("status") == "active")
    
    return {
        "service": "Sovereign Empire API",
        "status": "online",
        "version": "3.0.0",
        "features": ["one_time_packages", "monthly_subscriptions", "revenue_tracking", "mrr_calculation"],
        "revenue_summary": {
            "one_time_total": total_one_time,
            "monthly_total": total_monthly,
            "monthly_recurring_revenue": monthly_mrr,
            "total_revenue": total_one_time + total_monthly
        }
    }

# Create new order (supports both one-time and monthly)
@app.post("/api/orders/create")
async def create_order(order: OrderCreate):
    try:
        # Determine order ID prefix
        if order.order_type == "monthly":
            order_prefix = "SUB"
            monthly_orders = [o for o in orders_db if o.get("order_type") == "monthly"]
            order_number = len(monthly_orders) + 1
        else:
            order_prefix = "ORD"
            one_time_orders = [o for o in orders_db if o.get("order_type") == "one_time"]
            order_number = len(one_time_orders) + 1
        
        order_id = f"{order_prefix}-{order_number:04d}"
        
        # Set price based on package type
        if order.package_type == "boost":
            price = 359.00
        elif order.package_type == "dominance":
            price = 497.00
        elif order.package_type == "retainer":
            price = 297.00
        else:
            price = order.price
        
        # Calculate next billing date for subscriptions
        next_billing_date = None
        total_billed = 0
        
        if order.order_type == "monthly" and order.paid:
            next_billing_date = (datetime.now() + timedelta(days=30)).isoformat()
            total_billed = price
        
        new_order = {
            "order_id": order_id,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "industry": order.industry,
            "topic": order.topic,
            "wordpress_url": order.wordpress_url,
            "tenant_id": order.tenant_id,
            "order_type": order.order_type,
            "package_type": order.package_type,
            "status": "pending" if order.order_type == "one_time" else "active",
            "price": price,
            "paid": order.paid,
            "created_at": datetime.now().isoformat(),
            "next_billing_date": next_billing_date,
            "billing_cycle": "monthly" if order.order_type == "monthly" else None,
            "total_billed": total_billed
        }
        
        orders_db.append(new_order)
        return new_order
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")

# ADMIN DASHBOARD WITH MONTHLY SUBSCRIPTION TRACKING
@app.get("/admin/dashboard")
async def admin_dashboard():
    # Calculate all revenue metrics
    one_time_orders = [o for o in orders_db if o.get("order_type") == "one_time"]
    monthly_orders = [o for o in orders_db if o.get("order_type") == "monthly"]
    
    # One-time revenue
    one_time_total = sum(order["price"] for order in one_time_orders)
    one_time_paid = sum(order["price"] for order in one_time_orders if order.get("paid") == True)
    
    # Monthly subscription metrics
    monthly_mrr = sum(order["price"] for order in monthly_orders if order.get("status") == "active")
    monthly_total_billed = sum(order.get("total_billed", 0) for order in monthly_orders)
    active_subscriptions = len([o for o in monthly_orders if o.get("status") == "active"])
    
    # Package breakdown
    boost_orders = [o for o in orders_db if o.get("package_type") == "boost"]
    dominance_orders = [o for o in orders_db if o.get("package_type") == "dominance"]
    retainer_orders = [o for o in orders_db if o.get("package_type") == "retainer"]
    
    # Status counts
    status_counts = {}
    for order in orders_db:
        status = order.get("status", "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Generate HTML dashboard
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Business Dashboard - One-Time & Monthly Revenue</title>
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f5f5;
                color: #333;
            }}
            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            header {{
                background: linear-gradient(135deg, #1a2980 0%, #26d0ce 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
            }}
            h1 {{
                margin: 0;
                font-size: 2.5em;
            }}
            
            /* Revenue Overview */
            .revenue-overview {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .revenue-card {{
                background: white;
                padding: 25px;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
                text-align: center;
            }}
            .revenue-number {{
                font-size: 2.5em;
                font-weight: bold;
                margin: 10px 0;
            }}
            .revenue-one-time {{ color: #667eea; }}
            .revenue-monthly {{ color: #10b981; }}
            .revenue-total {{ color: #8b5cf6; }}
            .revenue-mrr {{ color: #f59e0b; }}
            
            /* Subscription Stats */
            .subscription-stats {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            }}
            .subscription-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-top: 20px;
            }}
            .subscription-item {{
                text-align: center;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
            }}
            
            /* Package Breakdown */
            .package-breakdown {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .package-card {{
                background: white;
                padding: 25px;
                border-radius: 10px;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
            }}
            .package-header {{
                font-size: 1.5em;
                font-weight: bold;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .package-boost {{ color: #3b82f6; }}
            .package-dominance {{ color: #8b5cf6; }}
            .package-retainer {{ color: #10b981; }}
            
            /* Orders Table */
            .orders-table {{
                background: white;
                border-radius: 10px;
                overflow: hidden;
                box-shadow: 0 5px 15px rgba(0,0,0,0.08);
                margin-top: 30px;
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
                color: #495057;
                border-bottom: 2px solid #e9ecef;
            }}
            td {{
                padding: 15px;
                border-bottom: 1px solid #e9ecef;
            }}
            tr:hover {{
                background: #f8f9fa;
            }}
            
            /* Badges */
            .badge {{
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: 600;
                display: inline-block;
            }}
            .type-one_time {{ background: #dbeafe; color: #1e40af; }}
            .type-monthly {{ background: #d1fae5; color: #065f46; }}
            .status-active {{ background: #d1fae5; color: #065f46; }}
            .status-pending {{ background: #fef3c7; color: #92400e; }}
            .status-in_progress {{ background: #dbeafe; color: #1e40af; }}
            .status-completed {{ background: #dcfce7; color: #166534; }}
            .package-boost-badge {{ background: #dbeafe; color: #1e40af; }}
            .package-dominance-badge {{ background: #ede9fe; color: #5b21b6; }}
            .package-retainer-badge {{ background: #d1fae5; color: #065f46; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📊 Business Dashboard</h1>
                <p>One-Time Sales & Monthly Recurring Revenue Tracking</p>
            </header>
            
            <!-- REVENUE OVERVIEW -->
            <div class="revenue-overview">
                <div class="revenue-card">
                    <div>💰 One-Time Revenue</div>
                    <div class="revenue-number revenue-one-time">${one_time_total:,.2f}</div>
                    <div>{len(one_time_orders)} orders • ${one_time_paid:,.2f} paid</div>
                </div>
                
                <div class="revenue-card">
                    <div>🔄 Monthly Revenue (MRR)</div>
                    <div class="revenue-number revenue-mrr">${monthly_mrr:,.2f}/mo</div>
                    <div>{active_subscriptions} active subscriptions</div>
                </div>
                
                <div class="revenue-card">
                    <div>📈 Total Monthly Billed</div>
                    <div class="revenue-number revenue-monthly">${monthly_total_billed:,.2f}</div>
                    <div>All subscription payments to date</div>
                </div>
                
                <div class="revenue-card">
                    <div>🏆 Total Business Value</div>
                    <div class="revenue-number revenue-total">${one_time_total + monthly_total_billed:,.2f}</div>
                    <div>Combined revenue streams</div>
                </div>
            </div>
            
            <!-- SUBSCRIPTION STATS -->
            <div class="subscription-stats">
                <h3 style="margin-top: 0;">🔄 Subscription Analytics</h3>
                <div class="subscription-grid">
                    <div class="subscription-item">
                        <div style="font-size: 2em; font-weight: bold; color: #10b981;">{active_subscriptions}</div>
                        <div>Active Subscriptions</div>
                    </div>
                    <div class="subscription-item">
                        <div style="font-size: 2em; font-weight: bold; color: #f59e0b;">${monthly_mrr * 12:,.2f}</div>
                        <div>Annual Projection</div>
                    </div>
                    <div class="subscription-item">
                        <div style="font-size: 2em; font-weight: bold; color: #8b5cf6;">${monthly_mrr/len(monthly_orders) if monthly_orders else 0:,.2f}</div>
                        <div>Average Subscription</div>
                    </div>
                    <div class="subscription-item">
                        <div style="font-size: 2em; font-weight: bold; color: #667eea;">{len(monthly_orders)}</div>
                        <div>Total Subscribers</div>
                    </div>
                </div>
            </div>
            
            <!-- PACKAGE BREAKDOWN -->
            <div class="package-breakdown">
                <div class="package-card">
                    <div class="package-header package-boost">🚀 Boost Package</div>
                    <div style="font-size: 2em; font-weight: bold; color: #3b82f6;">${sum(o['price'] for o in boost_orders):,.2f}</div>
                    <div>{len(boost_orders)} orders • ${sum(o['price'] for o in boost_orders if o['paid']):,.2f} paid</div>
                    <div style="margin-top: 15px; color: #666;">
                        One-time: {len([o for o in boost_orders if o.get('order_type') == 'one_time'])}<br>
                        Recurring: {len([o for o in boost_orders if o.get('order_type') == 'monthly'])}
                    </div>
                </div>
                
                <div class="package-card">
                    <div class="package-header package-dominance">🔥 Dominance Package</div>
                    <div style="font-size: 2em; font-weight: bold; color: #8b5cf6;">${sum(o['price'] for o in dominance_orders):,.2f}</div>
                    <div>{len(dominance_orders)} orders • ${sum(o['price'] for o in dominance_orders if o['paid']):,.2f} paid</div>
                    <div style="margin-top: 15px; color: #666;">
                        One-time: {len([o for o in dominance_orders if o.get('order_type') == 'one_time'])}<br>
                        Recurring: {len([o for o in dominance_orders if o.get('order_type') == 'monthly'])}
                    </div>
                </div>
                
                <div class="package-card">
                    <div class="package-header package-retainer">📅 Monthly Retainer</div>
                    <div style="font-size: 2em; font-weight: bold; color: #10b981;">${sum(o.get('total_billed', 0) for o in retainer_orders):,.2f}</div>
                    <div>{len(retainer_orders)} subscribers • ${sum(o['price'] for o in retainer_orders):,.2f}/mo MRR</div>
                    <div style="margin-top: 15px; color: #666;">
                        Active: {len([o for o in retainer_orders if o.get('status') == 'active'])}<br>
                        Churned: {len([o for o in retainer_orders if o.get('status') == 'cancelled'])}
                    </div>
                </div>
            </div>
            
            <!-- ORDERS TABLE -->
            <div class="orders-table">
                <table>
                    <thead>
                        <tr>
                            <th>Order ID</th>
                            <th>Type</th>
                            <th>Customer</th>
                            <th>Package</th>
                            <th>Price</th>
                            <th>Status</th>
                            <th>Next Billing</th>
                            <th>Total Billed</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    # Add each order as a table row
    for order in orders_db:
        # Determine type badge
        order_type = order.get('order_type', 'one_time')
        type_badge = f"<span class='badge type-{order_type}'>{'🔄 Monthly' if order_type == 'monthly' else '💰 One-Time'}</span>"
        
        # Package badge
        package_type = order.get('package_type', 'dominance')
        package_badge = f"<span class='badge package-{package_type}-badge'>"
        if package_type == 'boost':
            package_badge += "🚀 Boost"
        elif package_type == 'dominance':
            package_badge += "🔥 Dominance"
        else:
            package_badge += "📅 Retainer"
        package_badge += "</span>"
        
        # Status badge
        status = order.get('status', 'pending')
        status_badge = f"<span class='badge status-{status}'>{status.title()}</span>"
        
        # Next billing date
        next_billing = order.get('next_billing_date', 'N/A')
        if next_billing and next_billing != 'N/A':
            next_billing = next_billing[:10]  # Just the date part
        
        # Total billed (for subscriptions)
        total_billed = order.get('total_billed', 0)
        
        html_content += f"""
                        <tr>
                            <td><strong>{order['order_id']}</strong></td>
                            <td>{type_badge}</td>
                            <td>{order['customer_name']}<br><small>{order['customer_email']}</small></td>
                            <td>{package_badge}</td>
                            <td style="font-weight: bold; color: #10b981;">${order['price']:,.2f}</td>
                            <td>{status_badge}</td>
                            <td>{next_billing}</td>
                            <td>${total_billed:,.2f}</td>
                            <td>
                                <button onclick="viewOrder('{order['order_id']}')" style="padding: 5px 15px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer;">View</button>
                                <button onclick="editOrder('{order['order_id']}')" style="padding: 5px 15px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">Edit</button>
                            </td>
                        </tr>
        """
    
    # Add JavaScript
    html_content += """
                    </tbody>
                </table>
            </div>
        </div>
        
        <script>
            function viewOrder(orderId) {
                window.open(`/api/orders/${orderId}`, '_blank');
            }
            
            function editOrder(orderId) {
                const newStatus = prompt('Enter new status (pending/active/in_progress/completed/cancelled):', 'active');
                const newType = prompt('Enter order type (one_time/monthly):', 'one_time');
                const newPackage = prompt('Enter package (boost/dominance/retainer):', 'dominance');
                
                if (newStatus || newType || newPackage) {
                    const updateData = {};
                    if (newStatus) updateData.status = newStatus;
                    if (newType) updateData.order_type = newType;
                    if (newPackage) updateData.package_type = newPackage;
                    
                    fetch(`/api/orders/${orderId}`, {
                        method: 'PUT',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(updateData)
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert('✅ Order updated!');
                        location.reload();
                    })
                    .catch(error => {
                        alert('❌ Error: ' + error);
                    });
                }
            }
            
            // Auto-refresh every 60 seconds
            setTimeout(() => location.reload(), 60000);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

# Keep all other endpoints (they'll work with the new structure)
@app.get("/api/orders")
async def list_orders():
    return orders_db

@app.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    for order in orders_db:
        if order["order_id"] == order_id:
            return order
    raise HTTPException(status_code=404, detail="Order not found")

@app.put("/api/orders/{order_id}")
async def update_order(order_id: str, update: OrderUpdate):
    for order in orders_db:
        if order["order_id"] == order_id:
            if update.status:
                order["status"] = update.status
            if update.price is not None:
                order["price"] = update.price
                # If it's a monthly subscription, update total_billed if paid
                if order.get("order_type") == "monthly" and order.get("paid"):
                    order["total_billed"] = update.price
            if update.paid is not None:
                order["paid"] = update.paid
            if update.package_type:
                order["package_type"] = update.package_type
            if update.order_type:
                order["order_type"] = update.order_type
            if update.next_billing_date:
                order["next_billing_date"] = update.next_billing_date
            return order
    raise HTTPException(status_code=404, detail="Order not found")

@app.delete("/api/orders/{order_id}")
async def delete_order(order_id: str):
    global orders_db
    original_length = len(orders_db)
    orders_db = [order for order in orders_db if order["order_id"] != order_id]
    
    if len(orders_db) == original_length:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"message": "Order deleted successfully"}

@app.get("/health")
async def health_check():
    monthly_orders = [o for o in orders_db if o.get("order_type") == "monthly"]
    monthly_mrr = sum(order["price"] for order in monthly_orders if order.get("status") == "active")
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "business_metrics": {
            "total_orders": len(orders_db),
            "one_time_orders": len([o for o in orders_db if o.get("order_type") == "one_time"]),
            "monthly_subscriptions": len([o for o in orders_db if o.get("order_type") == "monthly"]),
            "monthly_recurring_revenue": monthly_mrr,
            "active_subscriptions": len([o for o in orders_db if o.get("order_type") == "monthly" and o.get("status") == "active"])
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
