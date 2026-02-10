import requests
import json

def test_simple():
    print("Testing Sovereign Empire API...")
    
    # Test 1: Root endpoint
    print("\n1. Testing root endpoint...")
    try:
        r = requests.get("https://sovereign-empire-api-production.up.railway.app/", timeout=5)
        print(f"   Status: {r.status_code}")
        print(f"   Response: {r.text}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return
    
    # Test 2: Create order
    print("\n2. Testing order creation...")
    
    order_data = {
        "business_type": "Plumbing",
        "service_area": "Austin TX",
        "package_tier": "dominance",
        "customer_email": "test@example.com",
        "customer_name": "Test Client",
        "order_total": 497.00
    }
    
    try:
        r = requests.post(
            "https://sovereign-empire-api-production.up.railway.app/api/orders/create",
            json=order_data,
            timeout=10
        )
        
        print(f"   Status: {r.status_code}")
        print(f"   Response: {r.text}")
        
        if r.status_code == 200:
            print("\n✅ SUCCESS! API is working!")
            data = r.json()
            print(f"   Order ID: {data.get('order_id')}")
            print(f"   Status: {data.get('status')}")
        else:
            print(f"\n❌ Failed with status {r.status_code}")
            
    except Exception as e:
        print(f"   ❌ Request failed: {e}")

if __name__ == "__main__":
    test_simple()
