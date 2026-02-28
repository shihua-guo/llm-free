from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM (OpenAI-compatible)
    LLM_API_BASE: str = "http://192.168.2.200:3000/v1"
    LLM_API_KEY: str = "YOUR_LLM_API_KEY"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://admin:password@192.168.2.200:5432/llm_free"

    # Port
    PORT: int = 8000

    class Config:
        env_file = ".env"

settings = Settings()
