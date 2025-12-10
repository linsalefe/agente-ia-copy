from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.generate_email import router as generate_email_router

app = FastAPI(
    title="CENAT Email Copy Agent",
    version="1.0.0"
)

# CORS – libera o front para chamar a API no navegador
origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "*"  # em dev, podemos deixar aberto
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok"}


# Rotas
app.include_router(generate_email_router)
