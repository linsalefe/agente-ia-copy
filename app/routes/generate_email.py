from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.email_generator import generate_email

router = APIRouter(prefix="/email", tags=["Email Generator"])


class EmailRequest(BaseModel):
    product: str
    objective: str
    briefing: str | None = None


@router.post("/generate")
def generate_email_route(payload: EmailRequest):
    try:
        # Chama serviço que faz o RAG + LLM
        result = generate_email(
            product=payload.product,
            objective=payload.objective,
            briefing=payload.briefing or ""
        )

        return {
            "assunto": result.get("assunto", ""),
            "corpo": result.get("corpo", "")
        }

    except Exception as e:
        print("❌ ERRO NO /email/generate:", str(e))
        raise HTTPException(status_code=500, detail="Erro interno ao gerar o e-mail.")
