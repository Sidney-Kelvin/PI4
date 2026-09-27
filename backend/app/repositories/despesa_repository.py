from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from typing import Optional
from app.models.despesa import Despesa
from app.schemas.despesa import DespesaCreate, DespesaUpdate


class DespesaRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, skip: int = 0, limit: int = 100) -> list[Despesa]:
        return (
            self.db.query(Despesa)
            .order_by(Despesa.data_despesa.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def buscar_por_id(self, despesa_id: int) -> Optional[Despesa]:
        return self.db.query(Despesa).filter(Despesa.id == despesa_id).first()

    def criar(self, dados: DespesaCreate) -> Despesa:
        despesa = Despesa(**dados.model_dump())
        self.db.add(despesa)
        self.db.commit()
        self.db.refresh(despesa)
        return despesa

    def atualizar(self, despesa: Despesa, dados: DespesaUpdate) -> Despesa:
        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(despesa, campo, valor)
        self.db.commit()
        self.db.refresh(despesa)
        return despesa

    def deletar(self, despesa: Despesa) -> None:
        self.db.delete(despesa)
        self.db.commit()

    def total_despesas(self) -> Decimal:
        resultado = self.db.query(func.sum(Despesa.valor)).scalar()
        return Decimal(resultado or 0)
