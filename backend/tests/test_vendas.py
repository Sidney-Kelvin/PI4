import pytest


@pytest.fixture()
def produto_id(client):
    response = client.post("/produtos/", json={
        "nome": "Produto Teste Venda",
        "preco": 10.00,
        "quantidade": 20,
    })
    return response.json()["id"]


def test_registrar_venda(client, produto_id):
    response = client.post("/vendas/", json={
        "produto_id": produto_id,
        "quantidade": 2,
        "cliente": "João Silva",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["total"] == 20.00


def test_venda_reduz_estoque(client, produto_id):
    estoque_antes = client.get(f"/produtos/{produto_id}").json()["quantidade"]
    client.post("/vendas/", json={"produto_id": produto_id, "quantidade": 3})
    estoque_depois = client.get(f"/produtos/{produto_id}").json()["quantidade"]
    assert estoque_depois == estoque_antes - 3


def test_venda_estoque_insuficiente(client, produto_id):
    response = client.post("/vendas/", json={"produto_id": produto_id, "quantidade": 9999})
    assert response.status_code == 422


def test_listar_vendas(client):
    response = client.get("/vendas/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_produto_com_venda_nao_pode_ser_excluido(client, produto_id):
    client.post("/vendas/", json={"produto_id": produto_id, "quantidade": 1})
    response = client.delete(f"/produtos/{produto_id}")
    assert response.status_code == 409


def test_valores_monetarios_sem_erro_de_ponto_flutuante(client):
    produto = client.post("/produtos/", json={"nome": "Item", "preco": 0.10, "quantidade": 10}).json()
    venda = client.post("/vendas/", json={"produto_id": produto["id"], "quantidade": 3}).json()
    # Com float puro, 3 * 0.1 = 0.30000000000000004
    assert venda["total"] == 0.30
