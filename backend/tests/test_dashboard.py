def test_dashboard(client):
    response = client.get("/dashboard/")
    assert response.status_code == 200
    data = response.json()
    assert "faturamento_total" in data
    assert "despesas_totais" in data
    assert "saldo" in data
    assert "total_vendas" in data
    assert "produtos_cadastrados" in data


def test_dashboard_saldo(client):
    antes = client.get("/dashboard/").json()
    client.post("/despesas/", json={"descricao": "Energia", "valor": 100.25})
    depois = client.get("/dashboard/").json()
    assert round(depois["despesas_totais"] - antes["despesas_totais"], 2) == 100.25
    assert round(depois["faturamento_total"] - depois["despesas_totais"], 2) == round(depois["saldo"], 2)
