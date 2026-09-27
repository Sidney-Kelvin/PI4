# PI4 — FinanTrack

Sistema web de **acompanhamento financeiro de uma operação de varejo**, com dados históricos reais do dataset
**Rossmann Store Sales** e um modelo local de **Deep Learning (LSTM)** para **previsão de vendas do próximo mês**.

Projeto acadêmico (Projeto Integrador 4), evolução do PI3 (gestão financeira e de estoque).

## Objetivo

Demonstrar de ponta a ponta:

* banco **PostgreSQL** com estrutura versionada por migrations (Alembic);
* **dados reais de varejo** (1.115 lojas, ~1 milhão de registros diários, 2013–2015);
* **API REST** em FastAPI com Swagger;
* **pipeline de dados** reproduzível (CSV → limpeza → PostgreSQL → série temporal);
* **modelo LSTM** treinado localmente, com divisão temporal e métricas reais (MAE, RMSE, MAPE);
* **dashboard** React com indicadores financeiros, histórico de vendas e histórico × previsão.

Os módulos do PI3 (produtos, vendas, despesas e consulta de CEP/CNPJ) foram mantidos.

## Tecnologias

| Camada | Tecnologia |
|---|---|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS, Recharts |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2, Alembic, Pydantic 2 |
| Dados / ML | pandas, NumPy, PyTorch (CPU) |
| Banco | PostgreSQL 16 |
| Infraestrutura | Docker Desktop + Docker Compose |
| CI | GitHub Actions (testes, lint e build) |

## Arquitetura

```
Navegador ─► Frontend React (nginx, :3000) ─► /api/* (proxy) ─► Backend FastAPI (:8080)
                                                                   Controller ─► Service ─► Repository ─► PostgreSQL
                                                                                   └─► modelo LSTM (models/sales_lstm)

Scripts no container do backend:
  python -m app.ml.ingest   data/raw/*.csv ─► limpeza ─► PostgreSQL
  python -m app.ml.train    PostgreSQL ─► série diária ─► treino e avaliação ─► models/sales_lstm/
```

Inicialização pelo Docker Compose: PostgreSQL → *healthcheck* → `alembic upgrade head` → FastAPI → frontend.

## Dataset

**Rossmann Store Sales** (Kaggle) — vendas diárias de 1.115 lojas, de 01/01/2013 a 31/07/2015.

* Fonte oficial: https://www.kaggle.com/c/rossmann-store-sales
* Dados: https://www.kaggle.com/c/rossmann-store-sales/data
* Regras de uso: https://www.kaggle.com/c/rossmann-store-sales/rules

O dataset está sujeito às regras da competição no Kaggle e é usado aqui **apenas para fins acadêmicos**.
**Os arquivos do dataset não fazem parte deste repositório** e devem ser baixados na fonte oficial.
Os valores de vendas são exibidos na unidade monetária original do dataset (não convertidos para R$).

## Como executar

### Pré-requisitos

* Windows 10/11 com [Docker Desktop](https://www.docker.com/products/docker-desktop/) em execução
* Git
* Conta no Kaggle (para baixar o dataset)

Não é necessário instalar Python, Node.js ou PostgreSQL: tudo roda nos containers.

### 1. Clonar

```bash
git clone https://github.com/Sidney-Kelvin/PI4.git
cd PI4
```

### 2. Obter os dados

1. Faça login no Kaggle e aceite as regras em https://www.kaggle.com/c/rossmann-store-sales/rules.
2. Baixe `train.csv`, `store.csv` e `test.csv` em https://www.kaggle.com/c/rossmann-store-sales/data.
3. Coloque os arquivos em `data/raw/`.

Detalhes em [`data/README.md`](data/README.md).

### 3. Subir o sistema

```bash
docker compose up -d --build
docker compose ps          # db e backend "healthy", frontend "Up"
```

As migrations são aplicadas automaticamente. Opcional: copie `.env.example` para `.env` para alterar senha e portas.

### 4. Importar os dados e treinar o modelo

```bash
docker compose exec backend python -m app.ml.ingest     # ~30 s
docker compose exec backend python -m app.ml.train      # ~15–60 s em CPU
```

### 5. Acessar

| Serviço | Endereço |
|---|---|
| Frontend (dashboard) | http://localhost:3000 |
| Swagger (API) | http://localhost:8080/docs |

Sem dados importados ou sem modelo treinado, o dashboard indica o comando a executar.

### Comandos úteis

```bash
docker compose logs backend --tail 50                          # logs
docker compose exec backend pytest tests/ -q                   # testes do backend
docker compose exec backend python -m app.ml.ingest --substituir  # reimportar dados
docker compose down                                            # parar (mantém o banco)
docker compose down -v                                         # parar e apagar o banco
```

## Modelo LSTM

* **Alvo:** venda média por loja aberta da rede, por dia (a venda total é esse valor × lojas abertas).
* **Entrada:** janela dos últimos 28 dias + dia da semana, sazonalidade (mês/dia do ano), dia do mês e percentual
  de lojas abertas, em promoção e em feriado. `Customers` não é usado, pois causaria vazamento de dados.
* **Rede:** LSTM (2 camadas, 64 unidades) + camadas densas; PyTorch, CPU, semente fixa.
* **Validação:** divisão temporal — treino até mar/2015, validação abr–mai/2015, teste jun–jul/2015;
  escalonador ajustado só no treino.
* **Previsão:** recursiva, dia a dia, somada para obter o total do próximo mês (agosto/2015).

Resultado no período de teste (dados não usados no treino):

| Modelo | MAE | RMSE | MAPE |
|---|---:|---:|---:|
| **LSTM** | 269.686,30 | 377.593,92 | **4,24%** |
| Baseline sazonal | 1.105.820,95 | 1.392.177,52 | 14,84% |

Detalhes, justificativas e limitações: [`docs/modelo-lstm.md`](docs/modelo-lstm.md).

## Dashboard

| Página | Conteúdo |
|---|---|
| Dashboard | faturamento, despesas e saldo; histórico de vendas; previsão do próximo mês e variação; MAE, RMSE e MAPE; gráfico histórico × previsão |
| Histórico de Varejo | vendas por dia/mês/ano, loja e período; por dia da semana, promoção, feriado, tipo de loja e sortimento; ranking de lojas |
| Previsão (LSTM) | previsão diária, real × previsto no teste, comparação com baseline, detalhes do modelo e curva de aprendizado |
| Vendas, Despesas, Estoque, Empresa | módulos do PI3 |

Endpoints da API: [`docs/api.md`](docs/api.md).

## Estrutura do projeto

```
PI4/
├── backend/
│   ├── app/
│   │   ├── controllers/    rotas HTTP
│   │   ├── services/       regras de negócio
│   │   ├── repositories/   acesso ao banco
│   │   ├── models/         modelos SQLAlchemy
│   │   ├── schemas/        schemas Pydantic
│   │   ├── core/           configuração e conexão
│   │   └── ml/             pipeline de dados e modelo LSTM
│   ├── alembic/            migrations
│   └── tests/              testes (pytest)
├── frontend/
│   └── src/                api, components, hooks, pages, types, utils
├── data/                   raw/ (dataset, não versionado) e processed/
├── models/                 modelo treinado (não versionado)
├── docs/                   documentação técnica
├── .github/workflows/      CI
├── docker-compose.yml
└── .env.example
```

## Licença e créditos

Projeto acadêmico. Dataset © Rossmann / Kaggle, sujeito às regras da competição
[Rossmann Store Sales](https://www.kaggle.com/c/rossmann-store-sales).
