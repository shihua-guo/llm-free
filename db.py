from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from config import settings

Base = declarative_base()
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class ModelStatus(Base):
    __tablename__ = "model_status"

    id = Column(Integer, primary_key=True)
    model_name = Column(String(100), unique=True, nullable=False)
    pool_type = Column(String(20)) # text, embedding, vision
    is_available = Column(Boolean, default=True)
    cool_down_until = Column(DateTime, nullable=True)
    last_error = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

async def init_db():
    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all) # Careful in prod
        await conn.run_sync(Base.metadata.create_all)
