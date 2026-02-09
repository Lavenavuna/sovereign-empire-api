import requests
import json

# Test if API is alive
print("Testing API connection...")
try:
    response = requests.get("https://sovereign-empire-api-production.up.railway.app/", timeout=10)
    print(f"✅ API Status: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"❌ API Error: {e}")
    exit()

# Test order creation
print("\n\nCreating order...")
url = "https://sovereign-empire-api-production.up.railway.app/api/orders/create"

payload = {
    "business_type": "Plumbing",
    "service_area": "Austin, TX",
    "package_tier": "dominance",
    "customer_email": "test@example.com",
    "customer_name": "Test Client",
    "order_total": 497.00
}

headers = {
    "Content-Type": "application/json",
    "accept": "application/json"
}

try:
    response = requests.post(url, json=payload, headers=headers, timeout=30)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2) if response.text else 'Empty response'}")
except Exception as e:
    print(f"Error: {e}")
