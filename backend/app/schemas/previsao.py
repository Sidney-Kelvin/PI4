from datetime import date
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.varejo import OBSERVACAO_MOEDA, TotalPeriodo


class StatusPrevisao(BaseModel):
    dados_importados: bool
    planejamento_disponivel: bool
    modelo_treinado: bool
    versao_modelo: Optional[str] = None
    treinado_em: Optional[str] = None
    mensagem: str


class MetricasModelo(BaseModel):
    mae: float = Field(..., description="Erro absoluto médio (vendas diárias)")
    rmse: float = Field(..., description="Raiz do erro quadrático médio (vendas diárias)")
    mape: Optional[float] = Field(None, description="Erro percentual absoluto médio (%)")
    dias_avaliados: int
    dias_excluidos_mape: int = Field(..., description="Dias com venda real zero, excluídos do MAPE")


class PontoPrevisao(BaseModel):
    data: date
    vendas_previstas: float
    lojas_abertas_estimadas: int
    fonte_calendario: str = Field(..., description="'planejamento' (test.csv) ou 'estimado'")


class PrevisaoProximoMes(BaseModel):
    mes_referencia: str = Field(..., description="Mês previsto (AAAA-MM)")
    periodo_inicio: date
    periodo_fim: date
    valor_previsto: float
    ultimo_mes_real: TotalPeriodo
    variacao_percentual: Optional[float] = Field(None, description="Previsão vs. último mês do histórico (%)")
    ultima_data_historico: date
    lojas_referencia: int
    fonte_calendario: str = Field(..., description="planejamento, estimado ou misto")
    versao_modelo: str
    metricas: MetricasModelo
    diario: list[PontoPrevisao]
    observacao_moeda: str = OBSERVACAO_MOEDA


class PontoComparacao(BaseModel):
    periodo: str
    real: Optional[float] = None
    previsto: Optional[float] = None


class HistoricoVsPrevisao(BaseModel):
    mes_previsto: str
    diario: list[PontoComparacao]
    mensal: list[PontoComparacao]


class PontoAvaliacao(BaseModel):
    data: date
    real: float
    previsto: float
    baseline: float


class ResumoMesAvaliacao(BaseModel):
    mes: str
    real: float
    previsto: float
    baseline: float
    erro_percentual: Optional[float] = None


class HistoricoTreino(BaseModel):
    epoca: int
    perda_treino: float
    perda_validacao: float


class AvaliacaoModelo(BaseModel):
    versao: str
    treinado_em: str
    arquitetura: str
    parametros_treinaveis: int
    config: dict
    features_exogenas: list[str]
    divisao: dict
    amostras: dict
    epocas_executadas: int
    melhor_epoca: int
    periodo_teste: dict
    metricas_lstm: MetricasModelo
    metricas_baseline: MetricasModelo
    meses: list[ResumoMesAvaliacao]
    diario: list[PontoAvaliacao]
    historico_treino: list[HistoricoTreino]
