"""
SOVEREIGN EMPIRE PREMIUM CONTENT API
FastAPI endpoint for premium content generation
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import uuid
import json
import os
import subprocess
import asyncio
from pathlib import Path

app = FastAPI(
    title="Sovereign Empire Content API",
    description="API for generating premium content packages ($359-$497 value)",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Order storage (in production, use a database)
orders_db = {}

class ContentOrder(BaseModel):
    """Model for content creation orders"""
    business_type: str
    service_area: str
    package_tier: str = "dominance"  # "jumpstart" or "dominance"
    customer_email: str
    customer_name: str
    order_total: float
    special_instructions: Optional[str] = None

class OrderResponse(BaseModel):
    """Response model for order creation"""
    order_id: str
    status: str
    message: str
    download_url: Optional[str] = None
    estimated_completion: str
    price_paid: float

def generate_order_id() -> str:
    """Generate unique order ID"""
    return f"SE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

def validate_order_data(order: ContentOrder) -> dict:
    """Validate and prepare order data"""
    
    # Validate package tier
    valid_tiers = ["jumpstart", "dominance"]
    if order.package_tier not in valid_tiers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid package tier '{order.package_tier}'. Must be one of: {valid_tiers}"
        )
    
    # Validate price matches package
    expected_prices = {
        "jumpstart": 359.00,
        "dominance": 497.00
    }
    
    expected_price = expected_prices[order.package_tier]
    if abs(order.order_total - expected_price) > 0.01:  # Allow small rounding differences
        raise HTTPException(
            status_code=400,
            detail=f"Order total ${order.order_total:.2f} doesn't match {order.package_tier} package price (${expected_price:.2f})"
        )
    
    return {
        "expected_price": expected_price,
        "package_name": "Google Visibility Dominance" if order.package_tier == "dominance" else "Google Visibility Jumpstart"
    }

async def generate_content_async(order_id: str, business_type: str, service_area: str, package_tier: str):
    """Async function to generate content in background"""
    try:
        # Create output directory
        output_dir = Path(f"generated_orders/{order_id}")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare command
        cmd = ["python", "create-premium-content.py", business_type, service_area]
        
        # Add package tier if it's jumpstart (dominance is default)
        if package_tier == "jumpstart":
            cmd.append("--jumpstart")
        
        # Execute the content generator
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=os.getcwd()
        )
        
        stdout, stderr = await process.communicate()
        
        # Update order status
        if process.returncode == 0:
            orders_db[order_id]["status"] = "completed"
            orders_db[order_id]["completed_at"] = datetime.now().isoformat()
            
            # Find generated files
            default_dir = Path(f"premium_delivery_{business_type.lower().replace(' ', '_')}")
            if default_dir.exists():
                # Move files to order directory
                for file in default_dir.iterdir():
                    file.rename(output_dir / file.name)
                default_dir.rmdir()
            
            # Create download package
            files = list(output_dir.glob("*"))
            orders_db[order_id]["files"] = [str(f.name) for f in files]
            orders_db[order_id]["download_path"] = str(output_dir)
            
            print(f"✅ Order {order_id} completed successfully")
            print(f"   Generated {len(files)} files")
            
        else:
            orders_db[order_id]["status"] = "failed"
            orders_db[order_id]["error"] = stderr.decode() if stderr else "Unknown error"
            print(f"❌ Order {order_id} failed: {stderr.decode() if stderr else 'Unknown error'}")
            
    except Exception as e:
        orders_db[order_id]["status"] = "failed"
        orders_db[order_id]["error"] = str(e)
        print(f"❌ Order {order_id} crashed: {str(e)}")

@app.get("/")
async def root():
    """Root endpoint - API status"""
    return {
        "service": "Sovereign Empire Premium Content API",
        "version": "2.0.0",
        "status": "active",
        "endpoints": {
            "packages": "/api/packages (GET)",
            "create_order": "/api/orders/create (POST)",
            "order_status": "/api/orders/{order_id} (GET)",
            "docs": "/docs"
        }
    }

@app.get("/api/packages")
async def get_packages():
    """Get available content packages"""
    return {
        "packages": [
            {
                "id": "jumpstart",
                "name": "Google Visibility Jumpstart",
                "price": 359.00,
                "description": "Perfect for businesses starting their online presence",
                "deliverables": [
                    "3 SEO-optimized blog posts targeting local customer questions",
                    "1 service page rewrite optimized for conversions",
                    "Google Business Profile setup & optimization",
                    "Local keyword research specific to your service area",
                    "On-page SEO implementation checklist"
                ],
                "delivery_time": "30-day delivery",
                "best_for": "New businesses or those with limited online presence"
            },
            {
                "id": "dominance",
                "name": "Google Visibility Dominance",
                "price": 497.00,
                "description": "For businesses serious about dominating local search",
                "deliverables": [
                    "5 SEO-optimized blog posts (2 extra posts)",
                    "1 service page rewrite with conversion optimization",
                    "Advanced Google Business optimization with posts & Q&A",
                    "Competitor gap analysis report",
                    "Local schema markup implementation guide",
                    "30-day performance tracking setup"
                ],
                "delivery_time": "30-day delivery",
                "best_for": "Established businesses wanting to dominate local search"
            }
        ],
        "retainer": {
            "available": True,
            "price": 297.00,
            "description": "Monthly ongoing optimization and content",
            "link": "/api/retainer-info"
        }
    }

@app.post("/api/orders/create", response_model=OrderResponse)
async def create_order(order: ContentOrder, background_tasks: BackgroundTasks):
    """Create a new premium content order"""
    
    # Validate order data
    validation = validate_order_data(order)
    
    # Generate order ID
    order_id = generate_order_id()
    
    # Create order record
    order_record = {
        "order_id": order_id,
        "created_at": datetime.now().isoformat(),
        "customer": {
            "name": order.customer_name,
            "email": order.customer_email
        },
        "business": {
            "type": order.business_type,
            "area": order.service_area
        },
        "package": {
            "tier": order.package_tier,
            "name": validation["package_name"],
            "price": order.order_total
        },
        "status": "processing",
        "special_instructions": order.special_instructions,
        "files": [],
        "download_path": None
    }
    
    # Store order
    orders_db[order_id] = order_record
    
    # Start content generation in background
    background_tasks.add_task(
        generate_content_async,
        order_id,
        order.business_type,
        order.service_area,
        order.package_tier
    )
    
    # Return immediate response
    return OrderResponse(
        order_id=order_id,
        status="processing",
        message=f"Premium content order created for {order.business_type} in {order.service_area}. Generation in progress.",
        download_url=f"/api/orders/{order_id}/download",
        estimated_completion="10-15 minutes",
        price_paid=order.order_total
    )

@app.get("/api/orders/{order_id}")
async def get_order_status(order_id: str):
    """Check order status and details"""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    
    order = orders_db[order_id]
    
    # Add extra info if completed
    if order["status"] == "completed":
        order["download_ready"] = True
        order["file_count"] = len(order["files"])
        order["preview_files"] = order["files"][:3]  # First 3 files
    
    return order

@app.get("/api/orders/{order_id}/download")
async def download_order(order_id: str):
    """Download generated content"""
    if order_id not in orders_db:
        raise HTTPException(status_code=404, detail=f"Order {order_id} not found")
    
    order = orders_db[order_id]
    
    if order["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Order {order_id} is not ready for download. Current status: {order['status']}"
        )
    
    # In production: create and serve ZIP file
    # For now, return file list and instructions
    return {
        "order_id": order_id,
        "status": "ready",
        "files": order["files"],
        "instructions": "Files are available for download. Contact support for access.",
        "package_summary": f"{order['package']['name']} - ${order['package']['price']:.2f}",
        "business": f"{order['business']['type']} in {order['business']['area']}",
        "generated_on": order.get("completed_at", "N/A")
    }

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "orders_processing": len([o for o in orders_db.values() if o["status"] == "processing"]),
        "orders_completed": len([o for o in orders_db.values() if o["status"] == "completed"]),
        "total_orders": len(orders_db)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
