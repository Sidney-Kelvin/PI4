# Modelo LSTM — previsão de vendas

Documentação técnica do pipeline de dados e do modelo de Deep Learning do FinanTrack.
Código em `backend/app/ml/`.

## 1. Pipeline de dados

| Etapa | Onde | O que faz |
|---|---|---|
| Verificação | `data_preparation.verificar_arquivos` | confere `train.csv` e `store.csv` (obrigatórios) e `test.csv` (recomendado) em `data/raw/` |
| Carga e limpeza | `data_preparation.carregar_*` | remove linhas sem loja/data e duplicatas (loja, data); vendas negativas → 0; converte datas |
| Valores ausentes | idem | `StateHoliday` (0 numérico e "0" texto misturados) → `0/a/b/c`; dados de concorrência e Promo2 ausentes → `NULL` ("não se aplica"); `Open` ausente no test.csv (11 linhas) → aberta |
| Integração | `integrar_vendas_lojas` | train × store: valida integridade referencial e cria `ano`, `mes`, `dia_do_ano` |
| Banco | `ingest.py` | grava `lojas`, `vendas_historicas` e `planejamento_lojas` no PostgreSQL via `COPY` (~30 s) |
| Série para o modelo | `features.py` | agrega por dia a partir do banco; salva `data/processed/serie_diaria.csv` no treino |

## 2. Série modelada

Série **diária da rede inteira**. O alvo é a **venda média por loja aberta**:

```
alvo(dia)            = soma das vendas do dia / lojas abertas no dia
venda total prevista = alvo previsto × lojas abertas no dia
```

* Separa o comportamento de venda do número de lojas abertas (aos domingos abrem em média 27 lojas; nos dias úteis, ~1.100).
* É robusto a uma característica do dataset: entre 01/07/2014 e 31/12/2014, 180 lojas não aparecem no train.csv.

## 3. Features (por dia)

| Feature | Justificativa |
|---|---|
| Venda média por loja aberta | a própria série, somente de dias **anteriores** ao previsto |
| Dia da semana (one-hot) | padrão semanal forte |
| Mês e dia do ano (seno/cosseno) | sazonalidade anual, de forma cíclica |
| Dia do mês | efeito de início/fim de mês |
| % lojas abertas | fechamentos e feriados |
| % lojas em promoção | promoção eleva a venda média em ~39% |
| % lojas em feriado estadual / escolar | efeitos de calendário |

As features do dia previsto são conhecidas antecipadamente (calendário, promoções planejadas, abertura de lojas —
exatamente o que o `test.csv` fornece para o período futuro).

**`Customers` não é usado**: o número de clientes só é conhecido depois que o dia acontece; usá-lo seria
vazamento de dados (*data leakage*).

## 4. Arquitetura

```
janela de 28 dias × 17 valores ─► LSTM (2 camadas, 64 unidades, dropout 0,2) ─► estado final (64)
                                                                                    │ concatena
                                               features do dia previsto (16) ──────┘
                                                                                    ▼
                                                        Densa(32, ReLU) ─► Densa(1) ─► alvo do dia
```

57.153 parâmetros · Adam (lr 0,001) · perda MSE · lote 32 · até 150 épocas com parada antecipada
(paciência 15, restaura a melhor época) · semente 42 (treino reprodutível).

## 5. Divisão temporal e prevenção de vazamento

```
2013-01-01 ── treino ──► 2015-03-31 │ 2015-04 a 2015-05: validação │ 2015-06 a 2015-07: teste
```

* Sem `train_test_split` aleatório: o teste é sempre posterior ao treino.
* O escalonador (z-score) do alvo é ajustado **somente com o treino**.
* A validação serve apenas para a parada antecipada; o teste não influencia o treino.

## 6. Previsão do próximo mês

Previsão **recursiva**: o modelo prevê o dia 1 a partir dos 28 dias reais anteriores; a previsão entra na janela para
prever o dia 2, e assim por diante até o fim do mês. O total do mês é a soma dos dias. O calendário do mês previsto
vem de `planejamento_lojas` (test.csv, 856 lojas, frações extrapoladas para 1.115); sem ele, é estimado pelas
últimas 4 semanas (`fonte_calendario = "estimado"`). O resultado é gravado em `previsoes_vendas`.

## 7. Métricas

Calculadas sobre as vendas totais diárias da rede no período de teste, com previsão recursiva mês a mês:

* **MAE** — erro absoluto médio por dia;
* **RMSE** — raiz do erro quadrático médio (penaliza erros grandes);
* **MAPE** — erro percentual absoluto médio. Dias com venda real igual a zero são excluídos (divisão por zero) e a
  quantidade excluída é informada.

Comparação com um **baseline sazonal ingênuo** (média do mesmo dia da semana nas 4 semanas anteriores).

Execução de referência (dataset completo, semente 42, CPU):

| Modelo | MAE | RMSE | MAPE |
|---|---:|---:|---:|
| **LSTM** | **269.686,30** | **377.593,92** | **4,24%** |
| Baseline sazonal | 1.105.820,95 | 1.392.177,52 | 14,84% |

| Mês de teste | Real | Previsto (LSTM) | Erro do total |
|---|---:|---:|---:|
| jun/2015 | 207.363.373,00 | 205.457.268,48 | −0,92% |
| jul/2015 | 212.322.616,00 | 214.237.340,88 | +0,90% |

Previsão de agosto/2015: **196.680.398,43** (−7,37% vs. julho), coerente com a sazonalidade histórica
(ago/jul: −5,2% em 2013 e −5,9% em 2014). O dashboard exibe sempre os valores do modelo treinado localmente.

## 8. Artefatos

```
models/sales_lstm/          (não versionado; gerado por python -m app.ml.train)
├── model.pt                pesos PyTorch (~230 KB)
├── metadata.json           versão, hiperparâmetros, features, escalonador, divisão temporal
├── metrics.json            métricas do teste (LSTM e baseline)
├── evaluation.json         real × previsto por dia do teste
└── history.json            perda de treino/validação por época
```

A API carrega o modelo sob demanda e recarrega quando um novo treino altera `metadata.json`. Sem modelo, os
endpoints de previsão respondem **HTTP 503** com a instrução de treino.

## 9. Limitações

* Prevê a rede como um todo, não cada loja; não usa variáveis externas (economia, clima, concorrência).
* Histórico de ~2,5 anos: poucos ciclos anuais.
* A previsão recursiva acumula erro ao longo do mês; o teste cobre 2 meses.
* O calendário do mês previsto vem de 856 das 1.115 lojas (extrapolado) ou é estimado.
* O modelo final é treinado até 31/03/2015, sem reincorporar validação/teste.
* Os dados terminam em 31/07/2015: o "próximo mês" é agosto/2015.
* A moeda de `Sales` não é especificada pela fonte; os valores não são convertidos para R$.
