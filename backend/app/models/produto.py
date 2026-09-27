from sqlalchemy import Column, Integer, String, Numeric, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(200), nullable=False)
    descricao = Column(String(500), nullable=True)
    preco = Column(Numeric(12, 2), nullable=False)
    quantidade = Column(Integer, nullable=False, default=0)
    categoria = Column(String(100), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())
