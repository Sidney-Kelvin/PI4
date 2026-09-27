"""valores monetarios de Float para Numeric(12,2)

Converte preços, totais e despesas de ponto flutuante (double precision) para
NUMERIC(12,2). A conversão usa ROUND(valor::numeric, 2): valores monetários já
são digitados com no máximo 2 casas, então nenhum dado é perdido, apenas o ruído
de representação binária do float é removido.

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-27
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None

COLUNAS_MONETARIAS = [
    ("produtos", "preco"),
    ("vendas", "preco_unitario"),
    ("vendas", "total"),
    ("despesas", "valor"),
]


def upgrade() -> None:
    for tabela, coluna in COLUNAS_MONETARIAS:
        op.alter_column(
            tabela,
            coluna,
            existing_type=sa.Float(),
            type_=sa.Numeric(12, 2),
            existing_nullable=False,
            postgresql_using=f"ROUND({coluna}::numeric, 2)",
        )


def downgrade() -> None:
    for tabela, coluna in COLUNAS_MONETARIAS:
        op.alter_column(
            tabela,
            coluna,
            existing_type=sa.Numeric(12, 2),
            type_=sa.Float(),
            existing_nullable=False,
            postgresql_using=f"{coluna}::double precision",
        )
