import requests

def test_routing():
    url = "http://localhost:8000/v1/chat/completions"
    
    # 测试 case 1: 使用通用名字 'text'
    print("--- Testing 'text' routing ---")
    payload = {
        "model": "text",
        "messages": [{"role": "user", "content": "hi"}]
    }
    r = requests.post(url, json=payload)
    print(f"Status: {r.status_code}, Model used: {r.json().get('model')}")

    # 测试 case 2: 使用具体存在的模型名
    print("\n--- Testing specific model routing (qwen-max) ---")
    payload["model"] = "qwen-max"
    r = requests.post(url, json=payload)
    print(f"Status: {r.status_code}, Model used: {r.json().get('model')}")

if __name__ == "__main__":
    test_routing()
