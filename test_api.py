import requests
import json

API_ENDPOINTS = [
    "http://127.0.0.1:8000/api/inventory/medicines/",
    "http://127.0.0.1:8000/api/inventory/categories/",
    "http://127.0.0.1:8000/api/inventory/suppliers/",
    "http://127.0.0.1:8000/admin/",
]

def test_endpoint(url):
    print(f"\nTesting endpoint: {url}")
    try:
        response = requests.get(url, timeout=5)
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200 and 'application/json' in response.headers.get('Content-Type', ''):
            # Limit the output to avoid overwhelming the console
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"Data received: List with {len(data)} items")
                if len(data) > 0:
                    print(f"First item sample: {json.dumps(data[0], indent=2)[:200]}...")
            else:
                print(f"Data received: {json.dumps(data, indent=2)[:200]}...")
        elif response.status_code == 200:
            print(f"Response received (not JSON): {response.text[:100]}...")
        else:
            print(f"Response: {response.text[:100]}...")
    except requests.exceptions.ConnectionError:
        print("ConnectionError: Could not connect to the server")
    except requests.exceptions.Timeout:
        print("Timeout: The request timed out")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Testing API endpoints...")
    for endpoint in API_ENDPOINTS:
        test_endpoint(endpoint) 