from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.varejo import ItemQuebra, LojaResponse, PontoSerie, RankingLoja, ResumoVarejo
from app.services.varejo_service import VarejoService

router = APIRouter(prefix="/varejo", tags=["Varejo (histórico Rossmann)"])


@router.get("/resumo", response_model=ResumoVarejo, summary="Indicadores gerais do histórico de vendas")
def resumo(db: Session = Depends(get_db)):
    return VarejoService(db).resumo()


@router.get("/vendas/serie", response_model=list[PontoSerie], summary="Vendas agregadas por dia, mês ou ano")
def serie(
    agrupamento: str = Query("mes", description="dia, mes ou ano"),
    loja_id: Optional[int] = Query(None, description="Filtra uma loja específica"),
    inicio: Optional[date] = Query(None, description="Data inicial (AAAA-MM-DD)"),
    fim: Optional[date] = Query(None, description="Data final (AAAA-MM-DD)"),
    db: Session = Depends(get_db),
):
    return VarejoService(db).serie(agrupamento, loja_id, inicio, fim)


@router.get("/vendas/por-tipo-loja", response_model=list[ItemQuebra], summary="Vendas por tipo de loja")
def por_tipo_loja(db: Session = Depends(get_db)):
    return VarejoService(db).por_tipo_loja()


@router.get("/vendas/por-sortimento", response_model=list[ItemQuebra], summary="Vendas por nível de sortimento")
def por_sortimento(db: Session = Depends(get_db)):
    return VarejoService(db).por_sortimento()


@router.get("/vendas/por-promocao", response_model=list[ItemQuebra], summary="Vendas com e sem promoção")
def por_promocao(db: Session = Depends(get_db)):
    return VarejoService(db).por_promocao()


@router.get("/vendas/por-feriado", response_model=list[ItemQuebra], summary="Vendas por feriado estadual e escolar")
def por_feriado(db: Session = Depends(get_db)):
    return VarejoService(db).por_feriado()


@router.get("/vendas/por-dia-semana", response_model=list[ItemQuebra], summary="Vendas por dia da semana")
def por_dia_semana(db: Session = Depends(get_db)):
    return VarejoService(db).por_dia_semana()


@router.get("/lojas/ranking", response_model=list[RankingLoja], summary="Lojas com maior ou menor faturamento")
def ranking_lojas(
    limite: int = Query(10, ge=1, le=100),
    ordem: str = Query("maiores", description="maiores ou menores"),
    db: Session = Depends(get_db),
):
    return VarejoService(db).ranking_lojas(limite, ordem)


@router.get("/lojas", response_model=list[LojaResponse], summary="Lista as lojas")
def listar_lojas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1200),
    tipo_loja: Optional[str] = Query(None, description="a, b, c ou d"),
    db: Session = Depends(get_db),
):
    return VarejoService(db).listar_lojas(skip, limit, tipo_loja)


@router.get("/lojas/{loja_id}", response_model=LojaResponse, summary="Detalhes de uma loja")
def obter_loja(loja_id: int, db: Session = Depends(get_db)):
    return VarejoService(db).obter_loja(loja_id)
