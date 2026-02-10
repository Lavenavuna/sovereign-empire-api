from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import subprocess
import json
import uuid
from datetime import datetime

app = FastAPI(title="Sovereign Empire API")

class Order(BaseModel):
    business_type: str
    service_area: str
    package_tier: str = "dominance"
    customer_email: str
    customer_name: str
    order_total: float
    special_instructions: Optional[str] = None

@app.get("/")
def root():
    return {"message": "Sovereign Empire Premium Content API", "status": "active"}

@app.get("/api/packages")
def get_packages():
    return {
        "packages": [
            {
                "id": "jumpstart",
                "name": "Google Visibility Jumpstart",
                "price": 359.00,
                "deliverables": ["3 blog posts", "GBP setup", "Local SEO"]
            },
            {
                "id": "dominance",
                "name": "Google Visibility Dominance", 
                "price": 497.00,
                "deliverables": ["5 blog posts", "Advanced GBP", "Competitor analysis"]
            }
        ]
    }

@app.post("/api/orders/create")
def create_order(order: Order):
    # Validate package tier
    if order.package_tier not in ["jumpstart", "dominance"]:
        raise HTTPException(400, detail="package_tier must be 'jumpstart' or 'dominance'")
    
    # Validate price
    expected_price = 359.00 if order.package_tier == "jumpstart" else 497.00
    if abs(order.order_total - expected_price) > 0.01:
        raise HTTPException(400, detail=f"Price must be ${expected_price} for {order.package_tier} package")
    
    # Generate order ID
    order_id = f"SE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    # Return success
    return {
        "order_id": order_id,
        "status": "processing",
        "message": f"Order received for {order.business_type} in {order.service_area}",
        "package": order.package_tier,
        "price": order.order_total,
        "next_step": "Content generation in progress"
    }
