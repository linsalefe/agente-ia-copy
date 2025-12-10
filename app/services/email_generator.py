import os
from openai import OpenAI

from app.rag.search import search_rag

# Carrega API KEY
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)


# ================================================
# Utilitário para carregar system prompt oficial
# ================================================
def load_system_prompt():
    prompt_path = "app/docs/prompts/agent_system.md"


    if not os.path.exists(prompt_path):
        return "Você é um agente de copywriting institucional do CENAT."

    with open(prompt_path, "r", encoding="utf-8") as f:
        return f.read()


# ================================================
# Função principal — gera e-mail completo
# ================================================
def generate_email(product: str, objective: str, briefing: str):
    """
    Recebe:
    - product: tipo (pos, congresso, intercambio, etc)
    - objective: ultimas_vagas, desconto, etc
    - briefing: instruções adicionais

    Retorna:
    - assunto
    - corpo do e-mail
    """

    # 1 — Busca contexto via RAG
    rag_context = search_rag(query=f"{product} {objective} {briefing}")

    # 2 — Carrega prompt oficial
    system_prompt = load_system_prompt()

    # 3 — Mensagem do usuário enviada ao modelo
    user_prompt = f"""
Gere um e-mail institucional completo do CENAT.

Informações enviadas pelo usuário:
- Produto: {product}
- Objetivo do e-mail: {objective}
- Briefing: {briefing}

Use o seguinte contexto do RAG caso seja útil:

{rag_context}

IMPORTANTE:
- Retorne APENAS um JSON no formato:
{{
  "assunto": "<linha do assunto>",
  "corpo": "<corpo completo do e-mail>"
}}
Sem comentários.
"""

    # ================================================
    # 4 — Chamada ao modelo da OpenAI
    # ================================================
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # leve, rápido e barato
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.5,
        max_tokens=700
    )

    # 5 — Extrai o conteúdo da resposta
    content = response.choices[0].message.content

    # 6 — Tenta converter retorno em JSON
    import json

    try:
        data = json.loads(content)
        assunto = data.get("assunto", "Assunto não definido")
        corpo = data.get("corpo", "")
    except Exception:
        # fallback caso modelo retorne algo inesperado
        assunto = "Assunto não definido"
        corpo = content

    # 7 — Retorna estrutura final
    return {
        "assunto": assunto,
        "corpo": corpo
    }
