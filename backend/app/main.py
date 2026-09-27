import logging

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.core.config import settings
from app.core.database import engine
from app.controllers import (
    produto_controller,
    venda_controller,
    despesa_controller,
    dashboard_controller,
    external_controller,
    varejo_controller,
    previsao_controller,
)

# A estrutura do banco é responsabilidade exclusiva do Alembic (alembic upgrade head),
# executado pelo container antes de iniciar a API. Não há create_all() aqui.

logger = logging.getLogger("finantrack")

app = FastAPI(
    title=settings.app_name,
    description=(
        "FinanTrack (PI4) — API REST de acompanhamento financeiro de varejo: cadastros operacionais "
        "(produtos, vendas, despesas), histórico de vendas do dataset Rossmann Store Sales e previsão "
        "de vendas com um modelo LSTM treinado localmente."
    ),
    version=settings.app_version,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(OperationalError)
async def banco_indisponivel(_: Request, erro: OperationalError):
    logger.error("Falha de conexão com o banco: %s", erro)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "Banco de dados indisponível. Verifique se o container 'db' está em execução."},
    )


@app.exception_handler(SQLAlchemyError)
async def erro_banco(_: Request, erro: SQLAlchemyError):
    logger.exception("Erro de banco de dados: %s", erro)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro ao acessar o banco de dados. Verifique se as migrations foram aplicadas."},
    )


app.include_router(dashboard_controller.router)
app.include_router(produto_controller.router)
app.include_router(venda_controller.router)
app.include_router(despesa_controller.router)
app.include_router(external_controller.router)
app.include_router(varejo_controller.router)
app.include_router(previsao_controller.router)


@app.get("/", tags=["Health"])
def health_check():
    return {"status": "ok", "app": settings.app_name, "versao": settings.app_version}


@app.get("/health/db", tags=["Health"])
def health_db():
    try:
        with engine.connect() as conexao:
            conexao.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "erro", "banco": "indisponível"})
    return {"status": "ok", "banco": "disponível"}
