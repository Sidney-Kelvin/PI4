from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.repositories.despesa_repository import DespesaRepository
from app.schemas.despesa import DespesaCreate, DespesaUpdate
from app.models.despesa import Despesa


class DespesaService:
    def __init__(self, db: Session):
        self.repo = DespesaRepository(db)

    def listar_despesas(self, skip: int = 0, limit: int = 100):
        return self.repo.listar(skip, limit)

    def obter_despesa(self, despesa_id: int) -> Despesa:
        despesa = self.repo.buscar_por_id(despesa_id)
        if not despesa:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Despesa não encontrada")
        return despesa

    def criar_despesa(self, dados: DespesaCreate) -> Despesa:
        return self.repo.criar(dados)

    def atualizar_despesa(self, despesa_id: int, dados: DespesaUpdate) -> Despesa:
        despesa = self.obter_despesa(despesa_id)
        return self.repo.atualizar(despesa, dados)

    def deletar_despesa(self, despesa_id: int) -> None:
        despesa = self.obter_despesa(despesa_id)
        self.repo.deletar(despesa)

    def total_despesas(self) -> Decimal:
        return self.repo.total_despesas()
