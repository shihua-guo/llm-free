from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from router import text_router, embedding_router, vision_router
from db import init_db, async_session, ModelStatus
from sqlalchemy import select, update
from datetime import datetime, timedelta
import litellm

app = FastAPI(title="LLM-Free")


def to_json_payload(resp):
    """Normalize LiteLLM/OpenAI objects to plain JSON-serializable dicts."""
    if hasattr(resp, "model_dump"):
        try:
            return resp.model_dump(mode="json", exclude_none=True)
        except Exception:
            return resp.model_dump(exclude_none=True)
    return jsonable_encoder(resp)

@app.on_event("startup")
async def startup():
    await init_db()

async def mark_model_down(model_name: str, error_msg: str):
    async with async_session() as session:
        # 去掉前缀以匹配数据库中的名字
        clean_name = model_name.replace("dashscope/", "")
        q = update(ModelStatus).where(ModelStatus.model_name == clean_name).values(
            is_available=False,
            last_error=error_msg[:254],
            cool_down_until=datetime.utcnow() + timedelta(days=1)
        )
        await session.execute(q)
        await session.commit()

@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    data = await request.json()
    # 当前实现统一走非流式返回，避免上游流对象无法被 FastAPI 直接序列化导致 500
    if data.get("stream") is True:
        data["stream"] = False

    # 获取用户请求的模型名
    user_model = data.get("model", "text")
    
    # 逻辑：
    # 1. 如果用户写 "text"、"gpt-3.5-turbo" 等不在池子里的名字，统一转为 "text" 自动路由
    # 2. 如果用户写了池子里存在的具体名字（如 "qwen-max"），尝试精准调用
    
    try:
        # 如果模型不是 "text" 且不是已知的池内模型名，强制设为 "text" 以便路由
        # 这里简化处理：只要不是 "text"，router 内部会根据 model_list 匹配具体模型或池子
        response = await text_router.acompletion(**data)
        return JSONResponse(content=to_json_payload(response))
    except litellm.exceptions.ContextWindowExceededError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_str = str(e).lower()
        # 捕获额度或限制相关错误
        if any(kw in error_str for kw in ["quota", "limit", "out of", "not authorized"]):
            model_used = getattr(e, "model", "unknown")
            await mark_model_down(model_used, str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/embeddings")
async def embeddings(request: Request):
    data = await request.json()
    try:
        # 强制使用池子路由，除非明确指定
        if data.get("model") not in ["embedding"]:
             data["model"] = "embedding"
        response = await embedding_router.aembedding(**data)
        return JSONResponse(content=to_json_payload(response))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/images/generations")
async def image_generation(request: Request):
    data = await request.json()
    try:
        if data.get("model") not in ["vision"]:
            data["model"] = "vision"
        response = await vision_router.aimage_generation(**data)
        return JSONResponse(content=to_json_payload(response))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status")
async def get_status():
    async with async_session() as session:
        result = await session.execute(select(ModelStatus))
        models = result.scalars().all()
        return models

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
