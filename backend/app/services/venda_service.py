from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.venda_repository import VendaRepository
from app.repositories.produto_repository import ProdutoRepository
from app.schemas.venda import VendaCreate
from app.models.venda import Venda


class VendaService:
    def __init__(self, db: Session):
        self.venda_repo = VendaRepository(db)
        self.produto_repo = ProdutoRepository(db)

    def listar_vendas(self, skip: int = 0, limit: int = 100):
        return self.venda_repo.listar(skip, limit)

    def obter_venda(self, venda_id: int) -> Venda:
        venda = self.venda_repo.buscar_por_id(venda_id)
        if not venda:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Venda não encontrada")
        return venda

    def registrar_venda(self, dados: VendaCreate) -> Venda:
        produto = self.produto_repo.buscar_por_id(dados.produto_id)
        if not produto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")

        if produto.quantidade < dados.quantidade:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Estoque insuficiente. Disponível: {produto.quantidade}, Solicitado: {dados.quantidade}",
            )

        self.produto_repo.decrementar_estoque(produto, dados.quantidade)

        return self.venda_repo.criar(
            produto_id=dados.produto_id,
            quantidade=dados.quantidade,
            preco_unitario=produto.preco,
            cliente=dados.cliente,
            observacao=dados.observacao,
        )

    def faturamento_total(self) -> Decimal:
        return self.venda_repo.faturamento_total()

    def total_vendas(self) -> int:
        return self.venda_repo.total_vendas()
