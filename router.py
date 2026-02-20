from litellm import Router
import logging
from config import settings
from db import async_session, ModelStatus
from sqlalchemy import select
from datetime import datetime

TEXT_MODELS_LIST = ["qwen3.5-plus","qwen3.5-plus-2026-02-15","qwen3.5-397b-a17b","qwen-plus","qwen-turbo","qwen-max","qwen-flash","qwq-plus","qwen-vl-max","qwen-vl-max-latest","qvq-max","qvq-plus","qvq-plus-latest","qwen3-vl-30b-a3b-thinking","qwen3-vl-30b-a3b-instruct","deepseek-v3.2","qwen3-vl-8b-thinking","deepseek-v3.2-exp","qwen-vl-max-2025-08-13","qwen3-vl-flash","qwen3-max","qwen3-vl-plus","qwen3-coder-flash","qvq-plus-2025-05-15","qwen-vl-max-2025-04-08","qwen3-vl-8b-instruct","qwen-vl-plus","qwen-vl-plus-latest","qwen3-vl-235b-a22b-thinking","qwen3-vl-235b-a22b-instruct","qwen-mt-plus","qwen3-next-80b-a3b-instruct","qwen-mt-flash","qwen3-next-80b-a3b-thinking","qwen-mt-turbo","qwen3-30b-a3b-instruct-2507","qwen3-30b-a3b-thinking-2507","qwen3-235b-a22b-thinking-2507","qwen3-235b-a22b-instruct-2507","qwen3-235b-a22b","qwen3-30b-a3b","qwen3-32b","qwen3-14b","qwen3-8b","qwen3-4b","qwen3-1.7b","qwen3-0.6b","qwen3-coder-480b-a35b-instruct","qwen3-coder-next","qwen3-coder-30b-a3b-instruct","kimi-k2.5","kimi-k2-thinking","Moonshot-Kimi-K2-Instruct","qwen2.5-vl-32b-instruct","qwen-turbo-latest","qvq-max-2025-05-15","qvq-max-latest","qvq-max-2025-03-25","glm-5","glm-4.7","glm-4.6","qwen3-coder-plus-2025-09-23","glm-4.5","qwen3-max-2026-01-23","qwen3-vl-plus-2025-12-19","qwen-mt-lite","qwen-flash-character","qwen3-vl-plus-2025-09-23","qwen3-max-preview","glm-4.5-air","qwen3-coder-flash-2025-07-28","qwen-flash-2025-07-28","qwen3-coder-plus-2025-07-22","qwen-long-latest","qwen-long-2025-01-25","qwen-coder-plus","qwen-coder-plus-1106","qwen-coder-plus-latest","qwen-max-latest","qwen-max-2025-01-25","qwen2.5-vl-72b-instruct","qwen2.5-vl-7b-instruct","qwen2.5-vl-3b-instruct","qwen2.5-7b-instruct-1m","qwen2.5-14b-instruct-1m","gui-plus","qvq-72b-preview","qwq-plus-latest","qwq-plus-2025-03-05","qwq-32b","qwen3-vl-flash-2026-01-22","tongyi-xiaomi-analysis-pro","tongyi-xiaomi-analysis-flash","qwen3-vl-flash-2025-10-15","deepseek-v3.1","qwq-32b-preview","qwen-vl-plus-2025-08-15","qwen-vl-plus-2025-05-07","qwen-vl-plus-2025-01-25","deepseek-r1-0528","deepseek-v3","deepseek-r1","qwen-plus-latest","qwen-max-0919","qwen-plus-2025-12-01","qwen-plus-2025-09-11","qwen-plus-2025-07-28","qwen-turbo-2025-07-15","qwen-plus-2025-07-14","qwen-plus-2025-04-28","qwen-turbo-2025-04-28","qwen-plus-2025-01-25","qwen-turbo-2025-02-11","qwen-vl-ocr-2025-11-20","qwen-vl-max-2025-04-02","qwen-vl-max-2025-01-25","qwen-vl-ocr-2025-08-28","qwen-vl-ocr-2025-04-13","qwen-vl-max-1230","qwen-vl-max-1119","qwen-vl-ocr-latest","qwen-vl-ocr-1028","qwen-vl-ocr","qwen2-vl-72b-instruct","qwen-turbo-1101","qwen2-vl-2b-instruct","qwen2-vl-7b-instruct","qwen2.5-72b-instruct","qwen2.5-32b-instruct","qwen2.5-14b-instruct","qwen2.5-math-72b-instruct","qwen2.5-math-7b-instruct","qwen2.5-coder-14b-instruct","qwen2.5-coder-32b-instruct","qwen2.5-coder-7b-instruct","qwen-math-plus","qwen-math-plus-0919","qwen-math-plus-latest","qwen-math-turbo","qwen-math-turbo-0919","qwen-math-turbo-latest","qwen-coder-turbo","qwen-coder-turbo-0919","qwen-coder-turbo-latest","qwen2.5-3b-instruct","qwen2.5-1.5b-instruct","qwen2.5-0.5b-instruct","qwen2.5-7b-instruct","deepseek-r1-distill-llama-70b","deepseek-r1-distill-qwen-32b","deepseek-r1-distill-qwen-14b","deepseek-r1-distill-qwen-7b","tongyi-intent-detect-v3","qwen2-7b-instruct","qwen2-57b-a14b-instruct","qwen2-72b-instruct","qwen-long","qwen-max-0428","qwen1.5-110b-chat","qwen-plus-0112","qwen-plus-1220","llama-4-maverick-17b-128e-instruct","llama-4-scout-17b-16e-instruct","qwen-plus-character","qwen-vl-plus-0102","qwen-math-plus-0816","MiniMax-M2.1","qwen1.5-14b-chat","qwen1.5-32b-chat","qwen1.5-72b-chat","qwen1.5-7b-chat","opennlu-v1"]
EMBEDDING_MODELS_LIST = ["tongyi-embedding-vision-flash","tongyi-embedding-vision-plus","text-embedding-v4","text-embedding-v3","qwen3-vl-rerank","qwen3-vl-embedding","qwen3-rerank","qwen2.5-vl-embedding","gte-rerank-v2","multimodal-embedding-v1","text-embedding-async-v1","text-embedding-async-v2","text-embedding-v1","text-embedding-v2"]
VISION_MODELS_LIST = ["qwen-image-plus-2026-01-09","wan2.6-i2v-flash","wan2.6-i2v","qwen-image-plus","qwen-image-edit-plus","qwen-image-max","wan2.5-i2v-preview","qwen-image","qwen-image-edit","z-image-turbo","qwen-image-edit-plus-2025-12-15","wan2.2-i2v-plus","qwen-mt-image","wan2.6-t2v","wan2.5-t2v-preview","wan2.6-t2i","wan2.5-t2i-preview","wan2.2-kf2v-flash","wan2.2-animate-mix","wan2.2-animate-move","wan2.6-image","wan2.2-s2v","wan2.2-s2v-detect","wan2.2-i2v-flash","wan2.2-t2v-plus","wan2.5-i2i-preview","wan2.2-t2i-plus","wan2.2-t2i-flash","wanx2.1-kf2v-plus","wan2.6-r2v-flash","wan2.6-r2v","wanx2.1-i2v-plus","wanx2.1-t2v-plus","wanx2.1-t2i-plus","wanx2.1-t2v-turbo","wanx2.1-t2i-turbo","qwen-image-edit-plus-2025-10-30","aitryon-plus","aitryon","wanx2.1-i2v-turbo","aitryon-parsing-v1","flux-schnell","flux-dev","emoji-v1","wanx-v1","emoji-detect-v1","animate-anyone-gen2","animate-anyone-template-gen2","animate-anyone-detect-gen2","videoretalk","emo-v1","video-style-transform","emo-detect-v1","liveportrait","liveportrait-detect","qwen-image-edit-max-2026-01-16","qwen-image-edit-max","wanx2.1-vace-plus","wanx2.1-imageedit","wanx2.0-t2i-turbo","flux-merged","aitryon-refiner","wanx-virtualmodel","wanx-poster-generation-v1","wanx-sketch-to-image-lite","wanx-x-painting","image-out-painting","wordart-semantic","wordart-texture","wanx-background-generation-v2","wanx-style-repaint-v1"]

def get_router(pool_type: str):
    if pool_type == "text":
        models = TEXT_MODELS_LIST
    elif pool_type == "embedding":
        models = EMBEDDING_MODELS_LIST
    else:
        models = VISION_MODELS_LIST

    model_list = []
    for i, m in enumerate(models):
        model_list.append({
            "model_name": pool_type, # 所有模型都在同一个池子里
            "litellm_params": {
                "model": f"dashscope/{m}",
                "api_key": settings.DASHSCOPE_API_KEY,
                "order": i # 按列表顺序优先级
            }
        })
    
    # 额外添加直接映射，允许通过具体模型名调用
    for m in models:
        model_list.append({
            "model_name": m,
            "litellm_params": {
                "model": f"dashscope/{m}",
                "api_key": settings.DASHSCOPE_API_KEY
            }
        })

    return Router(
        model_list=model_list,
        enable_pre_call_checks=True,
        num_retries=3,
        allowed_fails=1,
        cooldown_time=300 # 5分钟冷却
    )

text_router = get_router("text")
embedding_router = get_router("embedding")
vision_router = get_router("vision")
