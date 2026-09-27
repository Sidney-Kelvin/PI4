"""Camada de dados históricos de varejo (dataset Rossmann Store Sales).

Estas tabelas são independentes dos módulos operacionais herdados do PI3
(produtos/vendas/despesas) e alimentam a análise histórica e o modelo LSTM.
"""
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Loja(Base):
    """Cadastro de lojas (store.csv)."""

    __tablename__ = "lojas"

    id = Column(Integer, primary_key=True, autoincrement=False)  # "Store" do dataset
    tipo_loja = Column(String(1), nullable=False)  # StoreType: a, b, c, d
    sortimento = Column(String(1), nullable=False)  # Assortment: a=básico, b=extra, c=estendido
    distancia_concorrencia = Column(Integer, nullable=True)  # metros
    concorrencia_desde_mes = Column(SmallInteger, nullable=True)
    concorrencia_desde_ano = Column(SmallInteger, nullable=True)
    promo2 = Column(Boolean, nullable=False, default=False)
    promo2_desde_semana = Column(SmallInteger, nullable=True)
    promo2_desde_ano = Column(SmallInteger, nullable=True)
    intervalo_promo2 = Column(String(20), nullable=True)


class VendaHistorica(Base):
    """Venda diária de uma loja (train.csv). A coluna `data` é a data real do negócio."""

    __tablename__ = "vendas_historicas"
    __table_args__ = (
        UniqueConstraint("loja_id", "data", name="uq_vendas_historicas_loja_data"),
        Index("ix_vendas_historicas_data", "data"),
    )

    id = Column(Integer, primary_key=True)
    loja_id = Column(Integer, ForeignKey("lojas.id"), nullable=False)
    data = Column(Date, nullable=False)
    dia_semana = Column(SmallInteger, nullable=False)  # 1=segunda ... 7=domingo
    vendas = Column(Numeric(12, 2), nullable=False)
    clientes = Column(Integer, nullable=False)
    aberta = Column(Boolean, nullable=False)
    promo = Column(Boolean, nullable=False)
    feriado_estadual = Column(String(1), nullable=False, default="0")  # 0, a, b, c
    feriado_escolar = Column(Boolean, nullable=False)

    loja = relationship("Loja")


class PlanejamentoLoja(Base):
    """Calendário operacional futuro conhecido (test.csv): abertura, promoção e feriados.

    Não contém vendas. São informações planejadas, disponíveis antes do período
    previsto, e por isso podem ser usadas como entrada do modelo sem vazamento.
    """

    __tablename__ = "planejamento_lojas"
    __table_args__ = (
        UniqueConstraint("loja_id", "data", name="uq_planejamento_lojas_loja_data"),
        Index("ix_planejamento_lojas_data", "data"),
    )

    id = Column(Integer, primary_key=True)
    loja_id = Column(Integer, ForeignKey("lojas.id"), nullable=False)
    data = Column(Date, nullable=False)
    dia_semana = Column(SmallInteger, nullable=False)
    aberta = Column(Boolean, nullable=False)
    promo = Column(Boolean, nullable=False)
    feriado_estadual = Column(String(1), nullable=False, default="0")
    feriado_escolar = Column(Boolean, nullable=False)


class PrevisaoVenda(Base):
    """Resultado diário de previsão gerado pelo modelo LSTM."""

    __tablename__ = "previsoes_vendas"
    __table_args__ = (
        UniqueConstraint("data", "versao_modelo", name="uq_previsoes_vendas_data_versao"),
    )

    id = Column(Integer, primary_key=True)
    data = Column(Date, nullable=False, index=True)
    mes_referencia = Column(Date, nullable=False)  # primeiro dia do mês previsto
    vendas_previstas = Column(Numeric(14, 2), nullable=False)
    lojas_abertas_estimadas = Column(Integer, nullable=False)
    versao_modelo = Column(String(40), nullable=False)
    gerado_em = Column(DateTime(timezone=True), server_default=func.now())
