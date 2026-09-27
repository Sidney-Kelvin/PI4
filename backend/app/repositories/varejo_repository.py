from datetime import date
from typing import Optional

import pandas as pd
from sqlalchemy import Integer, case, cast, extract, func, select
from sqlalchemy.orm import Session

from app.models.varejo import Loja, PlanejamentoLoja, VendaHistorica


def _contar_se(condicao):
    return func.sum(case((condicao, 1), else_=0))


class VarejoRepository:
    """Consultas analíticas sobre os dados históricos de varejo (Rossmann)."""

    def __init__(self, db: Session):
        self.db = db

    # ── Séries agregadas usadas pelo modelo ─────────────────────────────
    def agregado_diario(self, desde: Optional[date] = None) -> pd.DataFrame:
        v = VendaHistorica
        consulta = (
            select(
                v.data.label("data"),
                func.count().label("lojas_reportando"),
                _contar_se(v.aberta).label("lojas_abertas"),
                _contar_se(v.promo).label("lojas_promo"),
                _contar_se(v.feriado_estadual != "0").label("lojas_feriado_estadual"),
                _contar_se(v.feriado_escolar).label("lojas_feriado_escolar"),
                func.sum(v.vendas).label("vendas_total"),
            )
            .group_by(v.data)
            .order_by(v.data)
        )
        if desde is not None:
            consulta = consulta.where(v.data >= desde)
        linhas = self.db.execute(consulta).all()
        df = pd.DataFrame(linhas, columns=["data", "lojas_reportando", "lojas_abertas", "lojas_promo",
                                           "lojas_feriado_estadual", "lojas_feriado_escolar", "vendas_total"])
        if not df.empty:
            df["vendas_total"] = df["vendas_total"].astype(float)
        return df

    def agregado_planejamento(self, desde: date, ate: date) -> pd.DataFrame:
        p = PlanejamentoLoja
        consulta = (
            select(
                p.data.label("data"),
                func.count().label("lojas_reportando"),
                _contar_se(p.aberta).label("lojas_abertas"),
                _contar_se(p.promo).label("lojas_promo"),
                _contar_se(p.feriado_estadual != "0").label("lojas_feriado_estadual"),
                _contar_se(p.feriado_escolar).label("lojas_feriado_escolar"),
            )
            .where(p.data >= desde, p.data <= ate)
            .group_by(p.data)
            .order_by(p.data)
        )
        linhas = self.db.execute(consulta).all()
        return pd.DataFrame(linhas, columns=["data", "lojas_reportando", "lojas_abertas", "lojas_promo",
                                             "lojas_feriado_estadual", "lojas_feriado_escolar"])

    # ── Resumo ─────────────────────────────────────────────────────────
    def resumo(self) -> dict:
        v = VendaHistorica
        linha = self.db.execute(
            select(
                func.count(v.id),
                func.coalesce(func.sum(v.vendas), 0),
                func.coalesce(func.sum(v.clientes), 0),
                func.min(v.data),
                func.max(v.data),
                func.count(func.distinct(v.data)),
                _contar_se(v.aberta),
            )
        ).one()
        total_lojas = self.db.execute(select(func.count(Loja.id))).scalar_one()
        dias_planejados = self.db.execute(select(func.count(func.distinct(PlanejamentoLoja.data)))).scalar_one()
        return {
            "registros": linha[0],
            "faturamento_total": linha[1],
            "clientes_total": linha[2],
            "data_inicio": linha[3],
            "data_fim": linha[4],
            "dias": linha[5],
            "dias_loja_abertos": linha[6] or 0,
            "total_lojas": total_lojas,
            "dias_planejados": dias_planejados,
        }

    def total_periodo(self, inicio: date, fim: date) -> float:
        total = self.db.execute(
            select(func.coalesce(func.sum(VendaHistorica.vendas), 0)).where(
                VendaHistorica.data >= inicio, VendaHistorica.data <= fim
            )
        ).scalar_one()
        return float(total)

    # ── Séries e quebras analíticas ──────────────────────────────────────
    def serie(self, agrupamento: str, loja_id: Optional[int] = None,
              inicio: Optional[date] = None, fim: Optional[date] = None) -> list[dict]:
        v = VendaHistorica
        ano = cast(extract("year", v.data), Integer)
        mes = cast(extract("month", v.data), Integer)
        if agrupamento == "dia":
            chaves = [v.data]
        elif agrupamento == "mes":
            chaves = [ano, mes]
        else:
            chaves = [ano]

        consulta = select(
            *chaves,
            func.sum(v.vendas),
            func.sum(v.clientes),
            _contar_se(v.aberta),
        ).group_by(*chaves).order_by(*chaves)
        if loja_id is not None:
            consulta = consulta.where(v.loja_id == loja_id)
        if inicio is not None:
            consulta = consulta.where(v.data >= inicio)
        if fim is not None:
            consulta = consulta.where(v.data <= fim)

        resultado = []
        for linha in self.db.execute(consulta).all():
            if agrupamento == "dia":
                periodo = linha[0].isoformat()
            elif agrupamento == "mes":
                periodo = f"{int(linha[0]):04d}-{int(linha[1]):02d}"
            else:
                periodo = f"{int(linha[0]):04d}"
            vendas, clientes, abertos = linha[-3], linha[-2], linha[-1]
            resultado.append({
                "periodo": periodo,
                "vendas": float(vendas or 0),
                "clientes": int(clientes or 0),
                "dias_loja_abertos": int(abertos or 0),
            })
        return resultado

    def _quebra(self, chave, filtro_aberta: bool = True, juncao_loja: bool = False) -> list[tuple]:
        v = VendaHistorica
        consulta = select(
            chave,
            func.sum(v.vendas),
            func.count(),
            func.avg(v.vendas),
        )
        if juncao_loja:
            consulta = consulta.join(Loja, Loja.id == v.loja_id)
        if filtro_aberta:
            consulta = consulta.where(v.aberta.is_(True))
        consulta = consulta.group_by(chave).order_by(chave)
        return self.db.execute(consulta).all()

    def por_tipo_loja(self) -> list[tuple]:
        return self._quebra(Loja.tipo_loja, juncao_loja=True)

    def por_sortimento(self) -> list[tuple]:
        return self._quebra(Loja.sortimento, juncao_loja=True)

    def por_promocao(self) -> list[tuple]:
        return self._quebra(VendaHistorica.promo)

    def por_feriado_estadual(self) -> list[tuple]:
        return self._quebra(VendaHistorica.feriado_estadual)

    def por_feriado_escolar(self) -> list[tuple]:
        return self._quebra(VendaHistorica.feriado_escolar)

    def por_dia_semana(self) -> list[tuple]:
        return self._quebra(VendaHistorica.dia_semana)

    def ranking_lojas(self, limite: int, ordem_desc: bool = True) -> list[tuple]:
        v = VendaHistorica
        total = func.sum(v.vendas)
        consulta = (
            select(v.loja_id, total, func.count(), func.avg(v.vendas), Loja.tipo_loja)
            .join(Loja, Loja.id == v.loja_id)
            .where(v.aberta.is_(True))
            .group_by(v.loja_id, Loja.tipo_loja)
            .order_by(total.desc() if ordem_desc else total.asc())
            .limit(limite)
        )
        return self.db.execute(consulta).all()

    # ── Lojas ─────────────────────────────────────────────────────────
    def listar_lojas(self, skip: int = 0, limit: int = 100, tipo_loja: Optional[str] = None) -> list[Loja]:
        consulta = self.db.query(Loja)
        if tipo_loja:
            consulta = consulta.filter(Loja.tipo_loja == tipo_loja)
        return consulta.order_by(Loja.id).offset(skip).limit(limit).all()

    def buscar_loja(self, loja_id: int) -> Optional[Loja]:
        return self.db.get(Loja, loja_id)

    def possui_dados(self) -> bool:
        return self.db.execute(select(VendaHistorica.id).limit(1)).first() is not None

    def possui_planejamento(self) -> bool:
        return self.db.execute(select(PlanejamentoLoja.id).limit(1)).first() is not None
