from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "THE-LIMBO"
    OPENAI_API_KEY: str = "sk-placeholder-key"
    GOOGLE_API_KEY: str = "ai-placeholder-key"
    DB_URL: str = "postgresql://user:pass@localhost/dbname" 
    SECRET_KEY: str = "dev-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()
