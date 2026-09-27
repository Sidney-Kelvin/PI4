"""Importa o dataset Rossmann para o PostgreSQL.

Uso (dentro do container do backend):
    python -m app.ml.ingest --verificar      # apenas confere se os CSVs estão presentes
    python -m app.ml.ingest                  # importa (falha se já houver dados)
    python -m app.ml.ingest --substituir     # apaga os dados de varejo e reimporta

A estrutura das tabelas é criada pelo Alembic (alembic upgrade head); este
script apenas carrega dados.
"""
import argparse
import io
import sys
import time
from pathlib import Path

import pandas as pd
from sqlalchemy import Engine, text

from app.core.config import settings
from app.core.database import engine as engine_padrao
from app.ml.data_preparation import (
    DadosAusentesError,
    integrar_vendas_lojas,
    preparar_dados,
    verificar_arquivos,
)

TABELAS_VAREJO = ("previsoes_vendas", "planejamento_lojas", "vendas_historicas", "lojas")


def _copiar_postgres(engine: Engine, tabela: str, df: pd.DataFrame) -> None:
    """Carga em massa via COPY (muito mais rápido que INSERT para ~1 milhão de linhas)."""
    buffer = io.StringIO()
    df.to_csv(buffer, index=False, header=False, na_rep="")
    buffer.seek(0)
    colunas = ", ".join(df.columns)
    conexao = engine.raw_connection()
    try:
        with conexao.cursor() as cursor:
            cursor.copy_expert(f"COPY {tabela} ({colunas}) FROM STDIN WITH (FORMAT csv, NULL '')", buffer)
        conexao.commit()
    finally:
        conexao.close()


def _gravar(engine: Engine, tabela: str, df: pd.DataFrame) -> None:
    if df.empty:
        return
    if engine.dialect.name == "postgresql":
        _copiar_postgres(engine, tabela, df)
    else:  # SQLite nos testes automatizados
        df.to_sql(tabela, engine, if_exists="append", index=False, chunksize=5000)


def dados_ja_importados(engine: Engine) -> bool:
    with engine.connect() as conexao:
        return conexao.execute(text("SELECT 1 FROM lojas LIMIT 1")).first() is not None


def limpar_tabelas_varejo(engine: Engine) -> None:
    with engine.begin() as conexao:
        for tabela in TABELAS_VAREJO:
            conexao.execute(text(f"DELETE FROM {tabela}"))


def importar(engine: Engine, data_dir: str | Path, substituir: bool = False, exportar_processado: bool = False) -> dict:
    inicio = time.perf_counter()
    dados = preparar_dados(data_dir)

    if dados_ja_importados(engine):
        if not substituir:
            raise RuntimeError(
                "Os dados de varejo já foram importados. Use --substituir para apagar e importar novamente."
            )
        limpar_tabelas_varejo(engine)

    _gravar(engine, "lojas", dados.lojas)
    _gravar(engine, "vendas_historicas", dados.vendas)
    if dados.planejamento is not None:
        _gravar(engine, "planejamento_lojas", dados.planejamento)

    if exportar_processado:
        pasta = Path(data_dir) / "processed"
        pasta.mkdir(parents=True, exist_ok=True)
        integrar_vendas_lojas(dados.vendas, dados.lojas).to_csv(
            pasta / "vendas_integradas.csv.gz", index=False, compression="gzip"
        )

    return {
        "lojas": len(dados.lojas),
        "vendas_historicas": len(dados.vendas),
        "planejamento_lojas": 0 if dados.planejamento is None else len(dados.planejamento),
        "periodo": f"{dados.vendas['data'].min()} a {dados.vendas['data'].max()}",
        "segundos": round(time.perf_counter() - inicio, 1),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Importa o dataset Rossmann Store Sales para o PostgreSQL.")
    parser.add_argument("--data-dir", default=settings.data_dir, help="Pasta com os CSVs (padrão: DATA_DIR)")
    parser.add_argument("--verificar", action="store_true", help="Apenas verifica se os arquivos existem")
    parser.add_argument("--substituir", action="store_true",
                        help="Apaga os dados de varejo existentes antes de importar")
    parser.add_argument("--exportar-processado", action="store_true",
                        help="Salva também data/processed/vendas_integradas.csv.gz (train + store)")
    args = parser.parse_args(argv)

    verificacao = verificar_arquivos(args.data_dir)
    print(f"Pasta de dados: {verificacao.pasta}")
    print(f"Encontrados: {', '.join(verificacao.encontrados) or 'nenhum'}")
    if verificacao.ausentes_opcionais:
        print(f"Opcionais ausentes: {', '.join(verificacao.ausentes_opcionais)} "
              "(sem test.csv o calendário do mês previsto será estimado)")
    if not verificacao.ok:
        print(f"ERRO: arquivos obrigatórios ausentes: {', '.join(verificacao.ausentes_obrigatorios)}")
        print("Baixe-os em https://www.kaggle.com/c/rossmann-store-sales/data e coloque em data/raw/.")
        return 1
    if args.verificar:
        print("OK: arquivos obrigatórios presentes.")
        return 0

    try:
        resumo = importar(engine_padrao, args.data_dir, args.substituir, args.exportar_processado)
    except (DadosAusentesError, RuntimeError, ValueError) as erro:
        print(f"ERRO: {erro}")
        return 1

    print("Importação concluída:")
    for chave, valor in resumo.items():
        print(f"  {chave}: {valor}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
