import requests
import json

print("=" * 60)
print("FOOLPROOF API TEST")
print("=" * 60)

base_url = "https://sovereign-empire-api-production.up.railway.app"

# TEST 1: Simple GET (no JSON involved)
print("\n1. Testing GET request (no JSON)...")
try:
    response = requests.get(base_url + "/", timeout=5)
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    print("   ✅ GET works!")
except Exception as e:
    print(f"   ❌ GET failed: {e}")
    exit()

# TEST 2: Test with VALID simple JSON
print("\n2. Testing POST with SIMPLE valid JSON...")
simple_json = {"test": "hello"}  # VALID JSON

print(f"   Sending: {json.dumps(simple_json)}")

try:
    response = requests.post(
        base_url + "/api/orders/create",
        json=simple_json,
        timeout=10
    )
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.text}")
    
    if response.status_code == 422:
        print("   ❌ Still getting 422 with valid JSON")
        print("   This means the API endpoint exists but expects different fields")
    else:
        print(f"   ✅ POST works! Status: {response.status_code}")
        
except Exception as e:
    print(f"   ❌ POST failed: {e}")

# TEST 3: Check what the API actually expects
print("\n3. Checking API documentation...")
try:
    # FastAPI usually has /docs or /openapi.json
    response = requests.get(base_url + "/docs", timeout=5)
    if response.status_code == 200:
        print("   ✅ API docs available at: " + base_url + "/docs")
    else:
        response = requests.get(base_url + "/openapi.json", timeout=5)
        if response.status_code == 200:
            print("   ✅ OpenAPI spec available")
        else:
            print("   ❌ No docs found")
except:
    print("   Could not access docs")

print("\n" + "=" * 60)
print("If you see 'GET works' but POST gets 422,")
print("the API needs specific fields like:")
print('  {"business_type": "...", "service_area": "...", etc}')
print("=" * 60)
