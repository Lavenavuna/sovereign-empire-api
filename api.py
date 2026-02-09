"""
Sovereign Empire API - Complete Working Version with Dual Pricing Tiers
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

app = FastAPI(title="Sovereign Empire API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# DATABASE WITH DUAL PRICING TIERS
orders_db = [
    {
        "order_id": "ORD-0001",
        "customer_name": "John Smith",
        "customer_email": "john@example.com",
        "industry": "Dental Practice",
        "topic": "Dental SEO",
        "wordpress_url": "https://johnsdental.com",
        "tenant_id": "DIRECT_CUSTOMER",
        "package_type": "dominance",
        "status": "completed",
        "price": 497.00,
        "paid": True,
        "created_at": "2024-01-01T10:00:00"
    },
    {
        "order_id": "ORD-0002",
        "customer_name": "Sarah Johnson",
        "customer_email": "sarah@example.com",
        "industry": "Plumbing",
        "topic": "Local Plumbing SEO",
        "wordpress_url": "https://sarahsplumbing.com",
        "tenant_id": "DIRECT_CUSTOMER",
        "package_type": "dominance",
        "status": "in_progress",
        "price": 497.00,
        "paid": True,
        "created_at": "2024-01-02T11:30:00"
    },
    {
        # Line ~55:
    "paid": True,  # Changed from False

# Line ~75:
    "paid": True,  # Changed from False
    },
    {
        "order_id": "ORD-0004",
        "customer_name": "Emma Davis",
        "customer_email": "emma@example.com",
        "industry": "HVAC Services",
        "topic": "HVAC Local SEO",
        "wordpress_url": "https://davishvac.com",
        "tenant_id": "DIRECT_CUSTOMER",
        "package_type": "dominance",
        "status": "completed",
        "price": 497.00,
        "paid": True,
        "created_at": "2024-01-04T09:15:00"
    },
    {
        "order_id": "ORD-0005",
        "customer_name": "Robert Brown",
        "customer_email": "robert@example.com",
        "industry": "Car Detailing",
        "topic": "Auto Detailing Marketing",
        "wordpress_url": "https://browndetailing.com",
        "tenant_id": "DIRECT_CUSTOMER",
        "package_type": "boost",
        "status": "pending",
        "price": 359.00,
        "paid": False,
        "created_at": "2024-01-05T16:20:00"
    },
    {
        "order_id": "ORD-0006",
        "customer_name": "Lisa Taylor",
        "customer_email": "lisa@example.com",
        "industry": "Cleaning Services",
        "topic": "Residential Cleaning SEO",
        "wordpress_url": "https://taylorcleaning.com",
        "tenant_id": "DIRECT_CUSTOMER",
        "package_type": "dominance",
        "status": "in_progress",
        "price": 497.00,
        "paid": True,
        "created_at": "2024-01-06T13:10:00"
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
    package_type: str = "dominance"  # "boost" or "dominance"
    price: float = 497.00  # Default to higher package
    paid: bool = False

class OrderUpdate(BaseModel):
    status: Optional[str] = None
    price: Optional[float] = None
    paid: Optional[bool] = None
    package_type: Optional[str] = None

# Root endpoint
@app.get("/")
async def root():
    total_revenue = sum(order["price"] for order in orders_db if order.get("paid") == True)
    boost_count = sum(1 for order in orders_db if order.get("package_type") == "boost")
    dominance_count = sum(1 for order in orders_db if order.get("package_type") == "dominance")
    
    return {
        "service": "Sovereign Empire API",
        "status": "online",
        "version": "2.1.0",
        "features": ["dual_pricing", "order_management", "revenue_tracking", "admin_dashboard"],
        "orders_count": len(orders_db),
        "package_stats": {
            "boost": boost_count,
            "dominance": dominance_count
        },
        "total_revenue": total_revenue
    }

# Health check
@app.get("/health")
async def health_check():
    paid_orders = sum(1 for order in orders_db if order.get("paid") == True)
    total_revenue = sum(order["price"] for order in orders_db if order.get("paid") == True)
    boost_revenue = sum(order["price"] for order in orders_db if order.get("package_type") == "boost" and order.get("paid") == True)
    dominance_revenue = sum(order["price"] for order in orders_db if order.get("package_type") == "dominance" and order.get("paid") == True)
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Sovereign Empire Order API",
        "orders": {
            "total": len(orders_db),
            "paid": paid_orders,
            "pending_payment": len(orders_db) - paid_orders
        },
        "revenue": {
            "total": total_revenue,
            "boost_package": boost_revenue,
            "dominance_package": dominance_revenue,
            "average_order": total_revenue / paid_orders if paid_orders > 0 else 0
        }
    }

# Create new order
@app.post("/api/orders/create")
async def create_order(order: OrderCreate):
    try:
        # Set price based on package type
        if order.package_type == "boost":
            price = 359.00
        elif order.package_type == "dominance":
            price = 497.00
        else:
            price = order.price  # Fallback to provided price
        
        order_id = f"ORD-{len(orders_db) + 1:04d}"
        new_order = {
            "order_id": order_id,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "industry": order.industry,
            "topic": order.topic,
            "wordpress_url": order.wordpress_url,
            "tenant_id": order.tenant_id,
            "package_type": order.package_type,
            "status": "pending",
            "price": price,
            "paid": order.paid,
            "created_at": datetime.now().isoformat()
        }
        orders_db.append(new_order)
        return new_order
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating order: {str(e)}")

# List all orders
@app.get("/api/orders")
async def list_orders():
    return orders_db

# Get specific order
@app.get("/api/orders/{order_id}")
async def get_order(order_id: str):
    for order in orders_db:
        if order["order_id"] == order_id:
            return order
    raise HTTPException(status_code=404, detail="Order not found")

# Update order (status, price, paid status, package)
@app.put("/api/orders/{order_id}")
async def update_order(order_id: str, update: OrderUpdate):
    for order in orders_db:
        if order["order_id"] == order_id:
            if update.status:
                order["status"] = update.status
            if update.price is not None:
                order["price"] = update.price
            if update.paid is not None:
                order["paid"] = update.paid
            if update.package_type:
                order["package_type"] = update.package_type
                # Auto-update price based on package
                if update.package_type == "boost":
                    order["price"] = 359.00
                elif update.package_type == "dominance":
                    order["price"] = 497.00
            return order
    raise HTTPException(status_code=404, detail="Order not found")

# Delete order
@app.delete("/api/orders/{order_id}")
async def delete_order(order_id: str):
    global orders_db
    original_length = len(orders_db)
    orders_db = [order for order in orders_db if order["order_id"] != order_id]
    
    if len(orders_db) == original_length:
        raise HTTPException(status_code=404, detail="Order not found")
    
    return {"message": "Order deleted successfully"}

# ADMIN DASHBOARD WITH DUAL PRICING
@app.get("/admin/dashboard")
async def admin_dashboard():
    # Calculate revenue stats
    paid_orders = [o for o in orders_db if o.get("paid") == True]
    pending_payment = [o for o in orders_db if o.get("paid") == False]
    
    total_revenue = sum(order["price"] for order in paid_orders)
    pending_revenue = sum(order["price"] for order in pending_payment)
    
    # Package statistics
    boost_orders = [o for o in orders_db if o.get("package_type") == "boost"]
    dominance_orders = [o for o in orders_db if o.get("package_type") == "dominance"]
    boost_revenue = sum(order["price"] for order in boost_orders if order.get("paid") == True)
    dominance_revenue = sum(order["price"] for order in dominance_orders if order.get("paid") == True)
    
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
        <title>Orders Dashboard - Sovereign Empire</title>
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
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
            }}
            h1 {{
                margin: 0;
                font-size: 2.5em;
            }}
            .stats {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}
            .stat-card {{
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
            }}
            .stat-number {{
                font-size: 2.5em;
                font-weight: bold;
                color: #667eea;
                margin: 10px 0;
            }}
            .revenue-card {{
                background: white;
                padding: 25px;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                text-align: center;
                grid-column: span 2;
            }}
            .revenue-number {{
                font-size: 3em;
                font-weight: bold;
                color: #10b981;
                margin: 10px 0;
            }}
            .package-stats {{
                display: flex;
                justify-content: space-around;
                background: white;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .package-stat {{
                text-align: center;
            }}
            .package-label {{
                font-size: 1.2em;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            .boost {{ color: #3b82f6; }}
            .dominance {{ color: #8b5cf6; }}
            .orders-table {{
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
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
            .status-badge {{
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: 600;
            }}
            .status-pending {{ background: #fff3cd; color: #856404; }}
            .status-in_progress {{ background: #cce5ff; color: #004085; }}
            .status-completed {{ background: #d4edda; color: #155724; }}
            .payment-badge {{
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: 600;
            }}
            .payment-paid {{ background: #d4edda; color: #155724; }}
            .payment-unpaid {{ background: #f8d7da; color: #721c24; }}
            .package-badge {{
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: 600;
            }}
            .package-boost {{ background: #dbeafe; color: #1e40af; }}
            .package-dominance {{ background: #ede9fe; color: #5b21b6; }}
            .price-cell {{
                font-weight: bold;
                color: #10b981;
            }}
            .actions {{
                display: flex;
                gap: 10px;
            }}
            .btn {{
                padding: 5px 15px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-weight: 500;
            }}
            .btn-view {{ background: #6c757d; color: white; }}
            .btn-edit {{ background: #007bff; color: white; }}
            .btn-delete {{ background: #dc3545; color: white; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📊 Orders Dashboard - Dual Pricing Tiers</h1>
                <p>Manage orders, track payments, and monitor revenue across both packages</p>
            </header>
            
            <div class="stats">
                <div class="stat-card">
                    <div>Total Orders</div>
                    <div class="stat-number">{len(orders_db)}</div>
                </div>
                <div class="stat-card">
                    <div>Pending</div>
                    <div class="stat-number">{status_counts.get('pending', 0)}</div>
                </div>
                <div class="stat-card">
                    <div>In Progress</div>
                    <div class="stat-number">{status_counts.get('in_progress', 0)}</div>
                </div>
                <div class="stat-card">
                    <div>Completed</div>
                    <div class="stat-number">{status_counts.get('completed', 0)}</div>
                </div>
                <div class="revenue-card">
                    <div>💰 Total Revenue</div>
                    <div class="revenue-number">${total_revenue:,.2f}</div>
                    <div>{len(paid_orders)} paid orders | ${pending_revenue:,.2f} pending</div>
                </div>
            </div>
            
            <div class="package-stats">
                <div class="package-stat">
                    <div class="package-label boost">🚀 Boost Package</div>
                    <div style="font-size: 2em; font-weight: bold; color: #3b82f6;">${boost_revenue:,.2f}</div>
                    <div>{len([o for o in boost_orders if o.get('paid') == True])} paid orders</div>
                    <div>{len(boost_orders)} total</div>
                </div>
                <div class="package-stat">
                    <div class="package-label dominance">🔥 Dominance Package</div>
                    <div style="font-size: 2em; font-weight: bold; color: #8b5cf6;">${dominance_revenue:,.2f}</div>
                    <div>{len([o for o in dominance_orders if o.get('paid') == True])} paid orders</div>
                    <div>{len(dominance_orders)} total</div>
                </div>
            </div>
            
            <div class="orders-table">
                <table>
                    <thead>
                        <tr>
                            <th>Order ID</th>
                            <th>Customer</th>
                            <th>Email</th>
                            <th>Package</th>
                            <th>Industry</th>
                            <th>Topic</th>
                            <th>Status</th>
                            <th>Price</th>
                            <th>Payment</th>
                            <th>Date</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    # Add each order as a table row
    for order in orders_db:
        status_class = f"status-{order['status']}"
        payment_class = f"payment-{'paid' if order['paid'] else 'unpaid'}"
        payment_text = "Paid ✅" if order['paid'] else "Unpaid ❌"
        package_class = f"package-{order.get('package_type', 'dominance')}"
        package_display = "🚀 Boost" if order.get('package_type') == 'boost' else '🔥 Dominance'
        
        html_content += f"""
                        <tr>
                            <td><strong>{order['order_id']}</strong></td>
                            <td>{order['customer_name']}</td>
                            <td>{order['customer_email']}</td>
                            <td><span class="package-badge {package_class}">{package_display}</span></td>
                            <td>{order['industry']}</td>
                            <td>{order['topic']}</td>
                            <td><span class="status-badge {status_class}">{order['status']}</span></td>
                            <td class="price-cell">${order['price']:,.2f}</td>
                            <td><span class="payment-badge {payment_class}">{payment_text}</span></td>
                            <td>{order['created_at'][:10]}</td>
                            <td class="actions">
                                <button class="btn btn-view" onclick="viewOrder('{order['order_id']}')">View</button>
                                <button class="btn btn-edit" onclick="editOrder('{order['order_id']}')">Edit</button>
                                <button class="btn btn-delete" onclick="deleteOrder('{order['order_id']}')">Delete</button>
                            </td>
                        </tr>
        """
    
    # Add JavaScript functions
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
                const newStatus = prompt('Enter new status (pending/in_progress/completed):', 'pending');
                const newPackage = prompt('Enter package type (boost/dominance):', 'dominance');
                const newPrice = prompt('Enter new price (e.g., 359.00 or 497.00):', '497.00');
                const newPaid = confirm('Is this order paid? (OK for Yes, Cancel for No)');
                
                if (newStatus || newPackage || newPrice) {
                    const updateData = {};
                    if (newStatus) updateData.status = newStatus;
                    if (newPackage) updateData.package_type = newPackage;
                    if (newPrice) updateData.price = parseFloat(newPrice);
                    updateData.paid = newPaid;
                    
                    fetch(`/api/orders/${orderId}`, {
                        method: 'PUT',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(updateData)
                    })
                    .then(response => {
                        if (response.ok) {
                            return response.json();
                        } else {
                            throw new Error('Update failed');
                        }
                    })
                    .then(data => {
                        alert('✅ Order updated successfully!');
                        location.reload();
                    })
                    .catch(error => {
                        alert('❌ Error updating order: ' + error);
                    });
                }
            }
            
            function deleteOrder(orderId) {
                if (confirm(`Are you sure you want to delete order ${orderId}?`)) {
                    fetch(`/api/orders/${orderId}`, {
                        method: 'DELETE'
                    })
                    .then(response => {
                        if (response.ok) {
                            return response.json();
                        } else {
                            throw new Error('Delete failed');
                        }
                    })
                    .then(data => {
                        alert('✅ Order deleted successfully!');
                        location.reload();
                    })
                    .catch(error => {
                        alert('❌ Error deleting order: ' + error);
                    });
                }
            }
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
