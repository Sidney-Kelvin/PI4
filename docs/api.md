# API — FinanTrack

Documentação interativa (Swagger): **http://localhost:8080/docs**

## Operação (módulos herdados do PI3)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/dashboard/` | Faturamento, despesas, saldo, vendas e produtos |
| GET, POST | `/produtos/` | Listar / criar produto |
| GET, PUT, DELETE | `/produtos/{id}` | Obter / atualizar / excluir (409 se houver vendas) |
| GET, POST | `/vendas/` | Listar / registrar venda (baixa de estoque na mesma transação) |
| GET | `/vendas/{id}` | Obter venda |
| GET, POST | `/despesas/` | Listar / criar despesa |
| GET, PUT, DELETE | `/despesas/{id}` | Obter / atualizar / excluir |
| GET | `/external/cep/{cep}` | Consulta ViaCEP |
| GET | `/external/cnpj/{cnpj}` | Consulta BrasilAPI |

## Varejo (histórico Rossmann)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/varejo/resumo` | Faturamento histórico, período, lojas, último mês e variação |
| GET | `/varejo/vendas/serie?agrupamento=dia\|mes\|ano&loja_id=&inicio=&fim=` | Série temporal de vendas |
| GET | `/varejo/vendas/por-tipo-loja` | Vendas por tipo de loja |
| GET | `/varejo/vendas/por-sortimento` | Vendas por sortimento |
| GET | `/varejo/vendas/por-promocao` | Vendas com e sem promoção |
| GET | `/varejo/vendas/por-feriado` | Vendas por feriado estadual e escolar |
| GET | `/varejo/vendas/por-dia-semana` | Vendas por dia da semana |
| GET | `/varejo/lojas` · `/varejo/lojas/{id}` | Lojas |
| GET | `/varejo/lojas/ranking?limite=10&ordem=maiores` | Ranking de faturamento |

## Previsões (LSTM)

| Método | Rota | Descrição |
|---|---|---|
| GET | `/previsoes/status` | Dados importados? Modelo treinado? (sempre 200) |
| GET | `/previsoes/proximo-mes` | Valor previsto do próximo mês, período, variação, métricas e previsão diária |
| GET | `/previsoes/historico-vs-previsao?dias=120` | Séries diária e mensal (real + previsto) para gráficos |
| GET | `/previsoes/avaliacao` | Métricas, real × previsto no teste, arquitetura e curva de perda |

## Saúde

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Status da API |
| GET | `/health/db` | Conexão com o PostgreSQL |

## Erros

Formato: `{"detail": "<mensagem em português>"}`

| Código | Situação |
|---|---|
| 404 | Dados históricos não importados / registro inexistente |
| 409 | Conflito (ex.: excluir produto com vendas) |
| 422 | Parâmetros inválidos / estoque insuficiente |
| 503 | Modelo não treinado ou banco de dados indisponível |
