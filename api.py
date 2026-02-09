"""
Sovereign Empire API - Ultra Simple Working Version
No database dependencies, no external services
"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

app = FastAPI(title="Sovereign Empire API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# SIMPLE IN-MEMORY DATABASE (no external DB needed)
orders_db = [
    {
        "order_id": "ORD-0001",
        "customer_name": "John Smith",
        "customer_email": "john@example.com",
        "industry": "Dental Practice",
        "topic": "Dental SEO",
        "wordpress_url": "https://johnsdental.com",
        "tenant_id": "DIRECT_CUSTOMER",
        "status": "completed",
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
        "status": "in_progress",
        "created_at": "2024-01-02T11:30:00"
    },
    {
        "order_id": "ORD-0003",
        "customer_name": "Mike Wilson",
        "customer_email": "mike@example.com",
        "industry": "Law Firm",
        "topic": "Legal Services Marketing",
        "wordpress_url": "https://wilsonlaw.com",
        "tenant_id": "DIRECT_CUSTOMER",
        "status": "pending",
        "created_at": "2024-01-03T14:45:00"
    },
    {
        "order_id": "ORD-0004",
        "customer_name": "Emma Davis",
        "customer_email": "emma@example.com",
        "industry": "HVAC Services",
        "topic": "HVAC Local SEO",
        "wordpress_url": "https://davishvac.com",
        "tenant_id": "DIRECT_CUSTOMER",
        "status": "completed",
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
        "status": "pending",
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
        "status": "in_progress",
        "created_at": "2024-01-06T13:10:00"
    }
]

# Pydantic models
class OrderCreate(BaseModel):
    customer_name: str
    customer_email: str
    industry: str
    topic: str
    wordpress_url: Optional[str] = ""
    tenant_id: str

class OrderUpdate(BaseModel):
    status: Optional[str] = None

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": "Sovereign Empire API",
        "status": "online",
        "version": "1.0.0",
        "orders_count": len(orders_db)
    }

# Health check
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Sovereign Empire Order API",
        "orders": len(orders_db)
    }

# Create new order
@app.post("/api/orders/create")
async def create_order(order: OrderCreate):
    try:
        order_id = f"ORD-{len(orders_db) + 1:04d}"
        new_order = {
            "order_id": order_id,
            "customer_name": order.customer_name,
            "customer_email": order.customer_email,
            "industry": order.industry,
            "topic": order.topic,
            "wordpress_url": order.wordpress_url,
            "tenant_id": order.tenant_id,
            "status": "pending",
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

# Update order status
@app.put("/api/orders/{order_id}")
async def update_order(order_id: str, update: OrderUpdate):
    for order in orders_db:
        if order["order_id"] == order_id:
            if update.status:
                order["status"] = update.status
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

# ADMIN DASHBOARD - THIS IS WHAT YOU NEED!
@app.get("/admin/dashboard")
async def admin_dashboard():
    # Count orders by status
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
                max-width: 1200px;
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
            .orders-table {{
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
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
                <h1>📊 Orders Dashboard</h1>
                <p>Manage all customer orders in one place</p>
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
            </div>
            
            <div class="orders-table">
                <table>
                    <thead>
                        <tr>
                            <th>Order ID</th>
                            <th>Customer</th>
                            <th>Email</th>
                            <th>Industry</th>
                            <th>Topic</th>
                            <th>Status</th>
                            <th>Date</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
    """
    
    # Add each order as a table row
    for order in orders_db:
        status_class = f"status-{order['status']}"
        html_content += f"""
                        <tr>
                            <td><strong>{order['order_id']}</strong></td>
                            <td>{order['customer_name']}</td>
                            <td>{order['customer_email']}</td>
                            <td>{order['industry']}</td>
                            <td>{order['topic']}</td>
                            <td><span class="status-badge {status_class}">{order['status']}</span></td>
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
                alert('View order: ' + orderId);
                // In production: window.location.href = `/api/orders/${orderId}`;
            }
            
            function editOrder(orderId) {
                const newStatus = prompt('Enter new status (pending/in_progress/completed):', 'pending');
                if (newStatus) {
                    fetch(`/api/orders/${orderId}`, {
                        method: 'PUT',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({status: newStatus})
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert('Order updated successfully!');
                        location.reload();
                    })
                    .catch(error => {
                        alert('Error updating order: ' + error);
                    });
                }
            }
            
            function deleteOrder(orderId) {
                if (confirm('Are you sure you want to delete order ' + orderId + '?')) {
                    fetch(`/api/orders/${orderId}`, {
                        method: 'DELETE'
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert('Order deleted successfully!');
                        location.reload();
                    })
                    .catch(error => {
                        alert('Error deleting order: ' + error);
                    });
                }
            }
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)

# Swagger/OpenAPI docs at /docs
# Already provided by FastAPI

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
