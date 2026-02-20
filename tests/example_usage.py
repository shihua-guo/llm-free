import requests

def test_llm_free():
    # 你的服务地址
    url = "http://localhost:8000/v1/chat/completions"
    
    # 构造请求数据 (符合 OpenAI 标准格式)
    payload = {
        "model": "text", # 或者使用具体模型名如 "qwen-max"，服务会自动路由
        "messages": [
            {"role": "system", "content": "你是一个专业的电子元器件专家。"},
            {"role": "user", "content": "请简述 TI 的 TPS5430 开关电源芯片的主要特点。"}
        ],
        "temperature": 0.7
    }
    
    headers = {
        "Content-Type": "application/json"
    }

    print(f"正在请求 {url}...")
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print("\n--- AI 回复 ---")
            print(content)
            print("\n--- 使用详情 ---")
            print(f"使用的具体模型: {result['model']}")
            print(f"Token 消耗: {result['usage']['total_tokens']}")
        else:
            print(f"请求失败: {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"发生错误: {e}")

if __name__ == "__main__":
    test_llm_free()
