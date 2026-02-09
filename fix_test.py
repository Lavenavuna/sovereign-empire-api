import requests
import json

url = "https://sovereign-empire-api-production.up.railway.app/api/orders/create"

# CORRECT JSON - no errors
payload = {
    "business_type": "Plumbing",
    "service_area": "Austin TX", 
    "package_tier": "dominance",
    "customer_email": "test@test.com",
    "customer_name": "Test",
    "order_total": 497.00
}

print("JSON being sent:")
print(json.dumps(payload, indent=2))

# Validate JSON is valid
try:
    json_str = json.dumps(payload)
    print("\n✅ JSON is valid")
except Exception as e:
    print(f"\n❌ JSON error: {e}")
    exit()

# Send request
try:
    response = requests.post(
        url,
        json=payload,  # This automatically sets Content-Type to application/json
        timeout=30
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {response.text}")
    
except requests.exceptions.RequestException as e:
    print(f"\n❌ Request failed: {e}")
except Exception as e:
    print(f"\n❌ Error: {e}")
