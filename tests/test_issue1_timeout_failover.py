import asyncio
from fastapi.testclient import TestClient

import main


class _DummyResult:
    def scalars(self):
        return self

    def all(self):
        return []


class _DummySession:
    async def execute(self, _):
        return _DummyResult()


class _DummySessionCtx:
    async def __aenter__(self):
        return _DummySession()

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _Resp:
    def model_dump(self, **kwargs):
        return {
            "id": "cmpl-test",
            "object": "chat.completion",
            "model": "model-b",
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "ok"}}],
        }


def test_chat_timeout_failover_to_next_model(monkeypatch):
    # keep test fast
    monkeypatch.setattr(main, "MODEL_TIMEOUT_SECONDS", 0.01)
    monkeypatch.setattr(main, "async_session", lambda: _DummySessionCtx())

    import router
    monkeypatch.setattr(router, "TEXT_MODELS_LIST", ["model-a", "model-b"])

    async def fake_acompletion(**kwargs):
        if kwargs["model"] == "model-a":
            await asyncio.sleep(0.05)  # trigger timeout
        return _Resp()

    monkeypatch.setattr(main.text_router, "acompletion", fake_acompletion)

    client = TestClient(main.app)
    res = client.post(
        "/v1/chat/completions",
        json={"model": "text", "messages": [{"role": "user", "content": "hi"}]},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["model"] == "model-b"
