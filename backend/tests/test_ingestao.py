from datetime import date

import pytest

from app.ml.data_preparation import (
    DadosAusentesError,
    integrar_vendas_lojas,
    preparar_dados,
    verificar_arquivos,
)
from app.ml.ingest import importar
from tests.conftest import engine_test


def test_verificar_arquivos_ausentes(tmp_path):
    resultado = verificar_arquivos(tmp_path)
    assert not resultado.ok
    assert set(resultado.ausentes_obrigatorios) == {"train.csv", "store.csv"}


def test_preparar_dados_sem_arquivos_gera_erro_claro(tmp_path):
    with pytest.raises(DadosAusentesError, match="kaggle.com"):
        preparar_dados(tmp_path)


def test_preparar_dados_limpa_e_converte(pasta_csv_sintetico):
    dados = preparar_dados(pasta_csv_sintetico)
    vendas = dados.vendas

    assert len(dados.lojas) == 4
    assert isinstance(vendas["data"].iloc[0], date)
    assert vendas["data"].is_monotonic_increasing
    assert set(vendas["feriado_estadual"].unique()) <= {"0", "a", "b", "c"}
    assert vendas["vendas"].min() >= 0
    # Loja sem concorrente conhecido mantém o valor ausente (nulo), não um número inventado
    assert dados.lojas.loc[dados.lojas["id"] == 3, "distancia_concorrencia"].isna().all()
    # Open ausente no test.csv é tratado como loja aberta
    plano = dados.planejamento
    assert bool(plano.loc[(plano["loja_id"] == 1) & (plano["data"] == date(2014, 4, 2)), "aberta"].iloc[0])
    assert dados.planejamento["data"].min() > vendas["data"].max()


def test_integracao_vendas_lojas_cria_variaveis(pasta_csv_sintetico):
    dados = preparar_dados(pasta_csv_sintetico)
    integrado = integrar_vendas_lojas(dados.vendas, dados.lojas)
    assert {"tipo_loja", "sortimento", "ano", "mes", "dia_do_ano"} <= set(integrado.columns)
    assert len(integrado) == len(dados.vendas)


def test_integracao_rejeita_loja_inexistente(pasta_csv_sintetico):
    dados = preparar_dados(pasta_csv_sintetico)
    with pytest.raises(ValueError, match="lojas inexistentes"):
        integrar_vendas_lojas(dados.vendas, dados.lojas[dados.lojas["id"] != 1])


def test_importacao_grava_no_banco(dados_varejo):
    assert dados_varejo["lojas"] == 4
    assert dados_varejo["vendas_historicas"] == 4 * 455
    assert dados_varejo["planejamento_lojas"] > 0


def test_reimportacao_exige_substituir(dados_varejo, pasta_csv_sintetico):
    with pytest.raises(RuntimeError, match="--substituir"):
        importar(engine_test, pasta_csv_sintetico)
