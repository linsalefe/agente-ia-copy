import json
import math
from typing import List, Optional, Tuple

from openai import OpenAI

from app.config import settings
from app.database import SessionLocal
from app.models.rag_models import Document, Chunk


client = OpenAI(api_key=settings.openai_api_key)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calcula similaridade de cosseno entre dois vetores."""
    if not a or not b or len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return dot / (norm_a * norm_b)


def embed_query(query: str) -> List[float]:
    """Gera embedding para a query."""
    response = client.embeddings.create(
        model=settings.embed_model,
        input=[query],
    )
    return response.data[0].embedding


def search_chunks(
    query: str,
    top_k: int = 5,
    type_filter: Optional[str] = None,
    product_hint: Optional[str] = None,
) -> List[Tuple[Chunk, float]]:
    """
    Busca os chunks mais relevantes para a query.

    - type_filter: filtrar por tipo de documento (ex: "pos", "congresso")
    - product_hint: filtrar por título/fonte contendo esse termo (ex: "Saúde Mental")
    """
    db = SessionLocal()
    try:
        query_emb = embed_query(query)

        # monta query base
        q = db.query(Chunk).join(Document)

        if type_filter:
            q = q.filter(Document.type == type_filter)

        if product_hint:
            like = f"%{product_hint}%"
            q = q.filter(Document.title.ilike(like))

        chunks: List[Chunk] = q.all()

        scored: List[Tuple[Chunk, float]] = []
        for ch in chunks:
            try:
                emb = json.loads(ch.embedding)
                score = cosine_similarity(query_emb, emb)
                scored.append((ch, score))
            except Exception:
                # se der erro no parse do embedding, ignora o chunk
                continue

        # ordena por score desc e pega top_k
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_k]

    finally:
        db.close()


def build_context_from_chunks(results: List[Tuple[Chunk, float]]) -> str:
    """
    Junta o conteúdo dos chunks em um único texto de contexto.
    """
    parts: List[str] = []
    for chunk, score in results:
        txt = chunk.content.strip()
        if not txt:
            continue
        parts.append(txt)

    return "\n\n---\n\n".join(parts)


if __name__ == "__main__":
    # Teste rápido de linha de comando
    query = "pós-graduação em saúde mental do CENAT"
    results = search_chunks(query, top_k=3)

    print(f"🔍 {len(results)} chunks encontrados")
    for idx, (chunk, score) in enumerate(results, start=1):
        print(f"\n#{idx} | score={score:.4f}")
        print(chunk.content[:300], "...")
