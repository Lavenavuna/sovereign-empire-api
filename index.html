from fastapi import APIRouter, Form, HTTPException
from typing import Optional

@router.post("/api/orders/create")
async def create_order(
    customer_name: str = Form(...),
    customer_email: str = Form(...),
    industry: str = Form(...),
    topic: str = Form(...),
    wordpress_url: Optional[str] = Form(None),
    tenant_id: str = Form("DIRECT_CUSTOMER")
):
    """Accept FORM data (not JSON)"""
    try:
        order_id = f"ORD_{uuid.uuid4().hex[:12].upper()}"
        
        new_order = Order(
            order_id=order_id,
            customer_name=customer_name,
            customer_email=customer_email,
            industry=industry,
            topic=topic,
            wordpress_url=wordpress_url,
            tenant_id=tenant_id,
            status="PENDING",
            cost=0.0,
            created_at=datetime.utcnow()
        )
        
        db.add(new_order)
        db.commit()
        
        # Return HTML response instead of JSON
        return HTMLResponse(content=f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Order Received</title>
            <style>
                body {{ font-family: Arial; text-align: center; padding: 50px; }}
                .success {{ background: #d4edda; color: #155724; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; }}
                h1 {{ margin-bottom: 20px; }}
                .button {{ background: #667eea; color: white; padding: 15px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="success">
                <h1>✅ Order Received!</h1>
                <p><strong>Order ID:</strong> {order_id}</p>
                <p><strong>Email:</strong> {customer_email}</p>
                <h3>What Happens Next:</h3>
                <ol style="text-align: left; max-width: 400px; margin: 20px auto;">
                    <li>Check your email for payment instructions</li>
                    <li>Pay via PayPal ($149)</li>
                    <li>We'll start your 30-Day Google Visibility Kickstart</li>
                </ol>
                <a href="https://lavenavuna.github.io/sovereign-empire-api/" class="button">Back to Home</a>
            </div>
        </body>
        </html>
        """)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
