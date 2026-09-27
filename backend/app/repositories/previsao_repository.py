from datetime import date
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models.varejo import PrevisaoVenda


class PrevisaoRepository:
    def __init__(self, db: Session):
        self.db = db

    def salvar(self, mes_referencia: date, versao_modelo: str, linhas: list[dict]) -> None:
        """Substitui as previsões do mês para a versão do modelo informada."""
        self.db.execute(
            delete(PrevisaoVenda).where(
                PrevisaoVenda.mes_referencia == mes_referencia,
                PrevisaoVenda.versao_modelo == versao_modelo,
            )
        )
        self.db.add_all(
            PrevisaoVenda(
                data=linha["data"],
                mes_referencia=mes_referencia,
                vendas_previstas=Decimal(str(round(linha["vendas_previstas"], 2))),
                lojas_abertas_estimadas=int(linha["lojas_abertas_estimadas"]),
                versao_modelo=versao_modelo,
            )
            for linha in linhas
        )
        self.db.commit()

    def listar(self, mes_referencia: date, versao_modelo: str) -> list[PrevisaoVenda]:
        return list(
            self.db.execute(
                select(PrevisaoVenda)
                .where(PrevisaoVenda.mes_referencia == mes_referencia, PrevisaoVenda.versao_modelo == versao_modelo)
                .order_by(PrevisaoVenda.data)
            ).scalars()
        )
