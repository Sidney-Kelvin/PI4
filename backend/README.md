# Backend — FinanTrack (PI4)

API REST em **FastAPI (Python 3.12)** com PostgreSQL, Alembic e um módulo de Deep Learning (PyTorch/LSTM)
para previsão de vendas. Visão geral, dataset e resultados: veja o [README principal](../README.md).

## Tecnologias

| Tecnologia | Versão | Função |
|---|---|---|
| FastAPI | 0.111 | Framework web REST + Swagger |
| SQLAlchemy | 2.0 | ORM |
| Alembic | 1.13 | Migrations (única fonte da estrutura do banco) |
| Pydantic | 2.7 | Validação e serialização |
| pandas / NumPy | 2.2 / 2.1 | Preparação dos dados |
| PyTorch (CPU) | 2.5.1 | Modelo LSTM |
| PostgreSQL | 16 | Banco de dados (SQLite apenas nos testes) |

## Arquitetura

```
Controller (rotas HTTP) → Service (regras) → Repository (consultas) → Model (SQLAlchemy) → PostgreSQL
                             └→ app/ml/predictor (inferência com o modelo salvo em MODEL_DIR)
```

```
app/
├── main.py            registra rotas, CORS e tratamento de banco indisponível (503)
├── core/              config.py (variáveis de ambiente) · database.py
├── controllers/       dashboard, produto, venda, despesa, external, varejo, previsao
├── services/          regras de negócio (inclui varejo_service e previsao_service)
├── repositories/      acesso ao banco (varejo_repository: agregações por dia/mês/ano, loja, promo, feriado)
├── models/            produto, venda, despesa, varejo (lojas, vendas_historicas, planejamento_lojas, previsoes_vendas)
├── schemas/           Pydantic
└── ml/                data_preparation · ingest · features · model · train · metrics · artifacts · predictor
alembic/versions/      0001 (PI3) · 0002 (Float → NUMERIC) · 0003 (varejo e previsões)
tests/                 pytest
```

## Variáveis de ambiente

| Variável | Padrão (fora do Docker) | No Docker Compose |
|---|---|---|
| `DATABASE_URL` | `postgresql://finantrack:finantrack@localhost:5432/finantrack` | aponta para o serviço `db` |
| `DATA_DIR` | `../data` | `/data` (bind de `./data`) |
| `MODEL_DIR` | `../models/sales_lstm` | `/models/sales_lstm` (bind de `./models`) |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | — |
| `SECRET_KEY`, `ENVIRONMENT` | valores de desenvolvimento | via `.env` da raiz |

## Comandos (dentro do container)

```bash
docker compose exec backend alembic upgrade head               # migrations (também automáticas no start)
docker compose exec backend python -m app.ml.ingest --verificar # confere data/raw
docker compose exec backend python -m app.ml.ingest            # importa o Rossmann (--substituir para refazer)
docker compose exec backend python -m app.ml.train             # treina e avalia a LSTM
docker compose exec backend pytest tests/ -q                   # testes
```

## Executar sem Docker (opcional)

Requer Python 3.12 e um PostgreSQL acessível.

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate                 # Windows  (Linux/macOS: source .venv/bin/activate)
pip install --index-url https://download.pytorch.org/whl/cpu torch==2.5.1
pip install -r requirements.txt
copy .env.example .env                 # ajuste DATABASE_URL
alembic upgrade head
uvicorn app.main:app --reload --port 8080
```

## Endpoints

Documentação completa e interativa em **http://localhost:8080/docs**. Resumo:

* PI3 (mantidos): `/dashboard/`, `/produtos/`, `/vendas/`, `/despesas/`, `/external/cep/{cep}`, `/external/cnpj/{cnpj}`
* Varejo: `/varejo/resumo`, `/varejo/vendas/serie`, `/varejo/vendas/por-{tipo-loja|sortimento|promocao|feriado|dia-semana}`,
  `/varejo/lojas`, `/varejo/lojas/{id}`, `/varejo/lojas/ranking`
* Previsões: `/previsoes/status`, `/previsoes/proximo-mes`, `/previsoes/historico-vs-previsao`, `/previsoes/avaliacao`
* Saúde: `/`, `/health/db`

## Mudanças em relação ao PI3

* `Base.metadata.create_all()` removido: a estrutura vem apenas do Alembic.
* Valores monetários em `NUMERIC(12,2)` (migration 0002, sem perda de dados); a API continua devolvendo números JSON.
* Registro de venda e baixa de estoque na **mesma transação** (antes eram dois commits).
* Excluir produto com vendas retorna **409** com mensagem clara (antes: erro 500 de chave estrangeira).
* Falha de conexão com o banco retorna **503** com mensagem em português.
