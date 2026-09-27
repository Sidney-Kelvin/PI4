from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

OBSERVACAO_MOEDA = (
    "Valores na unidade monetária original do dataset Rossmann Store Sales "
    "(não convertidos para R$)."
)


class TotalPeriodo(BaseModel):
    periodo: str = Field(..., description="Período no formato AAAA-MM")
    vendas: float


class ResumoVarejo(BaseModel):
    dados_importados: bool
    faturamento_total: float
    clientes_total: int
    registros: int = Field(..., description="Linhas loja × dia importadas de train.csv")
    total_lojas: int
    data_inicio: Optional[date] = None
    data_fim: Optional[date] = None
    dias: int
    media_diaria: float = Field(..., description="Faturamento médio da rede por dia")
    ultimo_mes: Optional[TotalPeriodo] = None
    mes_anterior: Optional[TotalPeriodo] = None
    variacao_mensal_percentual: Optional[float] = None
    dias_planejados: int = Field(..., description="Dias futuros com calendário planejado (test.csv)")
    observacao_moeda: str = OBSERVACAO_MOEDA


class PontoSerie(BaseModel):
    periodo: str
    vendas: float
    clientes: int
    dias_loja_abertos: int


class ItemQuebra(BaseModel):
    categoria: str
    descricao: str
    vendas_totais: float
    dias_loja_abertos: int
    media_por_dia_loja: float = Field(..., description="Venda média de uma loja aberta em um dia")


class RankingLoja(BaseModel):
    loja_id: int
    tipo_loja: str
    vendas_totais: float
    dias_abertos: int
    media_diaria: float


class LojaResponse(BaseModel):
    id: int
    tipo_loja: str
    sortimento: str
    distancia_concorrencia: Optional[int] = None
    concorrencia_desde_mes: Optional[int] = None
    concorrencia_desde_ano: Optional[int] = None
    promo2: bool
    promo2_desde_semana: Optional[int] = None
    promo2_desde_ano: Optional[int] = None
    intervalo_promo2: Optional[str] = None

    model_config = {"from_attributes": True}
