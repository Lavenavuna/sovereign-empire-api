from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime

app = FastAPI(
    title="Sovereign Empire Content API",
    description="API for premium content packages ($359-$497)",
    version="1.0.0"
)

class Order(BaseModel):
    business_type: str
    service_area: str
    package_tier: str = "dominance"
    customer_email: str
    customer_name: str
    order_total: float
    special_instructions: Optional[str] = None

@app.get("/")
async def root():
    return {
        "service": "Sovereign Empire Premium Content API",
        "version": "1.0.0",
        "status": "active",
        "endpoints": {
            "packages": "GET /api/packages",
            "create_order": "POST /api/orders/create"
        }
    }

@app.get("/api/packages")
async def get_packages():
    return {
        "packages": [
            {
                "id": "jumpstart",
                "name": "Google Visibility Jumpstart",
                "price": 359.00,
                "description": "Perfect for businesses starting their online presence",
                "deliverables": [
                    "3 SEO-optimized blog posts",
                    "Google Business Profile setup",
                    "Local keyword research",
                    "On-page SEO checklist"
                ]
            },
            {
                "id": "dominance",
                "name": "Google Visibility Dominance",
                "price": 497.00,
                "description": "For businesses serious about dominating local search",
                "deliverables": [
                    "5 SEO-optimized blog posts",
                    "Advanced GBP optimization",
                    "Competitor gap analysis",
                    "30-day tracking setup"
                ]
            }
        ]
    }

@app.post("/api/orders/create")
async def create_order(order: Order):
    # Validate package tier
    if order.package_tier not in ["jumpstart", "dominance"]:
        raise HTTPException(
            status_code=400,
            detail="package_tier must be 'jumpstart' or 'dominance'"
        )
    
    # Validate price
    expected_price = 359.00 if order.package_tier == "jumpstart" else 497.00
    if abs(order.order_total - expected_price) > 0.01:
        raise HTTPException(
            status_code=400,
            detail=f"Order total ${order.order_total} doesn't match {order.package_tier} package (${expected_price})"
        )
    
    # Generate order ID
    order_id = f"SE-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
    
    return {
        "order_id": order_id,
        "status": "processing",
        "message": f"Order received for {order.business_type} in {order.service_area}",
        "package": order.package_tier,
        "price": order.order_total,
        "customer": order.customer_name,
        "next_step": "Content generation will begin shortly"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
