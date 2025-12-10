import os
from dotenv import load_dotenv
from pydantic import BaseModel

# Carrega variáveis do .env
load_dotenv()


class Settings(BaseModel):
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    embed_model: str = os.getenv("EMBED_MODEL", "text-embedding-3-small")
    chunk_size: int = int(os.getenv("CHUNK_SIZE", 500))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", 100))
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./rag.db")
    env: str = os.getenv("ENV", "local")


settings = Settings()
