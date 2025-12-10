import os
import json
from openai import OpenAI

from app.rag.search import search_rag

# ============================================
# Config OpenAI
# ============================================
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY não definido no ambiente.")

client = OpenAI(api_key=OPENAI_API_KEY)


# ============================================
# Carrega o system prompt oficial do agente
# ============================================
def load_system_prompt() -> str:
    """
    Lê o prompt sistêmico do agente de copy do CENAT.
    """
    # Caminho relativo a partir da raiz do projeto
    prompt_path = os.path.join("app", "docs", "prompts", "agent_system.md")

    if not os.path.exists(prompt_path):
        # Fallback mínimo, só pra não quebrar
        return (
            "Você é um agente de copywriting institucional do CENAT. "
            "Gere e-mails profissionais, éticos e alinhados à saúde mental."
        )

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


# ============================================
# Função principal — gera e-mail com RAG
# ============================================
def generate_email(product: str, objective: str, briefing: str) -> dict:
    """
    Gera um e-mail completo (assunto + corpo) usando:
    - tipo de produto (pós, congresso, intercâmbio etc.)
    - objetivo do e-mail (ultimas_vagas, desconto, reaquecimento etc.)
    - briefing livre
    - contexto do RAG com os materiais do CENAT

    Retorna dict:
    {
        "assunto": "...",
        "corpo": "..."
    }
    """

    # 1) Busca contexto no RAG
    query = f"{product} {objective} {briefing}"
    rag_context = search_rag(query=query, top_k=8)

    # 2) Carrega o system prompt
    system_prompt = load_system_prompt()

    # 3) Monta mensagem de usuário orientando o formato JSON
    user_prompt = f"""
Você deve gerar um e-mail institucional do CENAT **usando fortemente o contexto abaixo**.

### Dados enviados pelo usuário:
- Produto (tipo): {product}
- Objetivo do e-mail: {objective}
- Briefing adicional: {briefing}

### Contexto do RAG (conteúdo oficial do CENAT):
{rag_context}

IMPORTANTE:
- Use o contexto do RAG como fonte principal de informações.
- Adapte o estilo aos e-mails reais do CENAT (Pablo, Mariana, Victória).
- Adapte o tom ao objetivo: por exemplo, 'ultimas_vagas', 'desconto', 'reaquecimento' etc.
- Nunca invente datas, preços ou números específicos se eles não estiverem no contexto.

RETORNO OBRIGATÓRIO:
Responda **APENAS** com um JSON válido, no formato:

{{
  "assunto": "<linha do assunto, sem emojis>",
  "corpo": "<corpo completo do e-mail, com quebras de linha em \\n>"
}}

Nada antes, nada depois, nenhum comentário. Apenas o JSON.
"""

    # 4) Chamada ao modelo
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.4,
        max_tokens=900,
    )

    content = response.choices[0].message.content

    # 5) Tenta interpretar como JSON
    try:
        data = json.loads(content)
        assunto = data.get("assunto", "").strip() or "Assunto não definido"
        corpo = data.get("corpo", "").strip() or ""
    except Exception:
        # fallback: se vier quebrado, devolve tudo no corpo
        assunto = "Assunto não definido"
        corpo = content.strip()

    return {
        "assunto": assunto,
        "corpo": corpo,
    }
