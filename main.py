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
    from router import TEXT_MODELS_LIST
    data = await request.json()
    if data.get("stream") is True:
        data["stream"] = False

    user_model = data.get("model", "text")
    is_pool = user_model in ["text"]

    async with async_session() as session:
        result = await session.execute(select(ModelStatus))
        db_models = result.scalars().all()
        unavailable = {m.model_name for m in db_models if not m.is_available}

    models_to_try = [user_model]
    if is_pool:
        models_to_try = [m for m in TEXT_MODELS_LIST if m not in unavailable]

    last_error = None
    for model_name in models_to_try:
        current_data = data.copy()
        current_data["model"] = model_name
        try:
            response = await text_router.acompletion(**current_data)
            return JSONResponse(content=to_json_payload(response))
        except litellm.exceptions.ContextWindowExceededError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            if any(kw in error_str for kw in ["quota", "limit", "out of", "not authorized", "allocationquota", "freetieronly"]):
                model_used = getattr(e, "model", model_name)
                # LiteLLM sometimes prefixes model, strip 'openai/' prefix
                model_used = model_used.replace("openai/", "")
                await mark_model_down(model_used, str(e))
                continue # Try next model
            break # other error, raise it

    raise HTTPException(status_code=500, detail=str(last_error) if last_error else "No available models")

@app.post("/v1/embeddings")
async def embeddings(request: Request):
    from router import EMBEDDING_MODELS_LIST
    data = await request.json()
    user_model = data.get("model", "embedding")
    is_pool = user_model in ["embedding"]

    async with async_session() as session:
        result = await session.execute(select(ModelStatus))
        db_models = result.scalars().all()
        unavailable = {m.model_name for m in db_models if not m.is_available}

    models_to_try = [user_model]
    if is_pool:
        models_to_try = [m for m in EMBEDDING_MODELS_LIST if m not in unavailable]

    last_error = None
    for model_name in models_to_try:
        current_data = data.copy()
        current_data["model"] = model_name
        try:
            response = await embedding_router.aembedding(**current_data)
            return JSONResponse(content=to_json_payload(response))
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            if any(kw in error_str for kw in ["quota", "limit", "out of", "not authorized", "allocationquota", "freetieronly"]):
                model_used = getattr(e, "model", model_name)
                model_used = model_used.replace("openai/", "")
                await mark_model_down(model_used, str(e))
                continue
            break

    raise HTTPException(status_code=500, detail=str(last_error) if last_error else "No available models")

@app.post("/v1/images/generations")
async def image_generation(request: Request):
    from router import VISION_MODELS_LIST
    data = await request.json()
    user_model = data.get("model", "vision")
    is_pool = user_model in ["vision"]

    async with async_session() as session:
        result = await session.execute(select(ModelStatus))
        db_models = result.scalars().all()
        unavailable = {m.model_name for m in db_models if not m.is_available}

    models_to_try = [user_model]
    if is_pool:
        models_to_try = [m for m in VISION_MODELS_LIST if m not in unavailable]

    last_error = None
    for model_name in models_to_try:
        current_data = data.copy()
        current_data["model"] = model_name
        try:
            response = await vision_router.aimage_generation(**current_data)
            return JSONResponse(content=to_json_payload(response))
        except Exception as e:
            last_error = e
            error_str = str(e).lower()
            if any(kw in error_str for kw in ["quota", "limit", "out of", "not authorized", "allocationquota", "freetieronly"]):
                model_used = getattr(e, "model", model_name)
                model_used = model_used.replace("openai/", "")
                await mark_model_down(model_used, str(e))
                continue
            break

    raise HTTPException(status_code=500, detail=str(last_error) if last_error else "No available models")

@app.get("/status")
async def get_status():
    async with async_session() as session:
        result = await session.execute(select(ModelStatus))
        models = result.scalars().all()
        return models

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
