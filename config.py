from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    DASHSCOPE_API_KEY: str = "YOUR_DASHSCOPE_API_KEY"
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://admin:password@192.168.2.200:5432/llm_free"
    
    # Port
    PORT: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()
