from app.database import SessionLocal
from app.models.rag_models import Chunk
from sqlalchemy import text

# Busca simples no RAG (keyword search)
def search_rag(query: str, top_k: int = 5):
    db = SessionLocal()

    # Busca por LIKE simples — funciona bem para MVP
    q = f"%{query.lower()}%"

    chunks = db.query
