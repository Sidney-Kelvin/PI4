from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from decimal import Decimal
from typing import Optional
from app.models.venda import Venda


class VendaRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, skip: int = 0, limit: int = 100) -> list[Venda]:
        return (
            self.db.query(Venda)
            .options(joinedload(Venda.produto))
            .order_by(Venda.criado_em.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def buscar_por_id(self, venda_id: int) -> Optional[Venda]:
        return (
            self.db.query(Venda)
            .options(joinedload(Venda.produto))
            .filter(Venda.id == venda_id)
            .first()
        )

    def criar(
        self,
        produto_id: int,
        quantidade: int,
        preco_unitario: Decimal,
        cliente: Optional[str],
        observacao: Optional[str],
    ) -> Venda:
        total = quantidade * Decimal(preco_unitario)
        venda = Venda(
            produto_id=produto_id,
            quantidade=quantidade,
            preco_unitario=preco_unitario,
            total=total,
            cliente=cliente,
            observacao=observacao,
        )
        self.db.add(venda)
        self.db.commit()
        self.db.refresh(venda)
        return venda

    def faturamento_total(self) -> Decimal:
        resultado = self.db.query(func.sum(Venda.total)).scalar()
        return Decimal(resultado or 0)

    def existe_para_produto(self, produto_id: int) -> bool:
        return self.db.query(Venda.id).filter(Venda.produto_id == produto_id).first() is not None

    def total_vendas(self) -> int:
        return self.db.query(func.count(Venda.id)).scalar()
