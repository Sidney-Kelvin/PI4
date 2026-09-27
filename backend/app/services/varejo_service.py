from datetime import date
from typing import Optional

import pandas as pd
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.varejo import Loja
from app.repositories.varejo_repository import VarejoRepository
from app.schemas.varejo import ItemQuebra, PontoSerie, RankingLoja, ResumoVarejo, TotalPeriodo

DIAS_SEMANA = {1: "Segunda", 2: "Terça", 3: "Quarta", 4: "Quinta", 5: "Sexta", 6: "Sábado", 7: "Domingo"}
FERIADOS = {"0": "Sem feriado", "a": "Feriado público", "b": "Páscoa", "c": "Natal"}
SORTIMENTOS = {"a": "Básico", "b": "Extra", "c": "Estendido"}
AGRUPAMENTOS = {"dia", "mes", "ano"}
MAX_DIAS_SERIE_DIARIA = 1100

MSG_SEM_DADOS = (
    "Nenhum dado histórico de varejo importado. Coloque os CSVs do Rossmann em data/raw/ "
    "e execute: docker compose exec backend python -m app.ml.ingest"
)


def _itens(linhas, rotulo) -> list[ItemQuebra]:
    return [
        ItemQuebra(
            categoria=str(chave).lower(),
            descricao=rotulo(chave),
            vendas_totais=float(total or 0),
            dias_loja_abertos=int(qtd or 0),
            media_por_dia_loja=float(media or 0),
        )
        for chave, total, qtd, media in linhas
    ]


class VarejoService:
    def __init__(self, db: Session):
        self.repo = VarejoRepository(db)

    def resumo(self) -> ResumoVarejo:
        dados = self.repo.resumo()
        if not dados["registros"]:
            return ResumoVarejo(
                dados_importados=False, faturamento_total=0, clientes_total=0, registros=0,
                total_lojas=dados["total_lojas"], dias=0, media_diaria=0, dias_planejados=0,
            )

        fim: date = dados["data_fim"]
        inicio_ultimo = fim.replace(day=1)
        inicio_anterior = (pd.Timestamp(inicio_ultimo) - pd.DateOffset(months=1)).date()
        fim_anterior = (pd.Timestamp(inicio_ultimo) - pd.Timedelta(days=1)).date()
        total_ultimo = self.repo.total_periodo(inicio_ultimo, fim)
        total_anterior = self.repo.total_periodo(inicio_anterior, fim_anterior)

        faturamento = float(dados["faturamento_total"])
        return ResumoVarejo(
            dados_importados=True,
            faturamento_total=faturamento,
            clientes_total=int(dados["clientes_total"]),
            registros=dados["registros"],
            total_lojas=dados["total_lojas"],
            data_inicio=dados["data_inicio"],
            data_fim=fim,
            dias=dados["dias"],
            media_diaria=faturamento / dados["dias"] if dados["dias"] else 0,
            ultimo_mes=TotalPeriodo(periodo=inicio_ultimo.strftime("%Y-%m"), vendas=total_ultimo),
            mes_anterior=TotalPeriodo(periodo=inicio_anterior.strftime("%Y-%m"), vendas=total_anterior)
            if total_anterior else None,
            variacao_mensal_percentual=(total_ultimo - total_anterior) / total_anterior * 100
            if total_anterior else None,
            dias_planejados=dados["dias_planejados"],
        )

    def serie(self, agrupamento: str, loja_id: Optional[int], inicio: Optional[date],
              fim: Optional[date]) -> list[PontoSerie]:
        if agrupamento not in AGRUPAMENTOS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Agrupamento inválido. Use: dia, mes ou ano.")
        if inicio and fim and inicio > fim:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="A data inicial deve ser anterior à data final.")
        if loja_id is not None:
            self.obter_loja(loja_id)
        pontos = self.repo.serie(agrupamento, loja_id, inicio, fim)
        if agrupamento == "dia":
            pontos = pontos[-MAX_DIAS_SERIE_DIARIA:]
        return [PontoSerie(**p) for p in pontos]

    def por_tipo_loja(self) -> list[ItemQuebra]:
        return _itens(self.repo.por_tipo_loja(), lambda c: f"Tipo {c}")

    def por_sortimento(self) -> list[ItemQuebra]:
        return _itens(self.repo.por_sortimento(), lambda c: SORTIMENTOS.get(c, c))

    def por_promocao(self) -> list[ItemQuebra]:
        return _itens(self.repo.por_promocao(), lambda c: "Com promoção" if c else "Sem promoção")

    def por_feriado(self) -> list[ItemQuebra]:
        estaduais = _itens(self.repo.por_feriado_estadual(), lambda c: FERIADOS.get(c, c))
        escolares = _itens(self.repo.por_feriado_escolar(),
                           lambda c: "Escolar: sim" if c == "true" or c is True else "Escolar: não")
        for item in escolares:
            item.categoria = f"escolar_{item.categoria}"
        return estaduais + escolares

    def por_dia_semana(self) -> list[ItemQuebra]:
        return _itens(self.repo.por_dia_semana(), lambda c: DIAS_SEMANA.get(int(c), str(c)))

    def ranking_lojas(self, limite: int, ordem: str) -> list[RankingLoja]:
        if ordem not in {"maiores", "menores"}:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Ordem inválida. Use: maiores ou menores.")
        return [
            RankingLoja(loja_id=loja, tipo_loja=tipo, vendas_totais=float(total), dias_abertos=int(qtd),
                        media_diaria=float(media))
            for loja, total, qtd, media, tipo in self.repo.ranking_lojas(limite, ordem == "maiores")
        ]

    def listar_lojas(self, skip: int, limit: int, tipo_loja: Optional[str]) -> list[Loja]:
        return self.repo.listar_lojas(skip, limit, tipo_loja)

    def obter_loja(self, loja_id: int) -> Loja:
        loja = self.repo.buscar_loja(loja_id)
        if not loja:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loja não encontrada.")
        return loja
