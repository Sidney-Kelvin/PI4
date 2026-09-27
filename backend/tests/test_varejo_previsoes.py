import pytest

from app.core.config import settings
from app.ml.train import ConfigTreino, treinar
from app.repositories.varejo_repository import VarejoRepository


@pytest.fixture()
def pasta_modelo_vazia(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "model_dir", str(tmp_path / "sem_modelo"))
    return tmp_path


@pytest.fixture(scope="module")
def pasta_modelo_treinado(dados_varejo, tmp_path_factory):
    from tests.conftest import TestingSessionLocal

    with TestingSessionLocal() as sessao:
        agregado = VarejoRepository(sessao).agregado_diario()
    pasta = tmp_path_factory.mktemp("api_modelo") / "sales_lstm"
    treinar(agregado, ConfigTreino(janela=14, hidden_size=8, num_layers=1, epocas=2, paciencia=2), pasta,
            verbose=False)
    return pasta


def test_resumo_varejo(client, dados_varejo):
    r = client.get("/varejo/resumo")
    assert r.status_code == 200
    dados = r.json()
    assert dados["dados_importados"] is True
    assert dados["total_lojas"] == 4
    assert dados["data_fim"] == "2014-03-31"
    assert dados["ultimo_mes"]["periodo"] == "2014-03"
    assert dados["faturamento_total"] > 0


@pytest.mark.parametrize("agrupamento,primeiro", [("ano", "2013"), ("mes", "2013-01"), ("dia", "2013-01-01")])
def test_serie_por_agrupamento(client, dados_varejo, agrupamento, primeiro):
    r = client.get("/varejo/vendas/serie", params={"agrupamento": agrupamento})
    assert r.status_code == 200
    assert r.json()[0]["periodo"] == primeiro


def test_serie_por_loja_e_periodo(client, dados_varejo):
    r = client.get("/varejo/vendas/serie",
                   params={"agrupamento": "dia", "loja_id": 2, "inicio": "2014-01-01", "fim": "2014-01-31"})
    assert r.status_code == 200
    assert len(r.json()) == 31


def test_serie_agrupamento_invalido(client, dados_varejo):
    assert client.get("/varejo/vendas/serie", params={"agrupamento": "semana"}).status_code == 422


@pytest.mark.parametrize("rota", ["por-tipo-loja", "por-sortimento", "por-promocao", "por-feriado", "por-dia-semana"])
def test_quebras(client, dados_varejo, rota):
    r = client.get(f"/varejo/vendas/{rota}")
    assert r.status_code == 200
    itens = r.json()
    assert itens and all(i["vendas_totais"] >= 0 for i in itens)


def test_promocao_aumenta_media(client, dados_varejo):
    itens = {i["categoria"]: i for i in client.get("/varejo/vendas/por-promocao").json()}
    assert itens["true"]["media_por_dia_loja"] > itens["false"]["media_por_dia_loja"]


def test_lojas_e_ranking(client, dados_varejo):
    assert len(client.get("/varejo/lojas").json()) == 4
    assert client.get("/varejo/lojas/1").json()["tipo_loja"] == "c"
    assert client.get("/varejo/lojas/999").status_code == 404
    ranking = client.get("/varejo/lojas/ranking", params={"limite": 2}).json()
    assert [r["loja_id"] for r in ranking] == [4, 3]


def test_status_sem_modelo(client, dados_varejo, pasta_modelo_vazia):
    dados = client.get("/previsoes/status").json()
    assert dados["dados_importados"] is True
    assert dados["planejamento_disponivel"] is True
    assert dados["modelo_treinado"] is False
    assert "app.ml.train" in dados["mensagem"]


def test_previsao_sem_modelo_retorna_503(client, dados_varejo, pasta_modelo_vazia):
    for rota in ("/previsoes/proximo-mes", "/previsoes/avaliacao", "/previsoes/historico-vs-previsao"):
        r = client.get(rota)
        assert r.status_code == 503
        assert "não foi treinado" in r.json()["detail"]


def test_previsao_com_modelo(client, dados_varejo, pasta_modelo_treinado, monkeypatch):
    monkeypatch.setattr(settings, "model_dir", str(pasta_modelo_treinado))

    status = client.get("/previsoes/status").json()
    assert status["modelo_treinado"] is True

    r = client.get("/previsoes/proximo-mes")
    assert r.status_code == 200, r.text
    dados = r.json()
    assert dados["mes_referencia"] == "2014-04"
    assert len(dados["diario"]) == 30
    assert dados["valor_previsto"] == pytest.approx(sum(d["vendas_previstas"] for d in dados["diario"]))
    assert dados["ultimo_mes_real"]["periodo"] == "2014-03"
    # test.csv sintético cobre 45 dias -> abril inteiro vem do planejamento
    assert dados["fonte_calendario"] == "planejamento"
    assert dados["metricas"]["mae"] >= 0

    comparacao = client.get("/previsoes/historico-vs-previsao", params={"dias": 60}).json()
    assert comparacao["mes_previsto"] == "2014-04"
    assert comparacao["mensal"][-1]["periodo"] == "2014-04"
    assert comparacao["mensal"][-1]["previsto"] == pytest.approx(dados["valor_previsto"])

    avaliacao = client.get("/previsoes/avaliacao").json()
    assert avaliacao["metricas_lstm"]["dias_avaliados"] == len(avaliacao["diario"])
    assert avaliacao["periodo_teste"]["inicio"] == "2014-02-01"
