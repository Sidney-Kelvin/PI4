from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from app.models.produto import Produto
from app.schemas.produto import ProdutoCreate, ProdutoUpdate


class ProdutoRepository:
    def __init__(self, db: Session):
        self.db = db

    def listar(self, skip: int = 0, limit: int = 100) -> list[Produto]:
        return self.db.query(Produto).offset(skip).limit(limit).all()

    def buscar_por_id(self, produto_id: int) -> Optional[Produto]:
        return self.db.query(Produto).filter(Produto.id == produto_id).first()

    def criar(self, dados: ProdutoCreate) -> Produto:
        produto = Produto(**dados.model_dump())
        self.db.add(produto)
        self.db.commit()
        self.db.refresh(produto)
        return produto

    def atualizar(self, produto: Produto, dados: ProdutoUpdate) -> Produto:
        for campo, valor in dados.model_dump(exclude_unset=True).items():
            setattr(produto, campo, valor)
        self.db.commit()
        self.db.refresh(produto)
        return produto

    def decrementar_estoque(self, produto: Produto, quantidade: int) -> Produto:
        # Sem commit: a baixa de estoque é confirmada junto com o registro da venda
        produto.quantidade -= quantidade
        self.db.flush()
        return produto

    def deletar(self, produto: Produto) -> None:
        self.db.delete(produto)
        self.db.commit()

    def contar(self) -> int:
        return self.db.query(func.count(Produto.id)).scalar()
