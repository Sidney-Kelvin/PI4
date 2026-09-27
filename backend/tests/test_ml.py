"""Testes do pipeline de ML com dados SINTÉTICOS (apenas verificam o funcionamento do código)."""
import json
from datetime import date

import numpy as np
import pandas as pd
import pytest

from app.ml.artifacts import carregar_artefatos, modelo_existe
from app.ml.features import (
    FEATURES_EXOGENAS,
    EscalonadorAlvo,
    dividir_temporalmente,
    features_exogenas,
    preparar_serie_diaria,
)
from app.ml.metrics import calcular_metricas, mape
from app.ml.predictor import prever_proximo_mes
from app.ml.train import ConfigTreino, treinar
from app.repositories.varejo_repository import VarejoRepository

CONFIG_RAPIDA = ConfigTreino(janela=14, hidden_size=8, num_layers=1, epocas=3, paciencia=2)


@pytest.fixture(scope="module")
def agregado(dados_varejo):
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as sessao:
        return VarejoRepository(sessao).agregado_diario()


@pytest.fixture(scope="module")
def modelo_treinado(agregado, tmp_path_factory):
    pasta = tmp_path_factory.mktemp("modelo") / "sales_lstm"
    resultado = treinar(agregado, CONFIG_RAPIDA, pasta, verbose=False)
    return pasta, resultado


def test_serie_diaria_continua_e_alvo_por_loja_aberta(agregado):
    serie = preparar_serie_diaria(agregado)
    datas = pd.to_datetime(serie["data"])
    assert (datas.diff().dropna() == pd.Timedelta(days=1)).all()
    aberto = serie[serie["lojas_abertas"] > 0].iloc[0]
    assert aberto["alvo"] == pytest.approx(aberto["vendas_total"] / aberto["lojas_abertas"])
    # Natal: todas as lojas fechadas -> alvo 0
    natal = serie[datas == pd.Timestamp("2013-12-25")].iloc[0]
    assert natal["lojas_abertas"] == 0 and natal["alvo"] == 0


def test_features_nao_usam_clientes_nem_vendas(agregado):
    serie = preparar_serie_diaria(agregado)
    features = features_exogenas(serie)
    assert list(features.columns) == FEATURES_EXOGENAS
    assert not any("client" in f or "venda" in f for f in FEATURES_EXOGENAS)
    assert features["frac_abertas"].between(0, 1).all()


def test_divisao_temporal_sem_sobreposicao(agregado):
    divisao = dividir_temporalmente(agregado["data"], meses_validacao=2, meses_teste=2)
    assert divisao.inicio < divisao.inicio_validacao < divisao.inicio_teste <= divisao.fim
    assert divisao.inicio_teste == date(2014, 2, 1)
    assert divisao.inicio_validacao == date(2013, 12, 1)


def test_escalonador_inverte():
    esc = EscalonadorAlvo.ajustar(np.array([10.0, 20.0, 30.0]))
    valores = np.array([5.0, 25.0])
    assert esc.inverter(esc.transformar(valores)) == pytest.approx(valores)


def test_mape_exclui_dias_com_venda_zero():
    valor, excluidos = mape(np.array([100.0, 0.0, 200.0]), np.array([110.0, 50.0, 180.0]))
    assert excluidos == 1
    assert valor == pytest.approx(10.0)


def test_metricas_basicas():
    m = calcular_metricas(np.array([10.0, 20.0]), np.array([12.0, 16.0]))
    assert m["mae"] == pytest.approx(3.0)
    assert m["rmse"] == pytest.approx(np.sqrt((4 + 16) / 2))


def test_treino_salva_artefatos(modelo_treinado):
    pasta, resultado = modelo_treinado
    assert modelo_existe(pasta)
    for nome in ("metrics.json", "evaluation.json", "history.json"):
        assert (pasta / nome).is_file()

    metadados = json.loads((pasta / "metadata.json").read_text(encoding="utf-8"))
    # Escalonador ajustado apenas com dias de treino (antes do início da validação)
    serie = resultado["serie"]
    treino = serie[(pd.to_datetime(serie["data"]) < pd.Timestamp(metadados["divisao"]["inicio_validacao"]))
                   & (serie["lojas_abertas"] > 0)]
    assert metadados["escalonador"]["media"] == pytest.approx(treino["alvo"].mean())

    avaliacao = json.loads((pasta / "evaluation.json").read_text(encoding="utf-8"))
    assert avaliacao[0]["data"] == metadados["divisao"]["inicio_teste"]
    assert resultado["metricas"]["lstm"]["dias_avaliados"] == len(avaliacao)


def test_previsao_proximo_mes(modelo_treinado, agregado):
    pasta, _ = modelo_treinado
    artefatos = carregar_artefatos(pasta)
    resultado = prever_proximo_mes(artefatos.modelo, artefatos.metadados, agregado, None)
    assert resultado.mes_referencia == date(2014, 4, 1)
    assert len(resultado.diario) == 30
    assert (resultado.diario["vendas_previstas"] >= 0).all()
    assert set(resultado.diario["fonte_calendario"]) == {"estimado"}
    # Domingos: nenhuma loja abre no histórico sintético -> previsão zero
    domingos = resultado.diario[pd.to_datetime(resultado.diario["data"]).dt.dayofweek == 6]
    assert (domingos["vendas_previstas"] == 0).all()
