from typing import List


def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100
) -> List[str]:
    """
    Divide um texto em pedaços (chunks) com sobreposição simples de caracteres.
    É bem simples, mas suficiente pro nosso MVP de RAG.

    - chunk_size: tamanho máximo de cada pedaço
    - overlap: quantidade de caracteres que se repetem entre um chunk e outro
    """
    if not text:
        return []

    text = text.strip().replace("\r\n", "\n")

    chunks: List[str] = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]

        chunks.append(chunk.strip())

        # próximo início com overlap
        start = end - overlap
        if start < 0:
            start = 0

    return chunks
