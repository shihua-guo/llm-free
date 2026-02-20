import asyncio
from db import async_session, ModelStatus, init_db
from router import TEXT_MODELS_LIST, EMBEDDING_MODELS_LIST, VISION_MODELS_LIST
from sqlalchemy import select

async def seed():
    # 确保表已创建
    await init_db()
    
    async with async_session() as session:
        # 检查是否已有数据
        try:
            res = await session.execute(select(ModelStatus).limit(1))
            if res.scalar():
                print("DB already seeded.")
                return
        except Exception:
            # 如果表不存在或其他错误，init_db 应该已经处理了创建
            pass

        def add_models(names, p_type):
            for name in names:
                session.add(ModelStatus(model_name=name, pool_type=p_type))

        add_models(TEXT_MODELS_LIST, "text")
        add_models(EMBEDDING_MODELS_LIST, "embedding")
        add_models(VISION_MODELS_LIST, "vision")
        
        await session.commit()
        print("Successfully seeded database with model lists.")

if __name__ == "__main__":
    asyncio.run(seed())
