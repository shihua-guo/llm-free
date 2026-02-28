#!/usr/bin/env python3
"""
Quick test script for llm-free OpenAI-compatible APIs:
- /v1/chat/completions
- /v1/embeddings

Usage:
  python test_llmfree_api.py \
    --base-url http://192.168.2.200:8010/v1 \
    --api-key sk-anything
"""

import argparse
import json
import sys
from urllib import request, error


def post_json(url: str, payload: dict, api_key: str, timeout: int = 30):
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", f"Bearer {api_key}")

    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body
    except error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        return e.code, body


def test_chat(base_url: str, api_key: str, model: str):
    url = f"{base_url.rstrip('/')}/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a concise assistant."},
            {"role": "user", "content": "Reply exactly: pong"},
        ],
        "temperature": 0,
    }

    code, body = post_json(url, payload, api_key)
    print("\n=== CHAT TEST ===")
    print(f"POST {url}")
    print(f"HTTP {code}")
    if code != 200:
        print(body)
        return False

    try:
        obj = json.loads(body)
        content = obj["choices"][0]["message"]["content"]
        model_used = obj.get("model")
        print(f"model: {model_used}")
        print(f"reply: {content}")
        return True
    except Exception:
        print("Response parse failed, raw body:")
        print(body)
        return False


def test_embedding(base_url: str, api_key: str, model: str):
    url = f"{base_url.rstrip('/')}/embeddings"
    payload = {
        "model": model,
        "input": "hello embedding",
    }

    code, body = post_json(url, payload, api_key)
    print("\n=== EMBEDDING TEST ===")
    print(f"POST {url}")
    print(f"HTTP {code}")
    if code != 200:
        print(body)
        return False

    try:
        obj = json.loads(body)
        vec = obj["data"][0]["embedding"]
        print(f"embedding_length: {len(vec)}")
        print(f"first_5: {vec[:5]}")
        return True
    except Exception:
        print("Response parse failed, raw body:")
        print(body)
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://192.168.2.200:8010/v1")
    parser.add_argument("--api-key", default="sk-anything")
    parser.add_argument("--chat-model", default="text", help="Use text for pool routing")
    parser.add_argument("--embedding-model", default="embedding", help="Use embedding for pool routing")
    args = parser.parse_args()

    ok_chat = test_chat(args.base_url, args.api_key, args.chat_model)
    ok_embed = test_embedding(args.base_url, args.api_key, args.embedding_model)

    if ok_chat and ok_embed:
        print("\n✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("\n❌ SOME TESTS FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
