from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.previsao import AvaliacaoModelo, HistoricoVsPrevisao, PrevisaoProximoMes, StatusPrevisao
from app.services.previsao_service import PrevisaoService

router = APIRouter(prefix="/previsoes", tags=["Previsões (LSTM)"])

RESPOSTAS_ERRO = {
    404: {"description": "Dados históricos ainda não importados"},
    503: {"description": "Modelo ainda não treinado"},
}


@router.get("/status", response_model=StatusPrevisao,
            summary="Situação dos dados e do modelo (sempre responde 200)")
def status_previsao(db: Session = Depends(get_db)):
    return PrevisaoService(db).status()


@router.get("/proximo-mes", response_model=PrevisaoProximoMes, responses=RESPOSTAS_ERRO,
            summary="Previsão de vendas do mês seguinte ao histórico")
def proximo_mes(db: Session = Depends(get_db)):
    """Executa a inferência com o modelo LSTM treinado: prevê cada dia do próximo mês
    de forma recursiva e soma os dias para obter o total mensal. O resultado também
    é gravado na tabela `previsoes_vendas`."""
    return PrevisaoService(db).proximo_mes()


@router.get("/historico-vs-previsao", response_model=HistoricoVsPrevisao, responses=RESPOSTAS_ERRO,
            summary="Série real recente + previsão (diária e mensal) para gráficos")
def historico_vs_previsao(
    dias: int = Query(120, ge=30, le=730, description="Dias de histórico real na série diária"),
    db: Session = Depends(get_db),
):
    return PrevisaoService(db).historico_vs_previsao(dias)


@router.get("/avaliacao", response_model=AvaliacaoModelo, responses={503: RESPOSTAS_ERRO[503]},
            summary="Métricas (MAE, RMSE, MAPE) e real × previsto no período de teste")
def avaliacao(db: Session = Depends(get_db)):
    return PrevisaoService(db).avaliacao()
