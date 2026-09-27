"""camada de varejo historico (Rossmann) e previsoes

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-27
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "lojas",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=False),
        sa.Column("tipo_loja", sa.String(1), nullable=False),
        sa.Column("sortimento", sa.String(1), nullable=False),
        sa.Column("distancia_concorrencia", sa.Integer(), nullable=True),
        sa.Column("concorrencia_desde_mes", sa.SmallInteger(), nullable=True),
        sa.Column("concorrencia_desde_ano", sa.SmallInteger(), nullable=True),
        sa.Column("promo2", sa.Boolean(), nullable=False),
        sa.Column("promo2_desde_semana", sa.SmallInteger(), nullable=True),
        sa.Column("promo2_desde_ano", sa.SmallInteger(), nullable=True),
        sa.Column("intervalo_promo2", sa.String(20), nullable=True),
    )

    op.create_table(
        "vendas_historicas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("loja_id", sa.Integer(), sa.ForeignKey("lojas.id"), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("dia_semana", sa.SmallInteger(), nullable=False),
        sa.Column("vendas", sa.Numeric(12, 2), nullable=False),
        sa.Column("clientes", sa.Integer(), nullable=False),
        sa.Column("aberta", sa.Boolean(), nullable=False),
        sa.Column("promo", sa.Boolean(), nullable=False),
        sa.Column("feriado_estadual", sa.String(1), nullable=False, server_default="0"),
        sa.Column("feriado_escolar", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("loja_id", "data", name="uq_vendas_historicas_loja_data"),
    )
    op.create_index("ix_vendas_historicas_data", "vendas_historicas", ["data"])

    op.create_table(
        "planejamento_lojas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("loja_id", sa.Integer(), sa.ForeignKey("lojas.id"), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("dia_semana", sa.SmallInteger(), nullable=False),
        sa.Column("aberta", sa.Boolean(), nullable=False),
        sa.Column("promo", sa.Boolean(), nullable=False),
        sa.Column("feriado_estadual", sa.String(1), nullable=False, server_default="0"),
        sa.Column("feriado_escolar", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("loja_id", "data", name="uq_planejamento_lojas_loja_data"),
    )
    op.create_index("ix_planejamento_lojas_data", "planejamento_lojas", ["data"])

    op.create_table(
        "previsoes_vendas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("mes_referencia", sa.Date(), nullable=False),
        sa.Column("vendas_previstas", sa.Numeric(14, 2), nullable=False),
        sa.Column("lojas_abertas_estimadas", sa.Integer(), nullable=False),
        sa.Column("versao_modelo", sa.String(40), nullable=False),
        sa.Column("gerado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("data", "versao_modelo", name="uq_previsoes_vendas_data_versao"),
    )
    op.create_index("ix_previsoes_vendas_data", "previsoes_vendas", ["data"])


def downgrade() -> None:
    op.drop_index("ix_previsoes_vendas_data", table_name="previsoes_vendas")
    op.drop_table("previsoes_vendas")
    op.drop_index("ix_planejamento_lojas_data", table_name="planejamento_lojas")
    op.drop_table("planejamento_lojas")
    op.drop_index("ix_vendas_historicas_data", table_name="vendas_historicas")
    op.drop_table("vendas_historicas")
    op.drop_table("lojas")
