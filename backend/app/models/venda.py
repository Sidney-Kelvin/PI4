from sqlalchemy import Column, Integer, Numeric, DateTime, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Venda(Base):
    __tablename__ = "vendas"

    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"), nullable=False)
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Numeric(12, 2), nullable=False)
    total = Column(Numeric(12, 2), nullable=False)
    cliente = Column(String(200), nullable=True)
    observacao = Column(String(500), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

    produto = relationship("Produto")
