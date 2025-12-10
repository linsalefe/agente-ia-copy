import os
import glob
import json
from typing import List, Tuple

from openai import OpenAI

from app.config import settings
from app.database import SessionLocal
from app.models.rag_models import Document, Chunk
from app.utils.chunker import chunk_text


client = OpenAI(api_key=settings.openai_api_key)


def get_project_root() -> str:
    """
    Retorna o diretório raiz do projeto (pasta agente-ia-copy).
    Estrutura:
        agente-ia-copy/
            app/
                rag/
                    ingest.py
            kb/
    """
    # __file__ = app/rag/ingest.py
    # subimos 3 níveis: ingest.py -> rag -> app -> raiz
    return os.path.dirname(
        os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )
    )


def load_markdown_files(kb_dir: str) -> List[Tuple[str, str]]:
    """
    Lê todos os arquivos .md da pasta kb (exceto README)
    Retorna lista de tuplas: (filename, content)
    """
    pattern = os.path.join(kb_dir, "*.md")
    files = glob.glob(pattern)

    md_files = []
    for path in files:
        name = os.path.basename(path)
        if name.lower().startswith("readme"):
            continue

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        md_files.append((name, content))

    return md_files


def extract_title_and_type(filename: str, content: str) -> Tuple[str, str]:
    """
    Extrai título e tipo do documento.
    """
    title = None
    for line in content.splitlines():
        line = line.strip()
        if line.startswith("#"):
            title = line.lstrip("#").strip()
            break

    if not title:
        title = filename

    lower_name = filename.lower()
    if "pos" in lower_name or "pós" in lower_name:
        doc_type = "pos"
    elif "congresso" in lower_name:
        doc_type = "congresso"
    elif "comunidade" in lower_name:
        doc_type = "comunidade"
    else:
        doc_type = "geral"

    return title, doc_type


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Gera embeddings usando OpenAI.
    """
    if not texts:
        return []

    response = client.embeddings.create(
        model=settings.embed_model,
        input=texts,
    )

    return [item.embedding for item in response.data]


def ingest():
    """
    Pipeline completo:
    - Lê .md da pasta kb/
    - Quebra em chunks
    - Gera embeddings
    - Salva em SQLite (documents + chunks)
    """
    project_root = get_project_root()
    kb_dir = os.path.join(project_root, "kb")

    print(f"📂 Lendo arquivos Markdown em: {kb_dir}")

    md_files = load_markdown_files(kb_dir)
    if not md_files:
        print("⚠️ Nenhum arquivo .md encontrado em kb/. Crie alguns arquivos primeiro.")
        return

    db = SessionLocal()

    try:
        for filename, content in md_files:
            print(f"➡️ Ingerindo arquivo: {filename}")

            title, doc_type = extract_title_and_type(filename, content)

            # Criar documento
            document = Document(
                title=title,
                source=title,
                type=doc_type,
                filename=filename,
            )
            db.add(document)
            db.flush()

            # Chunking
            chunks = chunk_text(
                content,
                chunk_size=settings.chunk_size,
                overlap=settings.chunk_overlap,
            )
            print(f"   - {len(chunks)} chunks gerados")

            # Embeddings
            embeddings = embed_texts(chunks)
            print(f"   - {len(embeddings)} embeddings gerados")

            # Salvar chunks
            for idx, (chunk_text_value, emb) in enumerate(zip(chunks, embeddings)):
                chunk = Chunk(
                    document_id=document.id,
                    chunk_index=idx,
                    content=chunk_text_value,
                    embedding=json.dumps(emb),
                )
                db.add(chunk)

            db.commit()
            print(f"✅ Documento '{title}' ingerido com sucesso.\n")

    except Exception as e:
        db.rollback()
        print(f"❌ Erro durante ingestão: {e}")
        raise
    finally:
        db.close()

    print("🎉 Ingestão finalizada.")


if __name__ == "__main__":
    ingest()
