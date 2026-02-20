import requests
import json

url = "http://localhost:8000/v1/chat/completions"
data = {
    "messages": [{"role": "user", "content": "hello"}]
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
