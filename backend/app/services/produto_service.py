from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.produto_repository import ProdutoRepository
from app.repositories.venda_repository import VendaRepository
from app.schemas.produto import ProdutoCreate, ProdutoUpdate
from app.models.produto import Produto


class ProdutoService:
    def __init__(self, db: Session):
        self.repo = ProdutoRepository(db)
        self.venda_repo = VendaRepository(db)

    def listar_produtos(self, skip: int = 0, limit: int = 100):
        return self.repo.listar(skip, limit)

    def obter_produto(self, produto_id: int) -> Produto:
        produto = self.repo.buscar_por_id(produto_id)
        if not produto:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Produto não encontrado")
        return produto

    def criar_produto(self, dados: ProdutoCreate) -> Produto:
        return self.repo.criar(dados)

    def atualizar_produto(self, produto_id: int, dados: ProdutoUpdate) -> Produto:
        produto = self.obter_produto(produto_id)
        return self.repo.atualizar(produto, dados)

    def deletar_produto(self, produto_id: int) -> None:
        produto = self.obter_produto(produto_id)
        if self.venda_repo.existe_para_produto(produto_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Produto possui vendas registradas e não pode ser excluído.",
            )
        self.repo.deletar(produto)

    def contar_produtos(self) -> int:
        return self.repo.contar()
