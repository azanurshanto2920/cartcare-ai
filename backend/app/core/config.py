from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./cartcare.db"
    groq_api_key: str = ""
    jwt_secret: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    llm_model: str = "openai/gpt-oss-120b"
    chroma_path: str = "./chroma_db"

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()